# Changelog — AI Production Studio

> Updated after each implementation phase with what was built, changed, and tested.

---

## [Unreleased] — Planning Phase

### Added
- `SYSTEM_SPEC.md` — Comprehensive system specification (1,005 lines, 16 sections)
  - 8-phase universal pipeline architecture
  - Universal ProductionState with ~40 fields
  - Capability registry (22 capabilities across generation, processing, analysis)
  - Model knowledge cards (Seedream 4.5, Veo 3.1, Seedance 1.5, Kling 3.0, Kling O1 Ref, Nano Banana Pro)
  - Quality gate protocol with Gemini 2.5 Pro vision-mode evaluation
  - Budget variant system (3 tiers with itemized costs)
  - Long-form chunking strategy (5-min segments)
  - Supabase schema for project history
  - Frontend design with pipeline sidebar
  - 9-phase implementation plan
- `BUILDING_PLAN.md` — File-by-file implementation plan (1,013 lines)
  - 77 files mapped: 38 new, 4 rewrite, 15 modify, 4 copy from v2, 16 keep
  - Dependency graph showing build order
  - Phase-by-phase with exact files, functions, and source references
- `architecture.md` — Living architecture document
- `project_status.md` — Phase tracking and status
- `changelog.md` — This file

### Changed
- `SYSTEM_SPEC.md` Section 6: Removed hardcoded blueprint schemas (Video Blueprint, Graphic Design Blueprint). Blueprint is now LLM-generated and freeform — the LLM decides what structure to generate based on the task and available capabilities.
- `SYSTEM_SPEC.md` Section 8: Added explicit Gemini vision/multimodal mode description — Gemini SEES images, WATCHES videos, LISTENS to audio for quality evaluation.
- `SYSTEM_SPEC.md` Section 7: Added `analyze_video_reference` capability (Gemini vision to understand existing videos for recreation) and `first_last_frame` capability (Nano Banana for motion graphics keyframes).
- `SYSTEM_SPEC.md` Section 15: Resolved all open questions — direct service calls, Gemini 2.5 Pro model, Next.js + Tailwind confirmed, model research session planned.

### Decisions Made
- Architecture: v1 pipeline reliability + v2 capabilities (not v2's ReAct agent)
- Blueprint: Freeform LLM-generated, NOT hardcoded per content type
- Gemini model: `gemini-2.5-pro` for quality evaluation (state-of-the-art multimodal)
- Frontend: Next.js + Tailwind (keep existing)
- Service calls: Direct (not MCP)
- Building in existing v1 codebase (not new directory)
- No re-entry for now (once approved, no going back)
- Model research session planned after skeleton is built

---

## [Phase 1] — Intake + Interview — 2026-02-09

### Added
- `backend/agent/prompts/intake.py` — Intake classification prompt (injects capability registry, returns structured JSON with content_type, platform, audience, constraints)
- `backend/agent/prompts/interview.py` — Smart follow-up questions prompt (production team interview pattern, 2-4 questions prioritized by impact)
- `backend/agent/nodes/intake.py` — REWRITTEN: Classifies any creative request via Claude, analyzes uploads with Gemini vision, extracts structured project details
- `backend/agent/nodes/interview.py` — REWRITTEN: Generates follow-up questions, handles interrupt(), decides research_needed

### Changed
- `backend/api/schemas.py` — Made video_model and concat_enabled optional (agent chooses now)
- `backend/api/routes.py` — Uses ProductionState with user_request instead of VideoState with input_topic
- `frontend/src/lib/types.ts` — REWRITTEN: Removed VideoModel/VIDEO_MODELS, added PipelineStage, BudgetVariant, CreativeBrief, new artifact types
- `frontend/src/lib/api.ts` — Simplified createSession (no model/concat params)
- `frontend/src/hooks/useSession.ts` — Removed VideoModel dependency, simplified start() signature
- `frontend/src/components/TopicForm.tsx` — Removed model selector and concat toggle, universal creative brief input with richer placeholder, audio file support

### Tested
- Backend: Graph compiles (17 nodes), intake prompt builds (4026 chars with capabilities), interview prompt builds (1436 chars)
- Frontend: `npm run build` passes with zero errors
- API schemas accept requests without video_model/concat_enabled

---

## [Phase 0] — Foundation — 2026-02-09

### Added
- `backend/agent/state.py` — REWRITTEN: Universal `ProductionState` TypedDict with 45 fields + 7 supporting types (UploadedFile, Scene, ImageAsset, VideoAsset, QualityResult, BudgetVariant, PipelineStage)
- `backend/agent/graph.py` — REWRITTEN: 16-node StateGraph with 8 conditional routing functions, MemorySaver checkpointer
- `backend/agent/capabilities/__init__.py` — NEW empty init
- `backend/agent/capabilities/registry.py` — NEW: 20 capabilities across 3 categories (generation, processing, analysis) + 8 model cards + lazy loading via importlib
- `backend/agent/capabilities/prompt_engineering.py` — NEW (from v2): Model-specific prompt formatting for 7 models, cinematography vocabulary, negative prompts
- `backend/agent/prompts/__init__.py` — NEW empty init
- 16 stub node files in `backend/agent/nodes/`: intake, interview, research, creative_direction, review_direction, blueprint, review_blueprint, produce, quality_gate, review_stage, assemble, review_assembly, polish, review_polish, deliver, review_final
- `backend/services/gemini_service.py` — NEW: Gemini 2.5 Pro vision analysis (image, video, audio) + text gen
- `backend/services/tavily_service.py` — NEW: Tavily web search (single + multi-query)
- `backend/services/nanana_service.py` — NEW: Nano Banana Pro image generation via REST API

### Changed
- `backend/config.py` — Added GOOGLE_API_KEY, TAVILY_API_KEY, NANANA_API_KEY
- `backend/main.py` — Updated title to "AI Production Studio", added service availability logging
- `backend/services/model_registry.py` — Added Nano Banana Pro image model, strengths/weaknesses/best_for to all models, first-last-frame to Veo
- `backend/services/ffmpeg_service.py` — COPIED from v2: full video assembly with transitions, audio mix, text overlay (518 lines)
- `backend/services/whisper_service.py` — COPIED from v2: word-level SRT transcription
- `backend/services/caption_styles.py` — COPIED from v2: 7 caption style presets + word-by-word SRT builder
- `backend/agent/nodes/__init__.py` — REWRITTEN: imports for 16 new production studio nodes (removed v1 legacy imports)

### Tested
- Graph compiles: 17 nodes (16 + START), all conditional edges resolve
- All 16 node modules import with callable `run()` functions
- Capability registry: 20 capabilities, 8 model cards
- Prompt engineering: format_for_image_model() and format_for_video_model() work correctly
- Model registry: 4 video models + 3 image models with full metadata
- ProductionState: 45 fields, all NotRequired except job_id and progress_messages

---

<!-- Template for future phases:

## [Phase N] — Phase Name — YYYY-MM-DD

### Added
- New files created
- New capabilities
- New frontend components

### Changed
- Modified files and what changed
- Refactored components

### Fixed
- Bugs found during testing

### Tested
- Test scenarios run
- Edge cases covered
- Results

### Metrics
- Lines of code added/modified
- API calls cost for testing
- Generation time benchmarks
-->
