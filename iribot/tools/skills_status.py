"""Skills status for tool status panel"""
from typing import Dict, Any, List
from pathlib import Path
import os


class SkillsStatus:
    """Provides status information about available skills"""
    
    @property
    def name(self) -> str:
        return "skills"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current skills status"""
        skills_dir = Path(os.getcwd()) / "skills"
        
        if not skills_dir.exists():
            return {
                "name": "skills",
                "status": "ok",
                "skills": []
            }
        
        skills = []
        
        # Iterate through all skill directories
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        skill_info = self._parse_skill_file(skill_md, skill_dir.name)
                        if skill_info:
                            skills.append(skill_info)
                    except Exception:
                        continue
        
        return {
            "name": "skills",
            "status": "ok",
            "skills": skills
        }
    
    def _parse_skill_file(self, skill_path: Path, skill_name: str) -> Dict[str, Any]:
        """Parse a skill file and extract metadata"""
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract YAML front matter if present
            yaml_content = ""
            markdown_content = content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 2:
                    yaml_content = parts[1].strip()
                    markdown_content = parts[2].strip() if len(parts) > 2 else ""
            
            # Parse YAML metadata
            title = ""
            description = ""
            version = ""
            author = ""
            tags = []
            
            if yaml_content:
                for yaml_line in yaml_content.split('\n'):
                    yaml_line = yaml_line.strip()
                    if yaml_line.lower().startswith('title:'):
                        title = yaml_line.split(':', 1)[1].strip().strip('"').strip("'")
                    elif yaml_line.lower().startswith('description:'):
                        description = yaml_line.split(':', 1)[1].strip().strip('"').strip("'")
                    elif yaml_line.lower().startswith('version:'):
                        version = yaml_line.split(':', 1)[1].strip().strip('"').strip("'")
                    elif yaml_line.lower().startswith('author:'):
                        author = yaml_line.split(':', 1)[1].strip().strip('"').strip("'")
                    elif yaml_line.lower().startswith('tags:'):
                        tags_str = yaml_line.split(':', 1)[1].strip()
                        # Parse tags (simple array format)
                        if tags_str.startswith('[') and tags_str.endswith(']'):
                            tags = [t.strip().strip('"').strip("'") for t in tags_str[1:-1].split(',')]
            
            # Fallback: extract title from first markdown header
            if not title:
                lines = markdown_content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break
            
            # Fallback: use directory name as title
            if not title:
                title = skill_name
            
            # Fallback: use first paragraph as description
            if not description:
                lines = markdown_content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        description = line
                        break
            
            return {
                "name": skill_name,
                "title": title,
                "description": description,
                "version": version,
                "author": author,
                "tags": tags
            }
            
        except Exception:
            return None
