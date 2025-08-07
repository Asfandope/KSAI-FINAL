import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID

from ..db.base import Base


class ContentType(str, enum.Enum):
    pdf = "pdf"
    youtube = "youtube"


class ContentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Language(str, enum.Enum):
    en = "en"
    ta = "ta"


class Content(Base):
    __tablename__ = "content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    source_type = Column(ENUM(ContentType, name="content_type", create_type=False), nullable=False)
    language = Column(ENUM(Language, name="language_code", create_type=False), nullable=False)
    category = Column(String(255), nullable=False)
    needs_translation = Column(Boolean, default=False, nullable=False)
    status = Column(ENUM(ContentStatus, name="content_status", create_type=False), default=ContentStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Content(id={self.id}, title={self.title}, status={self.status})>"
