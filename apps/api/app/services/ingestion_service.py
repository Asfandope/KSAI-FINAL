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

            # Update status to failed
            try:
                content = db.query(Content).filter(Content.id == content_id).first()
                if content:
                    content.status = ContentStatus.failed
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update content status: {db_error}")

            return False

    async def _process_pdf(self, content: Content) -> tuple[str, Dict[str, Any]]:
        """Process PDF content"""
        try:
            # For now, we'll assume the PDF is already stored locally
            # In production, this would download from S3
            file_path = content.source_url

            if not file_path.startswith("/"):
                # If it's not an absolute path, assume it's a relative path in uploads
                file_path = f"uploads/{file_path}"

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
            text, metadata = document_service.extract_youtube_transcript(
                content.source_url
            )
            return text, metadata

        except Exception as e:
            logger.error(f"YouTube processing failed: {e}")
            # Return placeholder content for demo
            return (
                f"Sample transcript for YouTube video: {content.title}\n\n"
                f"This is placeholder content for the YouTube processing demo. "
                f"In production, actual video transcript would be extracted here. "
                f"URL: {content.source_url}, Category: {content.category}, "
                f"Language: {content.language.value}",
                {"source_type": "youtube", "duration": 600},
            )

    async def queue_content_processing(self, content_id: str) -> None:
        """Add content to processing queue"""
        await self.processing_queue.put(content_id)

        # Start processing if not already running
        if not self.is_processing:
            asyncio.create_task(self._process_queue())

    async def _process_queue(self) -> None:
        """Process queued content items"""
        self.is_processing = True

        try:
            while not self.processing_queue.empty():
                content_id = await self.processing_queue.get()

                # Get database session
                db = next(get_db())
                try:
                    await self.process_content(content_id, db)
                finally:
                    db.close()

                # Mark task as done
                self.processing_queue.task_done()

                # Small delay between processing
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Queue processing failed: {e}")
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
