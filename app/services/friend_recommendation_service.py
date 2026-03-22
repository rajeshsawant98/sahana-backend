from __future__ import annotations

from dataclasses import dataclass
from math import radians, sin, cos, asin, sqrt
from typing import Any, Dict, List, Optional, Set, Tuple

from app.repositories.friends import FriendRepository
from app.repositories.users import UserRepository
from app.repositories.events.event_query_repository import EventQueryRepository
from app.utils.logger import get_service_logger


@dataclass
class _ScoredCandidate:
    email: str
    score: float
    reasons: Dict[str, Any]
    profile: Dict[str, Any]


def _haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Great-circle distance between two (lat, lon) points in KM."""
    lat1, lon1 = a
    lat2, lon2 = b
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(h))


class FriendRecommendationService:
    """Friend recommendations for "Find Friends".

    MVP goal: useful recommendations without adding new infrastructure.
    Long term: this becomes the orchestrator that can read from Neo4j / embeddings.
    """

    def __init__(
        self,
        friend_repo: Optional[FriendRepository] = None,
        user_repo: Optional[UserRepository] = None,
        event_query_repo: Optional[EventQueryRepository] = None,
    ):
        self.friend_repo = friend_repo or FriendRepository()
        self.user_repo = user_repo or UserRepository()
        self.event_query_repo = event_query_repo or EventQueryRepository()
        self.logger = get_service_logger(__name__)

    async def recommend(
        self,
        user_email: str,
        limit: int = 20,
        radius_km: float = 25.0,
        min_common_interests: int = 1,
    ) -> List[Dict[str, Any]]:
        """Return ranked friend recommendations.

        This implementation is intentionally simple and Firestore-only.
        It *will* become slow as user count grows (O(N)), so we also return
        reasons + score to help you evaluate and later move to a graph/vector index.
        """

        me = await self.user_repo.get_by_email(user_email)
        if not me:
            return []

        # Exclusions: self + accepted + any pending in either direction
        excluded: Set[str] = {user_email}
        excluded.update(await self.friend_repo.get_accepted_friendship_ids(user_email))
        pending = await self.friend_repo.get_requests_for_user(user_email, direction="all", status="pending")
        for r in pending:
            excluded.add(r.get("sender_id", ""))
            excluded.add(r.get("receiver_id", ""))

        me_interests = set((me.get("interests") or []))
        me_loc = (me.get("location") or {})
        me_coords: Optional[Tuple[float, float]] = None
        if me_loc.get("latitude") is not None and me_loc.get("longitude") is not None:
            try:
                me_coords = (float(me_loc["latitude"]), float(me_loc["longitude"]))
            except Exception:
                me_coords = None

        # Optional: use nearby events to build an "attended categories" signature.
        attended_cats_by_user: Dict[str, Set[str]] = {}
        try:
            city = (me_loc.get("city") or "").strip()
            state = (me_loc.get("state") or "").strip()
            if city:
                nearby_events = await self.event_query_repo.get_external_events(city=city, state=state)
                for ev in nearby_events:
                    cats = set((ev.get("categories") or []))
                    for rsvp in (ev.get("rsvpList") or []):
                        if rsvp.get("status") == "attended":
                            email = rsvp.get("email")
                            if email:
                                attended_cats_by_user.setdefault(email, set()).update(cats)
        except Exception as e:
            # This should never break recommendations; it just weakens the score.
            self.logger.warning(f"Failed to build attended-category signatures: {e}")

        me_attended = attended_cats_by_user.get(user_email, set())

        # Candidate pool (MVP): stream all users and rank.
        # NOTE: This will not scale to very large user bases.
        candidates = await self.user_repo.get_all_users()

        scored: List[_ScoredCandidate] = []
        for u in candidates:
            email = u.get("email")
            if not email or email in excluded:
                continue

            other_interests = set((u.get("interests") or []))
            common_interests = sorted(list(me_interests & other_interests))
            if len(common_interests) < min_common_interests:
                continue

            # Distance score (only if both have coordinates)
            dist_km: Optional[float] = None
            loc = (u.get("location") or {})
            other_coords: Optional[Tuple[float, float]] = None
            if loc.get("latitude") is not None and loc.get("longitude") is not None:
                try:
                    other_coords = (float(loc["latitude"]), float(loc["longitude"]))
                except Exception:
                    other_coords = None

            geo_score = 0.0
            if me_coords and other_coords:
                dist_km = _haversine_km(me_coords, other_coords)
                if dist_km <= radius_km:
                    # closer => higher (0..1)
                    geo_score = max(0.0, 1.0 - (dist_km / max(radius_km, 1.0)))
                else:
                    # too far for "nearby" recommendations
                    continue
            else:
                # If we don't have coords, fall back to same city/state if present
                if (me_loc.get("city") and loc.get("city")) and (str(me_loc.get("city")).lower() != str(loc.get("city")).lower()):
                    continue

            # Interest similarity (Jaccard)
            denom = max(1, len(me_interests | other_interests))
            interest_score = len(me_interests & other_interests) / denom

            # Attended-category similarity (soft signal)
            other_attended = attended_cats_by_user.get(email, set())
            attended_overlap = len(me_attended & other_attended)
            attended_score = 0.0
            if me_attended:
                attended_score = attended_overlap / max(1, len(me_attended))

            # Weighted score (tunable)
            score = (0.55 * interest_score) + (0.30 * geo_score) + (0.15 * attended_score)

            scored.append(
                _ScoredCandidate(
                    email=email,
                    score=score,
                    reasons={
                        "commonInterests": common_interests,
                        "distanceKm": round(dist_km, 2) if isinstance(dist_km, float) else None,
                        "sharedAttendedCategories": sorted(list(me_attended & other_attended))[:10],
                        "interestScore": round(interest_score, 4),
                        "geoScore": round(geo_score, 4),
                        "attendedScore": round(attended_score, 4),
                    },
                    profile={
                        "id": u.get("id", email),
                        "name": u.get("name", ""),
                        "email": email,
                        "bio": u.get("bio", ""),
                        "profession": u.get("profession", ""),
                        "profile_picture": u.get("profile_picture", ""),
                        "location": u.get("location"),
                        "interests": list(other_interests),
                    },
                )
            )

        scored.sort(key=lambda x: x.score, reverse=True)
        top = scored[: max(1, min(limit, 100))]

        return [
            {
                **c.profile,
                "score": round(c.score, 4),
                "reasons": c.reasons,
            }
            for c in top
        ]
