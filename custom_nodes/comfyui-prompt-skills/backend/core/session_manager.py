"""
Tier 3: SessionManager - Global Session State Management

Implements singleton pattern to manage all session states across the application.
Sessions persist in memory for the lifetime of the ComfyUI process.
"""

from __future__ import annotations
import uuid
import threading
from typing import Any, Callable
from dataclasses import dataclass, field


@dataclass
class Session:
    """Represents a single user session with conversation history and config."""
    
    id: str
    history: list[dict[str, Any]] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    status: str = "idle"  # idle, working, error
    # OpenCode session ID - persistent across messages
    opencode_session_id: str | None = None
    # Store latest generated output for ComfyUI node
    last_output: dict[str, str] = field(default_factory=lambda: {
        "prompt_english": "",
        "prompt_json": "",
        "prompt_bilingual": "",
    })
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize session to dictionary for WebSocket sync."""
        return {
            "id": self.id,
            "history": self.history,
            "skills": self.skills,
            "config": {k: v for k, v in self.config.items() if k != "api_key"},
            "status": self.status,
            "opencode_session_id": self.opencode_session_id,
        }


class SessionManager:
    """
    Singleton class for global session state management.
    
    Thread-safe operations for concurrent access from Flask routes.
    """
    
    _instance: SessionManager | None = None
    _lock = threading.Lock()
    
    def __new__(cls) -> SessionManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        self._sessions: dict[str, Session] = {}
        self._listeners: dict[str, list[Callable]] = {}
        self._initialized = True
    
    def create_session(self, session_id: str | None = None) -> Session:
        """Create a new session with optional custom ID."""
        if session_id is None:
            session_id = f"ses_{uuid.uuid4().hex[:12]}"
        
        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]
            
            session = Session(id=session_id)
            self._sessions[session_id] = session
            return session
    
    def get_session(self, session_id: str) -> Session | None:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)
    
    def get_or_create_session(self, session_id: str) -> Session:
        """Get existing session or create new one."""
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        return session
    
    def update_session_config(
        self, 
        session_id: str, 
        api_key: str | None = None,
        skills: list[str] | None = None,
        model_target: str | None = None,
    ) -> Session | None:
        """Update session configuration."""
        session = self.get_session(session_id)
        if session is None:
            return None
        
        with self._lock:
            if api_key is not None:
                session.config["api_key"] = api_key
            if skills is not None:
                session.skills = skills
            if model_target is not None:
                session.config["model_target"] = model_target
        
        return session
    
    def set_opencode_session(self, session_id: str, opencode_session_id: str) -> None:
        """Set the OpenCode session ID for a session."""
        session = self.get_session(session_id)
        if session:
            with self._lock:
                session.opencode_session_id = opencode_session_id
    
    def get_opencode_session(self, session_id: str) -> str | None:
        """Get the OpenCode session ID for a session."""
        session = self.get_session(session_id)
        return session.opencode_session_id if session else None
    
    def clear_opencode_session(self, session_id: str) -> None:
        """Clear the OpenCode session ID (for creating new session)."""
        session = self.get_session(session_id)
        if session:
            with self._lock:
                session.opencode_session_id = None
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to session history."""
        session = self.get_session(session_id)
        if session is None:
            return
        
        message = {
            "role": role,
            "content": content,
        }
        if metadata:
            message["metadata"] = metadata
        
        with self._lock:
            session.history.append(message)
    
    def set_status(self, session_id: str, status: str) -> None:
        """Update session status (idle, working, error)."""
        session = self.get_session(session_id)
        if session:
            with self._lock:
                session.status = status
    
    def list_sessions(self) -> list[str]:
        """List all active session IDs."""
        return list(self._sessions.keys())
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and release resources."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
        return False
    
    def clear_all(self) -> None:
        """Clear all sessions (for testing purposes)."""
        with self._lock:
            self._sessions.clear()
    
    def set_output(
        self,
        session_id: str,
        prompt_english: str,
        prompt_json: str,
        prompt_bilingual: str,
    ) -> None:
        """Store generated output for ComfyUI node to retrieve."""
        session = self.get_session(session_id)
        if session:
            with self._lock:
                session.last_output = {
                    "prompt_english": prompt_english,
                    "prompt_json": prompt_json,
                    "prompt_bilingual": prompt_bilingual,
                }
    
    def get_output(self, session_id: str) -> dict[str, str]:
        """
        Get the latest generated output for a session.
        Returns immediately with current output (no waiting).
        """
        session = self.get_session(session_id)
        if session:
            return session.last_output
        return {
            "prompt_english": "",
            "prompt_json": "",
            "prompt_bilingual": "",
        }


# Global singleton instance
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get the global SessionManager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
