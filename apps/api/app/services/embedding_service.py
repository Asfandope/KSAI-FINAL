"""
Embedding Service

This service handles:
- Text embedding generation using OpenAI
- Text chunking and preprocessing
- Embedding caching and optimization
"""

import logging
from typing import Any, Dict, List

import tiktoken
from openai import OpenAI

from ..core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "text-embedding-3-small"  # More cost-effective than ada-002
            self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            logger.info("OpenAI embedding service initialized")
        else:
            logger.warning("OpenAI API key not provided - embedding service disabled")
            self.client = None

    def is_available(self) -> bool:
        """Check if embedding service is available"""
        return self.client is not None

    def chunk_text(
        self, text: str, max_tokens: int = 500, overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap for better context preservation

        Args:
            text: Input text to chunk
            max_tokens: Maximum tokens per chunk
            overlap: Number of overlapping tokens between chunks

        Returns:
            List of chunks with metadata
        """
        if not text.strip():
            return []

        try:
            # Tokenize the text
            tokens = self.encoding.encode(text)

            if len(tokens) <= max_tokens:
                return [
                    {
                        "text": text,
                        "start_token": 0,
                        "end_token": len(tokens),
                        "token_count": len(tokens),
                    }
                ]

            chunks = []
            start = 0
            chunk_id = 0

            while start < len(tokens):
                # Calculate end position
                end = min(start + max_tokens, len(tokens))

                # Extract chunk tokens
                chunk_tokens = tokens[start:end]
                chunk_text = self.encoding.decode(chunk_tokens)

                chunks.append(
                    {
                        "text": chunk_text,
                        "chunk_id": chunk_id,
                        "start_token": start,
                        "end_token": end,
                        "token_count": len(chunk_tokens),
                    }
                )

                # Move start position with overlap
                start = end - overlap
                chunk_id += 1

                # Break if we've covered all tokens
                if end >= len(tokens):
                    break

            logger.info(f"Split text into {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Failed to chunk text: {e}")
            return []

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return []

        if not texts:
            return []

        try:
            # Filter out empty texts
            valid_texts = [text for text in texts if text.strip()]

            if not valid_texts:
                return []

            # Generate embeddings
            response = self.client.embeddings.create(
                input=valid_texts, model=self.model
            )

            embeddings = [item.embedding for item in response.data]

            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return []

    def generate_single_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text string to embed

        Returns:
            Embedding vector
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text before embedding generation

        Args:
            text: Raw text to preprocess

        Returns:
            Preprocessed text
        """
        if not text:
            return ""

        # Basic text cleaning
        text = text.strip()

        # Remove excessive whitespace
        text = " ".join(text.split())

        # Remove very short lines that are likely noise
        lines = text.split("\n")
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        text = "\n".join(cleaned_lines)

        return text

    def process_document(
        self, content: str, metadata: Dict[str, Any], chunk_size: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Process a document by chunking and generating embeddings

        Args:
            content: Document content
            metadata: Document metadata
            chunk_size: Maximum tokens per chunk

        Returns:
            List of processed chunks with embeddings
        """
        try:
            # Preprocess content
            cleaned_content = self.preprocess_text(content)

            if not cleaned_content:
                logger.warning("No content after preprocessing")
                return []

            # Chunk the content
            chunks = self.chunk_text(cleaned_content, max_tokens=chunk_size)

            if not chunks:
                logger.warning("No chunks generated")
                return []

            # Extract texts for embedding
            chunk_texts = [chunk["text"] for chunk in chunks]

            # Generate embeddings
            embeddings = self.generate_embeddings(chunk_texts)

            if len(embeddings) != len(chunks):
                logger.error(
                    f"Embedding count mismatch: {len(embeddings)} vs {len(chunks)}"
                )
                return []

            # Combine chunks with embeddings and metadata
            processed_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                processed_chunks.append(
                    {
                        "embedding": embedding,
                        "text": chunk["text"],
                        "metadata": {
                            **metadata,
                            "chunk_id": chunk["chunk_id"],
                            "token_count": chunk["token_count"],
                            "start_token": chunk["start_token"],
                            "end_token": chunk["end_token"],
                        },
                    }
                )

            logger.info(f"Processed document into {len(processed_chunks)} chunks")
            return processed_chunks

        except Exception as e:
            logger.error(f"Failed to process document: {e}")
            return []


# Global instance
embedding_service = EmbeddingService()
