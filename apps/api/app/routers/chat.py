from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.conversation import Conversation, Message, MessageSender
from ..models.user import User
from ..services.auth import get_current_user

router = APIRouter()


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
            sender=MessageSender.USER,
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
    if conversation:
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

    # Process query through RAG
    rag_response = await rag_service.process_query(
        query=request.query,
        topic=request.topic,
        language=request.language,
        conversation_context=conversation_context,
    )

    ai_response_text = rag_response.get(
        "answer", "I apologize, but I'm unable to process your query at the moment."
    )

    # Add source information if available
    sources = rag_response.get("sources", [])
    if sources and rag_response.get("success", False):
        sources_text = "\n\nSources:\n"
        for i, source in enumerate(sources[:3], 1):  # Limit to top 3 sources
            sources_text += f"{i}. {source.get('title', 'Unknown')} ({source.get('source_type', 'unknown')})\n"
        ai_response_text += sources_text

    # Save AI response
    ai_message = Message(
        conversation_id=conversation.id,
        sender=MessageSender.AI,
        text_content=ai_response_text,
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    return MessageResponse(
        id=str(ai_message.id),
        sender=ai_message.sender.value,
        text_content=ai_message.text_content,
        image_url=ai_message.image_url,
        video_url=ai_message.video_url,
        video_timestamp=ai_message.video_timestamp_seconds,
        created_at=ai_message.created_at.isoformat(),
    )
