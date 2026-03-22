"""
Unit tests for app/repositories/users/user_repository.py

All DB interactions are mocked — no real PostgreSQL connection.
"""
import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

pytestmark = pytest.mark.asyncio


# ─── Mock session factory ──────────────────────────────────────────────────────

def make_mock_session():
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


def _make_row(mapping: dict):
    row = MagicMock()
    row._mapping = mapping
    return row


# ─── _row_to_user_dict (pure function tests) ──────────────────────────────────

class TestRowToUserDict:

    def test_birthdate_date_object_converted_to_iso_string(self):
        from app.repositories.users.user_repository import _row_to_user_dict
        bd = datetime.date(1990, 5, 15)
        row = _make_row({
            "email": "test@example.com",
            "name": "Test User",
            "birthdate": bd,
            "phone_number": None,
            "password_hash": None,
            "latitude": None, "longitude": None,
            "city": None, "state": None, "country": None,
            "formatted_address": None, "location_name": None,
        })
        result = _row_to_user_dict(row)
        assert result["birthdate"] == "1990-05-15"
        assert isinstance(result["birthdate"], str)

    def test_phone_number_renamed_to_camel_case(self):
        from app.repositories.users.user_repository import _row_to_user_dict
        row = _make_row({
            "email": "test@example.com",
            "name": "Test",
            "birthdate": None,
            "phone_number": "+15551234567",
            "password_hash": None,
            "latitude": None, "longitude": None,
            "city": None, "state": None, "country": None,
            "formatted_address": None, "location_name": None,
        })
        result = _row_to_user_dict(row)
        assert result["phoneNumber"] == "+15551234567"
        assert "phone_number" not in result

    def test_password_hash_renamed_to_password(self):
        from app.repositories.users.user_repository import _row_to_user_dict
        row = _make_row({
            "email": "test@example.com",
            "name": "Test",
            "birthdate": None,
            "phone_number": None,
            "password_hash": "$bcrypt$hash",
            "latitude": None, "longitude": None,
            "city": None, "state": None, "country": None,
            "formatted_address": None, "location_name": None,
        })
        result = _row_to_user_dict(row)
        assert result["password"] == "$bcrypt$hash"
        assert "password_hash" not in result

    def test_location_nested_correctly(self):
        from app.repositories.users.user_repository import _row_to_user_dict
        row = _make_row({
            "email": "test@example.com",
            "name": "Test",
            "birthdate": None,
            "phone_number": None,
            "password_hash": None,
            "latitude": 30.26,
            "longitude": -97.74,
            "city": "Austin",
            "state": "TX",
            "country": "US",
            "formatted_address": "123 Main St",
            "location_name": "Home",
        })
        result = _row_to_user_dict(row)
        loc = result["location"]
        assert loc["city"] == "Austin"
        assert loc["state"] == "TX"
        assert loc["latitude"] == 30.26
        assert loc["formattedAddress"] == "123 Main St"
        assert loc["name"] == "Home"
        # Flat location columns must not appear at top level
        assert "city" not in result
        assert "latitude" not in result

    def test_id_equals_email(self):
        from app.repositories.users.user_repository import _row_to_user_dict
        row = _make_row({
            "email": "alice@example.com",
            "name": "Alice",
            "birthdate": None,
            "phone_number": None,
            "password_hash": None,
            "latitude": None, "longitude": None,
            "city": None, "state": None, "country": None,
            "formatted_address": None, "location_name": None,
        })
        result = _row_to_user_dict(row)
        assert result["id"] == "alice@example.com"

    def test_birthdate_none_stays_none(self):
        from app.repositories.users.user_repository import _row_to_user_dict
        row = _make_row({
            "email": "test@example.com",
            "name": "Test",
            "birthdate": None,
            "phone_number": None,
            "password_hash": None,
            "latitude": None, "longitude": None,
            "city": None, "state": None, "country": None,
            "formatted_address": None, "location_name": None,
        })
        result = _row_to_user_dict(row)
        assert result["birthdate"] is None


# ─── UserRepository.get_by_email ──────────────────────────────────────────────

class TestGetByEmail:

    async def test_returns_none_when_no_row(self):
        from app.repositories.users.user_repository import UserRepository
        session = make_mock_session()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.repositories.users.user_repository.AsyncSessionLocal', return_value=session):
            repo = UserRepository()
            result = await repo.get_by_email("nobody@example.com")

        assert result is None

    async def test_returns_dict_when_row_found(self):
        from app.repositories.users.user_repository import UserRepository
        session = make_mock_session()

        row = _make_row({
            "email": "alice@example.com",
            "name": "Alice",
            "birthdate": None,
            "phone_number": None,
            "password_hash": None,
            "latitude": None, "longitude": None,
            "city": None, "state": None, "country": None,
            "formatted_address": None, "location_name": None,
        })
        mock_result = MagicMock()
        mock_result.fetchone.return_value = row
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.repositories.users.user_repository.AsyncSessionLocal', return_value=session):
            repo = UserRepository()
            result = await repo.get_by_email("alice@example.com")

        assert result is not None
        assert result["email"] == "alice@example.com"
        assert result["id"] == "alice@example.com"


