import os
import uuid
import json
import asyncio
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from api.schemas import (
    CreateSessionRequest, CreateSessionResponse, ResumeRequest, UploadResponse,
)
from agent.graph import graph
from agent.state import ProductionState
from agent.session_store import create_session, get_session, set_project_id
from services import supabase_service
from utils.file_manager import get_job_path

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_UPLOAD_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "video/mp4", "video/quicktime", "video/webm",
    "audio/mpeg", "audio/wav", "audio/mp4", "audio/ogg", "audio/webm",
}


async def _run_graph(session_id: str, input_or_command):
    """Run or resume the LangGraph pipeline, pushing custom events to the session queue.

    Also persists each event to Supabase chat_messages for history/resume support.
    """
    session = get_session(session_id)
    if not session:
        return

    queue = session["queue"]
    config = {"configurable": {"thread_id": session_id}}

    # Track project_id for chat persistence — may already be set (resume case)
    project_id = session.get("project_id")
    event_buffer: list[dict] = []  # buffer events emitted before project_id is known
    ordinal = session.get("_ordinal", 0)

    async def _persist_event(evt: dict):
        """Save event to Supabase if project_id is known, otherwise buffer it."""
        nonlocal project_id, ordinal, event_buffer
        event_type = evt.get("event", "message")

        # Check if this event reveals the project_id
        if event_type == "project_created":
            pid = evt.get("data", {}).get("project_id")
            if pid:
                project_id = pid
                set_project_id(session_id, pid)
                # Flush buffered events
                for buf_evt in event_buffer:
                    ordinal += 1
                    supabase_service.save_chat_event(
                        project_id, session_id, buf_evt.get("event", "message"),
                        buf_evt.get("data", {}), ordinal,
                    )
                event_buffer.clear()

        if project_id:
            ordinal += 1
            supabase_service.save_chat_event(
                project_id, session_id, event_type,
                evt.get("data", {}), ordinal,
            )
        else:
            event_buffer.append(evt)

    try:
        async for chunk in graph.astream(
            input_or_command,
            config=config,
            stream_mode="custom",
        ):
            if isinstance(chunk, dict) and "event" in chunk:
                await queue.put(chunk)
                await _persist_event(chunk)

        # Check if graph is interrupted (waiting for user input)
        state = await graph.aget_state(config)
        if state.tasks:
            for task in state.tasks:
                if task.interrupts:
                    interrupt_data = task.interrupts[0].value
                    awaiting_evt = {
                        "event": "awaiting",
                        "data": interrupt_data,
                    }
                    await queue.put(awaiting_evt)
                    await _persist_event(awaiting_evt)
                    # Store ordinal for next resume
                    session["_ordinal"] = ordinal
                    return

        # Graph completed without interrupt

    except Exception as e:
        logger.exception(f"Graph error for session {session_id}")
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            error_msg = "An API authentication error occurred. Please check your API keys."
        elif "rate_limit" in error_msg.lower() or "429" in error_msg:
            error_msg = "API rate limit reached. Please wait a moment and try again."
        elif "timeout" in error_msg.lower():
            error_msg = "A request timed out. This can happen with large generations. Please try again."
        elif len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        error_evt = {"event": "error", "data": {"message": error_msg}}
        await queue.put(error_evt)
        await _persist_event(error_evt)

    # Store ordinal for potential resume
    session["_ordinal"] = ordinal


@router.post("/api/sessions", response_model=CreateSessionResponse)
async def create_new_session(body: CreateSessionRequest):
    """Create a new session and start the generation pipeline."""
    session_id = str(uuid.uuid4())

    create_session(
        session_id=session_id,
        topic=body.topic,
    )

    # Build initial state for the universal production pipeline
    initial_state: dict = {
        "job_id": session_id,
        "user_request": body.topic,
        "progress_messages": [],
    }

    # Pass uploaded file URLs into state if provided
    if body.uploaded_file_urls:
        initial_state["uploaded_files"] = [
            {"url": url, "type": _guess_type(url), "filename": url.rsplit("/", 1)[-1]}
            for url in body.uploaded_file_urls
        ]

    asyncio.create_task(_run_graph(session_id, initial_state))

    return CreateSessionResponse(session_id=session_id)


def _guess_type(url: str) -> str:
    """Guess MIME type from URL extension."""
    ext = url.rsplit(".", 1)[-1].lower() if "." in url else ""
    return {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "gif": "image/gif",
        "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
    }.get(ext, "application/octet-stream")


