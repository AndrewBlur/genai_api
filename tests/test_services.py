"""Tests for service-layer functions."""
from unittest.mock import MagicMock, patch

from app.core.security import hashpwd


class TestAuthService:
    def test_login_user_success(self):
        from app.services.authservices import login_user

        hashed = hashpwd("goodpass")
        with patch("app.services.authservices.get_user") as mock_get_user:
            mock_get_user.return_value = {
                "id": "u1",
                "username": "alice",
                "password": hashed,
            }
            result = login_user("alice", "goodpass")

        assert "access_token" in result
        assert result["token_type"] == "bearer"

    def test_login_user_not_found(self):
        import pytest
        from fastapi import HTTPException
        from app.services.authservices import login_user

        with patch("app.services.authservices.get_user", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                login_user("ghost", "pass")
            assert exc_info.value.status_code == 401

    def test_login_user_wrong_password(self):
        import pytest
        from fastapi import HTTPException
        from app.services.authservices import login_user

        hashed = hashpwd("realpass")
        with patch("app.services.authservices.get_user") as mock_get_user:
            mock_get_user.return_value = {
                "id": "u1",
                "username": "alice",
                "password": hashed,
            }
            with pytest.raises(HTTPException) as exc_info:
                login_user("alice", "wrongpass")
            assert exc_info.value.status_code == 401


class TestDBService:
    def test_create_user_success(self):
        from app.services.dbservices import create_user

        with (
            patch("app.services.dbservices.get_user", return_value=None),
            patch("app.services.dbservices.users_collection") as mock_col,
        ):
            mock_col.insert_one.return_value = MagicMock(inserted_id="new123")
            result = create_user("bob", "pass")

        assert result["username"] == "bob"
        assert result["id"] == "new123"

    def test_create_user_duplicate(self):
        import pytest
        from fastapi import HTTPException
        from app.services.dbservices import create_user

        with patch("app.services.dbservices.get_user") as mock_get:
            mock_get.return_value = {"id": "existing", "username": "bob", "password": "h"}
            with pytest.raises(HTTPException) as exc_info:
                create_user("bob", "pass")
            assert exc_info.value.status_code == 409

    def test_get_user_found(self):
        from app.services.dbservices import get_user

        with patch("app.services.dbservices.users_collection") as mock_col:
            mock_col.find_one.return_value = {
                "_id": "uid1",
                "username": "alice",
                "password": "hashed_pw",
            }
            result = get_user("alice")

        assert result["id"] == "uid1"
        assert result["username"] == "alice"

    def test_get_user_not_found(self):
        from app.services.dbservices import get_user

        with patch("app.services.dbservices.users_collection") as mock_col:
            mock_col.find_one.return_value = None
            result = get_user("nobody")

        assert result is None

    def test_get_chat_found(self):
        from app.services.dbservices import get_chat

        with patch("app.services.dbservices.chats_collection") as mock_col:
            mock_col.find_one.return_value = {
                "chat_id": "c1",
                "chat_history": [{"role": "user", "content": "hi"}],
                "tokens": 50,
            }
            result = get_chat("c1")

        assert result["chat_id"] == "c1"
        assert result["tokens"] == 50

    def test_get_chat_not_found(self):
        from app.services.dbservices import get_chat

        with patch("app.services.dbservices.chats_collection") as mock_col:
            mock_col.find_one.return_value = None
            result = get_chat("nonexistent")

        assert result is None

    def test_get_user_chats(self):
        from app.services.dbservices import get_user_chats

        mock_docs = [
            {
                "chat_id": "c1",
                "chat_history": [{"role": "user", "content": "First chat message here"}],
            },
            {
                "chat_id": "c2",
                "chat_history": [],
            },
        ]

        with patch("app.services.dbservices.chats_collection") as mock_col:
            mock_col.find.return_value = mock_docs
            result = get_user_chats("user1")

        assert len(result) == 2
        assert result[0]["chat_id"] == "c1"
        assert result[0]["title"] == "First chat message here"
        assert result[1]["title"] == "New Chat"  # empty chat_history fallback


class TestLLMService:
    def test_execute_tool_call_get_time(self):
        from app.services.llmservices import execute_tool_call

        tool_call = {
            "function": {
                "name": "get_time",
                "arguments": '{"format": "%Y"}',
            }
        }

        mock_time = MagicMock(return_value="2026")
        with patch.dict("app.services.llmservices.available_tools", {"get_time": mock_time}):
            result = execute_tool_call(tool_call, user_id=None)

        assert result == "2026"
        mock_time.assert_called_once_with(format="%Y")

    def test_execute_tool_call_rag_injects_user_id(self):
        from app.services.llmservices import execute_tool_call

        tool_call = {
            "function": {
                "name": "rag",
                "arguments": '{"query": "test query"}',
            }
        }

        mock_rag = MagicMock(return_value="context data")
        with patch.dict("app.services.llmservices.available_tools", {"rag": mock_rag}):
            result = execute_tool_call(tool_call, user_id="user_xyz")

        mock_rag.assert_called_once_with(query="test query", user_id="user_xyz")
        assert result == "context data"
