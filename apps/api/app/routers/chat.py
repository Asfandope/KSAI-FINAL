import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.content import Language
from ..models.conversation import Conversation, Message, MessageSender
from ..models.user import User
from ..services.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models
class ChatRequest(BaseModel):
    query: str
    language: str  # 'en' or 'ta'
    topic: str
    conversation_id: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    sender: str
    text_content: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    video_timestamp: Optional[int] = None
    created_at: str


@router.post("/", response_model=MessageResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Process chat message and return AI response"""

    try:
        # Find or create conversation
        conversation = None
        if request.conversation_id:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == request.conversation_id,
                    Conversation.user_id == current_user.id,
                )
                .first()
            )

        if not conversation:
            # Create new conversation
            conversation = Conversation(user_id=current_user.id, topic=request.topic)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            sender=MessageSender.user,
            text_content=request.query,
        )
        db.add(user_message)
        db.commit()
    except Exception as db_error:
        # Database connection issues - create fallback conversation
        import uuid
        conversation = type('MockConversation', (), {
            'id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'topic': request.topic
        })()

    # Process query through RAG pipeline
    from ..services.rag_service import rag_service

    # Get conversation context for better query understanding
    conversation_context = []
    if conversation and hasattr(conversation, 'id') and isinstance(conversation.id, (str, int)):
        try:
            recent_messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc())
                .limit(6)
                .all()
            )

            for msg in reversed(recent_messages):
                conversation_context.append(
                    {"sender": msg.sender.value, "text": msg.text_content}
                )
        except Exception:
            # If we can't get conversation context, continue without it
            conversation_context = []

    # Process query through RAG
    # Convert string language to Language enum
    language_enum = Language.en if request.language.lower() == "en" else Language.ta
    
    try:
        rag_response = await rag_service.process_query(
            query=request.query,
            topic=request.topic,
            language=language_enum,
            conversation_context=conversation_context,
        )
        
        logger.info(f"RAG response: {rag_response}")
        
        ai_response_text = rag_response.get(
            "answer", "I apologize, but I'm unable to process your query at the moment."
        )
        
        if not ai_response_text or ai_response_text.strip() == "":
            ai_response_text = "I apologize, but I received an empty response. Please try again."
            
    except Exception as e:
        logger.error(f"RAG processing failed: {e}")
        ai_response_text = f"I apologize, but I encountered an error processing your query: {str(e)}"

    # Add source information if available
    try:
        sources = rag_response.get("sources", [])
        if sources and rag_response.get("success", False):
            sources_text = "\n\nSources:\n"
            for i, source in enumerate(sources[:3], 1):  # Limit to top 3 sources
                sources_text += f"{i}. {source.get('title', 'Unknown')} ({source.get('source_type', 'unknown')})\n"
            ai_response_text += sources_text
    except NameError:
        # rag_response not defined if there was an error
        pass

    # Save AI response (only if we have a real conversation with database connection)
    try:
        if conversation and hasattr(conversation, 'id') and isinstance(conversation.id, (str, int)):
            ai_message = Message(
                conversation_id=conversation.id,
                sender=MessageSender.ai,
                text_content=ai_response_text,
            )
            db.add(ai_message)
            db.commit()
            db.refresh(ai_message)
        else:
            # Create a mock message for fallback scenarios
            import uuid
            from datetime import datetime
            ai_message = type('MockMessage', (), {
                'id': str(uuid.uuid4()),
                'sender': MessageSender.ai,
                'text_content': ai_response_text,
                'image_url': None,
                'video_url': None,
                'video_timestamp_seconds': None,
                'created_at': datetime.utcnow()
            })()
    except Exception:
        # Create a mock message if database save fails
        import uuid
        from datetime import datetime
        ai_message = type('MockMessage', (), {
            'id': str(uuid.uuid4()),
            'sender': MessageSender.ai,
            'text_content': ai_response_text,
            'image_url': None,
            'video_url': None,
            'video_timestamp_seconds': None,
            'created_at': datetime.utcnow()
        })()

    return MessageResponse(
        id=str(ai_message.id),
        sender=ai_message.sender.value if hasattr(ai_message.sender, 'value') else ai_message.sender,
        text_content=ai_message.text_content,
        image_url=ai_message.image_url,
        video_url=ai_message.video_url,
        video_timestamp=ai_message.video_timestamp_seconds,
        created_at=ai_message.created_at.isoformat() if hasattr(ai_message.created_at, 'isoformat') else str(ai_message.created_at),
    )
