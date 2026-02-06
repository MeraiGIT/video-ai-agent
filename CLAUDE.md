# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Content Maker — a conversational video creation agent. The user enters a topic and steps through a multi-stage pipeline: script writing, scene planning, image generation, video generation, voiceover, and final assembly. At each stage the user reviews output, can request modifications via chat, then approves to continue.

## Running the Project

### Backend (FastAPI + LangGraph)
```bash
cd backend
source .venv/bin/activate
python main.py              # Runs on http://0.0.0.0:8000
```

### Frontend (Next.js)
```bash
cd frontend
npm run dev                 # Runs on http://localhost:3000
npm run build               # Production build
npm run lint                # ESLint
```

### Environment
Copy `.env.example` to `.env` at the project root. Required keys: `ANTHROPIC_API_KEY`, `FAL_KEY`, `ELEVENLABS_API_KEY`. Config is loaded in `backend/config.py` via pydantic-settings.

## Architecture

### LangGraph Pipeline with Human-in-the-Loop

The backend uses a LangGraph `StateGraph` with `interrupt()` calls to pause for user review. The graph is compiled with `MemorySaver` checkpointer to persist state across interrupts.

**Graph flow** (defined in `backend/agent/graph.py`):
```
START → analyze_input → write_script → plan_scenes → generate_images
  → generate_videos → generate_voiceover → [conditional]
    → assemble_video → add_captions → END        (if concat_enabled)
    → finish_individual → END                     (if not concat_enabled)
```

Each review node (write_script, plan_scenes, generate_images, generate_videos, generate_voiceover) follows this pattern:
```python
def run(state):
    writer = get_stream_writer()
    result = generate_content(...)
    writer({"event": "artifact", "data": {...}})
    while True:
        response = interrupt({"stage": "...", "actions": [...]})
        if response["action"] == "approve":
            break
        result = modify_content(result, response["message"])
        writer({"event": "artifact", "data": {...}})
    return {updated state}
```

### Communication Pattern

- **SSE + REST**: Frontend connects to `GET /api/sessions/{id}/events` for server-sent events. User actions (approve/modify/regenerate) send `POST /api/sessions/{id}/resume` which resumes the graph via `Command(resume=...)`.
- **Event types**: `message` (chat bubbles), `artifact` (rich content cards), `progress` (loading bars), `awaiting` (enables input), `error`, `complete`.
- Nodes emit events via `get_stream_writer()` which pushes to an `asyncio.Queue` per session, consumed by the SSE endpoint.

### Backend API (4 endpoints in `backend/api/routes.py`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/sessions` | Create session, start graph |
| POST | `/api/sessions/{id}/resume` | Resume graph with user action |
| GET | `/api/sessions/{id}/events` | SSE event stream |
| GET | `/api/media/{id}/{filename}` | Serve generated media files |

### Frontend State Management

`useSession` hook (`frontend/src/hooks/useSession.ts`) is the central state manager. It holds `chatItems[]`, `currentProgress`, `awaiting`, `stage`, and exposes `start()`, `approve()`, `modify()`, `regenerate()`, `reset()`.

`ChatView` routes `ChatItem` objects to artifact renderers. Image/video artifacts are collected and rendered as grids only on the last artifact of that type to avoid duplicates.

### Services (all synchronous, run in LangGraph's thread pool)

| File | External API | Key functions |
|------|-------------|---------------|
| `claude_service.py` | Anthropic (claude-sonnet-4-5-20250929) | `generate_script()`, `plan_scenes_from_script()` |
| `fal_service.py` | fal.ai | `generate_image()` (Seedream 4.5), `generate_video()` (3 models) |
| `elevenlabs_service.py` | ElevenLabs | `generate_tts()` |
| `ffmpeg_service.py` | local FFmpeg | `concat_videos()`, `overlay_audio()`, `burn_subtitles()` |
| `whisper_service.py` | local faster-whisper | `transcribe_to_srt()` |

`modification.py` in `backend/agent/` provides Claude-powered content editing: `modify_script()`, `modify_scenes()`, `interpret_regeneration_request()`.

### Key Design Decisions

- **fal.ai image URLs are public CDN URLs** — pass directly to video generation without re-uploading.
- **Duration format varies by model**: Veo expects `"8s"` string, Seedance expects `int`, Kling expects `str(int)`.
- **FFmpeg `filter_complex` concat** is used instead of demuxer for cross-model codec compatibility.
- **faster-whisper** is used over openai-whisper (4x faster, same accuracy).
- **Generated files** live in `backend/workspace/{job_id}/` and are auto-cleaned after 2 hours.
- **Cache-busting**: `?t={timestamp}` is appended to media URLs when content is regenerated.

## State Shape

`VideoState` (`backend/agent/state.py`): `job_id`, `input_topic`, `video_model`, `concat_enabled`, `script`, `scenes` (list of `Scene` TypedDict with narration/visual_description/image_prompt/duration/image_url/video_local_path), `voiceover_path`, `assembled_video_path`, `final_video_path`, `status`, `error`, `progress_messages` (annotated with `operator.add`).
