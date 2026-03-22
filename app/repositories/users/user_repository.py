from datetime import date
from passlib.context import CryptContext
from sqlalchemy import text
from typing import Any, Dict, List, Optional, Tuple

from app.db.session import AsyncSessionLocal
from app.models.pagination import CursorInfo, CursorPaginationParams, PaginationParams, UserFilters
from app.utils.logger import get_service_logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _row_to_user_dict(row) -> Dict[str, Any]:
    """Convert a DB row to the dict shape the service layer expects.
    Preserves camelCase field names that Firestore used so the service layer
    doesn't need to change in this phase.
    """
    d = dict(row._mapping)
    # location nested object (service layer expects this shape)
    d["location"] = {
        "latitude": d.pop("latitude", None),
        "longitude": d.pop("longitude", None),
        "city": d.pop("city", None),
        "state": d.pop("state", None),
        "country": d.pop("country", None),
        "formattedAddress": d.pop("formatted_address", None),
        "name": d.pop("location_name", None),
    }
    # camelCase aliases expected by service layer
    d["phoneNumber"] = d.pop("phone_number", None)
    d["password"] = d.pop("password_hash", None)
    d["id"] = d["email"]
    # Convert date object → ISO string so UserResponse (str field) validates correctly
    if d.get("birthdate") is not None and hasattr(d["birthdate"], "isoformat"):
        d["birthdate"] = d["birthdate"].isoformat()
    return d


