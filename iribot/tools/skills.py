"""Skills management tools"""
import os
from typing import Any, Dict, List
from pathlib import Path
from .base import BaseTool


SKILLS_DIR = Path(os.getcwd()) / "skills"


class UseSkillTool(BaseTool):
    """Use a skill by ID"""

    @property
    def name(self) -> str:
        return "use_skill"

    @property
    def description(self) -> str:
        return "Get the content of a skill by its ID. Skill ID format: 'skill_name' for main skill, or 'skill_name/sub_skill' for sub-skills. Returns the markdown content of the skill file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_id": {
                    "type": "string",
                    "description": "Skill ID, e.g., 'python' for skills/python/SKILL.md, or 'python/debugging' for skills/python/debugging.md or skills/python/debugging/SKILL.md"
                }
            },
            "required": ["skill_id"]
        }

    def _resolve_skill_path(self, skill_id: str) -> Path:
        """Resolve skill ID to actual file path"""
        # Normalize path separators
        parts = skill_id.replace('\\', '/').split('/')

        # Build base path
        base_path = SKILLS_DIR / parts[0]

        if len(parts) == 1:
            # Main skill: skills/name/SKILL.md
            return base_path / "SKILL.md"
        else:
            # Sub-skill: try skills/name/sub.md first, then skills/name/sub/SKILL.md
            sub_path = '/'.join(parts[1:])
            direct_md = base_path / f"{sub_path}.md"
            if direct_md.exists():
                return direct_md

            nested_path = base_path / sub_path / "SKILL.md"
            if nested_path.exists():
                return nested_path

            return direct_md  # Return the first option even if it doesn't exist

    def execute(self, skill_id: str) -> Dict[str, Any]:
        """Get skill content by ID"""
        try:
            if not SKILLS_DIR.exists():
                return {
                    "success": False,
                    "error": "Skills directory not found"
                }

            skill_path = self._resolve_skill_path(skill_id)

            if not skill_path.exists():
                return {
                    "success": False,
                    "error": f"Skill '{skill_id}' not found at {skill_path}"
                }

            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "success": True,
                "skill_id": skill_id,
                "content": content,
                "path": str(skill_path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
