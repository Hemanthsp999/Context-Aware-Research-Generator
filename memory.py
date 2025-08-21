import json
from sqlalchemy.orm import Session
from schemas import ResearchBrief
from database import User, Conversation, ResearchHistory  # the classes above


def get_history(db: Session, user_id: int, conv_id: str):
    """Get conversation history from DB"""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id, Conversation.conversation_id == conv_id)
        .first()
    )
    if not conversation:
        return []

    briefs = []
    for item in conversation.history:
        try:
            briefs.append(
                ResearchBrief(
                    topic=item.topic,
                    summary=item.summary,
                    sources=json.loads(item.sources)
                )
            )
        except Exception as e:
            print(f"Error loading item {item.id}: {e}")
    return briefs


def append_brief(db: Session, user_id: int, conv_id: str, brief: ResearchBrief):
    """Append new brief to conversation history in DB"""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id, Conversation.conversation_id == conv_id)
        .first()
    )

    # If conversation doesn’t exist, create it
    if not conversation:
        conversation = Conversation(user_id=user_id, conversation_id=conv_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    history_entry = ResearchHistory(
        topic=brief.topic,
        summary=brief.summary,
        sources=json.dumps(brief.sources),  # convert list to JSON string
        conversation_id=conversation.id
    )

    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)


def clear_conversation(db: Session, user_id: int, conv_id: str):
    """Clear conversation history in DB"""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id, Conversation.conversation_id == conv_id)
        .first()
    )
    if conversation:
        db.delete(conversation)  # cascades delete to history
        db.commit()


def list_conversations(db: Session, user_id: int):
    """List all conversation IDs for a user"""
    conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
    return [c.conversation_id for c in conversations]

