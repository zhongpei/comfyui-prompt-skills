"""
ComfyUI Prompt Skills Plugin - Three-Tier Architecture

This plugin provides intelligent prompt generation capabilities
through integration with OpenCode Server.

Architecture:
- Tier 1 (Presentation): Vue.js application mounted in ComfyUI node
- Tier 2 (Logic): Flask + SocketIO for WebSocket communication
- Tier 3 (Core): Session management, skill registry, OpenCode client
"""

from __future__ import annotations
import os
import threading
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prompt-skills")

# Flask service singleton
_flask_thread: threading.Thread | None = None
_flask_started = False


def start_flask_service() -> None:
    """Start the Flask Logic Layer in a daemon thread."""
    global _flask_thread, _flask_started
    
    if _flask_started:
        return
    
    try:
        from .backend.logic import create_app, socketio
        
        def run_flask():
            app = create_app()
            logger.info("Starting Flask Logic Layer on port 5000...")
            socketio.run(
                app,
                host="127.0.0.1",
                port=5000,
                allow_unsafe_werkzeug=True,
                debug=False,
                use_reloader=False,
            )
        
        _flask_thread = threading.Thread(target=run_flask, daemon=True)
        _flask_thread.start()
        _flask_started = True
        logger.info("Flask Logic Layer started successfully")
    except Exception as e:
        logger.error(f"Failed to start Flask service: {e}")


# Only initialize ComfyUI-specific components when running in ComfyUI context
# This allows the backend module to be tested independently
_RUNNING_IN_COMFYUI = os.environ.get("COMFYUI_PROMPT_SKILLS_TESTING") != "1"

if _RUNNING_IN_COMFYUI:
    try:
        # Start Flask service when module is loaded
        start_flask_service()

        # Import node classes
        from .nodes import OpencodeContainerNode

        # ComfyUI node registration
        NODE_CLASS_MAPPINGS = {
            "OpencodeContainerNode": OpencodeContainerNode,
        }

        NODE_DISPLAY_NAME_MAPPINGS = {
            "OpencodeContainerNode": "Prompt Skills Generator",
        }

        # Web directory for JavaScript extensions
        WEB_DIRECTORY = "./js"

    except ImportError as e:
        # Graceful fallback if running outside ComfyUI
        logger.warning(f"Running outside ComfyUI context: {e}")
        NODE_CLASS_MAPPINGS = {}
        NODE_DISPLAY_NAME_MAPPINGS = {}
        WEB_DIRECTORY = "./js"
else:
    # Testing mode - don't load ComfyUI components
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}
    WEB_DIRECTORY = "./js"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
