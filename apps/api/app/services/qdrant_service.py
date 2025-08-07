"""
Qdrant Vector Database Service

This service handles all vector database operations including:
- Creating collections
- Storing embeddings
- Performing semantic search
- Managing vector data lifecycle
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from ..core.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    def __init__(self):
        try:
            # Initialize Qdrant client
            if settings.QDRANT_API_KEY:
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY,
                )
            else:
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                )

            # Test connection
            self.client.get_collections()
            logger.info("Successfully connected to Qdrant")

        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None

    def is_healthy(self) -> bool:
        """Check if Qdrant service is healthy"""
        try:
            if self.client is None:
                return False
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    def create_collection(self, collection_name: str, vector_size: int = 1536) -> bool:
        """Create a new collection for storing vectors"""
        try:
            if self.client is None:
                logger.error("Qdrant client not initialized")
                return False

            # Check if collection already exists
            collections = self.client.get_collections()
            existing_names = [col.name for col in collections.collections]

            if collection_name in existing_names:
                logger.info(f"Collection '{collection_name}' already exists")
                return True

            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Created collection '{collection_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            return False

    def store_embeddings(
        self,
        collection_name: str,
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]],
        texts: List[str],
    ) -> bool:
        """Store embeddings with metadata in a collection"""
        try:
            if self.client is None:
                logger.error("Qdrant client not initialized")
                return False

            if len(embeddings) != len(metadata) or len(embeddings) != len(texts):
                raise ValueError(
                    "Embeddings, metadata, and texts must have the same length"
                )

            # Create points for insertion
            points = []
            for i, (embedding, meta, text) in enumerate(
                zip(embeddings, metadata, texts)
            ):
                point_id = str(uuid.uuid4())
                payload = {
                    **meta,
                    "text": text,
                    "created_at": meta.get("created_at", ""),
                }

                points.append(
                    PointStruct(id=point_id, vector=embedding, payload=payload)
                )

            # Upload points to collection
            self.client.upsert(collection_name=collection_name, points=points)

            logger.info(f"Stored {len(points)} embeddings in '{collection_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            return False

    def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in a collection"""
        try:
            if self.client is None:
                logger.error("Qdrant client not initialized")
                return []

            # Build filter conditions
            query_filter = None
            if filter_conditions:
                conditions = []
                for field, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(key=field, match=MatchValue(value=value))
                    )
                if conditions:
                    query_filter = Filter(must=conditions)

            # Perform search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {"id": result.id, "score": result.score, "payload": result.payload}
                )

            logger.info(f"Found {len(formatted_results)} similar results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection and all its data"""
        try:
            if self.client is None:
                logger.error("Qdrant client not initialized")
                return False

            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            return False

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a collection"""
        try:
            if self.client is None:
                logger.error("Qdrant client not initialized")
                return None

            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "status": info.status,
                "vector_count": info.points_count,
                "config": {
                    "distance": info.config.params.vectors.distance,
                    "size": info.config.params.vectors.size,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None

    def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            if self.client is None:
                logger.error("Qdrant client not initialized")
                return []

            collections = self.client.get_collections()
            return [col.name for col in collections.collections]

        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []


# Global instance
qdrant_service = QdrantService()
