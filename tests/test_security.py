"""Tests for security utilities: hashing, JWT tokens."""
from datetime import datetime, timedelta
from unittest.mock import patch

from app.core.security import hashpwd, checkpwd, create_token, decode_token


class TestPasswordHashing:
    def test_hashpwd_returns_string(self):
        result = hashpwd("mypassword")
        assert isinstance(result, str)
        assert result != "mypassword"

    def test_hashpwd_different_salts(self):
        h1 = hashpwd("same")
        h2 = hashpwd("same")
        assert h1 != h2  # bcrypt uses random salt each time

    def test_checkpwd_correct(self):
        hashed = hashpwd("correct")
        assert checkpwd("correct", hashed) is True

    def test_checkpwd_incorrect(self):
        hashed = hashpwd("correct")
        assert checkpwd("wrong", hashed) is False


class TestJWTTokens:
    def test_create_and_decode_token(self):
        token = create_token({"sub": "testuser"})
        payload = decode_token(token)
        assert payload["sub"] == "testuser"

    def test_token_contains_expiry(self):
        token = create_token({"sub": "user"})
        payload = decode_token(token)
        assert "exp" in payload

    def test_decode_invalid_token_raises(self):
        import pytest
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_token("not.a.valid.token")
        assert exc_info.value.status_code == 401

    def test_decode_tampered_token_raises(self):
        import pytest
        from fastapi import HTTPException

        token = create_token({"sub": "user"})
        tampered = token[:-5] + "XXXXX"

        with pytest.raises(HTTPException) as exc_info:
            decode_token(tampered)
        assert exc_info.value.status_code == 401
