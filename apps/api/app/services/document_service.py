"""
Document Processing Service

This service handles:
- PDF text extraction
- YouTube video transcript extraction
- Document preprocessing and cleaning
- File management and storage
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# PDF processing
try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("PyPDF2 not available - PDF processing disabled")

# YouTube processing
try:
    import re

    from pytube import YouTube
    from youtube_transcript_api import YouTubeTranscriptApi

    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("YouTube libraries not available - YouTube processing disabled")

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "ks_ai_docs"
        self.temp_dir.mkdir(exist_ok=True)

    def extract_pdf_text(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text content from a PDF file

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (extracted_text, metadata)
        """
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 not available for PDF processing")

        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract metadata
                metadata = {
                    "page_count": len(pdf_reader.pages),
                    "source_type": "pdf",
                    "file_name": Path(file_path).name,
                }

                # Add PDF metadata if available
                if pdf_reader.metadata:
                    pdf_meta = pdf_reader.metadata
                    metadata.update(
                        {
                            "title": pdf_meta.get("/Title", ""),
                            "author": pdf_meta.get("/Author", ""),
                            "subject": pdf_meta.get("/Subject", ""),
                            "creator": pdf_meta.get("/Creator", ""),
                            "producer": pdf_meta.get("/Producer", ""),
                            "creation_date": str(pdf_meta.get("/CreationDate", "")),
                            "modification_date": str(pdf_meta.get("/ModDate", "")),
                        }
                    )

                # Extract text from all pages
                full_text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            full_text += f"\n--- Page {page_num + 1} ---\n"
                            full_text += page_text
                            full_text += "\n"
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract text from page {page_num + 1}: {e}"
                        )
                        continue

                if not full_text.strip():
                    raise ValueError("No readable text found in PDF")

                logger.info(
                    f"Extracted text from PDF: {len(full_text)} characters, {metadata['page_count']} pages"
                )
                return full_text.strip(), metadata

        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            raise

    def extract_youtube_transcript(self, video_url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract transcript from a YouTube video

        Args:
            video_url: YouTube video URL

        Returns:
            Tuple of (transcript_text, metadata)
        """
        if not YOUTUBE_AVAILABLE:
            raise ImportError("YouTube libraries not available")

        try:
            # Extract video ID from URL
            video_id = self._extract_video_id(video_url)
            if not video_id:
                raise ValueError(f"Could not extract video ID from URL: {video_url}")

            # Get video metadata
            yt = YouTube(video_url)
            metadata = {
                "video_id": video_id,
                "title": yt.title,
                "author": yt.author,
                "length": yt.length,
                "views": yt.views,
                "publish_date": str(yt.publish_date) if yt.publish_date else "",
                "description": yt.description[:500] + "..."
                if len(yt.description) > 500
                else yt.description,
                "source_type": "youtube",
                "video_url": video_url,
            }

            # Get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["en", "ta"]  # Support English and Tamil
            )

            # Format transcript with timestamps
            formatted_transcript = ""
            for entry in transcript_list:
                start_time = int(entry["start"])
                minutes = start_time // 60
                seconds = start_time % 60
                timestamp = f"{minutes:02d}:{seconds:02d}"

                formatted_transcript += f"[{timestamp}] {entry['text']}\n"

            if not formatted_transcript.strip():
                raise ValueError("No transcript found for video")

            logger.info(
                f"Extracted YouTube transcript: {len(formatted_transcript)} characters"
            )
            return formatted_transcript.strip(), metadata

        except Exception as e:
            logger.error(f"Failed to extract YouTube transcript: {e}")
            raise

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats"""
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded file to temporary storage

        Args:
            file_content: File content as bytes
            filename: Original filename

        Returns:
            Path to saved file
        """
        try:
            # Generate safe filename
            safe_filename = self._sanitize_filename(filename)
            file_path = self.temp_dir / safe_filename

            # Ensure unique filename
            counter = 1
            original_path = file_path
            while file_path.exists():
                name = original_path.stem
                suffix = original_path.suffix
                file_path = self.temp_dir / f"{name}_{counter}{suffix}"
                counter += 1

            # Save file
            with open(file_path, "wb") as f:
                f.write(file_content)

            logger.info(f"Saved uploaded file: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove path components
        filename = os.path.basename(filename)

        # Replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, "_")

        # Limit length
        if len(filename) > 100:
            name = filename[:90]
            ext = filename[-10:] if "." in filename[-10:] else ""
            filename = name + ext

        return filename

    def cleanup_temp_files(self, max_age_hours: int = 24) -> None:
        """Clean up old temporary files"""
        try:
            import time

            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        logger.info(f"Cleaned up old temp file: {file_path}")

        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")


# Global instance
document_service = DocumentService()
