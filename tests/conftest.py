"""
Shared fixtures for all test modules.

Sets up environment variables, mocks MongoDB collections and external services,
and provides a FastAPI TestClient that bypasses the real DB lifespan.
"""
import os
import pytest
from unittest.mock import MagicMock, patch

# ── Set env vars BEFORE any app imports so pydantic-settings doesn't fail ──
os.environ.setdefault("DB_CONN_STR", "mongodb://localhost:27017/?directConnection=true")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("TIME_TO_EXPIRE", "30")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("CHAT_COMPLETION_URL", "https://api.groq.com/openai/v1/chat/completions")
os.environ.setdefault("NOMIC_API_KEY", "test-nomic-key")


# ── Mock heavy modules before they are imported by app code ──
# Prevent nomic from trying to authenticate at module level
_nomic_mock = MagicMock()
_nomic_mock.login = MagicMock()
import sys
sys.modules.setdefault("nomic", _nomic_mock)


@pytest.fixture(scope="session")
def _mock_collections():
    """
    Patch all MongoDB collection objects and the DB client
    so that no real database connection is made.
    """
    mock_users = MagicMock()
    mock_chats = MagicMock()
    mock_knowledgestore = MagicMock()
    mock_db = MagicMock()

    patches = [
        patch("app.db.client.client", MagicMock()),
        patch("app.db.client.db", mock_db),
        patch("app.db.collections.db", mock_db),
        patch("app.db.collections.users_collection", mock_users),
        patch("app.db.collections.chats_collection", mock_chats),
        patch("app.db.collections.knowledgestore_collection", mock_knowledgestore),
        patch("app.services.dbservices.users_collection", mock_users),
        patch("app.services.dbservices.chats_collection", mock_chats),
        patch("app.services.dbservices.knowledgestore_collection", mock_knowledgestore),
        patch("app.services.dbservices.db", mock_db),
        patch("app.services.ragservices.knowledgestore_collection", mock_knowledgestore),
        patch("app.main.startDB", MagicMock()),
        patch("app.main.close_client", MagicMock()),
    ]
    for p in patches:
        p.start()

    yield {
        "users": mock_users,
        "chats": mock_chats,
        "knowledgestore": mock_knowledgestore,
        "db": mock_db,
    }

    for p in patches:
        p.stop()


@pytest.fixture(scope="session")
def client(_mock_collections):
    """
    Provide a FastAPI TestClient with the lifespan disabled
    (so startDB / close_client are never called against a real DB).
    """
    from fastapi.testclient import TestClient
    from app.main import app

    # Override lifespan to no-op so tests never hit real Mongo
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def mock_collections(_mock_collections):
    """Per-test access to the mocked collections (resets call history)."""
    for col in _mock_collections.values():
        col.reset_mock()
    return _mock_collections


@pytest.fixture()
def auth_header(client):
    """
    Register + login a test user and return an Authorization header dict.
    """
    from app.core.security import hashpwd
    hashed = hashpwd("testpass")
    mock_user_doc = {"_id": "abc123", "username": "testuser", "password": hashed}

    with patch("app.services.dbservices.users_collection") as mock_users:
        # Registration – user doesn't exist yet
        mock_users.find_one.return_value = None
        mock_users.insert_one.return_value = MagicMock(inserted_id="abc123")
        client.post("/register", json={"username": "testuser", "password": "testpass"})

        # Login – user exists now
        mock_users.find_one.return_value = mock_user_doc
        with patch("app.services.dbservices.get_user") as mock_get_user:
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashed,
            }
            resp = client.post("/login", data={"username": "testuser", "password": "testpass"})

    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
