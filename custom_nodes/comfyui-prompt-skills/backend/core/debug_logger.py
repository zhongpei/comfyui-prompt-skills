"""
Debug Logger - Unified Debug Logging for ComfyUI Prompt Skills

Provides centralized debug logging that can be enabled via environment variable:
    COMFYUI_PROMPT_SKILLS_DEBUG=1

Supports both console output and WebSocket emission to frontend.
"""

from __future__ import annotations
import os
import sys
import logging
from datetime import datetime
from typing import Any, Callable

# Check if debug mode is enabled
DEBUG_MODE = os.environ.get("COMFYUI_PROMPT_SKILLS_DEBUG", "0") == "1"

# Configure logging level based on debug mode
LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO


def setup_logging() -> logging.Logger:
    """Setup and configure the debug logger."""
    logger = logging.getLogger("prompt-skills")
    logger.setLevel(LOG_LEVEL)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(LOG_LEVEL)
    
    # Detailed format for debug mode
    if DEBUG_MODE:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s.%(module)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            "[%(levelname)s] %(name)s: %(message)s"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logging()


class DebugEmitter:
    """
    Emits debug messages to both console and WebSocket.
    
    Usage:
        debug = DebugEmitter(socketio, session_id)
        debug.info("SocketHandler", "Connected to session")
        debug.error("OpenCode", "Failed to connect")
    """
    
    def __init__(
        self, 
        emit_func: Callable[[str, dict, str], None] | None = None,
        session_id: str | None = None
    ) -> None:
        self._emit_func = emit_func
        self._session_id = session_id
    
    def _log(self, level: str, module: str, message: str, **kwargs: Any) -> None:
        """Internal method to log and emit debug message."""
        # Always log to console
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{module}] {message}")
        
        # Emit to WebSocket if available
        if self._emit_func and self._session_id:
            try:
                self._emit_func("debug_log", {
                    "level": level.upper(),
                    "module": module,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    **kwargs
                }, self._session_id)
            except Exception as e:
                logger.warning(f"Failed to emit debug_log: {e}")
    
    def debug(self, module: str, message: str, **kwargs: Any) -> None:
        """Log DEBUG level message (only in debug mode)."""
        if DEBUG_MODE:
            self._log("DEBUG", module, message, **kwargs)
    
    def info(self, module: str, message: str, **kwargs: Any) -> None:
        """Log INFO level message."""
        self._log("INFO", module, message, **kwargs)
    
    def warn(self, module: str, message: str, **kwargs: Any) -> None:
        """Log WARNING level message."""
        self._log("WARN", module, message, **kwargs)
    
    def error(self, module: str, message: str, **kwargs: Any) -> None:
        """Log ERROR level message."""
        self._log("ERROR", module, message, **kwargs)
    
    def trace_call(self, func_name: str, **args: Any) -> None:
        """Log function call with arguments (debug mode only)."""
        if DEBUG_MODE:
            args_str = ", ".join(f"{k}={repr(v)[:50]}" for k, v in args.items())
            self._log("DEBUG", "Trace", f"→ {func_name}({args_str})")
    
    def trace_return(self, func_name: str, result: Any = None) -> None:
        """Log function return (debug mode only)."""
        if DEBUG_MODE:
            result_str = repr(result)[:100] if result is not None else "None"
            self._log("DEBUG", "Trace", f"← {func_name} returned: {result_str}")


def get_debug_emitter(
    emit_func: Callable | None = None,
    session_id: str | None = None
) -> DebugEmitter:
    """Factory function to create a DebugEmitter instance."""
    return DebugEmitter(emit_func, session_id)


# Convenience function for simple console logging
def debug_log(module: str, message: str, level: str = "INFO") -> None:
    """Simple debug logging without WebSocket emission."""
    if level == "DEBUG" and not DEBUG_MODE:
        return
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[{module}] {message}")


# Log startup info
if DEBUG_MODE:
    logger.info("🔧 Debug mode ENABLED (COMFYUI_PROMPT_SKILLS_DEBUG=1)")
