"""Lightweight session metadata and SSE queues.

LangGraph's SqliteSaver handles actual graph state.
This module only tracks the asyncio.Queue for SSE, basic metadata, and
the project_id link to Supabase.
"""

import asyncio


_sessions: dict[str, dict] = {}


def create_session(
    session_id: str,
    topic: str,
    project_id: str | None = None,
) -> dict:
    """Create a new session with an event queue."""
    session = {
        "id": session_id,
        "topic": topic,
        "project_id": project_id,
        "queue": asyncio.Queue(),
    }
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> dict | None:
    """Get session metadata by ID."""
    return _sessions.get(session_id)


def set_project_id(session_id: str, project_id: str):
    """Link a session to its Supabase project (called when project is created)."""
    session = _sessions.get(session_id)
    if session:
        session["project_id"] = project_id


def remove_session(session_id: str):
    """Remove a session."""
    _sessions.pop(session_id, None)
