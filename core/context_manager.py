"""
Context Manager - Memory and State Management

This module manages conversation history, screen state tracking,
action history, and persistent context storage.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ScreenState:
    """Captured screen state."""
    timestamp: datetime
    active_window: str
    window_title: str
    ocr_text: Optional[str] = None
    ui_elements: list = field(default_factory=list)
    screenshot_path: Optional[str] = None


@dataclass
class ActionRecord:
    """Record of an executed action."""
    timestamp: datetime
    action_type: str
    tool_name: str
    parameters: dict
    result: Any
    success: bool
    error: Optional[str] = None


class ContextManager:
    """
    Manages all context for the agent including conversation history,
    screen state, action history, and persistent storage.
    """
    
    def __init__(
        self,
        max_context_messages: int = 50,
        max_action_history: int = 100,
        persistence_path: Optional[Path] = None,
    ):
        """
        Initialize the Context Manager.
        
        Args:
            max_context_messages: Maximum messages to keep in memory
            max_action_history: Maximum actions to track
            persistence_path: Path for SQLite database (optional)
        """
        self.max_context_messages = max_context_messages
        self.max_action_history = max_action_history
        
        # In-memory storage
        self._messages: deque[Message] = deque(maxlen=max_context_messages)
        self._action_history: deque[ActionRecord] = deque(maxlen=max_action_history)
        self._screen_state: Optional[ScreenState] = None
        self._session_data: dict = {}
        
        # Persistence
        self._db_path = persistence_path
        self._db: Optional[sqlite3.Connection] = None
        
        if persistence_path:
            self._init_database(persistence_path)
        
        logger.info("Context Manager initialized")
    
    def _init_database(self, path: Path):
        """Initialize SQLite database for persistence."""
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            );
            
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action_type TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                parameters TEXT,
                result TEXT,
                success INTEGER,
                error TEXT
            );
            
            CREATE TABLE IF NOT EXISTS session_data (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
            CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON actions(timestamp);
        """)
        self._db.commit()
        logger.info(f"Database initialized at {path}")
    
    # Message Management
    
    def add_message(self, role: str, content: str, metadata: Optional[dict] = None) -> Message:
        """Add a message to the conversation history."""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self._messages.append(message)
        
        if self._db:
            self._persist_message(message)
        
        return message
    
    def get_messages(self, limit: Optional[int] = None) -> list[Message]:
        """Get recent messages from conversation history."""
        messages = list(self._messages)
        if limit:
            messages = messages[-limit:]
        return messages
    
    def get_messages_for_llm(self, limit: Optional[int] = None) -> list[dict]:
        """Get messages formatted for LLM API."""
        messages = self.get_messages(limit)
        return [{"role": m.role, "content": m.content} for m in messages]
    
    def clear_messages(self):
        """Clear conversation history."""
        self._messages.clear()
        logger.info("Conversation history cleared")
    
    def _persist_message(self, message: Message):
        """Persist a message to the database."""
        self._db.execute(
            "INSERT INTO messages (role, content, timestamp, metadata) VALUES (?, ?, ?, ?)",
            (message.role, message.content, message.timestamp.isoformat(), json.dumps(message.metadata))
        )
        self._db.commit()
    
    # Screen State Management
    
    def update_screen_state(
        self,
        active_window: str,
        window_title: str,
        ocr_text: Optional[str] = None,
        ui_elements: Optional[list] = None,
        screenshot_path: Optional[str] = None,
    ) -> ScreenState:
        """Update the current screen state."""
        self._screen_state = ScreenState(
            timestamp=datetime.now(),
            active_window=active_window,
            window_title=window_title,
            ocr_text=ocr_text,
            ui_elements=ui_elements or [],
            screenshot_path=screenshot_path,
        )
        return self._screen_state
    
    def get_screen_state(self) -> Optional[ScreenState]:
        """Get the current screen state."""
        return self._screen_state
    
    def get_screen_context(self) -> str:
        """Get screen state as a context string for LLM."""
        if not self._screen_state:
            return "No screen information available."
        
        state = self._screen_state
        context = f"Active Window: {state.active_window} - {state.window_title}\n"
        
        if state.ocr_text:
            context += f"Visible Text:\n{state.ocr_text[:500]}...\n" if len(state.ocr_text) > 500 else f"Visible Text:\n{state.ocr_text}\n"
        
        if state.ui_elements:
            context += f"UI Elements: {len(state.ui_elements)} detected\n"
        
        return context
    
    # Action History Management
    
    def record_action(
        self,
        action_type: str,
        tool_name: str,
        parameters: dict,
        result: Any,
        success: bool,
        error: Optional[str] = None,
    ) -> ActionRecord:
        """Record an executed action."""
        record = ActionRecord(
            timestamp=datetime.now(),
            action_type=action_type,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            success=success,
            error=error,
        )
        self._action_history.append(record)
        
        if self._db:
            self._persist_action(record)
        
        return record
    
    def get_action_history(self, limit: Optional[int] = None) -> list[ActionRecord]:
        """Get recent action history."""
        history = list(self._action_history)
        if limit:
            history = history[-limit:]
        return history
    
    def get_last_action(self) -> Optional[ActionRecord]:
        """Get the most recent action."""
        return self._action_history[-1] if self._action_history else None
    
    def _persist_action(self, record: ActionRecord):
        """Persist an action to the database."""
        self._db.execute(
            """INSERT INTO actions 
               (timestamp, action_type, tool_name, parameters, result, success, error) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                record.timestamp.isoformat(),
                record.action_type,
                record.tool_name,
                json.dumps(record.parameters),
                json.dumps(str(record.result)),
                1 if record.success else 0,
                record.error,
            )
        )
        self._db.commit()
    
    # Session Data Management
    
    def set(self, key: str, value: Any):
        """Set a session data value."""
        self._session_data[key] = value
        
        if self._db:
            self._db.execute(
                """INSERT OR REPLACE INTO session_data (key, value, updated_at) 
                   VALUES (?, ?, ?)""",
                (key, json.dumps(value), datetime.now().isoformat())
            )
            self._db.commit()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a session data value."""
        return self._session_data.get(key, default)
    
    def delete(self, key: str):
        """Delete a session data value."""
        self._session_data.pop(key, None)
        
        if self._db:
            self._db.execute("DELETE FROM session_data WHERE key = ?", (key,))
            self._db.commit()
    
    # Context Building
    
    def build_context(self, include_screen: bool = True, include_actions: int = 5) -> str:
        """
        Build a comprehensive context string for the LLM.
        
        Args:
            include_screen: Include current screen state
            include_actions: Number of recent actions to include
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        if include_screen and self._screen_state:
            context_parts.append("## Current Screen State")
            context_parts.append(self.get_screen_context())
        
        if include_actions:
            recent_actions = self.get_action_history(include_actions)
            if recent_actions:
                context_parts.append("## Recent Actions")
                for action in recent_actions:
                    status = "✓" if action.success else "✗"
                    context_parts.append(f"- [{status}] {action.tool_name}: {action.action_type}")
        
        return "\n".join(context_parts)
    
    def __del__(self):
        """Cleanup database connection."""
        if self._db:
            self._db.close()
