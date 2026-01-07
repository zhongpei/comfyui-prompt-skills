"""
Pytest Configuration for Prompt Skills Tests

Provides fixtures for independent testing of the Logic Layer
without requiring ComfyUI environment.
"""

import os
import sys
from pathlib import Path

# Set testing environment variable BEFORE any imports
os.environ["COMFYUI_PROMPT_SKILLS_TESTING"] = "1"

# Add the plugin directory to path for imports
plugin_dir = Path(__file__).parent.parent
sys.path.insert(0, str(plugin_dir))

import pytest


@pytest.fixture
def app():
    """Create Flask app in testing mode."""
    from backend.logic import create_app, socketio
    app = create_app(debug=True, testing=True)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def socket_client(app):
    """Socket.IO test client for WebSocket testing."""
    from backend.logic import socketio
    return socketio.test_client(app)


@pytest.fixture
def session_manager():
    """Fresh SessionManager for each test."""
    from backend.core import SessionManager
    manager = SessionManager()
    manager.clear_all()
    yield manager
    manager.clear_all()
