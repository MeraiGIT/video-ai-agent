# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Production Studio — a universal AI content creation system that takes ANY creative request and produces professional output. The system acts as a full production team: interviewing the client, researching trends, planning creative direction with budget options, executing production with automated quality control, and delivering platform-optimized content.

**Not just video** — the system handles short videos, long-form films, graphic design, motion graphics, podcasts, and anything else the user requests. The LLM dynamically generates the production plan and blueprint based on available capabilities.

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
Copy `.env.example` to `.env` at the project root. Required keys: `ANTHROPIC_API_KEY`, `FAL_KEY`, `ELEVENLABS_API_KEY`, `GOOGLE_API_KEY`, `TAVILY_API_KEY`. Config is loaded in `backend/config.py` via pydantic-settings.

## Architecture

### 8-Phase Universal Pipeline (LangGraph StateGraph)

Every project flows through 8 phases. What changes between content types is what happens INSIDE each phase — driven by the LLM-generated creative brief and production plan.

```
INTAKE → RESEARCH → CREATIVE DIRECTION → BLUEPRINT → PRODUCE → ASSEMBLE → POLISH → DELIVER
```

**Graph nodes** (16 total, defined in `backend/agent/graph.py`):
- Phase 1: `intake` → `interview` (interrupt)
- Phase 2: `research` (conditional — only if needed)
- Phase 3: `creative_direction` → `review_direction` (interrupt)
- Phase 4: `blueprint` → `review_blueprint` (interrupt)
- Phase 5: `produce` → `quality_gate` → `review_stage` (interrupt at stage boundaries)
- Phase 6: `assemble` → `review_assembly` (interrupt)
- Phase 7: `polish` → `review_polish` (interrupt)
- Phase 8: `deliver` → `review_final` (interrupt)

### Core Principles (DO NOT VIOLATE)

1. **Nothing is hardcoded per content type.** The LLM dynamically generates the production plan, blueprint, and creative direction. No `if content_type == "video"` switches.
2. **Blueprint is freeform.** The LLM generates whatever structure is needed for the task. No fixed schema per content type.
3. **Dynamic capability execution.** The `production_plan` is a JSON list of capability steps. The produce node walks it and calls each capability function from the registry.
4. **Quality gate uses Gemini 2.5 Pro in vision mode.** It actually SEES images, WATCHES videos, LISTENS to audio. Not just metadata analysis.
5. **Stage-level user approval, not per-generation.** The quality gate runs autonomously. Users are only interrupted at stage boundaries or when the system needs permission to upgrade models.
6. **LangGraph interrupt() safety.** NEVER put API calls and interrupt() in the same node. The node re-executes entirely on resume. Always split into separate generate and review nodes.

### Hybrid Multi-Agent Pattern

- **Sequential**: Main 8-phase flow always in order
- **Supervisor**: Quality gate loop (generate → Gemini evaluate → Claude optimize → retry)
- **Parallel**: Batch asset generation (e.g., 5 images simultaneously)

### Communication Pattern

- **SSE + REST**: Frontend connects to `GET /api/sessions/{id}/events` for server-sent events. User actions send `POST /api/sessions/{id}/resume` which resumes the graph via `Command(resume=...)`.
- **Event types**: `message`, `artifact`, `progress`, `awaiting`, `pipeline_update`, `cost_update`, `quality_gate`, `error`, `complete`.
- Nodes emit events via `get_stream_writer()` which pushes to an `asyncio.Queue` per session.

### Capability Layer (`backend/agent/capabilities/`)

Each capability is a well-tested function that the production executor calls:
- **Generation**: `image_gen`, `video_gen`, `voiceover`, `voice_select`, `voice_clone`, `music_gen`, `sfx_gen`, `face_reference`, `first_last_frame`
- **Processing**: `audio_mix`, `video_concat`, `audio_overlay`, `caption_burn`, `text_overlay`, `image_composite`, `transcribe`
- **Analysis**: `analyze_image`, `analyze_video`, `analyze_reference`, `analyze_video_reference`, `check_consistency`, `web_search`

### Service Layer (`backend/services/`)

