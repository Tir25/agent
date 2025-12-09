"""
Tests for core module.
"""

import pytest
from core.context_manager import ContextManager, Message


class TestContextManager:
    """Tests for ContextManager."""
    
    def test_add_message(self):
        """Test adding messages to context."""
        ctx = ContextManager()
        
        msg = ctx.add_message("user", "Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        
        messages = ctx.get_messages()
        assert len(messages) == 1
    
    def test_message_limit(self):
        """Test that message limit is respected."""
        ctx = ContextManager(max_context_messages=5)
        
        for i in range(10):
            ctx.add_message("user", f"Message {i}")
        
        messages = ctx.get_messages()
        assert len(messages) == 5
        assert messages[0].content == "Message 5"
    
    def test_session_data(self):
        """Test session data storage."""
        ctx = ContextManager()
        
        ctx.set("key1", "value1")
        ctx.set("key2", {"nested": True})
        
        assert ctx.get("key1") == "value1"
        assert ctx.get("key2") == {"nested": True}
        assert ctx.get("missing") is None
        assert ctx.get("missing", "default") == "default"
    
    def test_action_recording(self):
        """Test action history recording."""
        ctx = ContextManager()
        
        ctx.record_action(
            action_type="click",
            tool_name="windows_control",
            parameters={"x": 100, "y": 200},
            result="success",
            success=True,
        )
        
        history = ctx.get_action_history()
        assert len(history) == 1
        assert history[0].tool_name == "windows_control"
        assert history[0].success is True
