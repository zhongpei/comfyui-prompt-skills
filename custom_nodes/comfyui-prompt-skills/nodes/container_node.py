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
                    "default": "http://127.0.0.1:5000",
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
    
    def run(
        self,
        session_id: str,
        api_endpoint: str = "http://127.0.0.1:5000",
        model_target: str = "z-image-turbo",
        unique_id: str = "",
    ) -> tuple[str, str, str]:
        """
        Execute the node.
        
        Note: This node does nothing on its own. Actual prompt generation
        happens via the Vue frontend which communicates with the Flask
        backend through WebSocket.
        
        The outputs are populated by the frontend storing results in
        the widget values, which persist in the workflow JSON.
        """
        # The node itself doesn't process - it's just a container
        # The Vue app handles all interaction and stores results
        # in sessionStorage or emits them through ComfyUI API
        
        # Return empty strings - actual values come from widget persistence
        return ("", "", "")


# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "OpencodeContainerNode": OpencodeContainerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OpencodeContainerNode": "Prompt Skills Generator",
}
