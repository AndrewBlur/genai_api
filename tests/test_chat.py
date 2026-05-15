"""Tests for /chat, /chats, /store, /retrieve endpoints."""
import io
from unittest.mock import MagicMock, patch

from app.core.security import hashpwd


class TestChatEndpoint:
    def test_chat_requires_auth(self, client):
        resp = client.post("/chat", json={"model_name": "llama3", "message": "hi"})
        assert resp.status_code == 401

    def test_chat_new_conversation(self, client, auth_header):
        mock_groq_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?",
                    }
                }
            ],
            "usage": {"total_tokens": 50},
        }

        with (
            patch("app.services.llmservices.call_groq", return_value=mock_groq_response),
            patch("app.services.llmservices.create_chat") as mock_create,
            patch("app.services.llmservices.update_chat_history"),
            patch("app.services.llmservices.update_chat_tokens"),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }

            resp = client.post(
                "/chat",
                json={"model_name": "llama3-70b", "message": "Hello"},
                headers=auth_header,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "ai"
        assert "chat_id" in data
        assert data["message"]["content"] == "Hello! How can I help you?"

    def test_chat_existing_conversation(self, client, auth_header):
        existing_chat = {
            "chat_id": "existing-chat-id",
            "chat_history": [{"role": "user", "content": "Previous message"}],
            "tokens": 100,
        }
        mock_groq_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Sure, continuing our chat.",
                    }
                }
            ],
            "usage": {"total_tokens": 200},
        }

        with (
            patch("app.services.llmservices.call_groq", return_value=mock_groq_response),
            patch("app.services.llmservices.get_chat", return_value=existing_chat),
            patch("app.services.llmservices.update_chat_history"),
            patch("app.services.llmservices.update_chat_tokens"),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }

            resp = client.post(
                "/chat",
                json={
                    "model_name": "llama3-70b",
                    "message": "Continue",
                    "chat_id": "existing-chat-id",
                },
                headers=auth_header,
            )

        assert resp.status_code == 200
        assert resp.json()["chat_id"] == "existing-chat-id"

    def test_chat_context_window_exceeded(self, client, auth_header):
        overloaded_chat = {
            "chat_id": "big-chat",
            "chat_history": [],
            "tokens": 999999,
        }

        with (
            patch("app.services.llmservices.get_chat", return_value=overloaded_chat),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }

            resp = client.post(
                "/chat",
                json={
                    "model_name": "llama3-70b",
                    "message": "too much",
                    "chat_id": "big-chat",
                },
                headers=auth_header,
            )

        assert resp.status_code == 413

    def test_chat_with_tool_calls(self, client, auth_header):
        """Test the tool-call loop: first response has tool_calls, second is final."""
        tool_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "function": {
                                    "name": "get_time",
                                    "arguments": '{"format": "%Y-%m-%d"}',
                                },
                            }
                        ],
                    }
                }
            ],
            "usage": {"total_tokens": 80},
        }
        final_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "The date is 2026-05-14.",
                    }
                }
            ],
            "usage": {"total_tokens": 120},
        }

        with (
            patch(
                "app.services.llmservices.call_groq",
                side_effect=[tool_response, final_response],
            ),
            patch("app.services.llmservices.create_chat"),
            patch("app.services.llmservices.update_chat_history"),
            patch("app.services.llmservices.update_chat_tokens"),
            patch("app.utils.tools.get_time", return_value="2026-05-14"),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }

            resp = client.post(
                "/chat",
                json={"model_name": "llama3-70b", "message": "What date is it?"},
                headers=auth_header,
            )

        assert resp.status_code == 200
        assert "2026-05-14" in resp.json()["message"]["content"]


class TestUserChats:
    def test_chats_requires_auth(self, client):
        resp = client.get("/chats")
        assert resp.status_code == 401

    def test_chats_returns_list(self, client, auth_header):
        mock_chats_data = [
            {
                "chat_id": "chat-1",
                "chat_history": [{"role": "user", "content": "First conversation opener"}],
            },
            {
                "chat_id": "chat-2",
                "chat_history": [{"role": "user", "content": "Second conversation opener"}],
            },
        ]

        with (
            patch("app.services.dbservices.chats_collection") as mock_chats_col,
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }
            mock_chats_col.find.return_value = mock_chats_data

            resp = client.get("/chats", headers=auth_header)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["chat_id"] == "chat-1"

    def test_chats_empty(self, client, auth_header):
        with (
            patch("app.services.dbservices.chats_collection") as mock_chats_col,
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }
            mock_chats_col.find.return_value = []

            resp = client.get("/chats", headers=auth_header)

        assert resp.status_code == 200
        assert resp.json() == []


