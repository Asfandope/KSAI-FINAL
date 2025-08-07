import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID

from ..db.base import Base


class ContentType(str, enum.Enum):
    PDF = "pdf"
    YOUTUBE = "youtube"


class ContentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Language(str, enum.Enum):
    EN = "en"
    TA = "ta"


class Content(Base):
    __tablename__ = "content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    source_type = Column(Enum(ContentType), nullable=False)
    language = Column(Enum(Language), nullable=False)
    category = Column(String(255), nullable=False)
    needs_translation = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(ContentStatus), default=ContentStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Content(id={self.id}, title={self.title}, status={self.status})>"
