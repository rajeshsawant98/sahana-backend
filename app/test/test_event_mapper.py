"""
Unit tests for app/repositories/events/event_mapper.py

Pure unit tests — no DB, no mocking needed for the mapper itself.
"""
import datetime
import types
import pytest
from unittest.mock import MagicMock

from app.repositories.events.event_mapper import (
    parse_datetime,
    row_to_event_dict,
    build_update_params,
)

pytestmark = pytest.mark.asyncio


# ── parse_datetime ─────────────────────────────────────────────────────────────

class TestParseDatetime:

    def test_none_returns_none(self):
        assert parse_datetime(None) is None

    def test_datetime_object_passthrough_with_tz(self):
        dt = datetime.datetime(2025, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        result = parse_datetime(dt)
        assert result == dt
        assert result.tzinfo is not None

    def test_naive_datetime_gets_utc_tz(self):
        dt = datetime.datetime(2025, 6, 1, 12, 0, 0)
        result = parse_datetime(dt)
        assert result.tzinfo == datetime.timezone.utc

    def test_iso_string_with_z(self):
        result = parse_datetime("2025-06-01T12:00:00Z")
        assert isinstance(result, datetime.datetime)
        assert result.year == 2025
        assert result.month == 6

    def test_iso_string_with_offset(self):
        result = parse_datetime("2025-06-01T12:00:00+00:00")
        assert isinstance(result, datetime.datetime)
        assert result.tzinfo is not None

    def test_iso_string_with_milliseconds(self):
        result = parse_datetime("2025-06-01T12:00:00.123456Z")
        assert isinstance(result, datetime.datetime)
        assert result.microsecond == 123456

    def test_bare_date_string_returns_none(self):
        # "2025-06-01" alone does not match any format → returns None
        result = parse_datetime("2025-06-01")
        assert result is None

    def test_garbage_string_returns_none(self):
        assert parse_datetime("not-a-date") is None

    def test_empty_string_returns_none(self):
        assert parse_datetime("") is None

    def test_iso_no_tz_gets_utc_tz(self):
        result = parse_datetime("2025-06-01T12:00:00")
        assert isinstance(result, datetime.datetime)
        assert result.tzinfo == datetime.timezone.utc


# ── row_to_event_dict ─────────────────────────────────────────────────────────

def _make_row(mapping: dict):
    """Create a mock DB row with _mapping attribute."""
    row = MagicMock()
    row._mapping = mapping
    return row


class TestRowToEventDict:

    def _base_mapping(self, **overrides):
        base = {
            "event_id": "evt-001",
            "event_name": "Test Event",
            "start_time": datetime.datetime(2025, 6, 1, 20, 0, 0, tzinfo=datetime.timezone.utc),
            "is_online": False,
            "join_link": None,
            "image_url": None,
            "created_by": "John",
            "created_by_email": "john@example.com",
            "is_archived": False,
            "archived_at": None,
            "archived_by": None,
            "archive_reason": None,
            "unarchived_at": None,
            "created_at": None,
            "updated_at": None,
            "sub_category": None,
            "ticket_name": None,
            "ticket_remaining": None,
            "ticket_currency": None,
            "ticket_price": None,
            "latitude": 30.26,
            "longitude": -97.74,
            "city": "Austin",
            "state": "TX",
            "country": "US",
            "formatted_address": "123 Main St, Austin, TX",
            "location_name": "Test Venue",
            "description": "A test event",
            "categories": [],
            "tags": [],
            "duration": 120,
        }
        base.update(overrides)
        return base

    def test_location_is_nested(self):
        row = _make_row(self._base_mapping())
        result = row_to_event_dict(row)
        loc = result["location"]
        assert loc["city"] == "Austin"
        assert loc["state"] == "TX"
        assert loc["country"] == "US"
        assert loc["latitude"] == 30.26
        assert loc["longitude"] == -97.74
        assert loc["formattedAddress"] == "123 Main St, Austin, TX"
        assert loc["name"] == "Test Venue"
        # flat location columns must not exist at top level
        assert "city" not in result
        assert "latitude" not in result

    def test_ticket_not_nested_when_all_none(self):
        row = _make_row(self._base_mapping())
        result = row_to_event_dict(row)
        assert "ticket" not in result

    def test_ticket_nested_when_at_least_one_set(self):
        row = _make_row(self._base_mapping(ticket_price=10.00, ticket_currency="USD"))
        result = row_to_event_dict(row)
        assert "ticket" in result
        assert result["ticket"]["price"] == 10.00
        assert result["ticket"]["currency"] == "USD"

    def test_snake_to_camel_rename(self):
        row = _make_row(self._base_mapping())
        result = row_to_event_dict(row)
        assert "eventId" in result
        assert "eventName" in result
        assert "isOnline" in result
        assert "createdBy" in result
        assert "createdByEmail" in result
        assert "event_id" not in result
        assert "event_name" not in result

    def test_datetime_fields_are_isoformat_strings(self):
        row = _make_row(self._base_mapping())
        result = row_to_event_dict(row)
        assert isinstance(result["startTime"], str)
        # Should be parseable as ISO datetime
        parsed = datetime.datetime.fromisoformat(result["startTime"])
        assert parsed.year == 2025

    def test_organizers_default_to_empty_list(self):
        row = _make_row(self._base_mapping())
        result = row_to_event_dict(row)
        assert result["organizers"] == []

    def test_moderators_default_to_empty_list(self):
        row = _make_row(self._base_mapping())
        result = row_to_event_dict(row)
        assert result["moderators"] == []

    def test_rsvp_list_default_to_empty_list(self):
        row = _make_row(self._base_mapping())
        result = row_to_event_dict(row)
        assert result["rsvpList"] == []

    def test_organizers_injected(self):
        row = _make_row(self._base_mapping())
        result = row_to_event_dict(row, organizers=["alice@example.com"])
        assert result["organizers"] == ["alice@example.com"]

    def test_moderators_injected(self):
        row = _make_row(self._base_mapping())
        result = row_to_event_dict(row, moderators=["bob@example.com"])
        assert result["moderators"] == ["bob@example.com"]

    def test_rsvp_list_injected(self):
        row = _make_row(self._base_mapping())
        rsvps = [{"email": "user@example.com", "status": "joined"}]
        result = row_to_event_dict(row, rsvp_list=rsvps)
        assert result["rsvpList"] == rsvps

    def test_total_count_column_removed(self):
        mapping = self._base_mapping()
        mapping["_total"] = 42
        row = _make_row(mapping)
        result = row_to_event_dict(row)
        assert "_total" not in result

    def test_ticket_price_converted_to_float(self):
        # ticket_price stored as Decimal in Postgres — test float conversion
        from decimal import Decimal
        row = _make_row(self._base_mapping(ticket_price=Decimal("9.99"), ticket_name="General"))
        result = row_to_event_dict(row)
        assert result["ticket"]["price"] == pytest.approx(9.99)
        assert isinstance(result["ticket"]["price"], float)


# ── build_update_params ────────────────────────────────────────────────────────

class TestBuildUpdateParams:

    def test_camel_to_snake_rename(self):
        params = build_update_params({"eventName": "New Name"})
        assert params["event_name"] == "New Name"

    def test_start_time_string_parsed_to_datetime(self):
        params = build_update_params({"startTime": "2025-07-04T18:00:00Z"})
        assert isinstance(params["start_time"], datetime.datetime)

    def test_location_dict_flattened(self):
        params = build_update_params({
            "location": {
                "city": "Denver",
                "state": "CO",
                "country": "US",
                "latitude": 39.73,
                "longitude": -104.98,
                "formattedAddress": "123 Colfax, Denver",
                "name": "Venue Name",
            }
        })
        assert params["city"] == "Denver"
        assert params["state"] == "CO"
        assert params["latitude"] == 39.73
        assert params["formatted_address"] == "123 Colfax, Denver"
        assert params["location_name"] == "Venue Name"

    def test_unknown_keys_ignored(self):
        params = build_update_params({"unknownField": "value", "anotherBadKey": 123})
        assert "unknownField" not in params
        assert "anotherBadKey" not in params

    def test_description_passes_through(self):
        params = build_update_params({"description": "A great event"})
        assert params["description"] == "A great event"

    def test_categories_passes_through(self):
        params = build_update_params({"categories": ["music", "outdoor"]})
        assert params["categories"] == ["music", "outdoor"]

    def test_is_online_camel_to_snake(self):
        params = build_update_params({"isOnline": True})
        assert params["is_online"] is True

    def test_image_url_camel_to_snake(self):
        params = build_update_params({"imageUrl": "https://example.com/img.png"})
        assert params["image_url"] == "https://example.com/img.png"

    def test_empty_input_returns_empty_dict(self):
        assert build_update_params({}) == {}
