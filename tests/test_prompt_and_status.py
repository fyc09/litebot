"""Tests for prompt generator and skills status."""
from pathlib import Path

from iribot.prompt_generator import (
    get_available_skills_description,
    get_available_tools_description,
    generate_system_prompt,
)
from iribot.tools.skills_status import SkillsStatus


def test_skills_status_no_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    status = SkillsStatus().get_status()
    assert status["skills"] == []


def test_skills_status_parses_yaml(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills" / "demo-skill"
    skills_dir.mkdir(parents=True)
    skill_md = skills_dir / "SKILL.md"
    skill_md.write_text(
        "---\n"
        "title: Demo Skill\n"
        "description: Demo description\n"
        "version: '1.2'\n"
        "author: Demo Author\n"
        "tags: [one, two]\n"
        "---\n\n"
        "# Demo Skill\n\n"
        "Details here.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    status = SkillsStatus().get_status()
    assert status["skills"][0]["name"] == "demo-skill"
    assert "one" in status["skills"][0]["tags"]


def test_skills_status_fallbacks(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills" / "plain-skill"
    skills_dir.mkdir(parents=True)
    skill_md = skills_dir / "SKILL.md"
    skill_md.write_text(
        "No yaml here.\n\nThis is the first paragraph.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    status = SkillsStatus().get_status()
    skill = status["skills"][0]
    assert skill["name"] == "plain-skill"
    assert skill["title"] == "plain-skill"
    assert "first paragraph" in skill["description"].lower()


def test_skills_description_no_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    description = get_available_skills_description()
    assert "No skills directory found" in description


def test_skills_description_fallbacks(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills" / "fallback-skill"
    skills_dir.mkdir(parents=True)
    skill_md = skills_dir / "SKILL.md"
    skill_md.write_text(
        "# Fallback Skill\n\nFirst line description.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    description = get_available_skills_description()
    assert "fallback-skill" in description
    assert "Fallback Skill" in description
    assert "First line description" in description


def test_tools_description_includes_tools():
    description = get_available_tools_description()
    assert "## Available Tools" in description
    assert "shell_run" in description


def test_generate_system_prompt_contains_sections():
    prompt = generate_system_prompt()
    assert "## Available Tools" in prompt
    assert "## Available Skills" in prompt
