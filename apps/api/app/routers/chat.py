# apps/api/app/routers/chat.py

import logging # Add this import
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
logger = logging.getLogger(__name__) # Add this line to get a logger instance


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
    
    # CRITICAL: Basic logging to verify function is called
    print("*** CHAT ENDPOINT HIT ***")
    logger.info("*** CHAT ENDPOINT HIT ***")
    
    # --- LOGGING START ---
    logger.info("="*60)
    logger.info("CHAT REQUEST RECEIVED")
    logger.info(f"Query: '{request.query}'")
    logger.info(f"Topic: {request.topic}")
    logger.info(f"Language: {request.language}")
    logger.info(f"Conversation ID: {request.conversation_id}")
    logger.info(f"User ID: {current_user.id}")
    logger.info("="*60)
    # --- LOGGING END ---

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
        # --- LOGGING START ---
        logger.error(f"Database error in chat router: {db_error}", exc_info=True)
        # --- LOGGING END ---
        # Rollback the transaction on error
        db.rollback()
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
    language_enum = Language.en if request.language.lower() == "en" else Language.ta
    
    logger.info("\n" + "-"*40)
    logger.info("SENDING TO RAG SERVICE...")
    logger.info("-"*40)
    
    rag_response = await rag_service.process_query(
        query=request.query,
        topic=request.topic,
        language=language_enum,
        conversation_context=conversation_context,
    )

    # --- LOGGING START ---
    logger.info("\n" + "="*60)
    logger.info("RAG SERVICE RESPONSE")
    logger.info(f"Success: {rag_response.get('success')}")
    logger.info(f"Sources Found: {len(rag_response.get('sources', []))}")
    if rag_response.get('success'):
        answer_preview = rag_response.get('answer', '')[:200]
        logger.info(f"Answer Preview: {answer_preview}...")
        if rag_response.get('sources'):
            logger.info("Sources:")
            for idx, source in enumerate(rag_response.get('sources', [])[:3], 1):
                logger.info(f"  {idx}. {source.get('title', 'Unknown')} ({source.get('source_type', 'unknown')})") 
    else:
        logger.warning(f"RAG Error: {rag_response.get('error', 'Unknown error')}")
    logger.info("="*60)
    # --- LOGGING END ---

    ai_response_text = rag_response.get(
        "answer", "I apologize, but I'm unable to process your query at the moment."
    )
    
    # --- LOGGING START ---
    # Add a check for empty or whitespace-only responses
    if not ai_response_text or not ai_response_text.strip():
        logger.warning("RAG service returned an empty or whitespace answer. Sending a fallback message.")
        ai_response_text = "I'm sorry, I couldn't find a specific answer for that. Could you try rephrasing your question?"
    
    logger.info("\n" + "-"*40)
    logger.info("FINAL RESPONSE TO USER")
    logger.info(f"Response Length: {len(ai_response_text)} characters")
    logger.info(f"Response: {ai_response_text[:150]}...")
    logger.info("-"*40 + "\n")
    # --- LOGGING END ---

    # Add source information if available
    sources = rag_response.get("sources", [])
    if sources and rag_response.get("success", False):
        sources_text = "\n\nSources:\n"
        for i, source in enumerate(sources[:3], 1):  # Limit to top 3 sources
            sources_text += f"{i}. {source.get('title', 'Unknown')} ({source.get('source_type', 'unknown')})\n"
        ai_response_text += sources_text

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
    except Exception as db_save_error:
        # --- LOGGING START ---
        logger.error(f"Database error saving AI message: {db_save_error}", exc_info=True)
        # --- LOGGING END ---
        # Rollback the transaction on error
        db.rollback()
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
        sender=ai_message.sender.value,
        text_content=ai_message.text_content,
        image_url=ai_message.image_url,
        video_url=ai_message.video_url,
        video_timestamp=ai_message.video_timestamp_seconds,
        created_at=ai_message.created_at.isoformat(),
    )