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
        content_type = ContentType.PDF
        source_url = f"uploads/{file.filename}"  # Will be replaced with S3 URL
        title = file.filename
    else:
        content_type = ContentType.YOUTUBE
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
        status=ContentStatus.PENDING,
    )

    db.add(new_content)
    db.commit()
    db.refresh(new_content)

    # Trigger async processing pipeline
    from ..services.ingestion_service import ingestion_service

    await ingestion_service.queue_content_processing(str(new_content.id))

    return UploadResponse(
        message="Content uploaded successfully and is being processed",
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
        "active_conversations": 0,  # TODO: Implement real-time tracking
    }
