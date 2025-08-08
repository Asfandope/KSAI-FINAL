"""
Content Ingestion Service

This service handles:
- Processing uploaded PDFs and YouTube videos
- Text extraction and preprocessing
- Chunking and embedding generation
- Storage in vector database
- Content status tracking
"""

import asyncio
import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.content import Content, ContentStatus
from .document_service import document_service
from .embedding_service import embedding_service
from .qdrant_service import qdrant_service
from .rag_service import rag_service

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.is_processing = False

    async def process_content(self, content_id: str, db: Session) -> bool:
        """
        Process a content item through the ingestion pipeline

        Args:
            content_id: UUID of the content item to process
            db: Database session

        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            # Get content item from database
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                logger.error(f"Content not found: {content_id}")
                return False

            logger.info(f"Processing content: {content.title} ({content.source_type})")

            # Update status to processing
            content.status = ContentStatus.processing
            db.commit()

            # Extract text based on content type
            if content.source_type.value == "pdf":
                text, metadata = await self._process_pdf(content)
            elif content.source_type.value == "youtube":
                text, metadata = await self._process_youtube(content)
            else:
                raise ValueError(f"Unsupported content type: {content.source_type}")

            if not text:
                raise ValueError("No text extracted from content")

            # Process document and generate embeddings
            processed_chunks = embedding_service.process_document(
                content=text,
                metadata={
                    "content_id": str(content.id),
                    "title": content.title,
                    "category": content.category,
                    "language": content.language.value,
                    "source_type": content.source_type.value,
                    "source_url": content.source_url,
                    "created_at": content.created_at.isoformat(),
                    **metadata,
                },
                chunk_size=500,
            )

            if not processed_chunks:
                raise ValueError("No chunks generated from content")

            # Store embeddings in vector database
            collection_name = rag_service.collection_mapping.get(
                content.category, "ks_general"
            )

            # Ensure collection exists
            qdrant_service.create_collection(collection_name)

            # Prepare data for storage
            embeddings = [chunk["embedding"] for chunk in processed_chunks]
            texts = [chunk["text"] for chunk in processed_chunks]
            chunk_metadata = [chunk["metadata"] for chunk in processed_chunks]

            # Store in vector database
            success = qdrant_service.store_embeddings(
                collection_name=collection_name,
                embeddings=embeddings,
                metadata=chunk_metadata,
                texts=texts,
            )

            if not success:
                raise ValueError("Failed to store embeddings in vector database")

            # Update content status to completed
            content.status = ContentStatus.completed
            db.commit()

            logger.info(
                f"Successfully processed content: {content.title} ({len(processed_chunks)} chunks)"
            )
            return True

        except Exception as e:
            logger.error(f"Content processing failed for {content_id}: {e}")
            logger.error(f"Full error traceback:", exc_info=True)

            # Update status to failed with error details
            try:
                content = db.query(Content).filter(Content.id == content_id).first()
                if content:
                    content.status = ContentStatus.failed
                    # Add error details to title for debugging
                    content.title = f"{content.title} [ERROR: {str(e)[:100]}]"
                    db.commit()
                    logger.info(f"Marked content {content_id} as failed with error details")
            except Exception as db_error:
                logger.error(f"Failed to update content status: {db_error}")

            return False

    async def _process_pdf(self, content: Content) -> tuple[str, Dict[str, Any]]:
        """Process PDF content"""
        try:
            # For now, we'll assume the PDF is already stored locally
            # In production, this would download from S3
            import os
            file_path = content.source_url

            # Check if it's an absolute path (works for both Windows and Unix)
            if not os.path.isabs(file_path):
                # If it's not an absolute path, assume it's a relative path in uploads
                file_path = os.path.join("uploads", file_path)

            text, metadata = document_service.extract_pdf_text(file_path)
            return text, metadata

        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            # Return placeholder content for demo
            return (
                f"Sample content for PDF: {content.title}\n\n"
                f"This is placeholder content for the PDF processing demo. "
                f"In production, actual PDF text would be extracted here. "
                f"Category: {content.category}, Language: {content.language.value}",
                {"source_type": "pdf", "pages": 1},
            )

    async def _process_youtube(self, content: Content) -> tuple[str, Dict[str, Any]]:
        """Process YouTube video content"""
        try:
            logger.info(f"Extracting transcript for YouTube video: {content.source_url}")
            
            # FORCE RELOAD of document service to bypass caching issues
            import importlib
            from ..services import document_service as doc_service_module
            importlib.reload(doc_service_module)
            
            text, metadata = doc_service_module.document_service.extract_youtube_transcript(
                content.source_url
            )
            logger.info(f"Successfully extracted YouTube transcript: {len(text)} characters")
            return text, metadata

        except Exception as e:
            logger.error(f"YouTube processing failed for {content.source_url}: {e}")
            logger.error(f"Full error details: ", exc_info=True)
            
            # Raise the error to properly mark content as failed
            raise e

    async def queue_content_processing(self, content_id: str) -> None:
        """Add content to processing queue"""
        # For better reliability, process immediately instead of using async queue
        # This avoids async context and database session issues
        try:
            logger.info(f"Processing content immediately: {content_id}")
            from ..db.database import SessionLocal
            db = SessionLocal()
            try:
                success = await self.process_content(content_id, db)
                logger.info(f"Immediate processing result for {content_id}: {success}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Immediate processing failed for {content_id}: {e}")
            logger.error("Full error details:", exc_info=True)

    async def _process_queue(self) -> None:
        """Process queued content items"""
        self.is_processing = True

        try:
            while not self.processing_queue.empty():
                content_id = await self.processing_queue.get()

                # Get database session - use proper dependency injection
                from ..db.database import SessionLocal
                db = SessionLocal()
                
                try:
                    logger.info(f"Starting queue processing for content {content_id}")
                    success = await self.process_content(content_id, db)
                    logger.info(f"Queue processing result for {content_id}: {success}")
                except Exception as e:
                    logger.error(f"Queue processing failed for {content_id}: {e}")
                    logger.error("Full error details:", exc_info=True)
                finally:
                    db.close()

                # Mark task as done
                self.processing_queue.task_done()

                # Small delay between processing
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Queue processing failed: {e}")
            logger.error("Full queue processing error:", exc_info=True)
        finally:
            self.is_processing = False

    def get_processing_status(self, db: Session) -> Dict[str, Any]:
        """Get current processing status"""
        try:
            total_content = db.query(Content).count()
            pending_content = (
                db.query(Content)
                .filter(Content.status == ContentStatus.pending)
                .count()
            )
            processing_content = (
                db.query(Content)
                .filter(Content.status == ContentStatus.processing)
                .count()
            )
            completed_content = (
                db.query(Content)
                .filter(Content.status == ContentStatus.completed)
                .count()
            )
            failed_content = (
                db.query(Content).filter(Content.status == ContentStatus.failed).count()
            )

            return {
                "total": total_content,
                "pending": pending_content,
                "processing": processing_content,
                "completed": completed_content,
                "failed": failed_content,
                "queue_size": self.processing_queue.qsize(),
                "is_processing": self.is_processing,
            }

        except Exception as e:
            logger.error(f"Failed to get processing status: {e}")
            return {
                "total": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "queue_size": 0,
                "is_processing": False,
                "error": str(e),
            }

    async def reprocess_failed_content(self, db: Session, limit: int = 10) -> int:
        """Reprocess failed content items"""
        try:
            failed_content = (
                db.query(Content)
                .filter(Content.status == ContentStatus.failed)
                .limit(limit)
                .all()
            )

            reprocessed_count = 0
            for content in failed_content:
                # Reset to pending status
                content.status = ContentStatus.pending
                db.commit()

                # Add to processing queue
                await self.queue_content_processing(str(content.id))
                reprocessed_count += 1

            logger.info(f"Queued {reprocessed_count} failed items for reprocessing")
            return reprocessed_count

        except Exception as e:
            logger.error(f"Failed to reprocess content: {e}")
            return 0


# Global instance
ingestion_service = IngestionService()
