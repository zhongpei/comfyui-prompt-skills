"""
Tier 1: OpencodeContainerNode - Pure Vue Container

This is a "dumb node" that acts as a placeholder in the ComfyUI graph
and a mount point for the Vue application. It contains NO business logic.

All actual processing happens via WebSocket communication with the
Flask Logic Layer (Tier 2) which is started as a daemon thread.
"""

from __future__ import annotations
from typing import Any


class OpencodeContainerNode:
    """
    Pure Container Node for ComfyUI.
    
    This node serves as:
    1. A visual placeholder in the workflow graph
    2. A configuration persistence layer (via widgets)
    3. A mount point for the Vue.js application
    
    All business logic is delegated to the Flask backend via WebSocket.
    """
    
    def __init__(self) -> None:
        pass
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "session_id": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Auto-generated session ID"
                }),
            },
            "optional": {
                "api_endpoint": ("STRING", {
                    "default": "http://127.0.0.1:8189",
                    "multiline": False,
                }),
                "model_target": (["z-image-turbo", "sdxl"], {
                    "default": "z-image-turbo"
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompt_english", "prompt_json", "prompt_bilingual")
    FUNCTION = "run"
    OUTPUT_NODE = True
    CATEGORY = "Prompt Skills"
    
    @classmethod
    def IS_CHANGED(cls, session_id, **kwargs):
        """
        Force ComfyUI to always re-execute this node.
        Returning NaN means the node output is never cached.
        This is necessary because the output depends on external state
        (SessionManager) that changes outside of ComfyUI's input tracking.
        """
        return float("NaN")
    
    def run(
        self,
        session_id: str,
        api_endpoint: str = "http://127.0.0.1:5000",
        model_target: str = "z-image-turbo",
        unique_id: str = "",
    ) -> tuple[str, str, str]:
        """
        Execute the node.
        
        Retrieves the latest generated prompts from the SessionManager.
        User should generate prompts via WebSocket/Vue UI first, then run the workflow.
        """
        # Get output directly from session manager (no waiting needed)
        try:
            from ..backend.core import get_session_manager
            
            session_manager = get_session_manager()
            
            # Debug: print session info
            print(f"[PromptSkills Node] run() called with session_id='{session_id}'")
            
            # Check if session exists
            session = session_manager.get_session(session_id)
            if session:
                print(f"[PromptSkills Node] Session found: status={session.status}, opencode_id={session.opencode_session_id}")
                print(f"[PromptSkills Node] last_output keys: {list(session.last_output.keys())}")
                print(f"[PromptSkills Node] prompt_english length: {len(session.last_output.get('prompt_english', ''))}")
            else:
                print(f"[PromptSkills Node] Session NOT FOUND for id='{session_id}'")
                # List all sessions for debugging
                all_sessions = session_manager.list_sessions()
                print(f"[PromptSkills Node] Available sessions: {all_sessions}")
            
            output = session_manager.get_output(session_id)
            
            result = (
                output.get("prompt_english", ""),
                output.get("prompt_json", ""),
                output.get("prompt_bilingual", ""),
            )
            print(f"[PromptSkills Node] Returning: english={len(result[0])} chars, json={len(result[1])} chars")
            return result
            
        except Exception as e:
            print(f"[PromptSkills Node] Exception: {e}")
            import traceback
            traceback.print_exc()
            return ("", "", "")


# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "OpencodeContainerNode": OpencodeContainerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OpencodeContainerNode": "Prompt Skills Generator",
}