# ─── UserRepository.update_profile_by_email ───────────────────────────────────

class TestUpdateProfileByEmail:

    async def test_execute_and_commit_called(self):
        from app.repositories.users.user_repository import UserRepository
        session = make_mock_session()
        mock_result = MagicMock()
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.repositories.users.user_repository.AsyncSessionLocal', return_value=session):
            repo = UserRepository()
            await repo.update_profile_by_email(
                {"name": "Updated Name", "birthdate": "1990-05-15"},
                "test@example.com"
            )

        session.execute.assert_called_once()
        session.commit.assert_called_once()

    async def test_birthdate_passed_as_date_object(self):
        from app.repositories.users.user_repository import UserRepository
        session = make_mock_session()
        captured_params = {}

        async def capture_execute(query, params=None):
            if params:
                captured_params.update(params)
            return MagicMock()

        session.execute = capture_execute

        with patch('app.repositories.users.user_repository.AsyncSessionLocal', return_value=session):
            repo = UserRepository()
            await repo.update_profile_by_email(
                {"birthdate": "1990-05-15"},
                "test@example.com"
            )

        assert "birthdate" in captured_params
        assert isinstance(captured_params["birthdate"], datetime.date)
        assert captured_params["birthdate"] == datetime.date(1990, 5, 15)

    async def test_no_birthdate_passes_none(self):
        from app.repositories.users.user_repository import UserRepository
        session = make_mock_session()
        captured_params = {}

        async def capture_execute(query, params=None):
            if params:
                captured_params.update(params)
            return MagicMock()

        session.execute = capture_execute

        with patch('app.repositories.users.user_repository.AsyncSessionLocal', return_value=session):
            repo = UserRepository()
            await repo.update_profile_by_email({"name": "Bob"}, "bob@example.com")

        assert captured_params.get("birthdate") is None


# ─── UserRepository.create_with_password ──────────────────────────────────────

class TestCreateWithPassword:

    async def test_insert_called_with_hashed_password(self):
        from app.repositories.users.user_repository import UserRepository
        session = make_mock_session()
        mock_result = MagicMock()
        session.execute = AsyncMock(return_value=mock_result)
        captured_params = {}

        async def capture_execute(query, params=None):
            if params:
                captured_params.update(params)
            return MagicMock()

        session.execute = capture_execute

        with patch('app.repositories.users.user_repository.AsyncSessionLocal', return_value=session):
            repo = UserRepository()
            await repo.create_with_password("new@example.com", "plainpassword", "New User")

        assert "hash" in captured_params
        # Should not store plaintext password
        assert captured_params["hash"] != "plainpassword"
        # Should be a bcrypt hash (starts with $2b$ or similar)
        assert captured_params["hash"].startswith("$2")
        session.commit.assert_called_once()

    async def test_commit_is_called(self):
        from app.repositories.users.user_repository import UserRepository
        session = make_mock_session()
        session.execute = AsyncMock(return_value=MagicMock())

        with patch('app.repositories.users.user_repository.AsyncSessionLocal', return_value=session):
            repo = UserRepository()
            await repo.create_with_password("new@example.com", "pass", "Name")

        session.commit.assert_called_once()


# ─── UserRepository.search_users ──────────────────────────────────────────────

class TestSearchUsers:

    async def test_returns_empty_list_for_short_term(self):
        from app.repositories.users.user_repository import UserRepository
        repo = UserRepository()
        result = await repo.search_users("a", "someone@example.com")
        assert result == []

    async def test_returns_empty_list_for_single_char(self):
        from app.repositories.users.user_repository import UserRepository
        repo = UserRepository()
        result = await repo.search_users("x", "someone@example.com")
        assert result == []

    async def test_returns_empty_list_for_empty_string(self):
        from app.repositories.users.user_repository import UserRepository
        repo = UserRepository()
        result = await repo.search_users("", "someone@example.com")
        assert result == []

    async def test_returns_empty_list_for_whitespace_only(self):
        from app.repositories.users.user_repository import UserRepository
        repo = UserRepository()
        result = await repo.search_users("  ", "someone@example.com")
        assert result == []

    async def test_executes_query_for_valid_term(self):
        from app.repositories.users.user_repository import UserRepository
        session = make_mock_session()
        row = _make_row({
            "email": "alice@example.com",
            "name": "Alice Smith",
            "birthdate": None,
            "phone_number": None,
            "password_hash": None,
            "latitude": None, "longitude": None,
            "city": None, "state": None, "country": None,
            "formatted_address": None, "location_name": None,
        })
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row]
        session.execute = AsyncMock(return_value=mock_result)

        with patch('app.repositories.users.user_repository.AsyncSessionLocal', return_value=session):
            repo = UserRepository()
            result = await repo.search_users("alice", "other@example.com")

        assert len(result) == 1
        assert result[0]["email"] == "alice@example.com"
