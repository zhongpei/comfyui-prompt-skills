"""
Tier 2: HTTP Routes for Testing and Health Check

Provides HTTP endpoints for testing and debugging the Logic Layer
independently from ComfyUI.
"""

from __future__ import annotations
from flask import Blueprint, jsonify, request

from ..core import (
    get_session_manager,
    get_skill_registry,
    get_opencode_client,
)

bp = Blueprint("routes", __name__)


@bp.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "prompt-skills-logic-layer",
        "version": "2.0.0",
    })


@bp.route("/api/sessions")
def list_sessions():
    """List all active sessions."""
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
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    if session:
        return jsonify(session.to_dict())
    return jsonify({"error": "Session not found"}), 404


@bp.route("/api/skills")
def list_skills():
    """List all available skills."""
    skill_registry = get_skill_registry()
    skills = skill_registry.list_all()
    return jsonify({"skills": skills})


@bp.route("/api/opencode/status")
def opencode_status():
    """Check OpenCode Server status."""
    client = get_opencode_client()
    is_running = client.is_server_running()
    return jsonify({
        "running": is_running,
        "base_url": client._config.base_url,
    })


@bp.route("/test/echo", methods=["POST"])
def test_echo():
    """Echo endpoint for testing."""
    data = request.get_json() or {}
    return jsonify({"echo": data})
