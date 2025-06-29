from datetime import datetime
from google.cloud.firestore_v1 import Query, CollectionReference
from app.auth.firebase_init import get_firestore_client
from app.models.pagination import PaginationParams, EventFilters
from app.utils.logger import get_repository_logger
from typing import Optional, Union

class BaseRepository:
    """Base repository with common query building methods"""
    
    def __init__(self, collection_name: str):
        self.db = get_firestore_client()
        self.collection = self.db.collection(collection_name)
        self.logger = get_repository_logger(__name__)

    def _apply_base_filters(self, query: Union[Query, CollectionReference], include_archived: bool = False) -> Query:
        """Apply base filters that are common across most queries"""
        # Convert CollectionReference to Query if needed
        if isinstance(query, CollectionReference):
            # Create a simple query to convert CollectionReference to Query
            query = query.limit(1000000)  # Large limit to get all documents
        
        # Note: For archived filtering, we'll handle it in individual repositories
        # to avoid Firestore's single != limitation when combined with other filters
        return query

    def _apply_non_archived_filter(self, query: Query) -> Query:
        """Apply non-archived filter - use this method separately when needed"""
        # Filter for events where isArchived is false
        return query.where("isArchived", "==", False)

    def _apply_location_filters(self, query: Query, city: Optional[str] = None, state: Optional[str] = None) -> Query:
        """Apply location-based filters"""
        if city:
            query = query.where("location.city", "==", city)
        if state:
            query = query.where("location.state", "==", state)
        return query

    def _apply_user_filters(self, query: Query, creator_email: Optional[str] = None, user_email: Optional[str] = None, 
                           organizer_email: Optional[str] = None, moderator_email: Optional[str] = None, 
                           rsvp_email: Optional[str] = None) -> Query:
        """Apply user-related filters"""
        if creator_email:
            query = query.where("createdByEmail", "==", creator_email)
        if organizer_email:
            query = query.where("organizers", "array_contains", organizer_email)
        if moderator_email:
            query = query.where("moderators", "array_contains", moderator_email)
        if rsvp_email:
            query = query.where("rsvpList", "array_contains", rsvp_email)
        return query

    def _apply_event_filters(self, query: Query, filters: Optional[EventFilters] = None) -> Query:
        """Apply event-specific filters from EventFilters object"""
        if not filters:
            return query
            
        if filters.city:
            query = query.where("location.city", "==", filters.city)
        if filters.state:
            query = query.where("location.state", "==", filters.state)
        if filters.category:
            query = query.where("categories", "array_contains", filters.category)
        if filters.is_online is not None:
            query = query.where("isOnline", "==", filters.is_online)
        if filters.creator_email:
            query = query.where("createdByEmail", "==", filters.creator_email)
        if filters.start_date:
            query = query.where("startTime", ">=", filters.start_date)
        if filters.end_date:
            query = query.where("startTime", "<=", filters.end_date)
        return query

    def _apply_origin_filter(self, query: Query, origin: Optional[str] = None) -> Query:
        """Apply origin filter (external, community, etc.)"""
        if origin:
            query = query.where("origin", "==", origin)
        return query

    def _apply_archived_filter(self, query: Query, archived_only: bool = False, user_email: Optional[str] = None) -> Query:
        """Apply archived event filters"""
        if archived_only:
            query = query.where("isArchived", "==", True)
            if user_email:
                query = query.where("createdByEmail", "==", user_email)
        return query

    def _apply_sorting(self, query: Query, sort_by: str = "createdAt", direction: str = "DESCENDING") -> Query:
        """Apply sorting to query"""
        return query.order_by(sort_by, direction=direction)

    def _apply_pagination(self, query: Query, pagination: PaginationParams) -> Query:
        """Apply pagination to query"""
        return query.offset(pagination.offset).limit(pagination.page_size)

    def _get_total_count(self, query: Query) -> int:
        """Get total count for pagination metadata"""
        return len(list(query.stream()))

    def get_by_id(self, doc_id: str) -> dict | None:
        """Generic get by ID method"""
        doc = self.collection.document(doc_id).get()
        return doc.to_dict() if doc.exists else None

    def update_by_id(self, doc_id: str, update_data: dict) -> bool:
        """Generic update by ID method"""
        doc_ref = self.collection.document(doc_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.update(update_data)
        return True

    def delete_by_id(self, doc_id: str) -> bool:
        """Generic delete by ID method"""
        doc_ref = self.collection.document(doc_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True