@router.post("/api/sessions/{session_id}/upload", response_model=UploadResponse)
async def upload_file(session_id: str, file: UploadFile = File(...)):
    """Upload a file (image or video) to a session workspace."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate content type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: images and videos.",
        )

    # Read and validate size
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    # Sanitize filename
    original_name = file.filename or "upload"
    safe_name = "".join(
        c for c in original_name if c.isalnum() or c in "._-"
    ).strip() or "upload"

    # Save to workspace
    upload_dir = Path(get_job_path(session_id, "")) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Avoid collisions
    dest = upload_dir / safe_name
    if dest.exists():
        stem, ext = safe_name.rsplit(".", 1) if "." in safe_name else (safe_name, "")
        safe_name = f"{stem}_{uuid.uuid4().hex[:6]}.{ext}" if ext else f"{safe_name}_{uuid.uuid4().hex[:6]}"
        dest = upload_dir / safe_name

    dest.write_bytes(contents)

    file_url = f"/api/media/{session_id}/uploads/{safe_name}"

    return UploadResponse(
        file_url=file_url,
        file_type=content_type,
        filename=safe_name,
    )


@router.post("/api/sessions/{session_id}/resume")
async def resume_session(session_id: str, body: ResumeRequest):
    """Resume the graph from an interrupt with user's action."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from langgraph.types import Command

    # Build resume payload
    resume_value = {"action": body.action}
    if body.payload:
        resume_value.update(body.payload)

    # Persist the user's action to chat history
    project_id = session.get("project_id")
    if project_id:
        ordinal = session.get("_ordinal", 0) + 1
        session["_ordinal"] = ordinal
        supabase_service.save_chat_event(
            project_id, session_id, "user_action",
            {"action": body.action, "payload": body.payload or {}},
            ordinal,
        )

    asyncio.create_task(_run_graph(session_id, Command(resume=resume_value)))

    return {"status": "accepted"}


@router.get("/api/sessions/{session_id}/events")
async def stream_events(request: Request, session_id: str):
    """SSE stream for real-time session events."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    queue = session["queue"]

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                try:
                    item = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield {"comment": "keepalive"}
                    continue

                if item is None:
                    break

                # Skip any non-dict items (safety check)
                if not isinstance(item, dict):
                    continue

                # Events from nodes have {event, data} structure
                event_type = item.get("event", "message")
                event_data = item.get("data", item)

                yield {
                    "event": event_type,
                    "data": json.dumps(event_data),
                }
        except asyncio.CancelledError:
            pass

    return EventSourceResponse(event_generator())


@router.get("/api/media/{session_id}/{filename:path}")
async def serve_media(session_id: str, filename: str):
    """Serve any media file (images, videos, audio, uploads) from a session workspace."""
    # Security: prevent path traversal
    if ".." in filename or ".." in session_id:
        raise HTTPException(status_code=400, detail="Invalid path")

    file_path = get_job_path(session_id, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type from extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "mp4": "video/mp4",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "srt": "text/plain",
        "gif": "image/gif",
        "mov": "video/quicktime",
        "webm": "video/webm",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(file_path, media_type=media_type)


# ── History Endpoints ─────────────────────────────────────────


@router.get("/api/projects")
async def list_projects():
    """List all projects (newest first)."""
    projects = supabase_service.list_projects()
    return {"projects": projects}


@router.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get a project with all its media items."""
    project = supabase_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its media (cascade)."""
    success = supabase_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found or delete failed")
    return {"status": "deleted"}


@router.delete("/api/media-items/{media_id}")
async def delete_media_item(media_id: str):
    """Delete a single media item."""
    success = supabase_service.delete_media(media_id)
    if not success:
        raise HTTPException(status_code=404, detail="Media item not found or delete failed")
    return {"status": "deleted"}


# ── Resume / Chat / Abandon ──────────────────────────────────


@router.post("/api/projects/{project_id}/resume")
async def resume_project(project_id: str):
    """Resume an in-progress project — recreate a session using the original session_id.

    The SqliteSaver checkpoint is keyed by thread_id (== session_id), so reusing
    the same session_id lets the graph pick up exactly where it left off.
    """
    project = supabase_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    status = project.get("status", "")
    if status != "in_progress":
        raise HTTPException(status_code=400, detail=f"Cannot resume project with status '{status}'")

    original_session_id = project.get("session_id")
    if not original_session_id:
        raise HTTPException(status_code=400, detail="Project has no linked session")

    # Check if session is already active
    existing = get_session(original_session_id)
    if existing:
        return {"session_id": original_session_id, "status": "already_active"}

    # Create a fresh session with the original session_id so SqliteSaver matches
    create_session(
        session_id=original_session_id,
        topic=project.get("topic", ""),
        project_id=project_id,
    )

    # Load ordinal from last chat event so new events continue the sequence
    chat_events = supabase_service.get_chat_history(project_id)
    last_ordinal = chat_events[-1]["ordinal"] if chat_events else 0
    session = get_session(original_session_id)
    if session:
        session["_ordinal"] = last_ordinal

    # Re-invoke the graph — SqliteSaver will find the checkpoint and resume
    # from the interrupt point. We send None input + empty Command to trigger
    # the interrupted state to re-emit the awaiting event.
    from langgraph.types import Command

    config = {"configurable": {"thread_id": original_session_id}}
    state = await graph.aget_state(config)

    if state.tasks:
        # Graph is interrupted — re-emit the awaiting event so frontend picks it up
        for task in state.tasks:
            if task.interrupts:
                interrupt_data = task.interrupts[0].value
                if session:
                    await session["queue"].put({
                        "event": "awaiting",
                        "data": interrupt_data,
                    })
                break

    return {"session_id": original_session_id, "status": "resumed"}


@router.get("/api/projects/{project_id}/chat")
async def get_project_chat(project_id: str):
    """Get all saved chat events for a project (for replaying history)."""
    events = supabase_service.get_chat_history(project_id)
    return {"events": events}


@router.post("/api/projects/{project_id}/abandon")
async def abandon_project(project_id: str):
    """Mark a project as abandoned and clean up chat history."""
    project = supabase_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    supabase_service.update_project(project_id, {"status": "abandoned"})
    supabase_service.delete_chat_history(project_id)

    return {"status": "abandoned"}
