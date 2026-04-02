import json
import os

from app.repositories.friends import FriendRepository
from app.repositories.users import UserRepository
from app.models.friend import UserSearchResult
from app.utils.logger import get_service_logger
from typing import List, Dict, Any, Optional, Literal, Set

_PERSON_PARSE_PROMPT = """\
You are a profile trait extractor for a people-matching app.
Given a natural language description of a person the user wants to meet, extract traits and rewrite them in the same structured format used for user profiles.

Output ONLY a plain text string (no JSON, no markdown) in this format — omit any line whose value is unknown:
Interests: <comma-separated interest keywords>
Profession: <profession or field if mentioned>
Bio: <short descriptive phrase capturing personality, lifestyle, or vibe>

Examples:
"someone who likes japanese food and hikes on weekends" →
Interests: japanese food, hiking, outdoors

"looking for a software engineer who loves coffee and jazz" →
Profession: software engineer
Interests: coffee, jazz music

"someone adventurous who travels and does yoga" →
Interests: travel, yoga, adventure
Bio: adventurous lifestyle, loves exploring new places
"""


async def _enrich_user_query(description: str) -> str:
    """Use GPT-4o-mini to reformat a conversational description into profile-structured text.
    Falls back to the raw description if OpenAI is unavailable.
    """
    try:
        from openai import AsyncOpenAI
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            return description
        client = AsyncOpenAI(api_key=key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _PERSON_PARSE_PROMPT},
                {"role": "user", "content": description},
            ],
            temperature=0,
            max_tokens=100,
        )
        enriched = (response.choices[0].message.content or "").strip()
        return enriched if enriched else description
    except Exception:
        return description

