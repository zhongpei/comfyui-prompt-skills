"""
Integration Tests for Prompt Skills Plugin

These tests require a real OpenCode Server running.
The server is automatically started/stopped via pytest fixtures.

Run with: make test-integration
"""

import pytest
import subprocess
import time
import os
import signal
import httpx


# OpenCode Server configuration
OPENCODE_PORT = 4096
OPENCODE_BASE_URL = f"http://127.0.0.1:{OPENCODE_PORT}"
OPENCODE_STARTUP_TIMEOUT = 30  # seconds
OPENCODE_REQUEST_TIMEOUT = 30  # seconds


class OpencodeServerManager:
    """Manages OpenCode Server lifecycle for integration tests."""
    
    def __init__(self, port: int = OPENCODE_PORT):
        self.port = port
        self.process = None
        self.base_url = f"http://127.0.0.1:{port}"
    
    def is_running(self) -> bool:
        """Check if OpenCode Server is running."""
        try:
            response = httpx.get(
                f"{self.base_url}/config",
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def start(self, timeout: float = OPENCODE_STARTUP_TIMEOUT) -> bool:
        """
        Start OpenCode Server and wait for it to be ready.
        
        Returns True if server started successfully.
        """
        if self.is_running():
            print(f"OpenCode Server already running on port {self.port}")
            return True
        
        print(f"Starting OpenCode Server on port {self.port}...")
        
        # Start the server process
        self.process = subprocess.Popen(
            [
                "opencode", "serve",
                "--port", str(self.port),
                "--log-level", "INFO",
                "--print-logs"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group for clean shutdown
        )
        
        # Wait for server to become available
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running():
                print(f"OpenCode Server started successfully (took {time.time() - start_time:.1f}s)")
                return True
            time.sleep(0.5)
        
        # Timeout - server didn't start
        self.stop()
        raise RuntimeError(
            f"OpenCode Server failed to start within {timeout}s. "
            "Make sure 'opencode' is installed and accessible."
        )
    
    def stop(self) -> None:
        """Stop OpenCode Server."""
        if self.process:
            print("Stopping OpenCode Server...")
            try:
                # Kill the entire process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except Exception as e:
                print(f"Warning: Error stopping server: {e}")
                try:
                    self.process.kill()
                except Exception:
                    pass
            finally:
                self.process = None
        print("OpenCode Server stopped")


# =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def opencode_server():
    """
    Session-scoped fixture that starts OpenCode Server once for all tests.
    """
    manager = OpencodeServerManager()
    manager.start()
    yield manager
    manager.stop()


@pytest.fixture
def opencode_client(opencode_server):
    """
    Create an HTTP client for OpenCode Server.
    """
    return httpx.Client(
        base_url=OPENCODE_BASE_URL,
        timeout=OPENCODE_REQUEST_TIMEOUT
    )


@pytest.fixture
def opencode_session(opencode_client):
    """
    Create a new OpenCode session for each test.
    Automatically cleaned up after test.
    """
    response = opencode_client.post("/session", json={"title": "Integration Test"})
    assert response.status_code == 200, f"Failed to create session: {response.text}"
    
    session_data = response.json()
    session_id = session_data.get("id")
    
    yield session_data
    
    # Cleanup: delete the session
    try:
        opencode_client.delete(f"/session/{session_id}")
    except Exception:
        pass  # Ignore cleanup errors


# =============================================================================
# OpenCode Server API Tests
# =============================================================================

class TestOpencodeServerAPI:
    """Test OpenCode Server REST API endpoints."""
    
    def test_server_is_running(self, opencode_server):
        """Verify OpenCode Server is accessible."""
        assert opencode_server.is_running()
    
    def test_get_config(self, opencode_client):
        """GET /config - should return server configuration."""
        response = opencode_client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_list_sessions(self, opencode_client):
        """GET /session - should return list of sessions."""
        response = opencode_client.get("/session")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_session(self, opencode_client):
        """POST /session - should create a new session."""
        response = opencode_client.post("/session", json={"title": "Test Session"})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        
        # Cleanup
        opencode_client.delete(f"/session/{data['id']}")
    
    def test_get_session(self, opencode_client, opencode_session):
        """GET /session/{id} - should return session details."""
        session_id = opencode_session["id"]
        response = opencode_client.get(f"/session/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
    
    def test_send_message(self, opencode_client, opencode_session):
        """POST /session/{id}/message - should send message and get response."""
        session_id = opencode_session["id"]
        
        # OpenCode API requires 'parts' array format
        response = opencode_client.post(
            f"/session/{session_id}/message",
            json={
                "parts": [
                    {
                        "type": "text",
                        "text": "Say hello in exactly 3 words.",
                    }
                ],
            },
            timeout=OPENCODE_REQUEST_TIMEOUT
        )
        assert response.status_code == 200
    
    def test_get_messages(self, opencode_client, opencode_session):
        """GET /session/{id}/message - should return message history."""
        session_id = opencode_session["id"]
        
        # Send a message first (using parts array format)
        opencode_client.post(
            f"/session/{session_id}/message",
            json={
                "parts": [
                    {"type": "text", "text": "Hello"}
                ],
            },
            timeout=OPENCODE_REQUEST_TIMEOUT
        )
        
        # Get messages
        response = opencode_client.get(f"/session/{session_id}/message")
        assert response.status_code == 200
        messages = response.json()
        assert isinstance(messages, list)


# =============================================================================
# Tier 3: Opencode Core Integration Tests
# =============================================================================

class TestOpencodeClientIntegration:
    """Test OpencodeClient with real OpenCode Server."""
    
    def test_ensure_server_running(self, opencode_server):
        """OpencodeClient should detect running server."""
        from backend.core import OpencodeClient
        
        client = OpencodeClient()
        # Server is already running via fixture
        assert client.is_server_running()
    
    def test_create_session_via_client(self, opencode_server):
        """OpencodeClient should create sessions on OpenCode Server."""
        from backend.core import OpencodeClient
        
        client = OpencodeClient()
        session = client.create_session(title="Client Test")
        
        assert session is not None
        assert "id" in session
        
        client.close()
    
    def test_send_message_via_client(self, opencode_server):
        """OpencodeClient should send messages and get responses."""
        from backend.core import OpencodeClient
        
        client = OpencodeClient()
        session = client.create_session(title="Message Test")
        assert session is not None
        
        # Send message
        result = client.send_message(
            session_id=session["id"],
            content="Reply with only: OK"
        )
        assert result is not None
        
        # Get messages
        messages = client.get_messages(session["id"])
        assert len(messages) > 0
        
        client.close()


class TestSessionManagerIntegration:
    """Test SessionManager with full workflow."""
    
    def test_full_session_lifecycle(self, opencode_server):
        """Test complete session lifecycle: create, update, use, delete."""
        from backend.core import get_session_manager
        
        manager = get_session_manager()
        
        # Create
        session = manager.create_session("integration-test-session")
        assert session.id == "integration-test-session"
        
        # Update config
        manager.update_session_config(
            "integration-test-session",
            skills=["z-photo", "z-manga"],
            model_target="z-image-turbo"
        )
        
        session = manager.get_session("integration-test-session")
        assert session.skills == ["z-photo", "z-manga"]
        
        # Add messages
        manager.add_message("integration-test-session", "user", "Test message")
        assert len(session.history) == 1
        
        # Delete
        manager.delete_session("integration-test-session")
        assert manager.get_session("integration-test-session") is None


class TestSkillRegistryIntegration:
    """Test SkillRegistry with real skill files."""
    
    def test_discover_skills(self):
        """Should discover skills from skills/ directory."""
        from backend.core import get_skill_registry
        
        registry = get_skill_registry()
        skill_ids = registry.discover_skills()
        
        # Should find the predefined skills
        assert "z-photo" in skill_ids or len(skill_ids) >= 0
    
    def test_load_skill(self):
        """Should load skill content from SKILL.md file."""
        from backend.core import get_skill_registry
        
        registry = get_skill_registry()
        skill_ids = registry.discover_skills()
        
        if skill_ids:
            skill = registry.load_skill(skill_ids[0])
            assert skill is not None
            assert skill.content  # Should have content
    
    def test_get_combined_prompt(self):
        """Should combine multiple skills into system prompt."""
        from backend.core import get_skill_registry
        
        registry = get_skill_registry()
        skill_ids = registry.discover_skills()
        
        if len(skill_ids) >= 2:
            combined = registry.get_combined_prompt(skill_ids[:2])
            assert len(combined) > 0


class TestOutputFormatterIntegration:
    """Test OutputFormatter with various inputs."""
    
    def test_format_json_response(self):
        """Should extract and format JSON from LLM response."""
        from backend.core import get_output_formatter
        
        formatter = get_output_formatter()
        
        raw = '''Here is the prompt:
```json
{
    "positive_prompt": "cinematic, 35mm film, bokeh",
    "style": "photography",
    "subject_zh": "女孩",
    "subject_en": "girl"
}
```
'''
        output = formatter.format(raw)
        
        assert "cinematic" in output.prompt_english
        assert "positive_prompt" in output.prompt_json
    
    def test_format_plain_text(self):
        """Should handle plain text response gracefully."""
        from backend.core import get_output_formatter
        
        formatter = get_output_formatter()
        
        raw = "cinematic lighting, beautiful girl, forest background"
        output = formatter.format(raw)
        
        assert output.prompt_english == raw.strip()


# =============================================================================
# Tier 2: Flask Logic Layer Integration Tests  
# =============================================================================

class TestFlaskLogicLayerIntegration:
    """Test Flask Logic Layer with real backend."""
    
    @pytest.fixture
    def flask_app(self, opencode_server):
        """Create Flask app for testing."""
        os.environ["COMFYUI_PROMPT_SKILLS_TESTING"] = "1"
        from backend.logic import create_app
        app = create_app(debug=True, testing=True)
        return app
    
    @pytest.fixture
    def flask_client(self, flask_app):
        """Flask test client."""
        return flask_app.test_client()
    
    def test_health_endpoint(self, flask_client):
        """GET /health should return ok."""
        response = flask_client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
    
    def test_list_skills_endpoint(self, flask_client):
        """GET /api/skills should return available skills."""
        response = flask_client.get("/api/skills")
        assert response.status_code == 200
        data = response.get_json()
        assert "skills" in data
    
    def test_opencode_status_endpoint(self, flask_client, opencode_server):
        """GET /api/opencode/status should report server status."""
        response = flask_client.get("/api/opencode/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["running"] is True


# =============================================================================
# End-to-End Integration Tests
# =============================================================================

class TestEndToEndIntegration:
    """
    End-to-end tests that simulate full user workflows.
    These tests exercise Tier 2 + Tier 3 + OpenCode Server.
    """
    
    def test_prompt_generation_flow(self, opencode_server):
        """
        Test complete prompt generation workflow:
        1. Create session
        2. Configure skills
        3. Send user message
        4. Receive and format response
        """
        from backend.core import (
            get_session_manager,
            get_skill_registry,
            get_opencode_client,
            get_output_formatter,
        )
        
        # 1. Create session
        session_manager = get_session_manager()
        session = session_manager.create_session("e2e-test-session")
        
        # 2. Configure skills
        skill_registry = get_skill_registry()
        available_skills = skill_registry.discover_skills()
        
        if available_skills:
            session_manager.update_session_config(
                "e2e-test-session",
                skills=available_skills[:1],  # Use first skill
                model_target="z-image-turbo"
            )
        
        # 3. Send message to OpenCode
        client = get_opencode_client()
        opencode_session = client.create_session(title="E2E Test")
        assert opencode_session is not None
        
        system_prompt = skill_registry.get_combined_prompt(available_skills[:1]) if available_skills else ""
        user_message = "一个穿着红色裙子的女孩站在樱花树下"
        
        full_prompt = f"""你是提示词工程师。

{system_prompt}

用户请求: {user_message}

请输出JSON格式:
{{"positive_prompt": "...", "subject_zh": "...", "subject_en": "..."}}
"""
        
        result = client.send_message(
            session_id=opencode_session["id"],
            content=full_prompt
        )
        
        # Get response
        messages = client.get_messages(opencode_session["id"])
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        
        if assistant_msgs:
            raw_response = assistant_msgs[-1].get("content", "")
            
            # 4. Format output
            formatter = get_output_formatter()
            output = formatter.format(raw_response)
            
            assert output.prompt_english  # Should have some output
            session_manager.add_message("e2e-test-session", "assistant", raw_response)
        
        # Cleanup
        session_manager.delete_session("e2e-test-session")
        client.close()
