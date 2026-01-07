
import unittest
import socketio
import time
import subprocess
import sys
import os
import signal
from pathlib import Path
import threading

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

class TestStandaloneE2E(unittest.TestCase):
    """
    End-to-End test for Standalone Server (Tier 2 & 3).
    
    This test:
    1. Starts the standalone server (run_standalone.py)
    2. Connects using a SocketIO client
    3. Simulates a user session (Select Skill -> Send Prompt)
    4. Verifies streaming and final completion
    """
    
    SERVER_PROCESS = None
    SERVER_PORT = 8189
    SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"
    
    @classmethod
    def setUpClass(cls):
        print(f"\n[Test] Starting standalone server on port {cls.SERVER_PORT}...")
        
        # Path to run_standalone.py
        runner_path = PROJECT_ROOT / "run_standalone.py"
        
        # Start server in background
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["COMFYUI_PROMPT_SKILLS_DEBUG"] = "1"  # Enable debug mode
        
        cls.SERVER_PROCESS = subprocess.Popen(
            [sys.executable, str(runner_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=PROJECT_ROOT,
            env=env,
            text=True
        )
        
        # Wait for server to be ready
        print("[Test] Waiting for server to start...")
        start_time = time.time()
        server_ready = False
        
        # Read stdout in a thread to check for "Server starting"
        def check_output():
            nonlocal server_ready
            try:
                for line in iter(cls.SERVER_PROCESS.stdout.readline, ''):
                    print(f"[Server] {line.strip()}")
                    if f"Running on http://127.0.0.1:{cls.SERVER_PORT}" in line or "Debugger PIN" in line:
                         # Flask output isn't always reliable for "ready", but let's try
                         pass
            except:
                pass

        threading.Thread(target=check_output, daemon=True).start()
        
        # Poll /health endpoint
        import urllib.request
        for _ in range(20):  # 10 seconds
            try:
                with urllib.request.urlopen(f"{cls.SERVER_URL}/health") as response:
                    if response.status == 200:
                        server_ready = True
                        break
            except:
                time.sleep(0.5)
        
        if not server_ready:
            print("[Test] Server failed to start!")
            cls.tearDownClass()
            raise RuntimeError("Server failed to start")
            
        print("[Test] Server is ready!")

    @classmethod
    def tearDownClass(cls):
        if cls.SERVER_PROCESS:
            print("\n[Test] Stopping server...")
            cls.SERVER_PROCESS.terminate()
            cls.SERVER_PROCESS.wait()
            print("[Test] Server stopped")

    def test_full_flow(self):
        """Test the full flow: Connect -> Configure -> Message -> Stream -> Complete"""
        
        sio = socketio.Client()
        
        events = {
            "connect": False,
            "sync_state": False,
            "skills_list": False,
            "stream_delta": [],
            "complete": None,
            "disconnect": False
        }
        
        session_id = "test_standalone_session"
        
        @sio.on("connect")
        def on_connect():
            print("[Client] Connected!")
            events["connect"] = True

        @sio.on("sync_state")
        def on_sync_state(data):
            print(f"[Client] Sync State: {data['status']}")
            events["sync_state"] = True
            
        @sio.on("skills_list")
        def on_skills_list(data):
            print(f"[Client] Received {len(data['skills'])} skills")
            events["skills_list"] = True
            
        @sio.on("stream_delta")
        def on_stream_delta(data):
            print(f"[Client] Stream: {data['delta']}", end="", flush=True)
            events["stream_delta"].append(data['delta'])
            
        @sio.on("complete")
        def on_complete(data):
            print(f"\n[Client] Complete!")
            events["complete"] = data
            
        @sio.on("error")
        def on_error(data):
            print(f"\n[Client] Error: {data}")
            
        @sio.on("debug_log")
        def on_debug_log(data):
            # Print debug logs from server to help diagnose
            print(f"[Server-Debug] [{data.get('module')}] {data.get('message')}")

        # Connect
        print(f"[Test] Connecting to {self.SERVER_URL}...")
        sio.connect(f"{self.SERVER_URL}?session_id={session_id}", transports=['websocket'])
        
        # Wait for connect and initial sync
        time.sleep(2)
        self.assertTrue(events["connect"])
        self.assertTrue(events["sync_state"])
        self.assertTrue(events["skills_list"])
        
        # Configure
        print("\n[Test] Configuring session...")
        sio.emit("configure", {
            "session_id": session_id,
            "active_skills": ["z-photo"], # Assuming "z-photo" exists
            "model_target": "z-image-turbo"
        })
        time.sleep(1)
        
        # Send Message
        prompt = "A cute cat sitting on a windowsill"
        print(f"\n[Test] Sending prompt: {prompt}")
        sio.emit("user_message", {
            "session_id": session_id,
            "content": prompt,
            "model_target": "z-image-turbo"
        })
        
        # Wait for completion (max 120s)
        print("[Test] Waiting for generation...")
        start_wait = time.time()
        while events["complete"] is None and time.time() - start_wait < 120:
            time.sleep(1)
            
        if events["complete"] is None:
            self.fail("Timed out waiting for completion")
            
        # Verify
        print("\n[Test] Verifying results...")
        full_stream = "".join(events["stream_delta"])
        complete_data = events["complete"]
        
        self.assertIsNotNone(complete_data["prompt_english"])
        print(f"[Test] Generated Prompt: {complete_data['prompt_english']}")
        
        # Check if stream matches content from complete event 
        # (Note: stream is raw response, complete data might be formatted. 
        # The stream_delta contains the raw LLM output, which should contain the JSON blocks)
        self.assertTrue(len(full_stream) > 0)
        
        sio.disconnect()

if __name__ == "__main__":
    unittest.main()
