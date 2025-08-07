"""
RAG (Retrieval-Augmented Generation) Service

This service implements the core RAG pipeline:
1. Query processing and embedding
2. Semantic search in vector database
3. Context retrieval and ranking
4. LLM generation with grounded context
5. Response formatting with source citations
"""

import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..core.config import settings
from ..models.content import Language
from .embedding_service import embedding_service
from .qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        # Initialize OpenAI client for LLM generation
        if settings.OPENAI_API_KEY:
            self.llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "gpt-3.5-turbo"  # Cost-effective model
            logger.info("RAG service initialized with OpenAI")
        else:
            logger.warning("OpenAI API key not provided - RAG service disabled")
            self.llm_client = None

        # Collection names for different topics
        self.collection_mapping = {
            "Politics": "ks_politics",
            "Environmentalism": "ks_environment",
            "SKCRF": "ks_skcrf",
            "Educational Trust": "ks_education",
        }

    def is_available(self) -> bool:
        """Check if RAG service is available"""
        return (
            self.llm_client is not None
            and embedding_service.is_available()
            and qdrant_service.is_healthy()
        )

    async def process_query(
        self,
        query: str,
        topic: str,
        language: Language,
        conversation_context: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user query through the RAG pipeline

        Args:
            query: User's question
            topic: Selected topic category
            language: Language preference (en/ta)
            conversation_context: Previous conversation messages for context

        Returns:
            RAG response with answer, sources, and metadata
        """
        try:
            if not self.is_available():
                return self._create_error_response("RAG service not available")

            logger.info(
                f"Processing query: '{query}' for topic: {topic}, language: {language}"
            )

            # Step 1: Process and embed the query
            processed_query = self._preprocess_query(query, conversation_context)
            query_embedding = embedding_service.generate_single_embedding(
                processed_query
            )

            if not query_embedding:
                return self._create_error_response("Failed to generate query embedding")

            # Step 2: Retrieve relevant context from vector database
            context_chunks = await self._retrieve_context(
                query_embedding=query_embedding,
                topic=topic,
                language=language,
                limit=5,  # Top 5 most relevant chunks
            )

            if not context_chunks:
                return self._create_fallback_response(query, topic, language)

            # Step 3: Generate response using LLM
            response = await self._generate_response(
                query=query,
                context_chunks=context_chunks,
                language=language,
                topic=topic,
            )

            logger.info(
                f"Successfully processed query, found {len(context_chunks)} relevant sources"
            )
            return response

        except Exception as e:
            logger.error(f"RAG query processing failed: {e}")
            return self._create_error_response(f"Query processing failed: {str(e)}")

    def _preprocess_query(
        self, query: str, conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Preprocess query with conversation context"""
        if not conversation_context:
            return query.strip()

        # Add recent conversation context to improve query understanding
        context_text = ""
        for msg in conversation_context[-3:]:  # Last 3 messages
            if msg.get("sender") == "user":
                context_text += f"Previous question: {msg.get('text', '')}\n"
            elif msg.get("sender") == "ai":
                context_text += f"Previous answer: {msg.get('text', '')[:100]}...\n"

        if context_text:
            return f"{context_text}\nCurrent question: {query}"

        return query

    async def _retrieve_context(
        self,
        query_embedding: List[float],
        topic: str,
        language: Language,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context chunks from vector database"""
        try:
            collection_name = self.collection_mapping.get(topic, "ks_general")

            # Set up filter conditions
            filter_conditions = {
                "category": topic,
            }

            # Language filtering - include both target language and English content
            # This allows for cross-language retrieval when content is limited
            if language == "ta":
                # For Tamil queries, search both Tamil and English content
                pass  # We'll search all content and let the LLM handle language

            # Perform semantic search
            search_results = qdrant_service.search_similar(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit * 2,  # Get more results to filter
                score_threshold=0.6,  # Relevance threshold
                filter_conditions=filter_conditions,
            )

            # Post-process and rank results
            processed_chunks = []
            for result in search_results[:limit]:
                chunk_data = {
                    "text": result["payload"].get("text", ""),
                    "score": result["score"],
                    "source": {
                        "title": result["payload"].get("title", "Unknown"),
                        "source_type": result["payload"].get("source_type", "unknown"),
                        "category": result["payload"].get("category", topic),
                        "language": result["payload"].get("language", "en"),
                        "source_url": result["payload"].get("source_url", ""),
                        "chunk_id": result["payload"].get("chunk_id", 0),
                    },
                }
                processed_chunks.append(chunk_data)

            return processed_chunks

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return []

    async def _generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        language: Language,
        topic: str,
    ) -> Dict[str, Any]:
        """Generate response using LLM with retrieved context"""
        try:
            # Prepare context text
            context_text = self._format_context(context_chunks)

            # Create system prompt
            system_prompt = self._create_system_prompt(language, topic)

            # Create user prompt
            user_prompt = f"""Context Information:
{context_text}

User Question: {query}

Please provide a comprehensive answer based ONLY on the provided context. If the context doesn't contain enough information to answer the question, please say so clearly."""

            # Generate response
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for factual accuracy
                max_tokens=1000,
            )

            answer = response.choices[0].message.content.strip()

            # Format final response
            return {
                "success": True,
                "answer": answer,
                "sources": [chunk["source"] for chunk in context_chunks],
                "metadata": {
                    "query": query,
                    "topic": topic,
                    "language": language,
                    "model": self.model,
                    "sources_count": len(context_chunks),
                    "avg_relevance_score": sum(
                        chunk["score"] for chunk in context_chunks
                    )
                    / len(context_chunks),
                },
            }

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._create_error_response(f"Failed to generate response: {str(e)}")

    def _format_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Format context chunks for LLM input"""
        formatted_context = ""

        for i, chunk in enumerate(context_chunks, 1):
            source_info = chunk["source"]
            formatted_context += f"""Source {i} (Relevance: {chunk['score']:.2f}):
Title: {source_info['title']}
Category: {source_info['category']}
Content: {chunk['text']}

---

"""

        return formatted_context

    def _create_system_prompt(self, language: Language, topic: str) -> str:
        """Create system prompt based on language and topic"""
        base_prompt = f"""You are KS AI, an expert assistant providing information about Karthikeya Sivasenapathy (KS) and his work in {topic}.

CRITICAL INSTRUCTIONS:
1. Answer ONLY based on the provided context - never use external knowledge
2. If the context doesn't contain sufficient information, clearly state this
3. Provide accurate, factual responses with proper citations
4. Be helpful but maintain strict adherence to the source material
5. Do not hallucinate or make up information"""

        if language == "ta":
            base_prompt += """
6. Respond in Tamil (தமிழ்) when possible, but you may include English terms if Tamil translations are not clear
7. Maintain respectful and formal tone appropriate for Tamil cultural context"""
        else:
            base_prompt += """
6. Respond in clear, professional English
7. Use accessible language while maintaining accuracy"""

        return base_prompt

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "answer": "I apologize, but I'm unable to process your query at the moment. Please try again later.",
            "error": error_message,
            "sources": [],
            "metadata": {},
        }

    def _create_fallback_response(
        self, query: str, topic: str, language: Language
    ) -> Dict[str, Any]:
        """Create fallback response when no relevant context is found"""
        if language == "ta":
            answer = f"மன்னிக்கவும், {topic} பற்றிய உங்கள் கேள்விக்கு எனது தரவுத்தளத்தில் போதுமான தகவல் இல்லை. தயவுசெய்து வேறு வழியில் கேள்வியை கேட்க முயற்சிக்கவும்."
        else:
            answer = f"I apologize, but I don't have sufficient information in my knowledge base to answer your question about {topic}. Please try rephrasing your question or asking about a different aspect of this topic."

        return {
            "success": True,
            "answer": answer,
            "sources": [],
            "metadata": {
                "query": query,
                "topic": topic,
                "language": language,
                "type": "fallback_response",
            },
        }

    async def initialize_collections(self) -> bool:
        """Initialize vector database collections for each topic"""
        try:
            success_count = 0
            for topic, collection_name in self.collection_mapping.items():
                if qdrant_service.create_collection(collection_name):
                    success_count += 1
                    logger.info(
                        f"Initialized collection for {topic}: {collection_name}"
                    )
                else:
                    logger.error(f"Failed to initialize collection for {topic}")

            return success_count == len(self.collection_mapping)

        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            return False


# Global instance
rag_service = RAGService()
