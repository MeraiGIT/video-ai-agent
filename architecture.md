# Architecture — AI Production Studio

> This is a living document. Updated after each implementation phase.

**Last updated**: Phase 0 complete
**Current state**: Foundation built — 16-node graph skeleton, universal state, capability registry, all services

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Browser)                               │
│  Next.js + Tailwind frontend with pipeline sidebar + chat interface  │
└──────────┬──────────────────────────────────────────┬───────────────┘
           │ POST /api/sessions                        │ GET /events (SSE)
           │ POST /api/sessions/{id}/resume            │
           ▼                                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐  │
│  │  API Routes  │  │ Session Store │  │  asyncio.Queue (per session)│ │
│  └──────┬──────┘  └──────────────┘  └────────────────────────────┘  │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │              LangGraph StateGraph (8 phases)                     │ │
│  │                                                                  │ │
│  │  INTAKE → RESEARCH → CREATIVE DIRECTION → BLUEPRINT              │ │
│  │    → PRODUCE (capability executor + quality gate loop)           │ │
│  │    → ASSEMBLE → POLISH → DELIVER                                │ │
│  │                                                                  │ │
│  │  Each phase: generate node + review node (interrupt)             │ │
│  └──────┬──────────────────────────────────────────────────────────┘ │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │              Capability Layer                                    │ │
│  │  registry.py — maps capability IDs to functions                  │ │
│  │  prompt_engineering.py — model-specific prompt formatting        │ │
│  │  20+ capability functions (image_gen, video_gen, voiceover...)   │ │
│  └──────┬──────────────────────────────────────────────────────────┘ │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │              Service Layer (external API wrappers)               │ │
│  │  claude_service  │ gemini_service  │ fal_service │ kie_service   │ │
│  │  elevenlabs_svc  │ ffmpeg_service  │ whisper_svc │ tavily_svc    │ │
│  │  nanana_service  │ supabase_svc    │ video_router│ caption_styles│ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌────────────┐     ┌──────────────┐     ┌──────────────┐
    │  Anthropic  │     │   Google AI   │     │   fal.ai     │
    │  (Claude)   │     │ (Gemini Pro)  │     │   Kie AI     │
    └────────────┘     └──────────────┘     │   ElevenLabs │
                                            │   Nanana AI  │
                                            │   Tavily     │
                                            └──────────────┘
```

---

## Graph Structure (Target)

```
START
  ↓
intake ──→ interview ──→ [research_needed?]
                              │ yes → research ──→ creative_direction
                              │ no  ──────────────→ creative_direction
                                                        ↓
                                                  review_direction ←──┐
                                                        │ approve     │ modify
                                                        ↓             │
                                                    blueprint ────────┘
                                                        ↓
                                                  review_blueprint ←──┐
                                                        │ approve     │ modify
                                                        ↓             │
                                                    produce ──────────┘
                                                        ↓
                                                  quality_gate ←──┐
                                                    │ pass        │ fail (retry)
                                                    ↓             │
                                                  review_stage ───┘
                                                    │ approve (all stages done?)
                                                    ↓ yes
                                                  assemble
                                                    ↓
                                                  review_assembly
                                                    ↓ approve
                                                  polish
                                                    ↓
                                                  review_polish
                                                    ↓ approve
                                                  deliver
                                                    ↓
                                                  review_final
                                                    ↓
                                                   END
```

---

## Key Patterns

### Dynamic Capability Execution
The LLM generates a `production_plan` (JSON list of capability steps). The produce node walks this list and calls each capability function from the registry. The LLM decides what to use and in what order; the executor runs it reliably.

### Quality Gate (Supervisor Loop)
```
Generate → Gemini 2.5 Pro SEES output (vision mode) → Score 1-10
  → Pass (≥7): next asset
  → Fail (<7, retry<3): Claude optimizes prompt → regenerate
  → Fail (retry≥3): propose model upgrade to user
  → Fail (expensive model 2x): escalate to user
```

### Hybrid Multi-Agent
- **Sequential**: Main 8-phase flow always in order
- **Supervisor**: Quality gate loop (generate → evaluate → optimize → retry)
- **Parallel**: Batch asset generation (e.g., 5 images simultaneously)

### SSE Communication
- POST `/api/sessions` → create session, start graph
- GET `/api/sessions/{id}/events` → SSE stream (messages, artifacts, progress, pipeline updates)
- POST `/api/sessions/{id}/resume` → resume after interrupt

---

## Data Flow

```
User Request
  ↓
ProductionState (universal state object, ~40 fields)
  ↓ populated incrementally by each phase
  ├── content_type, platform, audience, constraints
  ├── research_insights
  ├── creative_brief, production_plan, budget_variants
  ├── blueprint (freeform, LLM-generated)
  ├── images[], videos[], voiceover, music, sfx
  ├── assembled_path, polished_path, final_output_path
  └── cost_breakdown, pipeline_stages (for UI)
```

---

## File Structure (Current → Target)

See `BUILDING_PLAN.md` for the complete target file structure with action per file (NEW/MODIFY/KEEP/COPY/REWRITE).

---

## External Dependencies

| Service | Purpose | Model/Endpoint | Auth |
|---------|---------|---------------|------|
| Anthropic | LLM calls (planning, scripting, optimization) | claude-sonnet-4-5-20250929 | ANTHROPIC_API_KEY |
| Google AI | Quality evaluation (vision mode) | gemini-2.5-pro | GOOGLE_API_KEY |
| fal.ai | Image gen (Seedream), Video gen (Seedance, Kling) | Various endpoints | FAL_KEY |
| Kie AI | Video gen (Veo 3.1, Kling) | REST + polling | KIE_AI_API_KEY |
| ElevenLabs | TTS, SFX, voice search/clone | Multilingual v2 | ELEVENLABS_API_KEY |
| Nanana AI | Image gen (Nano Banana Pro) for motion graphics | MCP tool | NANANA_API_KEY |
| Tavily | Web search for research phase | Search API | TAVILY_API_KEY |
| Supabase | Project history, media storage | PostgreSQL + Storage | SUPABASE_URL + KEY |
| FFmpeg | Video concat, audio mix, captions, overlays | Local binary | N/A |
| faster-whisper | Audio transcription to SRT | Local model | N/A |
