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


class TestSessionManagerOutput:
    """Test SessionManager output storage (simplified, no waiting)."""
    
    def test_set_output(self, session_manager):
        """Should store output in session."""
        session_manager.create_session("output-test")
        session_manager.set_output(
            "output-test",
            prompt_english="a beautiful sunset",
            prompt_json='{"prompt": "sunset"}',
            prompt_bilingual="日落 / sunset",
        )
        
        session = session_manager.get_session("output-test")
        assert session.last_output["prompt_english"] == "a beautiful sunset"
        assert session.last_output["prompt_json"] == '{"prompt": "sunset"}'
        assert session.last_output["prompt_bilingual"] == "日落 / sunset"
    
    def test_get_output_immediate(self, session_manager):
        """Should get output immediately."""
        session_manager.create_session("get-output-test")
        session_manager.set_output(
            "get-output-test",
            prompt_english="test prompt",
            prompt_json="{}",
            prompt_bilingual="测试",
        )
        
        output = session_manager.get_output("get-output-test")
        assert output["prompt_english"] == "test prompt"
    
    def test_get_output_nonexistent_session(self, session_manager):
        """Should return empty dict for nonexistent session."""
        output = session_manager.get_output("nonexistent-session")
        assert output["prompt_english"] == ""
        assert output["prompt_json"] == ""
        assert output["prompt_bilingual"] == ""
    
    def test_get_output_empty_before_set(self, session_manager):
        """Should return empty output before any set_output call."""
        session_manager.create_session("empty-output-test")
        output = session_manager.get_output("empty-output-test")
        assert output["prompt_english"] == ""
        assert output["prompt_json"] == ""
        assert output["prompt_bilingual"] == ""


class TestSessionManagerOpencode:
    """Test SessionManager OpenCode session management."""
    
    def test_set_opencode_session(self, session_manager):
        """Should store OpenCode session ID."""
        session_manager.create_session("opencode-test")
        session_manager.set_opencode_session("opencode-test", "oc-12345")
        
        assert session_manager.get_opencode_session("opencode-test") == "oc-12345"
    
    def test_get_opencode_session_nonexistent(self, session_manager):
        """Should return None for session without OpenCode ID."""
        session_manager.create_session("no-opencode-test")
        assert session_manager.get_opencode_session("no-opencode-test") is None
    
    def test_clear_opencode_session(self, session_manager):
        """Should clear OpenCode session ID."""
        session_manager.create_session("clear-opencode-test")
        session_manager.set_opencode_session("clear-opencode-test", "oc-54321")
        assert session_manager.get_opencode_session("clear-opencode-test") == "oc-54321"
        
        session_manager.clear_opencode_session("clear-opencode-test")
        assert session_manager.get_opencode_session("clear-opencode-test") is None
    
    def test_session_to_dict_includes_opencode_id(self, session_manager):
        """Session.to_dict should include opencode_session_id."""
        session_manager.create_session("dict-opencode-test")
        session_manager.set_opencode_session("dict-opencode-test", "oc-abcdef")
        
        session = session_manager.get_session("dict-opencode-test")
        data = session.to_dict()
        
        assert data["opencode_session_id"] == "oc-abcdef"
