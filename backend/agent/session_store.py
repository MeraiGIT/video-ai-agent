"""Lightweight session metadata and SSE queues.

LangGraph's MemorySaver handles actual graph state.
This module only tracks the asyncio.Queue for SSE and basic metadata.
"""

import asyncio


_sessions: dict[str, dict] = {}


def create_session(
    session_id: str,
    topic: str,
) -> dict:
    """Create a new session with an event queue."""
    session = {
        "id": session_id,
        "topic": topic,
        "queue": asyncio.Queue(),
    }
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> dict | None:
    """Get session metadata by ID."""
    return _sessions.get(session_id)


def remove_session(session_id: str):
    """Remove a session."""
    _sessions.pop(session_id, None)
