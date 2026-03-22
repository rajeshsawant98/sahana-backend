from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.utils.logger import get_service_logger


def _row_to_dict(row) -> Dict[str, Any]:
    return dict(row._mapping)


class FriendRepository:
    """
    Repository for friend request data access.
    Contains ONLY data access logic - no business rules.
    """

    def __init__(self):
        self.logger = get_service_logger(__name__)

    # ==================== BASIC CRUD OPERATIONS ====================

    async def create_friend_request(self, sender_id: str, receiver_id: str) -> str:
        request_id = str(uuid.uuid4())
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    INSERT INTO friend_requests (id, sender_id, receiver_id, status)
                    VALUES (:id, :sender_id, :receiver_id, 'pending')
                """), {"id": request_id, "sender_id": sender_id, "receiver_id": receiver_id})
                await session.commit()
            return request_id
        except Exception as e:
            self.logger.error(f"Error creating friend request: {e}")
            raise

    async def get_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text("SELECT * FROM friend_requests WHERE id = :id"),
                    {"id": request_id}
                )
                row = result.fetchone()
                return _row_to_dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting request by ID: {e}")
            return None

    async def update_friend_request_status(self, request_id: str, status: str) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    UPDATE friend_requests
                    SET status = :status, updated_at = NOW()
                    WHERE id = :id
                """), {"id": request_id, "status": status})
                await session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating friend request status: {e}")
            return False

    async def delete_friend_request(self, request_id: str) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("DELETE FROM friend_requests WHERE id = :id"),
                    {"id": request_id}
                )
                await session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting friend request: {e}")
            return False

    # ==================== SIMPLE QUERY OPERATIONS ====================

    async def find_request_between_users(
        self, user1_id: str, user2_id: str, statuses: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        if statuses is None:
            statuses = ["pending", "accepted"]
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT * FROM friend_requests
                    WHERE status = ANY(:statuses)
                      AND (
                            (sender_id = :u1 AND receiver_id = :u2)
                         OR (sender_id = :u2 AND receiver_id = :u1)
                      )
                    LIMIT 1
                """), {"statuses": statuses, "u1": user1_id, "u2": user2_id})
                row = result.fetchone()
                return _row_to_dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error finding request between users: {e}")
            return None

    async def get_requests_for_user(
        self, user_id: str, direction: str = "all", status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            requests = []
            async with AsyncSessionLocal() as session:
                if direction in ("received", "all"):
                    q = "SELECT * FROM friend_requests WHERE receiver_id = :uid"
                    params: Dict[str, Any] = {"uid": user_id}
                    if status:
                        q += " AND status = :status"
                        params["status"] = status
                    result = await session.execute(text(q), params)
                    for row in result.fetchall():
                        d = _row_to_dict(row)
                        d["direction"] = "received"
                        requests.append(d)

                if direction in ("sent", "all"):
                    q = "SELECT * FROM friend_requests WHERE sender_id = :uid"
                    params = {"uid": user_id}
                    if status:
                        q += " AND status = :status"
                        params["status"] = status
                    result = await session.execute(text(q), params)
                    for row in result.fetchall():
                        d = _row_to_dict(row)
                        d["direction"] = "sent"
                        requests.append(d)

            return requests
        except Exception as e:
            self.logger.error(f"Error getting requests for user: {e}")
            return []

    async def get_accepted_friendship_ids(self, user_id: str) -> List[str]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT
                        CASE
                            WHEN sender_id = :uid THEN receiver_id
                            ELSE sender_id
                        END AS friend_id
                    FROM friend_requests
                    WHERE status = 'accepted'
                      AND (sender_id = :uid OR receiver_id = :uid)
                """), {"uid": user_id})
                return [row.friend_id for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting friend IDs: {e}")
            return []

    async def get_request_by_sender_receiver(
        self, sender_id: str, receiver_id: str
    ) -> Optional[Dict[str, Any]]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT * FROM friend_requests
                    WHERE sender_id = :sender_id AND receiver_id = :receiver_id
                    LIMIT 1
                """), {"sender_id": sender_id, "receiver_id": receiver_id})
                row = result.fetchone()
                return _row_to_dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting request by sender/receiver: {e}")
            return None
