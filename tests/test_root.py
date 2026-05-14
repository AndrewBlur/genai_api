"""Tests for the root endpoint."""


class TestRootEndpoint:
    def test_root_returns_hello_world(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json() == "hello world"
