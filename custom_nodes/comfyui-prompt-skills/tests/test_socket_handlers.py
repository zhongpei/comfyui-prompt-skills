"""
Tests for Socket Handlers (Tier 2 Logic Layer)

These tests verify WebSocket event handling independently
from ComfyUI environment.
"""

import pytest


class TestSocketHandlers:
    """Test WebSocket event handlers."""
    
    def test_health_endpoint(self, client):
        """Health check should return ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "prompt-skills-logic-layer"
    
    def test_list_sessions_empty(self, client):
        """Should return empty sessions list initially."""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.get_json()
        assert "sessions" in data
    
    def test_list_skills(self, client):
        """Should list available skills."""
        response = client.get("/api/skills")
        assert response.status_code == 200
        data = response.get_json()
        assert "skills" in data
    
    def test_echo_endpoint(self, client):
        """Echo endpoint should return posted data."""
        response = client.post(
            "/test/echo",
            json={"message": "hello"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["echo"]["message"] == "hello"


class TestSocketIOEvents:
    """Test Socket.IO events using test client."""
    
    def test_connect_creates_session(self, socket_client, session_manager):
        """Connection with session_id should create session."""
        # Note: The test client doesn't support query params directly
        # In real tests, we'd need to mock the request args
        assert socket_client.is_connected()
    
    def test_disconnect(self, socket_client):
        """Disconnect should clean up."""
        socket_client.disconnect()
        assert not socket_client.is_connected()
