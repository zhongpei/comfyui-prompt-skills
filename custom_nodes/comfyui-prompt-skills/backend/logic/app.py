"""
Tier 2: Flask Application Factory

Creates and configures the Flask application with SocketIO for
real-time WebSocket communication.
"""

from __future__ import annotations
from flask import Flask
from flask_socketio import SocketIO

# Global SocketIO instance (needed for handlers registration)
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",  # Use threading for compatibility with ComfyUI
    logger=False,
    engineio_logger=False,
)


def create_app(debug: bool = False, testing: bool = False) -> Flask:
    """
    Application factory for Flask app.
    
    Args:
        debug: Enable debug mode
        testing: Enable testing mode (no real network calls)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Configuration
    app.config["DEBUG"] = debug
    app.config["TESTING"] = testing
    app.config["SECRET_KEY"] = "prompt-skills-secret-key"
    
    # Register HTTP routes
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    # Initialize SocketIO with app
    socketio.init_app(app)
    
    # Register WebSocket event handlers
    from .socket_handlers import register_handlers
    register_handlers(socketio)
    
    return app
