#!/usr/bin/env python3
"""
Standalone Runner for Prompt Skills Logic Layer (Tier 2/3)

This script starts the Flask server and SocketIO interface independent of ComfyUI.
It allows testing the backend logic and OpenCode integration directly.
"""

import sys
import os
import signal
import threading
import webbrowser
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from backend import create_app, socketio, get_opencode_client

def main():
    print("=" * 60)
    print("🎨 Prompt Skills - Standalone Server")
    print("=" * 60)
    
    # 1. Start OpenCode Server (Tier 3)
    print("\n[Tier 3] Checking OpenCode Server...")
    client = get_opencode_client()
    if client.ensure_server_running():
        print("✅ OpenCode Server is running")
    else:
        print("❌ Failed to start OpenCode Server. Please install: npm install -g opencode")
        sys.exit(1)
        
    # 2. Create Flask App (Tier 2)
    print("\n[Tier 2] Initializing Logic Layer...")
    app = create_app(debug=True)
    
    # 3. Start Server
    port = 8189
    url = f"http://127.0.0.1:{port}/standalone"
    print(f"\n🚀 Server starting on port {port}")
    print(f"👉 Open web interface: {url}")
    
    def open_browser():
        # Wait a bit for server to start
        import time
        time.sleep(1.5)
        print(f"Opening browser: {url}")
        webbrowser.open(url)
    
    # Uncomment to auto-open browser
    # threading.Thread(target=open_browser).start()
    
    try:
        socketio.run(
            app,
            host="127.0.0.1",
            port=port,
            debug=True,
            use_reloader=False, # Disable reloader to avoid duplicate process issues in some envs
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\nStopping server...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Cleanup
        print("Cleaning up...")
        if client:
            client.close()

if __name__ == "__main__":
    main()
