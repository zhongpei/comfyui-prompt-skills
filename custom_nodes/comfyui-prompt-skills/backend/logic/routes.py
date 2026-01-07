"""
Tier 2: HTTP Routes for Testing and Health Check

Provides HTTP endpoints for testing and debugging the Logic Layer
independently from ComfyUI.
"""

from __future__ import annotations
from pathlib import Path
from flask import Blueprint, jsonify, request, send_from_directory

from ..core import (
    get_session_manager,
    get_skill_registry,
    get_opencode_client,
    debug_log,
)

bp = Blueprint("routes", __name__)

# Standalone directory path
STANDALONE_DIR = Path(__file__).parent.parent.parent / "standalone"


@bp.route("/health")
def health_check():
    """Health check endpoint."""
    debug_log("Routes", "→ /health")
    return jsonify({
        "status": "ok",
        "service": "prompt-skills-logic-layer",
        "version": "2.0.0",
    })


@bp.route("/api/sessions")
def list_sessions():
    """List all active sessions."""
    debug_log("Routes", "→ /api/sessions")
    session_manager = get_session_manager()
    session_ids = session_manager.list_sessions()
    sessions = []
    for sid in session_ids:
        session = session_manager.get_session(sid)
        if session:
            sessions.append(session.to_dict())
    return jsonify({"sessions": sessions})


@bp.route("/api/sessions/<session_id>")
def get_session(session_id: str):
    """Get a specific session."""
    debug_log("Routes", f"→ /api/sessions/{session_id}")
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    if session:
        return jsonify(session.to_dict())
    return jsonify({"error": "Session not found"}), 404


@bp.route("/api/skills")
def list_skills():
    """List all available skills."""
    debug_log("Routes", "→ /api/skills")
    skill_registry = get_skill_registry()
    skills = skill_registry.list_all()
    debug_log("Routes", f"  Found {len(skills)} skills")
    return jsonify({"skills": skills})


@bp.route("/api/opencode/status")
def opencode_status():
    """Check OpenCode Server status."""
    debug_log("Routes", "→ /api/opencode/status")
    client = get_opencode_client()
    is_running = client.is_server_running()
    debug_log("Routes", f"  OpenCode running: {is_running}")
    return jsonify({
        "running": is_running,
        "base_url": client._config.base_url,
    })


@bp.route("/test/echo", methods=["POST"])
def test_echo():
    """Echo endpoint for testing."""
    data = request.get_json() or {}
    debug_log("Routes", f"→ /test/echo: {data}")
    return jsonify({"echo": data})


@bp.route("/standalone/")
@bp.route("/standalone")
def standalone_index():
    """Serve the standalone testing interface."""
    debug_log("Routes", "→ /standalone/ (serving index.html)")
    return send_from_directory(STANDALONE_DIR, "index.html")

