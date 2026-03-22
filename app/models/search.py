from typing import Optional
from pydantic import BaseModel


class ParsedSearchQuery(BaseModel):
    """
    Structured intent extracted from a natural language event search query
    by GPT-4o-mini. Hard filters (city, state, dates) are passed directly to
    SQL; keywords feeds the ILIKE fulltext condition.
    """
    city: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None          # one of the canonical category values
    keywords: Optional[str] = None          # vibe/descriptor words for ILIKE match
    is_online: Optional[bool] = None
    start_date: Optional[str] = None        # ISO date string e.g. "2025-04-01"
    end_date: Optional[str] = None          # ISO date string
