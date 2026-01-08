"""
Tier 3: OpencodeClient - HTTP Client for OpenCode Server

Handles communication with the OpenCode Server REST API.
Supports session management, message sending, and streaming responses.
"""

from __future__ import annotations
import os
import subprocess
import time
import threading
from typing import Any, Callable, Iterator
from dataclasses import dataclass

import httpx


@dataclass
class OpencodeConfig:
    """Configuration for OpenCode Server connection."""
    
    host: str = "127.0.0.1"
    port: int = 4096
    timeout: float = 60.0
    message_timeout: float = 300.0  # Longer timeout for AI generation
    max_retries: int = 3
    config_path: str | None = None
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class OpencodeClient:
    """
    HTTP client for OpenCode Server API.
    
    Handles server lifecycle, session creation, and message exchange.
    """
    
    def __init__(self, config: OpencodeConfig | None = None) -> None:
        self._config = config or OpencodeConfig()
        self._client: httpx.Client | None = None
        self._server_process: subprocess.Popen | None = None
        self._lock = threading.Lock()
    
    @property
    def client(self) -> httpx.Client:
        """Lazy-initialized HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._config.base_url,
                timeout=self._config.timeout,
            )
        return self._client
    
    def is_server_running(self) -> bool:
        """Check if OpenCode Server is running and healthy."""
        try:
            # OpenCode API doesn't have /health, use /config as health check
            response = self.client.get("/config")
            return response.status_code == 200
        except Exception:
            return False
    
    def ensure_server_running(self) -> bool:
        """
        Ensure OpenCode Server is running, starting it if necessary.
        
        Returns True if server is available, False otherwise.
        """
        if self.is_server_running():
            return True
        
        with self._lock:
            # Double-check after acquiring lock
            if self.is_server_running():
                return True
            
            try:
                # Start OpenCode Server
                cmd = ["opencode", "serve", "--port", str(self._config.port)]
                if self._config.config_path:
                    cmd.extend(["--config", self._config.config_path])

                self._server_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                
                # Wait for server to become available
                for _ in range(30):  # 30 attempts with 0.5s delay = 15s max
                    time.sleep(0.5)
                    if self.is_server_running():
                        return True
                
                return False
            except FileNotFoundError:
                # opencode command not found
                return False
            except Exception:
                return False
    
    def create_session(self, title: str | None = None) -> dict[str, Any] | None:
        """Create a new session on OpenCode Server."""
        try:
            payload = {}
            if title:
                payload["title"] = title
            
            response = self.client.post("/session", json=payload)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session details from OpenCode Server."""
        try:
            response = self.client.get(f"/session/{session_id}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions."""
        try:
            response = self.client.get("/session")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []
    
    def send_message(
        self, 
        session_id: str, 
        content: str,
        system: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Send a message to a session.
        
        Args:
            session_id: The session ID
            content: Message content text
            system: Optional system prompt
            
        Returns:
            Response data or None on failure
        """
        try:
            # OpenCode API requires 'parts' array with text objects
            payload: dict[str, Any] = {
                "parts": [
                    {
                        "type": "text",
                        "text": content,
                    }
                ],
            }
            
            if system:
                payload["system"] = system
            
            # Use longer timeout for message operations (AI generation can take a while)
            response = self.client.post(
                f"/session/{session_id}/message",
                json=payload,
                timeout=self._config.message_timeout,
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Get all messages for a session."""
        try:
            response = self.client.get(f"/session/{session_id}/message")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []
    
    def stream_events(
        self, 
        on_delta: Callable[[str], None] | None = None,
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        """
        Stream events from OpenCode Server using SSE.
        
        This is a blocking call that should be run in a separate thread.
        """
        try:
            with self.client.stream("GET", "/global/event") as response:
                for line in response.iter_lines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if on_delta:
                            on_delta(data)
                
                if on_complete:
                    on_complete()
        except Exception:
            pass
    
    def get_config(self) -> dict[str, Any] | None:
        """Get OpenCode configuration."""
        try:
            response = self.client.get("/config")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    def update_config(self, config: dict[str, Any]) -> dict[str, Any] | None:
        """Update OpenCode configuration."""
        try:
            response = self.client.patch("/config", json=config)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    def close(self) -> None:
        """Clean up resources."""
        if self._client:
            self._client.close()
            self._client = None
        
        if self._server_process:
            self._server_process.terminate()
            self._server_process = None

    def configure(self, config: OpencodeConfig) -> None:
        """Update client configuration."""
        self._config = config
        # Reset client to ensure new config takes effect
        if self._client:
            self._client.close()
            self._client = None


# Global singleton instance
_opencode_client: OpencodeClient | None = None


def get_opencode_client() -> OpencodeClient:
    """Get the global OpencodeClient instance."""
    global _opencode_client
    if _opencode_client is None:
        _opencode_client = OpencodeClient()
    return _opencode_client
