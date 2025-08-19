# memory.py - Fixed version with proper error handling
import json
import os
import logging
from typing import List, Optional
from schemas import ResearchBrief

logger = logging.getLogger(__name__)

ROOT = os.environ.get("RA_MEM_DIR", ".ra_mem")
os.makedirs(ROOT, exist_ok=True)


def _path(cid: Optional[str]) -> str:
    cid = cid or "default"
    return os.path.join(ROOT, f"{cid}.json")


def get_history(conversation_id: Optional[str]) -> List[ResearchBrief]:
    """Get conversation history with proper error handling"""
    p = _path(conversation_id)
    if not os.path.exists(p):
        logger.debug(f"No history file found for conversation {conversation_id}")
        return []

    try:
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # Check if file is empty
        if not content:
            logger.warning(f"Empty history file for conversation {conversation_id}")
            return []

        # Try to parse JSON
        raw = json.loads(content)

        # Validate that it's a list
        if not isinstance(raw, list):
            logger.error(f"History file contains invalid data type: {type(raw)}")
            return []

        # Convert to ResearchBrief objects with error handling
        briefs = []
        for i, item in enumerate(raw):
            try:
                if isinstance(item, dict):
                    briefs.append(ResearchBrief(**item))
                else:
                    logger.warning(f"Skipping invalid item {i} in history: {type(item)}")
            except Exception as e:
                logger.error(f"Error parsing history item {i}: {e}")
                continue

        logger.info(f"Loaded {len(briefs)} briefs for conversation {conversation_id}")
        return briefs

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {p}: {e}")
        logger.error(f"File content preview: {content[:200]}...")
        # Backup corrupted file and return empty list
        backup_path = f"{p}.corrupted.backup"
        try:
            os.rename(p, backup_path)
            logger.info(f"Corrupted file backed up to {backup_path}")
        except Exception as e:
            logger.error(f"Debug Error: {str(e)}")
            pass
        return []
    except Exception as e:
        logger.error(f"Unexpected error reading history from {p}: {e}")
        return []


def append_brief(conversation_id: Optional[str], brief: ResearchBrief):
    """Append brief to conversation history with atomic writes"""
    p = _path(conversation_id)
    temp_path = f"{p}.tmp"

    try:
        # Load existing items
        items = []
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if content:
                    items = json.loads(content)
                    if not isinstance(items, list):
                        logger.error("Existing file contains invalid data, starting fresh")
                        items = []
            except Exception as e:
                logger.error(f"Error reading existing history, starting fresh: {e}")
                items = []

        # Add new brief
        items.append(brief.model_dump())

        # Write to temporary file first (atomic write)
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

        # Move temp file to final location (atomic on most systems)
        os.replace(temp_path, p)

        logger.info(f"Successfully appended brief to conversation {conversation_id}")

    except Exception as e:
        logger.error(f"Error appending brief to {p}: {e}")
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warn("Error: ", str(e))
                pass
        raise


def clear_conversation(conversation_id: Optional[str]):
    """Clear conversation history (useful for debugging)"""
    p = _path(conversation_id)
    if os.path.exists(p):
        try:
            os.remove(p)
            logger.info(f"Cleared conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error clearing conversation {conversation_id}: {e}")


def list_conversations() -> List[str]:
    """List all conversation IDs (useful for debugging)"""
    try:
        files = os.listdir(ROOT)
        conversations = [f.replace('.json', '') for f in files if f.endswith('.json')]
        return conversations
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        return []
