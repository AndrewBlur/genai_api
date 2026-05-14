"""Tests for /register and /login auth endpoints."""
from unittest.mock import MagicMock, patch

from app.core.security import hashpwd


class TestRegister:
    def test_register_success(self, client, mock_collections):
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="new_id_123")

        resp = client.post("/register", json={"username": "newuser", "password": "pass123"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "new_id_123"
        assert data["username"] == "newuser"
        mock_collections["users"].insert_one.assert_called_once()

    def test_register_duplicate_user(self, client, mock_collections):
        mock_collections["users"].find_one.return_value = {
            "_id": "existing",
            "username": "taken",
            "password": "hashed",
        }

        resp = client.post("/register", json={"username": "taken", "password": "pass123"})

        assert resp.status_code == 409
        assert "user exists" in resp.json()["detail"]

    def test_register_missing_fields(self, client):
        resp = client.post("/register", json={"username": "onlyname"})
        assert resp.status_code == 422  # Pydantic validation

    def test_register_empty_body(self, client):
        resp = client.post("/register", json={})
        assert resp.status_code == 422


class TestLogin:
    def _setup_user(self, mock_collections, username="testlogin", password="secret"):
        hashed = hashpwd(password)
        mock_collections["users"].find_one.return_value = {
            "_id": "user_abc",
            "username": username,
            "password": hashed,
        }
        return hashed

    def test_login_success(self, client, mock_collections):
        self._setup_user(mock_collections)

        resp = client.post("/login", data={"username": "testlogin", "password": "secret"})

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, mock_collections):
        self._setup_user(mock_collections)

        resp = client.post("/login", data={"username": "testlogin", "password": "wrongpass"})

        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client, mock_collections):
        mock_collections["users"].find_one.return_value = None

        resp = client.post("/login", data={"username": "ghost", "password": "pass"})

        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/login", data={})
        assert resp.status_code == 422
