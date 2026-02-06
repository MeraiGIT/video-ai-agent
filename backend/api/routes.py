import os
import uuid
import json
import asyncio
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from api.schemas import CreateSessionRequest, CreateSessionResponse, ResumeRequest
from agent.graph import graph
from agent.state import VideoState
from agent.session_store import create_session, get_session
from utils.file_manager import get_job_path

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_graph(session_id: str, input_or_command):
    """Run or resume the LangGraph pipeline, pushing custom events to the session queue."""
    session = get_session(session_id)
    if not session:
        return

    queue = session["queue"]
    config = {"configurable": {"thread_id": session_id}}

    try:
        async for chunk in graph.astream(
            input_or_command,
            config=config,
            stream_mode="custom",
        ):
            if isinstance(chunk, dict) and "event" in chunk:
                await queue.put(chunk)

        # Check if graph is interrupted (waiting for user input)
        state = await graph.aget_state(config)
        if state.tasks:
            for task in state.tasks:
                if task.interrupts:
                    interrupt_data = task.interrupts[0].value
                    await queue.put({
                        "event": "awaiting",
                        "data": interrupt_data,
                    })
                    return

        # Graph completed without interrupt
        # (complete event already emitted by add_captions or finish_individual node)

    except Exception as e:
        logger.exception(f"Graph error for session {session_id}")
        await queue.put({
            "event": "error",
            "data": {"message": str(e)},
        })


@router.post("/api/sessions", response_model=CreateSessionResponse)
async def create_new_session(body: CreateSessionRequest):
    """Create a new session and start the generation pipeline."""
    session_id = str(uuid.uuid4())

    create_session(
        session_id=session_id,
        topic=body.topic,
        video_model=body.video_model,
        concat_enabled=body.concat_enabled,
    )

    # Build initial state and start graph
    initial_state: VideoState = {
        "job_id": session_id,
        "input_topic": body.topic,
        "video_model": body.video_model,
        "concat_enabled": body.concat_enabled,
        "progress_messages": [],
    }

    asyncio.create_task(_run_graph(session_id, initial_state))

    return CreateSessionResponse(session_id=session_id)


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


@router.get("/api/media/{session_id}/{filename}")
async def serve_media(session_id: str, filename: str):
    """Serve any media file (images, videos, audio) from a session workspace."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or ".." in session_id:
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
        "mp4": "video/mp4",
        "mp3": "audio/mpeg",
        "srt": "text/plain",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(file_path, media_type=media_type)
