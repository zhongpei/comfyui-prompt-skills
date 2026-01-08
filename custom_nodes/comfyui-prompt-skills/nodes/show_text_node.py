"""
ShowText Node - Display text output for debugging

A simple utility node to display text in the ComfyUI console.
"""

from __future__ import annotations
from typing import Any


class ShowTextNode:
    """
    Simple text display node for debugging.
    
    Shows the input text in the console and passes it through.
    """
    
    def __init__(self) -> None:
        pass
    
    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                }),
            },
            "optional": {
                "prefix": ("STRING", {
                    "default": "[ShowText]",
                    "multiline": False,
                }),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    OUTPUT_NODE = True
    CATEGORY = "Prompt Skills"
    
    def run(
        self,
        text: str,
        prefix: str = "[ShowText]",
    ) -> tuple[str]:
        """
        Display text and pass it through.
        """
        print(f"{prefix} {text}")
        return (text,)


# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "ShowTextNode": ShowTextNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ShowTextNode": "Show Text",
}
