"""Tier 2: Logic Layer - Flask + SocketIO"""

from .app import create_app, socketio
from .socket_handlers import register_handlers

__all__ = [
    "create_app",
    "socketio",
    "register_handlers",
]