class TestGetChat:
    def test_get_chat_requires_auth(self, client):
        resp = client.get("/chats/some-id")
        assert resp.status_code == 401

    def test_get_chat_success(self, client, auth_header):
        mock_chat = {"chat_id": "chat-1", "chat_history": [], "tokens": 0}
        with (
            patch("app.routes.chat.get_chat", return_value=mock_chat),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }
            resp = client.get("/chats/chat-1", headers=auth_header)

        assert resp.status_code == 200
        assert resp.json()["chat_id"] == "chat-1"

    def test_get_chat_not_found(self, client, auth_header):
        with (
            patch("app.routes.chat.get_chat", return_value=None),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }
            resp = client.get("/chats/non-existent", headers=auth_header)

        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestDeleteChat:
    def test_delete_chat_requires_auth(self, client):
        resp = client.delete("/chats/some-id")
        assert resp.status_code == 401

    def test_delete_chat_success(self, client, auth_header):
        with (
            patch("app.routes.chat.delete_chat", return_value=True),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }
            resp = client.delete("/chats/chat-1", headers=auth_header)

        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

    def test_delete_chat_not_found(self, client, auth_header):
        with (
            patch("app.routes.chat.delete_chat", return_value=False),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }
            resp = client.delete("/chats/non-existent", headers=auth_header)

        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestStoreEndpoint:
    def test_store_requires_auth(self, client):
        resp = client.post("/store", files={"file": ("test.txt", b"content")})
        assert resp.status_code == 401

    def test_store_txt_file(self, client, auth_header):
        with (
            patch("app.routes.chat.store_in_knowledgestore") as mock_store,
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }

            resp = client.post(
                "/store",
                files={"file": ("notes.txt", b"Some text content", "text/plain")},
                headers=auth_header,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["file_name"] == "notes.txt"
        assert data["user"] == "abc123"
        mock_store.assert_called_once()

    def test_store_md_file(self, client, auth_header):
        with (
            patch("app.routes.chat.store_in_knowledgestore") as mock_store,
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }

            resp = client.post(
                "/store",
                files={"file": ("readme.md", b"# Heading\nContent here", "text/markdown")},
                headers=auth_header,
            )

        assert resp.status_code == 200
        assert resp.json()["file_name"] == "readme.md"

    def test_store_unsupported_file_type(self, client, auth_header):
        with patch("app.dependencies.auth.get_user") as mock_get_user:
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }

            resp = client.post(
                "/store",
                files={"file": ("image.png", b"\x89PNG", "image/png")},
                headers=auth_header,
            )

        assert resp.status_code == 415

    def test_store_pdf_file(self, client, auth_header):
        with (
            patch("app.routes.chat.store_in_knowledgestore") as mock_store,
            patch("app.routes.chat.load_pdf", return_value="extracted pdf text"),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }

            resp = client.post(
                "/store",
                files={"file": ("doc.pdf", b"%PDF-fake", "application/pdf")},
                headers=auth_header,
            )

        assert resp.status_code == 200
        assert resp.json()["file_name"] == "doc.pdf"
        mock_store.assert_called_once_with("doc.pdf", "extracted pdf text", "abc123")


class TestRetrieveEndpoint:
    def test_retrieve_requires_auth(self, client):
        resp = client.post("/retrieve", json={"query": "test"})
        assert resp.status_code == 401

    def test_retrieve_returns_chunks(self, client, auth_header):
        mock_chunks = [
            {"_id": "chunk1", "text": "relevant text", "filename": "doc.txt", "score": 0.95},
            {"_id": "chunk2", "text": "more text", "filename": "doc.txt", "score": 0.88},
        ]

        with (
            patch("app.routes.chat.retrieve_from_knowledgestore", return_value=mock_chunks),
            patch("app.dependencies.auth.get_user") as mock_get_user,
        ):
            mock_get_user.return_value = {
                "id": "abc123",
                "username": "testuser",
                "password": hashpwd("testpass"),
            }

            resp = client.post(
                "/retrieve",
                json={"query": "find relevant info"},
                headers=auth_header,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["score"] == 0.95
