"""
Integration Bug Reproduction Tests

This module reproduces the "No assistant message found" bug reported by the user.
It mocks the OpenCode server interactions to simulate:
1. Successful message sending
2. Receiving response messages that do NOT contain an "assistant" role
3. Validating the system logs the full response for debugging
"""

import pytest
from unittest.mock import MagicMock, patch
from backend.logic import create_app, socketio
from backend.core import get_session_manager, get_opencode_client, get_skill_registry


@pytest.fixture
def flask_app():
    return create_app(debug=True, testing=True)


@pytest.fixture
def app_client(flask_app):
    return flask_app.test_client()


@pytest.fixture
def socket_client(flask_app):
    return socketio.test_client(flask_app)

class SyncExecutor:
    def submit(self, fn, *args, **kwargs):
        fn(*args, **kwargs)
        return MagicMock()

    def shutdown(self, wait=True):
        pass


@pytest.fixture(autouse=True)
def mock_executor():
    with patch("backend.logic.socket_handlers._executor", SyncExecutor()):
        yield

@patch("backend.core.opencode_client.OpencodeClient.ensure_server_running")
@patch("backend.core.opencode_client.OpencodeClient.create_session")
@patch("backend.core.opencode_client.OpencodeClient.send_message")
@patch("backend.core.opencode_client.OpencodeClient.get_messages")
def test_repro_no_assistant_message(
    mock_get_messages, 
    mock_send_message, 
    mock_create_session, 
    mock_ensure_server,
    flask_app
):
    """
    Test scenario:
    1. Connect and create session
    2. Send user message
    3. Opencode accepts message (send_message returns ID)
    4. Opencode returns updated thread messages BUT missing the assistant response
    5. Server should log detailed debug info about received messages
    """
    
    # Mock OpenCode behavior
    mock_ensure_server.return_value = True
    mock_create_session.return_value = {"id": "test_opencode_session_id"}
    mock_send_message.return_value = {"id": "msg_user_123"}
    
    # CRITICAL: Return messages that do NOT include an assistant response
    # Only user message is present
    mock_get_messages.return_value = [
        {"id": "msg_user_123", "role": "user", "content": "Help me draw a cat"}
    ]
    
    # Create a new socket client with query_string
    socket_client = socketio.test_client(flask_app, query_string="session_id=test_bug_repro")
    socket_client.connect()
    
    # Wait for session creation (sync_state)
    received = socket_client.get_received()
    assert any(e["name"] == "sync_state" for e in received), "Session creation failed"

    
    # Send message
    socket_client.emit("user_message", {
        "session_id": "test_bug_repro",
        "content": "Help me draw a cat",
        "model_target": "z-image-turbo"
    })
    
    # Wait for processing events
    received = socket_client.get_received()
    
    # Filter for interesting events
    log_events = [e for e in received if e["name"] == "debug_log"]
    error_events = [e for e in received if e["name"] == "error"]
    status_events = [e for e in received if e["name"] == "status_update"]
    
    # Check if we got the warning about no assistant message
    warning_logs = [
        l["args"][0] for l in log_events 
        if l["args"][0].get("level") == "WARN" 
        and "No assistant message found" in l["args"][0].get("message")
    ]
    
    assert len(warning_logs) > 0, "Should have logged warning about missing assistant message"
    
    # Verify status went back to idle despite failure to find answer
    idle_status = [
        s for s in status_events 
        if s["args"][0].get("status") == "idle"
    ]
    assert len(idle_status) > 0, "Session should return to idle state"


@patch("backend.core.opencode_client.OpencodeClient.ensure_server_running")
@patch("backend.core.opencode_client.OpencodeClient.create_session")
@patch("backend.core.opencode_client.OpencodeClient.send_message")
def test_repro_send_message_failure(
    mock_send_message, 
    mock_create_session, 
    mock_ensure_server,
    flask_app
):
    """
    Test scenario: send_message returns None (simulating timeout or 500 error)
    """
    mock_ensure_server.return_value = True
    mock_create_session.return_value = {"id": "test_opencode_session_id"}
    mock_send_message.return_value = None  # SIMULATED FAILURE
    
    socket_client = socketio.test_client(flask_app, query_string="session_id=test_bug_repro_fail")
    socket_client.connect()
    
    # Wait for session creation
    received = socket_client.get_received()
    assert any(e["name"] == "sync_state" for e in received), "Session creation failed"

    socket_client.emit("user_message", {
        "session_id": "test_bug_repro_fail",
        "content": "Fail me",
        "model_target": "z-image-turbo"
    })
    
    received = socket_client.get_received()
    error_events = [e for e in received if e["name"] == "error"]
    
    assert len(error_events) > 0, "Should emit error event"
    assert "Failed to get response" in error_events[0]["args"][0]["message"]
