"""Backend package - Three-Tier Architecture"""

from .core import (
    SessionManager,
    SkillRegistry,
    OpencodeClient,
    OutputFormatter,
    get_session_manager,
    get_skill_registry,
    get_opencode_client,
    get_output_formatter,
)

from .logic import (
    create_app,
    socketio,
    register_handlers,
)

__all__ = [
    # Core (Tier 3)
    "SessionManager",
    "SkillRegistry",
    "OpencodeClient",
    "OutputFormatter",
    "get_session_manager",
    "get_skill_registry",
    "get_opencode_client",
    "get_output_formatter",
    # Logic (Tier 2)
    "create_app",
    "socketio",
    "register_handlers",
]
