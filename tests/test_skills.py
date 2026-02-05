"""Tests for skills tools"""
import pytest
import tempfile
import os
from pathlib import Path
from iribot.tools.skills import SearchSkillTool, UseSkillTool


class TestSearchSkillTool:
    """Tests for SearchSkillTool"""

    def test_search_existing_skill(self, tmp_path, monkeypatch):
        """Test searching for an existing skill"""
        # Create a temporary skills directory
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create a skill directory with SKILL.md
        python_skill = skills_dir / "python"
        python_skill.mkdir()
        (python_skill / "SKILL.md").write_text("# Python Development\n\nPython coding guide.")

        # Mock the SKILLS_DIR
        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = SearchSkillTool()
        result = tool.execute(keyword="python")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["skills"][0]["id"] == "python"
        assert result["skills"][0]["title"] == "Python Development"

    def test_search_no_results(self, tmp_path, monkeypatch):
        """Test searching when no skills match"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = SearchSkillTool()
        result = tool.execute(keyword="nonexistent")

        assert result["success"] is True
        assert result["count"] == 0
        assert result["skills"] == []

    def test_search_no_skills_directory(self, tmp_path, monkeypatch):
        """Test searching when skills directory doesn't exist"""
        skills_dir = tmp_path / "nonexistent_skills"

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = SearchSkillTool()
        result = tool.execute(keyword="python")

        assert result["success"] is True
        assert result["skills"] == []

    def test_search_sub_skills_not_returned(self, tmp_path, monkeypatch):
        """Test that sub-skills are not returned in search results"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create main skill
        python_skill = skills_dir / "python"
        python_skill.mkdir()
        (python_skill / "SKILL.md").write_text("# Python Development")

        # Create sub-skill as a file
        (python_skill / "debugging.md").write_text("# Debugging")

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = SearchSkillTool()
        result = tool.execute(keyword="debugging")

        # Should not find debugging as a top-level skill
        assert result["success"] is True
        assert result["count"] == 0

    def test_search_case_insensitive(self, tmp_path, monkeypatch):
        """Test that search is case insensitive"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        python_skill = skills_dir / "PythonGuide"
        python_skill.mkdir()
        (python_skill / "SKILL.md").write_text("# Python Guide")

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = SearchSkillTool()
        result = tool.execute(keyword="python")

        assert result["success"] is True
        assert result["count"] == 1


class TestUseSkillTool:
    """Tests for UseSkillTool"""

    def test_use_main_skill(self, tmp_path, monkeypatch):
        """Test using a main skill"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        python_skill = skills_dir / "python"
        python_skill.mkdir()
        content = "# Python Development\n\nBest practices for Python."
        (python_skill / "SKILL.md").write_text(content)

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = UseSkillTool()
        result = tool.execute(skill_id="python")

        assert result["success"] is True
        assert result["skill_id"] == "python"
        assert result["content"] == content

    def test_use_sub_skill_as_file(self, tmp_path, monkeypatch):
        """Test using a sub-skill stored as a file"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        python_skill = skills_dir / "python"
        python_skill.mkdir()
        (python_skill / "SKILL.md").write_text("# Python")

        sub_content = "# Debugging\n\nDebug techniques."
        (python_skill / "debugging.md").write_text(sub_content)

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = UseSkillTool()
        result = tool.execute(skill_id="python/debugging")

        assert result["success"] is True
        assert result["content"] == sub_content

    def test_use_sub_skill_as_directory(self, tmp_path, monkeypatch):
        """Test using a sub-skill stored as a directory with SKILL.md"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        python_skill = skills_dir / "python"
        python_skill.mkdir()

        debugging_dir = python_skill / "debugging"
        debugging_dir.mkdir()
        sub_content = "# Debugging Guide"
        (debugging_dir / "SKILL.md").write_text(sub_content)

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = UseSkillTool()
        result = tool.execute(skill_id="python/debugging")

        assert result["success"] is True
        assert result["content"] == sub_content

    def test_use_nonexistent_skill(self, tmp_path, monkeypatch):
        """Test using a skill that doesn't exist"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = UseSkillTool()
        result = tool.execute(skill_id="nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_use_skill_no_directory(self, tmp_path, monkeypatch):
        """Test using a skill when skills directory doesn't exist"""
        skills_dir = tmp_path / "nonexistent"

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        tool = UseSkillTool()
        result = tool.execute(skill_id="python")

        assert result["success"] is False
        assert "not found" in result["error"]


class TestSkillToolsIntegration:
    """Integration tests for skill tools"""

    def test_search_then_use(self, tmp_path, monkeypatch):
        """Test searching for a skill then using it"""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        web_skill = skills_dir / "web"
        web_skill.mkdir()
        content = "# Web Development\n\nWeb dev guide."
        (web_skill / "SKILL.md").write_text(content)

        monkeypatch.setattr("iribot.tools.skills.SKILLS_DIR", skills_dir)

        # Search for the skill
        search_tool = SearchSkillTool()
        search_result = search_tool.execute(keyword="web")

        assert search_result["success"] is True
        assert search_result["count"] == 1
        skill_id = search_result["skills"][0]["id"]

        # Use the skill
        use_tool = UseSkillTool()
        use_result = use_tool.execute(skill_id=skill_id)

        assert use_result["success"] is True
        assert use_result["content"] == content
