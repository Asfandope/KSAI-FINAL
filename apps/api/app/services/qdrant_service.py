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


# in apps/api/app/services/qdrant_service.py

class QdrantService:
    def __init__(self):
        try:
            # Determine if we should use HTTPS based on host
            is_cloud = settings.QDRANT_HOST != "localhost" and settings.QDRANT_HOST != "127.0.0.1"
            
            if settings.QDRANT_API_KEY and is_cloud:
                # Qdrant Cloud with API key
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY,
                    https=True
                )
            elif settings.QDRANT_API_KEY and not is_cloud:
                # Local Qdrant with API key (for secured local instances)
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY,
                    https=False
                )
            else:
                # Local Qdrant without API key
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    https=False 
                )
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

    def get_collection_stats_simple(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection stats using simple approach to avoid parsing issues"""
        try:
            if self.client is None:
                logger.error("Qdrant client not initialized")
                return None

            # Generate a real embedding to get accurate search results
            from ..services.embedding_service import embedding_service
            
            # Use a generic query to search for any content
            test_embedding = embedding_service.generate_single_embedding("content data information")
            
            if not test_embedding:
                logger.warning(f"Failed to generate embedding for collection stats: {collection_name}")
                return None
            
            # Search with very low threshold to get all vectors
            results = self.search_similar(
                collection_name=collection_name,
                query_vector=test_embedding,
                limit=10000,  # Large limit to count all
                score_threshold=0.0
            )
            
            vector_count = len(results)
            
            return {
                "name": collection_name,
                "vector_count": vector_count,
                "status": "active" if vector_count > 0 else "inactive",
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats for {collection_name}: {e}")
            return None

    def delete_vectors_by_source(self, collection_name: str, source_url: str) -> bool:
        """Delete all vectors associated with a specific source document"""
        try:
            if self.client is None:
                logger.error("Qdrant client not initialized")
                return False

            # Create filter to match vectors by source_url
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            
            delete_filter = Filter(
                must=[
                    FieldCondition(
                        key="source_url",
                        match=MatchValue(value=source_url)
                    )
                ]
            )

            # Delete points matching the filter
            result = self.client.delete(
                collection_name=collection_name,
                points_selector=delete_filter
            )

            logger.info(f"Deleted vectors for source {source_url} from collection {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete vectors for source {source_url}: {e}")
            return False

    def delete_vectors_by_content_id(self, content_id: str) -> bool:
        """Delete vectors from all collections for a specific content ID"""
        try:
            if self.client is None:
                logger.error("Qdrant client not initialized")
                return False

            collections = self.list_collections()
            deleted_from_collections = []

            for collection_name in collections:
                try:
                    # Create filter to match vectors by content_id
                    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
                    
                    delete_filter = Filter(
                        must=[
                            FieldCondition(
                                key="content_id",
                                match=MatchValue(value=content_id)
                            )
                        ]
                    )

                    # Delete points matching the filter
                    result = self.client.delete(
                        collection_name=collection_name,
                        points_selector=delete_filter
                    )

                    deleted_from_collections.append(collection_name)
                    logger.info(f"Deleted vectors for content {content_id} from collection {collection_name}")

                except Exception as e:
                    logger.warning(f"Failed to delete from collection {collection_name}: {e}")
                    continue

            if deleted_from_collections:
                logger.info(f"Successfully deleted content {content_id} vectors from collections: {deleted_from_collections}")
                return True
            else:
                logger.warning(f"No vectors found for content {content_id}")
                return True  # Not finding vectors to delete is still considered success

        except Exception as e:
            logger.error(f"Failed to delete vectors for content {content_id}: {e}")
            return False


# Global instance
qdrant_service = QdrantService()