class UserRepository:
    def __init__(self):
        self.logger = get_service_logger(__name__)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _build_filter_clause(self, filters: Optional[UserFilters]) -> Tuple[str, Dict[str, Any]]:
        conditions, params = [], {}
        if filters:
            if filters.role:
                conditions.append("role = :role")
                params["role"] = filters.role
            if filters.profession:
                conditions.append("profession = :profession")
                params["profession"] = filters.profession
        clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        return clause, params

    # ─── Read ─────────────────────────────────────────────────────────────────

    async def get_all_users(self) -> List[Dict[str, Any]]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT * FROM users"))
                return [_row_to_user_dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Error retrieving users: {e}")
            return []

    async def get_all_users_paginated(
        self, pagination: PaginationParams, filters: Optional[UserFilters] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        try:
            where, params = self._build_filter_clause(filters)
            params["limit"] = pagination.page_size
            params["offset"] = pagination.offset
            async with AsyncSessionLocal() as session:
                result = await session.execute(text(f"""
                    SELECT *, COUNT(*) OVER() AS _total
                    FROM users
                    {where}
                    ORDER BY email
                    LIMIT :limit OFFSET :offset
                """), params)
                rows = result.fetchall()
                total = rows[0]._mapping["_total"] if rows else 0
                users = []
                for row in rows:
                    d = _row_to_user_dict(row)
                    d.pop("_total", None)
                    users.append(d)
                return users, total
        except Exception as e:
            self.logger.error(f"Error retrieving paginated users: {e}")
            return [], 0

    async def get_all_users_cursor_paginated(
        self, cursor_params: CursorPaginationParams, filters: Optional[UserFilters] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        try:
            cursor_info = None
            if cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if not cursor_info:
                    raise ValueError("Invalid cursor format")

            where_parts = []
            params: Dict[str, Any] = {"limit": cursor_params.page_size + 1}

            filter_clause, filter_params = self._build_filter_clause(filters)
            params.update(filter_params)
            if filter_clause:
                where_parts.append(filter_clause.replace("WHERE ", ""))

            if cursor_info and cursor_info.start_time:
                if cursor_params.direction == "next":
                    where_parts.append("email > :cursor_email")
                else:
                    where_parts.append("email < :cursor_email")
                params["cursor_email"] = cursor_info.start_time

            where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
            order = "ASC" if cursor_params.direction == "next" else "DESC"

            async with AsyncSessionLocal() as session:
                result = await session.execute(text(f"""
                    SELECT * FROM users
                    {where}
                    ORDER BY email {order}
                    LIMIT :limit
                """), params)
                rows = result.fetchall()

            users = [_row_to_user_dict(row) for row in rows]

            if cursor_params.direction == "prev":
                users.reverse()

            has_more = len(users) > cursor_params.page_size
            if has_more:
                if cursor_params.direction == "next":
                    users = users[:cursor_params.page_size]
                else:
                    users = users[-cursor_params.page_size:]

            has_next = has_more if cursor_params.direction == "next" else cursor_params.cursor is not None
            has_prev = cursor_params.cursor is not None if cursor_params.direction == "next" else has_more

            next_cursor = prev_cursor = None
            if users:
                if has_next:
                    next_cursor = CursorInfo(
                        start_time=users[-1]["email"], event_id=users[-1]["email"]
                    ).encode()
                if has_prev:
                    prev_cursor = CursorInfo(
                        start_time=users[0]["email"], event_id=users[0]["email"]
                    ).encode()

            return users, next_cursor, prev_cursor, has_next, has_prev

        except Exception as e:
            self.logger.error(f"Error in users cursor pagination: {e}", exc_info=True)
            return [], None, None, False, False

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text("SELECT * FROM users WHERE email = :email"),
                    {"email": email}
                )
                row = result.fetchone()
                return _row_to_user_dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error retrieving user: {e}")
            return None

    async def get_by_emails(self, emails: List[str]) -> Dict[str, Any]:
        """Fetch multiple users by email in a single query. Returns dict keyed by email."""
        if not emails:
            return {}
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text("SELECT * FROM users WHERE email = ANY(:emails)"),
                    {"emails": list(emails)}
                )
                return {row._mapping["email"]: _row_to_user_dict(row) for row in result.fetchall()}
        except Exception as e:
            self.logger.error(f"Error bulk-fetching users: {e}")
            return {}

    async def get_by_id(self, uid: str) -> Optional[Dict[str, Any]]:
        """uid is email (Firestore used email as document ID)."""
        return await self.get_by_email(uid)

    async def verify_password(self, email: str, password: str) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text("SELECT password_hash FROM users WHERE email = :email"),
                    {"email": email}
                )
                row = result.fetchone()
                if not row or not row.password_hash:
                    return False
                return pwd_context.verify(password, row.password_hash)
        except Exception as e:
            self.logger.error(f"Error verifying password: {e}")
            return False

    async def search_users(self, search_term: str, exclude_email: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search users by name or email using SQL — replaces full-table scan."""
        if not search_term or len(search_term.strip()) < 2:
            return []
        term = search_term.strip().lower()
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT *,
                        CASE
                            WHEN lower(name)  = :term              THEN 100
                            WHEN lower(name)  ILIKE :prefix        THEN 90
                            WHEN lower(name)  ILIKE :any_word      THEN 80
                            WHEN lower(name)  ILIKE :contains      THEN 70
                            WHEN lower(email) ILIKE :contains      THEN 50
                            ELSE 0
                        END AS _score
                    FROM users
                    WHERE email != :exclude
                      AND (
                            lower(name)  ILIKE :contains
                         OR lower(email) ILIKE :contains
                      )
                    ORDER BY _score DESC
                    LIMIT :limit
                """), {
                    "term": term,
                    "prefix": term + "%",
                    "any_word": "% " + term + "%",
                    "contains": "%" + term + "%",
                    "exclude": exclude_email,
                    "limit": limit,
                })
                users = []
                for row in result.fetchall():
                    d = _row_to_user_dict(row)
                    d.pop("_score", None)
                    users.append(d)
                return users
        except Exception as e:
            self.logger.error(f"Error searching users: {e}")
            return []

    async def get_semantic_matches(
        self,
        user_email: str,
        embedding: List[float],
        city: Optional[str] = None,
        limit: int = 20,
        excluded_emails: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Return users ranked by cosine similarity to the given embedding.
        Excludes the requesting user, existing connections, and pending requests.
        Optionally filters to same city.
        """
        try:
            excluded = list(set([user_email] + (excluded_emails or [])))
            params: Dict[str, Any] = {
                "embedding": str(embedding),
                "excluded": excluded,
                "limit": limit,
            }
            city_clause = ""
            if city:
                city_clause = "AND LOWER(u.city) = LOWER(:city)"
                params["city"] = city

            async with AsyncSessionLocal() as session:
                result = await session.execute(text(f"""
                    SELECT u.*,
                           1 - (u.embedding <=> CAST(:embedding AS vector)) AS similarity_score
                    FROM users u
                    WHERE u.email != ALL(:excluded)
                      AND u.embedding IS NOT NULL
                      {city_clause}
                    ORDER BY u.embedding <=> CAST(:embedding AS vector) ASC
                    LIMIT :limit
                """), params)
                rows = result.fetchall()

            users = []
            for row in rows:
                d = _row_to_user_dict(row)
                d["similarity_score"] = float(row._mapping.get("similarity_score") or 0)
                users.append(d)
            return users
        except Exception as e:
            self.logger.error(f"Error in semantic match query: {e}", exc_info=True)
            return []

    # ─── Write ────────────────────────────────────────────────────────────────

    async def create_with_password(self, email: str, password: str, name: str) -> None:
        try:
            hashed = pwd_context.hash(password)
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    INSERT INTO users (email, name, password_hash, role)
                    VALUES (:email, :name, :hash, 'user')
                    ON CONFLICT (email) DO NOTHING
                """), {"email": email, "name": name, "hash": hashed})
                await session.commit()
            self.logger.info(f"User {email} created.")
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")

    async def store_google_user(self, user_data: Dict[str, Any]) -> None:
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    INSERT INTO users (email, name, profile_picture, google_uid, role)
                    VALUES (:email, :name, :pic, :uid, 'user')
                    ON CONFLICT (email) DO UPDATE SET
                        name            = EXCLUDED.name,
                        profile_picture = EXCLUDED.profile_picture,
                        google_uid      = EXCLUDED.google_uid,
                        updated_at      = NOW()
                """), {
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "pic": user_data.get("profile_picture"),
                    "uid": user_data.get("uid"),
                })
                await session.commit()
            self.logger.info(f"Google user stored: {user_data['email']}")
        except Exception as e:
            self.logger.error(f"Error storing Google user: {e}")

    async def update_profile_by_email(self, user_data: Dict[str, Any], user_email: str) -> None:
        try:
            loc = user_data.get("location") or {}
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    UPDATE users SET
                        name              = COALESCE(:name, name),
                        profile_picture   = COALESCE(:profile_picture, profile_picture),
                        interests         = COALESCE(:interests, interests),
                        profession        = COALESCE(:profession, profession),
                        bio               = COALESCE(:bio, bio),
                        phone_number      = COALESCE(:phone_number, phone_number),
                        birthdate         = COALESCE(:birthdate, birthdate),
                        latitude          = COALESCE(:latitude, latitude),
                        longitude         = COALESCE(:longitude, longitude),
                        city              = COALESCE(:city, city),
                        state             = COALESCE(:state, state),
                        country           = COALESCE(:country, country),
                        formatted_address = COALESCE(:formatted_address, formatted_address),
                        location_name     = COALESCE(:location_name, location_name),
                        vibe_description  = COALESCE(:vibe_description, vibe_description),
                        updated_at        = NOW()
                    WHERE email = :email
                """), {
                    "email": user_email,
                    "name": user_data.get("name"),
                    "profile_picture": user_data.get("profile_picture"),
                    "interests": user_data.get("interests"),
                    "profession": user_data.get("profession"),
                    "bio": user_data.get("bio"),
                    "phone_number": user_data.get("phoneNumber"),
                    "birthdate": date.fromisoformat(user_data["birthdate"]) if user_data.get("birthdate") else None,
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                    "city": loc.get("city"),
                    "state": loc.get("state"),
                    "country": loc.get("country"),
                    "formatted_address": loc.get("formattedAddress"),
                    "location_name": loc.get("name"),
                    "vibe_description": user_data.get("vibe_description"),
                })
                await session.commit()
            self.logger.info(f"Profile updated: {user_email}")

            # Refresh embedding if any embeddable field changed
            _embedding_fields = {"name", "profession", "bio", "interests", "vibe_description"}
            if any(user_data.get(f) is not None for f in _embedding_fields):
                try:
                    from app.services.embedding_service import generate_and_store_user_embedding
                    updated_user = await self.get_by_email(user_email)
                    if updated_user:
                        await generate_and_store_user_embedding(updated_user)
                except Exception as emb_err:
                    self.logger.warning(f"Embedding refresh failed for {user_email}: {emb_err}")

        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
