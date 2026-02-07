"""Tests for SessionManager."""
from iribot.session_manager import SessionManager
from iribot.models import MessageRecord, ToolCallRecord


def test_session_manager_basic_flow(tmp_path):
    manager = SessionManager(storage_path=str(tmp_path))
    session = manager.create_session(title="Test")

    user_record = MessageRecord(role="user", content="hello").model_dump()
    manager.add_record(session.id, user_record)

    assistant_record = MessageRecord(role="assistant", content="thinking").model_dump()
    manager.add_record(session.id, assistant_record)

    tool_record = ToolCallRecord(
        tool_call_id="call-1",
        tool_name="shell_run",
        arguments={"cmd": "echo"},
        result={"ok": True},
        success=True,
    ).model_dump()
    manager.add_record(session.id, tool_record)

    messages = manager.get_messages_for_llm(session.id)
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["tool_calls"][0]["function"]["name"] == "shell_run"
    assert messages[-1]["role"] == "tool"

    assert manager.get_session(session.id) is not None
    assert manager.delete_session(session.id) is True
    assert manager.get_session(session.id) is None


def test_migrate_old_format(tmp_path):
    manager = SessionManager(storage_path=str(tmp_path))
    data = {
        "id": "1",
        "title": "Old",
        "messages": [
            {"role": "user", "content": "hi", "timestamp": "t"},
        ],
        "system_prompt": "sys",
        "created_at": "t0",
    }
    migrated = manager._migrate_old_format(data)
    assert "records" in migrated
    assert "messages" not in migrated
    assert migrated["records"][0]["role"] == "system"


def test_delete_missing_session(tmp_path):
    manager = SessionManager(storage_path=str(tmp_path))
    assert manager.delete_session("does-not-exist") is False
