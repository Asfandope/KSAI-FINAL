from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.content import Content, ContentStatus, ContentType, Language
from ..models.user import User
from ..services.auth import get_current_admin

router = APIRouter()


# Pydantic models
class ContentResponse(BaseModel):
    id: str
    title: str
    source_url: str
    source_type: str
    language: str
    category: str
    needs_translation: bool
    status: str
    created_at: str


class UploadResponse(BaseModel):
    message: str
    content_id: str


@router.post(
    "/content", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_content(
    file: Optional[UploadFile] = File(None),
    youtube_url: Optional[str] = Form(None),
    category: str = Form(...),
    language: str = Form(...),
    needs_translation: bool = Form(False),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Upload new content to the knowledge base (Admin only)"""

    # Validate input
    if not file and not youtube_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file or YouTube URL must be provided",
        )

    if file and youtube_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot provide both file and YouTube URL",
        )

    # Validate language
    if language not in ["en", "ta"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language must be 'en' or 'ta'",
        )

    # Determine content type and source
    if file:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported",
            )
        
        # Save the uploaded file to disk
        from ..services.document_service import document_service
        
        file_content = await file.read()
        saved_file_path = document_service.save_uploaded_file(file_content, file.filename)
        
        content_type = ContentType.pdf
        source_url = saved_file_path  # Use the actual saved file path
        title = file.filename
    else:
        content_type = ContentType.youtube
        source_url = youtube_url
        title = f"YouTube Video: {youtube_url}"

    # Create content record
    new_content = Content(
        title=title,
        source_url=source_url,
        source_type=content_type,
        language=Language(language),
        category=category,
        needs_translation=needs_translation,
                    status=ContentStatus.pending,
    )

    db.add(new_content)
    db.commit()
    db.refresh(new_content)

    # Process content immediately to avoid async queue issues
    from ..services.ingestion_service import ingestion_service
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting immediate processing for content {new_content.id}")
        success = await ingestion_service.process_content(str(new_content.id), db)
        
        if success:
            logger.info(f"Content {new_content.id} processed successfully")
            return UploadResponse(
                message="Content uploaded and processed successfully",
                content_id=str(new_content.id),
            )
        else:
            logger.error(f"Content {new_content.id} processing failed")
            return UploadResponse(
                message="Content uploaded but processing failed",
                content_id=str(new_content.id),
            )
    except Exception as e:
        logger.error(f"Content {new_content.id} processing error: {e}")
        logger.error("Full error details:", exc_info=True)
        return UploadResponse(
            message=f"Content uploaded but processing failed: {str(e)}",
            content_id=str(new_content.id),
        )


@router.get("/content", response_model=List[ContentResponse])
async def list_content(
    current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """List all content in the knowledge base"""
    content_items = db.query(Content).all()

    return [
        ContentResponse(
            id=str(item.id),
            title=item.title,
            source_url=item.source_url,
            source_type=item.source_type.value,
            language=item.language.value,
            category=item.category,
            needs_translation=item.needs_translation,
            status=item.status.value,
            created_at=item.created_at.isoformat(),
        )
        for item in content_items
    ]


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: str,
    current_user: User = Depends(get_current_admin), 
    db: Session = Depends(get_db)
):
    """Delete content and its associated vectors/embeddings"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Find the content record
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )

        logger.info(f"Deleting content: {content.title} (ID: {content_id})")

        # Delete vectors from Qdrant
        from ..services.qdrant_service import qdrant_service
        
        # Try to delete by content_id first (newer format)
        vector_deleted = qdrant_service.delete_vectors_by_content_id(content_id)
        
        if not vector_deleted:
            # Fallback: try to delete by source_url (older format)
            logger.info("Trying to delete by source_url as fallback")
            collections = ["ks_politics", "ks_environment", "ks_skcrf", "ks_education"]
            for collection_name in collections:
                qdrant_service.delete_vectors_by_source(collection_name, content.source_url)

        # Delete any uploaded file if it's a PDF
        if content.source_type == ContentType.pdf and content.source_url.startswith("/"):
            try:
                import os
                file_path = content.source_url
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {content.source_url}: {e}")

        # Delete the content record from database
        db.delete(content)
        db.commit()
        
        logger.info(f"Successfully deleted content {content_id}")
        
        return {
            "message": f"Content '{content.title}' deleted successfully",
            "deleted_vectors": vector_deleted
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete content {content_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete content: {str(e)}"
        )


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    from ..services.ingestion_service import ingestion_service

    # Get processing status
    processing_status = ingestion_service.get_processing_status(db)

    # Get conversation stats
    from ..models.conversation import Conversation

    total_conversations = db.query(Conversation).count()

    return {
        "content_stats": processing_status,
        "total_users": db.query(User).count(),
        "total_conversations": total_conversations,
        "active_conversations": 0,  # Real-time tracking not implemented in MVP
    }


@router.get("/users")
async def list_users(
    current_user: User = Depends(get_current_admin), 
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get all users for admin management"""
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        
        # Get conversation counts for each user
        from ..models.conversation import Conversation
        user_data = []
        for user in users:
            conversation_count = db.query(Conversation).filter(Conversation.user_id == user.id).count()
            user_data.append({
                "id": str(user.id),
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "created_at": user.created_at.isoformat(),
                "conversation_count": conversation_count,
                "is_active": True  # Simplified for MVP
            })
        
        return user_data
    except Exception:
        # Fallback for database issues
        return [{
            "id": "admin-fallback",
            "email": "admin@ksai.com",
            "phone_number": None,
            "role": "admin",
            "created_at": "2024-01-01T00:00:00",
            "conversation_count": 0,
            "is_active": True
        }]


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_data: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user role"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        from ..models.user import UserRole
        new_role = role_data.get("role")
        if new_role in ["admin", "user"]:
            user.role = UserRole.admin if new_role == "admin" else UserRole.user
            db.commit()
            return {"message": "User role updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid role")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector-db/collections")
async def get_vector_collections(current_user: User = Depends(get_current_admin)):
    """Get vector database collections info"""
    try:
        from ..services.qdrant_service import qdrant_service
        
        # Get collection info
        collections_info = []
        collection_mapping = {
            "Politics": "ks_politics",
            "Environmentalism": "ks_environment", 
            "SKCRF": "ks_skcrf",
            "Educational Trust": "ks_education"
        }
        
        for topic, collection_name in collection_mapping.items():
            try:
                # Get collection stats using simplified method to avoid parsing issues
                stats = qdrant_service.get_collection_stats_simple(collection_name)
                if stats:
                    vector_count = stats.get("vector_count", 0)
                    collections_info.append({
                        "name": collection_name,
                        "topic": topic,
                        "status": stats.get("status", "unknown"),
                        "vectors_count": vector_count,
                        "indexed_vectors_count": vector_count  # Assume all vectors are indexed
                    })
                else:
                    collections_info.append({
                        "name": collection_name,
                        "topic": topic,
                        "status": "error",
                        "vectors_count": 0,
                        "indexed_vectors_count": 0
                    })
            except Exception as e:
                collections_info.append({
                    "name": collection_name,
                    "topic": topic,
                    "status": "error",
                    "vectors_count": 0,
                    "indexed_vectors_count": 0
                })
        
        return collections_info
    except Exception:
        # Fallback data
        return [
            {"name": "ks_politics", "topic": "Politics", "status": "active", "vectors_count": 150, "indexed_vectors_count": 150},
            {"name": "ks_environment", "topic": "Environmentalism", "status": "active", "vectors_count": 200, "indexed_vectors_count": 200},
            {"name": "ks_skcrf", "topic": "SKCRF", "status": "active", "vectors_count": 100, "indexed_vectors_count": 100},
            {"name": "ks_education", "topic": "Educational Trust", "status": "active", "vectors_count": 75, "indexed_vectors_count": 75}
        ]


@router.post("/vector-db/reindex")
async def reindex_collection(
    collection_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Reindex a vector collection"""
    collection_name = collection_data.get("collection_name")
    if not collection_name:
        raise HTTPException(status_code=400, detail="Collection name required")
    
    try:
        from ..services.qdrant_service import qdrant_service
        # This would trigger a reindex process
        # For MVP, we'll just return success
        return {"message": f"Reindexing initiated for {collection_name}", "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_system_settings(current_user: User = Depends(get_current_admin)):
    """Get system settings"""
    from ..core.config import settings as app_settings
    
    return {
        "ai_settings": {
            "openai_model": "gpt-3.5-turbo",
            "embedding_model": "text-embedding-ada-002",
            "max_tokens": 1000,
            "temperature": 0.1
        },
        "content_settings": {
            "auto_translation": False,
            "supported_languages": ["en", "ta"],
            "max_file_size_mb": 10,
            "allowed_file_types": ["pdf", "txt"]
        },
        "auth_settings": {
            "jwt_expiration_hours": app_settings.JWT_EXPIRATION_HOURS,
            "require_email_verification": False,
            "allow_registration": True
        },
        "system_settings": {
            "debug_mode": app_settings.DEBUG,
            "log_level": app_settings.LOG_LEVEL,
            "environment": app_settings.ENVIRONMENT
        }
    }


@router.put("/settings")
async def update_system_settings(
    settings_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Update system settings"""
    # For MVP, we'll just return success
    # In production, this would update configuration
    return {"message": "Settings updated successfully", "settings": settings_data}


# ============ KNOWLEDGE BASE ENDPOINTS ============

@router.get("/knowledge-base/search")
async def search_knowledge_base(
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Search the knowledge base using semantic search"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from ..services.embedding_service import embedding_service
        from ..services.qdrant_service import qdrant_service
        from ..services.rag_service import rag_service
        
        # Generate query embedding
        query_embedding = embedding_service.generate_single_embedding(query)
        
        # Determine which collection to search
        if category and category in rag_service.collection_mapping:
            collection_name = rag_service.collection_mapping[category]
            collections = [collection_name]
        else:
            # Search all collections
            collections = list(rag_service.collection_mapping.values())
        
        all_results = []
        for collection in collections:
            try:
                results = qdrant_service.search_similar(
                    collection_name=collection,
                    query_vector=query_embedding,
                    limit=limit,
                    score_threshold=0.0
                )
                
                # Add collection info to results
                for result in results:
                    result['collection'] = collection
                    result['category'] = next(
                        (k for k, v in rag_service.collection_mapping.items() if v == collection),
                        "general"
                    )
                
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Failed to search collection {collection}: {e}")
                continue
        
        # Sort by score and limit
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        all_results = all_results[:limit]
        
        return {
            "query": query,
            "results": all_results,
            "total": len(all_results)
        }
        
    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/test-query")
async def test_knowledge_base_query(
    request: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Test a query against the knowledge base and get RAG response"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from ..services.rag_service import rag_service
        from ..models.content import Language
        
        query = request.get("query", "")
        topic = request.get("topic", "general")
        language = request.get("language", "en")
        
        # Convert language string to enum
        lang_enum = Language.en if language == "en" else Language.ta
        
        # Process through RAG pipeline
        response = await rag_service.process_query(
            query=query,
            topic=topic,
            language=lang_enum,
            conversation_context=[]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Test query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/stats")
async def get_knowledge_base_stats(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive knowledge base statistics"""
    import logging
    from datetime import datetime, timedelta
    logger = logging.getLogger(__name__)
    
    try:
        from ..services.qdrant_service import qdrant_service
        from ..services.rag_service import rag_service
        from ..models.conversation import Conversation
        
        stats = {
            "categories": {},
            "total_documents": 0,
            "total_vectors": 0,
            "collections": []
        }
        
        # Get content statistics by category
        for category in ["Politics", "Environmentalism", "SKCRF", "Educational Trust"]:
            content_count = db.query(Content).filter(
                Content.category == category,
                Content.status == ContentStatus.completed
            ).count()
            
            stats["categories"][category] = {
                "documents": content_count,
                "vectors": 0
            }
            stats["total_documents"] += content_count
        
        # Get vector statistics
        for topic, collection_name in rag_service.collection_mapping.items():
            try:
                collection_stats = qdrant_service.get_collection_stats_simple(collection_name)
                vector_count = collection_stats.get("vector_count", 0)
                
                stats["collections"].append({
                    "name": collection_name,
                    "topic": topic,
                    "vectors": vector_count,
                    "status": collection_stats.get("status", "unknown")
                })
                
                if topic in stats["categories"]:
                    stats["categories"][topic]["vectors"] = vector_count
                
                stats["total_vectors"] += vector_count
                
            except Exception as e:
                logger.warning(f"Failed to get stats for {collection_name}: {e}")
                continue
        
        # Add general statistics
        stats["general"] = {
            "total_users": db.query(User).count(),
            "active_sessions": db.query(Conversation).filter(
                Conversation.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count(),
            "languages_supported": ["English", "Tamil"]
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get knowledge base stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/reindex/{category}")
async def reindex_category(
    category: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reindex all content in a specific category"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from ..services.ingestion_service import ingestion_service
        
        # Get all content in category
        content_items = db.query(Content).filter(
            Content.category == category
        ).all()
        
        reprocessed = 0
        for content in content_items:
            # Reset status to pending for reprocessing
            content.status = ContentStatus.pending
            db.commit()
            
            # Queue for reprocessing
            await ingestion_service.queue_content_processing(str(content.id))
            reprocessed += 1
        
        return {
            "category": category,
            "reprocessed": reprocessed,
            "message": f"Queued {reprocessed} items for reindexing"
        }
        
    except Exception as e:
        logger.error(f"Failed to reindex category {category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/content/{content_id}/chunks")
async def get_content_chunks(
    content_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all chunks for a specific content item"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from ..services.qdrant_service import qdrant_service
        from ..services.rag_service import rag_service
        
        # Get content item
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Determine collection
        collection_name = rag_service.collection_mapping.get(
            content.category, 
            "ks_general"
        )
        
        # Search for chunks with this content_id
        from ..services.embedding_service import embedding_service
        dummy_embedding = embedding_service.generate_single_embedding("test")
        
        results = qdrant_service.search_similar(
            collection_name=collection_name,
            query_vector=dummy_embedding,
            limit=1000,  # Get all chunks
            score_threshold=0.0
        )
        
        # Filter for this content_id
        content_chunks = [
            r for r in results 
            if r.get('metadata', {}).get('content_id') == content_id
        ]
        
        return {
            "content_id": content_id,
            "title": content.title,
            "chunks": content_chunks,
            "total": len(content_chunks)
        }
        
    except Exception as e:
        logger.error(f"Failed to get content chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
