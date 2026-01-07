"""
Tier 3: SkillRegistry - Dynamic Skill Loading and Management

Manages skill discovery, loading, and execution for multi-role prompt generation.
"""

from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Skill:
    """Represents a loaded skill with metadata and content."""
    
    id: str
    name: str
    name_zh: str
    description: str
    content: str
    file_path: Path
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize skill metadata (without content)."""
        return {
            "id": self.id,
            "name": self.name,
            "name_zh": self.name_zh,
            "description": self.description,
        }


class SkillRegistry:
    """
    Registry for dynamically loading and managing skills.
    
    Skills are loaded from the skills/ directory on-demand.
    """
    
    def __init__(self, skills_dir: Path | str | None = None) -> None:
        if skills_dir is None:
            # Default to skills/ directory relative to this file
            skills_dir = Path(__file__).parent.parent.parent / "skills"
        self._skills_dir = Path(skills_dir)
        self._cache: dict[str, Skill] = {}
    
    def _parse_skill_file(self, file_path: Path) -> Skill | None:
        """Parse a SKILL.md file and extract metadata and content."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return None
        
        # Extract YAML frontmatter if present
        name = file_path.parent.name
        name_zh = name
        description = ""
        
        lines = content.split("\n")
        if lines and lines[0].strip() == "---":
            # Find end of frontmatter
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    # Parse frontmatter
                    for fm_line in lines[1:i]:
                        if fm_line.startswith("name:"):
                            name = fm_line.split(":", 1)[1].strip().strip("\"'")
                        elif fm_line.startswith("name_zh:"):
                            name_zh = fm_line.split(":", 1)[1].strip().strip("\"'")
                        elif fm_line.startswith("description:"):
                            description = fm_line.split(":", 1)[1].strip().strip("\"'")
                    # Content is after frontmatter
                    content = "\n".join(lines[i+1:])
                    break
        
        skill_id = file_path.parent.name
        
        return Skill(
            id=skill_id,
            name=name,
            name_zh=name_zh,
            description=description,
            content=content.strip(),
            file_path=file_path,
        )
    
    def discover_skills(self) -> list[str]:
        """Discover all available skills from the skills directory."""
        if not self._skills_dir.exists():
            return []
        
        skill_ids = []
        for item in self._skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    skill_ids.append(item.name)
        
        return sorted(skill_ids)
    
    def load_skill(self, skill_id: str) -> Skill | None:
        """Load a skill by ID, using cache if available."""
        if skill_id in self._cache:
            return self._cache[skill_id]
        
        skill_file = self._skills_dir / skill_id / "SKILL.md"
        if not skill_file.exists():
            return None
        
        skill = self._parse_skill_file(skill_file)
        if skill:
            self._cache[skill_id] = skill
        
        return skill
    
    def load_skills(self, skill_ids: list[str]) -> list[Skill]:
        """Load multiple skills by ID."""
        skills = []
        for skill_id in skill_ids:
            skill = self.load_skill(skill_id)
            if skill:
                skills.append(skill)
        return skills
    
    def get_combined_prompt(self, skill_ids: list[str]) -> str:
        """Combine multiple skill contents into a single system prompt."""
        skills = self.load_skills(skill_ids)
        if not skills:
            return ""
        
        parts = []
        for skill in skills:
            parts.append(f"## Skill: {skill.name} ({skill.name_zh})\n\n{skill.content}")
        
        return "\n\n---\n\n".join(parts)
    
    def list_all(self) -> list[dict[str, Any]]:
        """List all available skills with metadata."""
        skill_ids = self.discover_skills()
        result = []
        for skill_id in skill_ids:
            skill = self.load_skill(skill_id)
            if skill:
                result.append(skill.to_dict())
        return result
    
    def clear_cache(self) -> None:
        """Clear the skill cache (for reloading)."""
        self._cache.clear()


# Global singleton instance  
_skill_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """Get the global SkillRegistry instance."""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
