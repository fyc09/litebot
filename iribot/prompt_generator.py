"""System Prompt Generator for Agent"""

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .executor import tool_executor
import os


# Initialize Jinja2 Environment
TEMPLATE_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False
)


def get_current_datetime_info() -> Dict[str, str]:
    """
    Get current date, time and timezone information
    
    Returns:
        Dictionary containing formatted date/time/timezone
    """
    # Get current UTC time
    utc_now = datetime.now(ZoneInfo("UTC"))
    
    # Also get local timezone (system timezone)
    local_tz = datetime.now().astimezone().tzinfo
    local_now = datetime.now(local_tz)
    
    return {
        "current_utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "current_local": local_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "timezone": str(local_tz),
    }


def get_available_tools_description() -> str:
    """
    Get descriptions of all available tools for the prompt
    
    Returns:
        Formatted string describing all available tools
    """
    tools = tool_executor.get_all_tools()
    
    if not tools:
        return "No tools are currently available."
    
    tools_description = "## Available Tools\n\n"
    
    for tool in tools:
        # Extract tool info from OpenAI function format
        func = tool.get('function', {})
        tool_name = func.get('name', 'Unknown')
        tool_desc = func.get('description', 'No description available')
        params = func.get('parameters', {})
        
        tools_description += f"### {tool_name}\n"
        tools_description += f"Description: {tool_desc}\n"
        
        if 'properties' in params:
            tools_description += "Parameters:\n"
            for param_name, param_info in params['properties'].items():
                param_type = param_info.get('type', 'unknown')
                param_desc = param_info.get('description', 'No description')
                required = param_name in params.get('required', [])
                req_mark = " (required)" if required else " (optional)"
                tools_description += f"  - `{param_name}` ({param_type}){req_mark}: {param_desc}\n"
        
        tools_description += "\n"
    
    return tools_description


def get_available_skills_description() -> str:
    """
    Get descriptions of all available skills for the prompt
    
    Returns:
        Formatted string describing all available skills
    """
    skills_dir = Path(os.getcwd()) / "skills"
    
    if not skills_dir.exists():
        return "## Available Skills\n\nNo skills directory found.\n"
    
    skills_description = "## Available Skills\n\n"
    skills_found = False
    
    # Iterate through all skill directories
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                try:
                    with open(skill_md, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract YAML front matter if present
                    yaml_content = ""
                    markdown_content = content
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 2:
                            yaml_content = parts[1].strip()
                            markdown_content = parts[2].strip() if len(parts) > 2 else ""
                    
                    # Extract title and description from YAML front matter first
                    title = ""
                    description = ""
                    if yaml_content:
                        for yaml_line in yaml_content.split('\n'):
                            yaml_line = yaml_line.strip()
                            if yaml_line.lower().startswith('title:'):
                                title = yaml_line.split(':', 1)[1].strip().strip('"').strip("'")
                            elif yaml_line.lower().startswith('description:'):
                                description = yaml_line.split(':', 1)[1].strip().strip('"').strip("'")
                    
                    # Fallback: extract title from first markdown header
                    lines = markdown_content.split('\n')
                    if not title:
                        for line in lines:
                            line = line.strip()
                            if line.startswith('# '):
                                title = line[2:].strip()
                                break
                    
                    # Fallback: use directory name as title
                    if not title:
                        title = skill_dir.name

                    # Fallback: use first paragraph in markdown as description
                    if not description:
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                description = line
                                break

                    # Add skill info to description
                    skills_description += f"### {skill_dir.name}\n"
                    skills_description += f"**Title:** {title}\n"
                    if description:
                        skills_description += f"**Description:** {description}\n"
                    skills_description += f"**Location:** skills/{skill_dir.name}/SKILL.md\n"
                    skills_description += "\n"
                    skills_found = True
                except Exception:
                    continue
    
    if not skills_found:
        skills_description += "No skills found.\n"
    
    return skills_description


def generate_system_prompt(custom_instructions: str = "") -> str:
    """
    Generate a system prompt for the Agent using Jinja2 template
    
    Args:
        custom_instructions: Optional custom instructions to append to the prompt
    
    Returns:
        Complete system prompt string
    """
    datetime_info = get_current_datetime_info()
    tools_desc = get_available_tools_description()
    skills_desc = get_available_skills_description()
    
    # Load and render template
    template = jinja_env.get_template("system_prompt.j2")
    
    prompt = template.render(
        current_utc=datetime_info['current_utc'],
        current_local=datetime_info['current_local'],
        timezone=datetime_info['timezone'],
        tools_description=tools_desc,
        skills_description=skills_desc,
        custom_instructions=custom_instructions
    )
    
    return prompt