| File | External API | Key Functions |
|------|-------------|---------------|
| `claude_service.py` | Anthropic | LLM calls for planning, scripting, optimization |
| `gemini_service.py` | Google AI (gemini-2.5-pro) | Vision-mode quality evaluation |
| `fal_service.py` | fal.ai | Image gen (Seedream), Video gen (Seedance, Kling) |
| `kie_service.py` | Kie AI | Video gen (Veo 3.1, Kling) with async polling |
| `elevenlabs_service.py` | ElevenLabs | TTS, SFX, voice search/clone |
| `ffmpeg_service.py` | local FFmpeg | Concat, transitions, audio mix, captions, overlays |
| `whisper_service.py` | local faster-whisper | Audio transcription to SRT |
| `tavily_service.py` | Tavily | Web search for research phase |
| `nanana_service.py` | Nanana AI | Nano Banana Pro image generation |
| `video_router.py` | — | Routes to correct video provider based on model |
| `caption_styles.py` | — | 7 caption presets (tiktok, youtube, cinematic, etc.) |
| `model_registry.py` | — | Model knowledge cards (costs, strengths, prompting) |
| `supabase_service.py` | Supabase | Project history, media storage |

### Key Design Decisions

- **fal.ai image URLs are public CDN URLs** — pass directly to video generation without re-uploading.
- **Duration format varies by model**: Veo expects `"8s"` string, Seedance expects `int`, Kling expects `str(int)`.
- **FFmpeg `filter_complex` concat** is used instead of demuxer for cross-model codec compatibility.
- **faster-whisper** is used over openai-whisper (4x faster, same accuracy).
- **Generated files** live in `backend/workspace/{job_id}/` and are auto-cleaned after 2 hours.
- **Long-form content** (>5 min) is processed in 5-minute chunks with inter-chunk context passing.
- **Motion graphics** use Nano Banana first/last frame + video gen with first/last frame support.
- **Video recreation** uses Gemini vision to analyze uploaded video → feeds creative direction.

## State Shape

`ProductionState` (`backend/agent/state.py`): Universal state with ~40 fields covering all phases — identity, user input, intake, research, creative direction (brief + plan + budget variants), blueprint (freeform), production artifacts (images, videos, audio), quality tracking, post-production paths, cost tracking, and pipeline visualization.

## Planning Documents

| Document | Purpose |
|----------|---------|
| `SYSTEM_SPEC.md` | Comprehensive system specification (how everything works) |
| `BUILDING_PLAN.md` | File-by-file implementation plan (what to build, in what order) |
| `how_it_should_work.md` | User's original 120-line spec (reference) |
| `architecture.md` | Living architecture diagram (updated per phase) |
| `project_status.md` | Current phase tracking (updated per phase) |
| `changelog.md` | What changed per phase (updated per phase) |

## Development Workflow

**CRITICAL: Follow this workflow for every implementation phase. Do not skip steps.**

### Per-Phase Workflow

1. **Code**: Implement the phase's files per BUILDING_PLAN.md
   - Use Context7 MCP for up-to-date library docs
   - Use any tools needed to produce best possible code
   - Reference v2 codebase at `../video-ai-agent-v2/` for reusable patterns

2. **Test**: Run real tests that stress edge cases
   - Test happy path AND failure scenarios
   - Test with various input types (if applicable to the phase)
   - Verify SSE events emit correctly
   - Verify state updates correctly

3. **Iterate**: Fix issues found in testing
   - Do not move on until the phase works correctly
   - Fix edge cases, error handling, graceful degradation

4. **Update Docs**: After phase is complete and tested:
   - Update `architecture.md` with any architectural changes
   - Update `project_status.md` with phase status, files changed, test results
   - Update `changelog.md` with what was added/changed/fixed/tested
   - Update this `CLAUDE.md` if the architecture section needs changes

5. **Git Commit + Push**: After docs are updated:
   - Stage all changed files for the phase
   - Commit with descriptive message: `"Phase N: [Phase Name] — [brief summary]"`
   - Push to remote

6. **Next Phase**: Only after commit + push, move to next phase
