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
            # Configure OpenCode Client
            from .backend.core import get_opencode_client, OpencodeConfig
            
            # Determine config path: check sibling first, then repo root
            current_dir = Path(__file__).parent.resolve()
            config_path = current_dir / "opencode.json"
            
            if not config_path.exists():
                # Fallback to repo root (development environment)
                repo_root = current_dir.parent.parent
                config_path = repo_root / "opencode.json"
            
            if config_path.exists():
                logger.info(f"Using OpenCode config: {config_path}")
                client = get_opencode_client()
                client.configure(OpencodeConfig(config_path=str(config_path)))
                
                # Ensure server is running with this config
                if client.ensure_server_running():
                    logger.info("OpenCode Server is ready")
                else:
                    logger.error("Failed to start OpenCode Server")
            else:
                logger.warning("opencode.json not found, using default configuration")

            app = create_app()
            # Get port from environment or use default 8189 (avoid 5000 which is AirPlay on Mac)
            port = int(os.environ.get("COMFYUI_PROMPT_SKILLS_PORT", 8189))
            logger.info(f"Starting Flask Logic Layer on port {port}...")
            socketio.run(
                app,
                host="0.0.0.0",
                port=port,
                allow_unsafe_werkzeug=True,
                debug=True,
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

try:
    # Start Flask service when module is loaded
    start_flask_service()

    # Import node classes
    from .nodes import OpencodeContainerNode, ShowTextNode

    # ComfyUI node registration
    NODE_CLASS_MAPPINGS = {
        "OpencodeContainerNode": OpencodeContainerNode,
        "ShowTextNode": ShowTextNode,
    }

    NODE_DISPLAY_NAME_MAPPINGS = {
        "OpencodeContainerNode": "Prompt Skills Generator",
        "ShowTextNode": "Show Text",
    }

    # Web directory for JavaScript extensions
    WEB_DIRECTORY = "./js"

except ImportError as e:
    # Graceful fallback if running outside ComfyUI
    logger.warning(f"Running outside ComfyUI context: {e}")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}
    WEB_DIRECTORY = "./js"


__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
