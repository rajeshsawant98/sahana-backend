"""
Embedding generation and storage for users and events.
Uses OpenAI text-embedding-3-small (1536 dims) to match the embedding columns.
"""
import logging
import os

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.utils.logger import get_service_logger

logger = get_service_logger(__name__)

_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        try:
            from openai import AsyncOpenAI
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                logger.warning("OPENAI_API_KEY not set — embedding generation unavailable")
                return None
            _openai_client = AsyncOpenAI(api_key=key)
        except ImportError:
            logger.warning("openai package not installed")
            return None
    return _openai_client


def _build_user_text(user: dict) -> str:
    """Concatenate user fields into a single string for embedding."""
    parts = []
    if user.get("name"):
        parts.append(user["name"] + ".")
    if user.get("profession"):
        parts.append(user["profession"] + ".")
    if user.get("bio"):
        parts.append(user["bio"] + ".")
    interests = user.get("interests") or []
    if interests:
        parts.append("Interests: " + ", ".join(interests) + ".")
    if user.get("vibe_description"):
        parts.append("Looking for: " + user["vibe_description"] + ".")
    return " ".join(parts).strip()


async def generate_user_embedding(user: dict) -> list[float] | None:
    """Generate an embedding vector for a user dict. Returns None if unavailable."""
    client = _get_openai_client()
    if not client:
        return None
    text_input = _build_user_text(user)
    if not text_input:
        return None
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text_input,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding for {user.get('email')}: {e}")
        return None


async def store_user_embedding(email: str, embedding: list[float]) -> None:
    """Persist an embedding vector to users.embedding."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("UPDATE users SET embedding = :emb WHERE email = :email"),
                {"emb": str(embedding), "email": email},
            )
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to store embedding for {email}: {e}")


async def generate_and_store_user_embedding(user: dict) -> bool:
    """Generate embedding and store it. Returns True on success."""
    embedding = await generate_user_embedding(user)
    if embedding is None:
        return False
    await store_user_embedding(user["email"], embedding)
    return True


# ---------------------------------------------------------------------------
# Event embeddings
# ---------------------------------------------------------------------------

def _build_event_text(event: dict) -> str:
    """Concatenate event fields into a single string for embedding."""
    cats = ", ".join(event.get("categories") or [])
    parts = []
    if event.get("event_name"):
        parts.append(event["event_name"] + ".")
    if event.get("description"):
        parts.append(event["description"] + ".")
    if cats:
        parts.append("Categories: " + cats + ".")
    city = event.get("city", "")
    state = event.get("state", "")
    if city or state:
        parts.append("Location: " + ", ".join(filter(None, [city, state])) + ".")
    return " ".join(parts).strip()


async def generate_event_embedding(event: dict) -> list[float] | None:
    """Generate an embedding vector for an event dict. Returns None if unavailable."""
    client = _get_openai_client()
    if not client:
        return None
    text_input = _build_event_text(event)
    if not text_input:
        return None
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text_input,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding for event {event.get('event_id')}: {e}")
        return None


async def store_event_embedding(event_id: str, embedding: list[float]) -> None:
    """Persist an embedding vector to events.embedding."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("UPDATE events SET embedding = :emb WHERE event_id = :event_id"),
                {"emb": str(embedding), "event_id": event_id},
            )
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to store embedding for event {event_id}: {e}")


async def generate_and_store_event_embedding(event: dict) -> bool:
    """Generate event embedding and store it. Returns True on success."""
    embedding = await generate_event_embedding(event)
    if embedding is None:
        return False
    await store_event_embedding(event["event_id"], embedding)
    return True


# ---------------------------------------------------------------------------
# Query embedding (for semantic search)
# ---------------------------------------------------------------------------

async def generate_query_embedding(query_text: str) -> list[float] | None:
    """Embed a raw NL search query for vector similarity search."""
    client = _get_openai_client()
    if not client:
        return None
    if not query_text or not query_text.strip():
        return None
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=query_text.strip(),
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return None