class UserDiscoveryService:
    """Service for discovering and searching users"""
    
    def __init__(self, friend_repo: Optional[FriendRepository] = None, user_repo: Optional[UserRepository] = None):
        self.friend_repo = friend_repo or FriendRepository()
        self.user_repo = user_repo or UserRepository()
        self.logger = get_service_logger(__name__)

    async def search_users(self, search_term: str, user_email: str, limit: int = 20) -> List[UserSearchResult]:
        """Search for users and include friendship status"""
        try:
            # Validate current user exists
            current_user = await self.user_repo.get_by_email(user_email)
            if not current_user:
                return []
            
            # Use user repository to search for users
            users_data = await self.user_repo.search_users(search_term, user_email, limit)
            
            search_results = []
            for user_data in users_data:
                # Get friendship status using existing repository methods
                request = await self.friend_repo.find_request_between_users(user_email, user_data.get("email", ""), ["accepted"])
                if request:
                    friendship_status = "friends"
                else:
                    # Check for pending requests
                    pending_request = await self.friend_repo.find_request_between_users(
                        user_email,
                        user_data.get("email", ""),
                        ["pending"],
                    )
                    if pending_request:
                        if pending_request["sender_id"] == user_email:
                            friendship_status = "pending_sent"
                        else:
                            friendship_status = "pending_received"
                    else:
                        friendship_status = "none"
                
                # Ensure friendship_status is one of the valid literal values
                valid_status: Literal["friends", "pending_sent", "pending_received", "none"] = "none"
                if friendship_status in ["friends", "pending_sent", "pending_received", "none"]:
                    valid_status = friendship_status  # type: ignore
                
                user_result = UserSearchResult(
                    id=user_data.get("id", user_data.get("email", "")),  # Use ID or email as fallback
                    name=user_data.get("name", ""),
                    email=user_data.get("email", ""),
                    bio=user_data.get("bio"),
                    profile_picture=user_data.get("profile_picture"),
                    location=user_data.get("location"),
                    interests=user_data.get("interests", []),
                    friendship_status=valid_status
                )
                search_results.append(user_result)
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error searching users: {str(e)}")
            return []

    async def get_user_suggestions(self, user_email: str, limit: int = 10) -> List[UserSearchResult]:
        """Get friend suggestions based on shared interests.
        Single query — joins out already-connected users instead of N+1 checks.
        """
        try:
            current_user = await self.user_repo.get_by_email(user_email)
            if not current_user:
                return []

            user_interests = current_user.get("interests") or []
            if not user_interests:
                return []

            from sqlalchemy import text
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT u.email, u.name, u.bio, u.profile_picture,
                           u.interests, u.latitude, u.longitude,
                           u.city, u.state, u.country, u.formatted_address, u.location_name
                    FROM users u
                    WHERE u.email != :me
                      AND u.interests && :interests
                      AND NOT EXISTS (
                          SELECT 1 FROM friend_requests fr
                          WHERE (fr.sender_id = :me AND fr.receiver_id = u.email)
                             OR (fr.receiver_id = :me AND fr.sender_id = u.email)
                      )
                    LIMIT :limit
                """), {
                    "me": user_email,
                    "interests": user_interests,
                    "limit": limit,
                })
                rows = result.fetchall()

            from app.repositories.users.user_repository import _row_to_user_dict
            suggestions = []
            for row in rows:
                u = _row_to_user_dict(row)
                suggestions.append(UserSearchResult(
                    id=u.get("email", ""),
                    name=u.get("name", ""),
                    email=u.get("email", ""),
                    bio=u.get("bio"),
                    profile_picture=u.get("profile_picture"),
                    location=u.get("location"),
                    interests=u.get("interests", []),
                    friendship_status="none",
                ))
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting user suggestions: {str(e)}")
            return []

    async def search_users_semantic(
        self,
        description: str,
        user_email: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search users by natural language description using pgvector similarity.

        Embeds the description and finds users whose profile embedding is closest.
        Excludes the requester, existing friends, and pending-request users.
        """
        from app.services.embedding_service import (
            EmbeddingProviderError,
            EmbeddingUnavailableError,
            generate_query_embedding,
        )
        from fastapi import HTTPException

        if not description or not description.strip():
            return []

        # Guard: verify the caller still exists in the DB (mirrors search_users()).
        # Uses get_by_email_strict so a DB outage raises (→ 503) rather than being
        # misreported as a missing account (→ 401).
        try:
            caller = await self.user_repo.get_by_email_strict(user_email)
        except Exception as e:
            self.logger.error(f"[SemanticSearch] DB error checking caller {user_email}: {e}", exc_info=True)
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        if caller is None:
            raise HTTPException(status_code=401, detail="Account not found")

        # Permanent misconfiguration → 503, no point attempting the call.
        # Transient provider failure → also 503 (caller should retry, not cache [] as 'no results').
        enriched = await _enrich_user_query(description)
        self.logger.info(f"[SemanticSearch] query='{description}' → enriched='{enriched}'")
        try:
            query_embedding = await generate_query_embedding(enriched)
        except EmbeddingUnavailableError as e:
            self.logger.error(f"[SemanticSearch] Embedding service not configured: {e}")
            raise HTTPException(status_code=503, detail="Semantic search is not available")
        except EmbeddingProviderError as e:
            self.logger.warning(f"[SemanticSearch] Embedding provider error (transient): {e}")
            raise HTTPException(status_code=503, detail="Semantic search temporarily unavailable")

        # Build exclusion set using strict queries so a DB failure cannot silently
        # collapse the exclusion set and leak friends/pending users into results.
        try:
            excluded: Set[str] = {user_email}
            excluded.update(await self.friend_repo.get_accepted_friendship_ids_strict(user_email))
            pending = await self.friend_repo.get_requests_for_user_strict(user_email, direction="all", status="pending")
            for r in pending:
                excluded.add(r.get("sender_id", ""))
                excluded.add(r.get("receiver_id", ""))
            excluded.discard("")
        except Exception as e:
            self.logger.error(f"[SemanticSearch] DB error building exclusion set: {e}", exc_info=True)
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")

        users_data = await self.user_repo.get_semantic_matches(
            user_email=user_email,
            embedding=query_embedding,
            limit=limit,
            excluded_emails=list(excluded),
        )

        results = []
        for u in users_data:
            results.append({
                "id": u.get("id", u.get("email", "")),
                "name": u.get("name", ""),
                "email": u.get("email", ""),
                "bio": u.get("bio"),
                "profession": u.get("profession"),
                "profile_picture": u.get("profile_picture"),
                "location": u.get("location"),
                "interests": list(u.get("interests") or []),
                "vibe_description": u.get("vibe_description"),
                "similarity_score": round(float(u.get("similarity_score") or 0), 4),
                "friendship_status": "none",
            })
        return results


# Create service instance
user_discovery_service = UserDiscoveryService()
