"""
Tests for SessionManager (Tier 3 Core)
"""

import pytest
from backend.core import SessionManager, get_session_manager


class TestSessionManager:
    """Test SessionManager functionality."""
    
    def test_singleton_pattern(self):
        """SessionManager should be singleton."""
        m1 = SessionManager()
        m2 = SessionManager()
        assert m1 is m2
    
    def test_create_session(self, session_manager):
        """Should create new session with unique ID."""
        session = session_manager.create_session()
        assert session.id.startswith("ses_")
        assert session.status == "idle"
        assert session.history == []
        assert session.skills == []
    
    def test_create_session_with_custom_id(self, session_manager):
        """Should create session with custom ID."""
        session = session_manager.create_session("my-custom-session")
        assert session.id == "my-custom-session"
    
    def test_get_session(self, session_manager):
        """Should retrieve existing session."""
        created = session_manager.create_session("test-session")
        retrieved = session_manager.get_session("test-session")
        assert created is retrieved
    
    def test_get_nonexistent_session(self, session_manager):
        """Should return None for nonexistent session."""
        session = session_manager.get_session("nonexistent")
        assert session is None
    
    def test_get_or_create_session(self, session_manager):
        """Should create session if not exists."""
        session1 = session_manager.get_or_create_session("new-session")
        assert session1.id == "new-session"
        
        session2 = session_manager.get_or_create_session("new-session")
        assert session1 is session2
    
    def test_update_session_config(self, session_manager):
        """Should update session configuration."""
        session_manager.create_session("config-test")
        session = session_manager.update_session_config(
            "config-test",
            api_key="sk-test",
            skills=["z-photo", "z-manga"],
            model_target="sdxl",
        )
        assert session.config["api_key"] == "sk-test"
        assert session.skills == ["z-photo", "z-manga"]
        assert session.config["model_target"] == "sdxl"
    
    def test_add_message(self, session_manager):
        """Should add messages to history."""
        session_manager.create_session("msg-test")
        session_manager.add_message("msg-test", "user", "Hello")
        session_manager.add_message("msg-test", "assistant", "Hi there")
        
        session = session_manager.get_session("msg-test")
        assert len(session.history) == 2
        assert session.history[0]["role"] == "user"
        assert session.history[1]["content"] == "Hi there"
    
    def test_set_status(self, session_manager):
        """Should update session status."""
        session = session_manager.create_session("status-test")
        assert session.status == "idle"
        
        session_manager.set_status("status-test", "working")
        assert session.status == "working"
    
    def test_list_sessions(self, session_manager):
        """Should list all session IDs."""
        session_manager.create_session("session-1")
        session_manager.create_session("session-2")
        
        sessions = session_manager.list_sessions()
        assert "session-1" in sessions
        assert "session-2" in sessions
    
    def test_delete_session(self, session_manager):
        """Should delete session."""
        session_manager.create_session("to-delete")
        assert session_manager.get_session("to-delete") is not None
        
        result = session_manager.delete_session("to-delete")
        assert result is True
        assert session_manager.get_session("to-delete") is None
    
    def test_session_to_dict(self, session_manager):
        """Session.to_dict should not expose api_key."""
        session_manager.create_session("dict-test")
        session_manager.update_session_config("dict-test", api_key="secret-key")
        
        session = session_manager.get_session("dict-test")
        data = session.to_dict()
        
        assert "api_key" not in data.get("config", {})
        assert "id" in data
        assert "history" in data
