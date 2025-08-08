# In apps/api/app/services/youtube_processor.py

import logging
import re
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

def extract_video_id(url: str) -> Optional[str]:
    """Extracts the 11-character video ID from a YouTube URL."""
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_transcript(video_url: str) -> Tuple[str, Dict[str, Any]]:
    """
    Extracts a YouTube transcript using the single most reliable method.
    THIS IS THE FINAL, SIMPLIFIED, AND CORRECTED VERSION.
    """
    
    sanitized_url = video_url.replace(" ", "")
    logger.info(f"Sanitized YouTube URL: '{sanitized_url}'")
    
    video_id = extract_video_id(sanitized_url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {sanitized_url}")
    logger.info(f"Extracted video ID: {video_id}")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
        logger.info("Attempting transcript extraction with 'youtube_transcript_api'...")
        
        # CORRECTED USAGE FOR API v1.2.2: Create instance then call fetch
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id, languages=['en', 'en-US'])
        
        formatted_transcript = ""
        for entry in transcript_list:
            start = int(float(entry.get('start', 0)))
            timestamp = f"{start // 60:02d}:{start % 60:02d}"
            text = entry.get('text', '').strip().replace('\n', ' ')
            if text:
                formatted_transcript += f"[{timestamp}] {text}\n"
        
        if not formatted_transcript.strip():
            raise ValueError("Transcript was found but was empty after formatting.")

        logger.info("SUCCESS: Extracted transcript using 'youtube_transcript_api'.")
        metadata = {
            "video_id": video_id, 
            "title": f"YouTube Video: {video_id}", 
            "source_type": "youtube", 
            "video_url": sanitized_url, 
            "method_used": "youtube_transcript_api"
        }
        return formatted_transcript.strip(), metadata

    except TranscriptsDisabled:
        logger.error(f"Transcripts are disabled for video {video_id}.")
        raise ValueError(f"This video does not have captions enabled. Please try a different video.")
    except Exception as e:
        logger.error(f"Transcript extraction failed for {video_id}: {e}", exc_info=True)
        raise Exception(f"Failed to retrieve transcript. This is likely an IP block from YouTube or the video is unavailable. Please wait 10-15 minutes and try again with a different video.") from e