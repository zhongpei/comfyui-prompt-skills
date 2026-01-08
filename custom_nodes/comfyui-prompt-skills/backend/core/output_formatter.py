"""
Tier 3: OutputFormatter - Multi-format Prompt Output

Formats LLM-generated prompts into multiple output formats:
- Comma-separated English
- Structured JSON
- Bilingual (Chinese/English)
"""

from __future__ import annotations
import json
import re
from typing import Any
from dataclasses import dataclass


@dataclass
class FormattedOutput:
    """Container for multi-format prompt output."""
    
    prompt_english: str
    prompt_json: str
    prompt_bilingual: str
    raw_response: str
    
    def to_dict(self) -> dict[str, str]:
        return {
            "prompt_english": self.prompt_english,
            "prompt_json": self.prompt_json,
            "prompt_bilingual": self.prompt_bilingual,
            "raw_response": self.raw_response,
        }


class OutputFormatter:
    """
    Formats LLM responses into multiple output formats for ComfyUI nodes.
    """
    
    def __init__(self) -> None:
        self._json_pattern = re.compile(r'```json\s*(.*?)\s*```', re.DOTALL)
    
    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """Extract JSON from markdown code blocks or raw text."""
        # Try markdown code block first
        match = self._json_pattern.search(text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try parsing the whole text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try finding JSON-like structure
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _to_comma_separated(self, data: dict[str, Any]) -> str:
        """Convert structured data to comma-separated string."""
        # Priority 1: if positive_prompt exists and is non-empty, use it directly
        if "positive_prompt" in data and isinstance(data["positive_prompt"], str) and data["positive_prompt"].strip():
            return data["positive_prompt"].strip()
        
        # Priority 2: if prompt exists (common alternative name)
        if "prompt" in data and isinstance(data["prompt"], str) and data["prompt"].strip():
            return data["prompt"].strip()
        
        # Priority 3: Build from structured fields
        parts = []
        
        # Extract from common field names for subject/content
        for key in ["subject", "subject_en", "main", "content"]:
            if key in data and isinstance(data[key], str) and data[key].strip():
                parts.append(data[key].strip())
                break
        
        # Add style if present
        for key in ["style", "style_en", "styles", "aesthetic"]:
            if key in data:
                value = data[key]
                if isinstance(value, str) and value.strip():
                    parts.append(value.strip())
                    break
                elif isinstance(value, list):
                    parts.extend(str(v).strip() for v in value if str(v).strip())
                    break
        
        # Add environment if present
        for key in ["environment", "environment_en", "setting", "background"]:
            if key in data and isinstance(data[key], str) and data[key].strip():
                parts.append(data[key].strip())
                break
        
        # Add technical specs if present
        for key in ["tech_specs", "technical", "camera", "lighting"]:
            if key in data and isinstance(data[key], str) and data[key].strip():
                parts.append(data[key].strip())
                break
        
        if parts:
            return ", ".join(parts)
        
        # Fallback: try to find any human-readable string value
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 10 and not key.startswith("_"):
                return value.strip()
        
        return ""
    
    def _to_bilingual(self, data: dict[str, Any]) -> str:
        """Convert to bilingual format (Chinese/English pairs)."""
        pairs = []
        
        # Look for paired fields
        field_pairs = [
            ("subject_zh", "subject_en"),
            ("subject_zh", "subject"),
            ("style_zh", "style_en"),
            ("style_zh", "style"),
            ("environment_zh", "environment_en"),
            ("environment_zh", "environment"),
        ]
        
        for zh_key, en_key in field_pairs:
            if zh_key in data and en_key in data:
                pairs.append(f"{data[zh_key]}({data[en_key]})")
        
        if pairs:
            return ", ".join(pairs)
        
        # Fallback: if bilingual field exists
        if "bilingual" in data and isinstance(data["bilingual"], dict):
            bi = data["bilingual"]
            for key in bi:
                if key.endswith("_zh") or key.endswith("_cn"):
                    en_key = key.rsplit("_", 1)[0] + "_en"
                    if en_key in bi:
                        pairs.append(f"{bi[key]}({bi[en_key]})")
        
        return ", ".join(pairs) if pairs else self._to_comma_separated(data)
    
    def format(self, raw_response: str) -> FormattedOutput:
        """
        Format raw LLM response into multiple output formats.
        
        Args:
            raw_response: Raw text from LLM
            
        Returns:
            FormattedOutput with all format variants
        """
        # Try to extract structured JSON
        data = self._extract_json(raw_response)
        
        if data:
            prompt_english = self._to_comma_separated(data)
            prompt_json = json.dumps(data, ensure_ascii=False, indent=2)
            prompt_bilingual = self._to_bilingual(data)
        else:
            # Plain text fallback
            # Clean up markdown formatting
            clean = raw_response.strip()
            clean = re.sub(r'^#+\s*', '', clean, flags=re.MULTILINE)
            clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)
            clean = re.sub(r'\*(.+?)\*', r'\1', clean)
            
            prompt_english = clean
            prompt_json = json.dumps({"prompt": clean}, ensure_ascii=False)
            prompt_bilingual = clean
        
        return FormattedOutput(
            prompt_english=prompt_english,
            prompt_json=prompt_json,
            prompt_bilingual=prompt_bilingual,
            raw_response=raw_response,
        )
    
    def format_for_model(
        self, 
        raw_response: str, 
        model_target: str = "z-image-turbo"
    ) -> FormattedOutput:
        """
        Format response with model-specific adjustments.
        
        Args:
            raw_response: Raw text from LLM
            model_target: Target model ("z-image-turbo" or "sdxl")
            
        Returns:
            FormattedOutput optimized for the target model
        """
        output = self.format(raw_response)
        
        if model_target == "z-image-turbo":
            # Z-Image Turbo: Remove negative prompt, emphasize tech specs
            data = self._extract_json(raw_response)
            if data and "negative_prompt" in data:
                del data["negative_prompt"]
                output.prompt_json = json.dumps(data, ensure_ascii=False, indent=2)
        
        elif model_target == "sdxl":
            # SDXL: Keep negative prompt, add weight syntax if not present
            # Weight syntax like (word:1.5) is already expected in the prompt
            pass
        
        return output


# Global singleton instance
_output_formatter: OutputFormatter | None = None


def get_output_formatter() -> OutputFormatter:
    """Get the global OutputFormatter instance."""
    global _output_formatter
    if _output_formatter is None:
        _output_formatter = OutputFormatter()
    return _output_formatter
