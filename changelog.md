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

## [Post-Phase 9] — Production Readiness Fixes — 2026-02-09

### Fixed
- **CRITICAL**: Budget selection flow was broken — BudgetSelector sends `action: "modify"` with `message: "approve:tier"`, but `review_direction.py` only checked `action == "approve"`. Added message parsing to detect "approve:" prefix, extract tier name, and reroute to approval flow. Without this fix, budget selection would loop forever.
- `review_direction.py` — Now checks multiple field names for tier selection (`selected_tier`, `selected_variant`, `tier`) for frontend flexibility

### Added
- `backend/supabase_schema.sql` — Complete Supabase schema DDL for the AI Production Studio (projects table with JSONB columns for creative_brief/production_plan/blueprint/pipeline_stages/cost_breakdown, media table with stage/model_used/cost tracking, indexes)
- `.env.example` — Added GOOGLE_API_KEY, TAVILY_API_KEY, NANANA_API_KEY with descriptions

### Technical Details
- Budget selection fix: `review_direction.py` lines 41-47 parse `message.startswith("approve:")` to extract tier from modify-path budget selections
- Supabase schema: `CREATE TABLE IF NOT EXISTS` for both tables, indexes on project_id/status/created_at, ON DELETE CASCADE for media→projects

### Tested
- Backend: Graph compiles (17 nodes)
- Frontend: `npm run build` passes with zero errors

---

## [Phase 9] — Testing + Polish — 2026-02-09

### Changed
- `backend/agent/nodes/produce.py` — Added budget enforcement (halt production at 1.5x budget limit), budget warning at 80% threshold, timeout protection for single and batch capability executions (5-minute timeout via ThreadPoolExecutor), timeout-specific error handling in batch operations
- `backend/api/routes.py` — User-friendly error messages in graph runner (sanitizes API key errors, rate limit messages, timeout messages, truncates long errors)
- `backend/utils/file_manager.py` — Added `cleanup_old_workspaces()` function for removing workspace dirs older than 2 hours, centralized from main.py
- `backend/main.py` — Refactored cleanup task to use centralized `cleanup_old_workspaces()`, removed unused `time` import

### Technical Details
- Budget safety: `BUDGET_SAFETY_FACTOR = 1.5` — production halts and jumps to assembly if cost exceeds 150% of budget
- Budget warning: emits assistant message at 80% budget consumption
- Timeout: `CAPABILITY_TIMEOUT = 300` seconds (5 min) — protects against hung video generation APIs
- Batch timeout: each item in a batch has its own timeout, failed items don't block others
- Error sanitization: API key/auth errors → generic message, rate limits → user-friendly message, all errors truncated to 200 chars
- Workspace cleanup: periodic (every 10 min), removes dirs with mtime > 2 hours

### Tested
- Backend: Graph compiles (17 nodes), produce node budget/timeout logic correct
- Frontend: `npm run build` passes with zero errors
- Error handling reviewed across all 16 nodes — all have graceful fallbacks

---

## [Phase 8] — API Routes + Session Management — 2026-02-09

### Changed
- `backend/agent/session_store.py` — Simplified `create_session()` to remove legacy `video_model`/`concat_enabled` params; now only takes session_id + topic
- `backend/api/schemas.py` — Expanded `ResumeRequest.action` to include `"answer"` (interview) and `"select_budget"` in addition to approve/modify/regenerate
- `backend/api/routes.py` — Updated `create_new_session()` to match simplified session_store, added audio MIME types to upload whitelist (mpeg, wav, mp4, ogg, webm), added wav/ogg/webm to media type mapping
- `frontend/src/lib/types.ts` — Added `"metadata"` and `"chunk_progress"` to ChatArtifact type union
- `frontend/src/hooks/useSession.ts` — Added `quality_gate` SSE event handler (renders as quality_report artifact), added `selectBudget()` action, exported from hook
- `frontend/src/components/chat/ChatView.tsx` — Added artifact renderers for `quality_report` (score bar with pass/fail), `metadata` (title/description/hashtags), `chunk_progress` (chapter progress indicator); imported ChunkProgress component

### Technical Details
- Backend session store simplified: LangGraph MemorySaver handles all state; session_store only tracks asyncio.Queue + topic
- ResumeRequest now accepts 5 action types covering all interrupt stages
- Audio uploads now supported (for voice reference, podcast input, etc.)
- Quality gate SSE events (`quality_gate`) are rendered inline as visual score bars
- Metadata artifact shows delivery info (title, description, hashtags) in a clean card
- Chunk progress delegates to existing ChunkProgress component

### Tested
- Backend: Graph compiles (17 nodes), session_store simplified, routes match
- Frontend: `npm run build` passes with zero errors (fixed TypeScript narrowing on metadata.title)

---

## [Phase 7] — History + Persistence — 2026-02-09

### Changed
- `backend/services/supabase_service.py` — Enhanced `create_project()` with `content_type` parameter, added `save_project_state()` for auto-saving at phase boundaries (saves creative_brief, production_plan, blueprint, pipeline_stages, cost_breakdown, status as JSONB), enhanced `create_media_record()` with stage/model_used/cost tracking
- `backend/agent/nodes/review_direction.py` — Auto-save to Supabase after creative direction approval
- `backend/agent/nodes/review_blueprint.py` — Auto-save to Supabase after blueprint approval
- `backend/agent/nodes/review_final.py` — Auto-save marking project as completed on final approval
- `frontend/src/lib/api.ts` — Project interface updated with optional content_type, total_cost, video_model, concat_enabled fields
- `frontend/src/components/history/ProjectCard.tsx` — Shows content_type badge and total cost instead of video model
- `frontend/src/app/history/page.tsx` — Updated text from "video creations" to "projects" for universal content

### Technical Details
- Phase boundary auto-save: review_direction, review_blueprint, review_final all call `save_project_state()` on approval
- Supabase JSONB columns used for complex state (creative_brief, production_plan, blueprint, pipeline_stages, cost_breakdown)
- Media records now track stage, model_used, and cost for per-asset analytics
- Frontend history is now content-type agnostic (shows any project, not just videos)

### Tested
- Backend: Graph compiles (17 nodes), all review nodes import with auto-save
- Frontend: `npm run build` passes with zero errors
- Project interface backwards compatible (new fields are optional)

---

## [Phase 6] — Long-Form Chunking — 2026-02-09

### Added
- `frontend/src/components/artifacts/ChunkProgress.tsx` — NEW: Chapter progress indicator with dot visualization, animated current chapter, indigo styling

### Changed
- `backend/agent/prompts/blueprint.py` — Added long-form chunking guidelines: for content >5 min, blueprint must include `chapters` array with ~5-min segments, continuity notes between chapters
- `backend/agent/nodes/blueprint.py` — Detects chapters in generated blueprint, sets `total_chunks` and `current_chunk` in state
- `backend/agent/nodes/produce.py` — Chunk-aware execution: `_get_chunk_blueprint()` extracts current chapter's scenes/audio from blueprint, resets stage index between chunks, processes one chapter at a time
- `backend/agent/nodes/review_stage.py` — Shows chapter progress (e.g., "Chapter 2 of 5") and remaining chapters count when processing long-form content

### Technical Details
- Long-form threshold: estimated duration > 5 minutes
- Chapter size: ~5 minutes each
- Inter-chunk context: continuity_notes, style_guide, and character_sheets carry across chapters
- Chunk flow: produce all steps for chapter N → review_stage → approve → reset stage_index → advance current_chunk → produce chapter N+1

### Tested
- Backend: Graph compiles (17 nodes), `_get_chunk_blueprint` helper works, all modified nodes import
- Frontend: `npm run build` passes with zero errors, ChunkProgress component imports

---

## [Phase 5] — Frontend Pipeline Sidebar — 2026-02-09

### Added
- `frontend/src/components/pipeline/PipelineSidebar.tsx` — NEW (~90 lines): Vertical phase list with overall progress bar, default 8 stages, click-to-scroll on completed stages, cost tracker at bottom
- `frontend/src/components/pipeline/StageCard.tsx` — NEW (~90 lines): Individual phase card with status icons (pending/active/completed/failed), substep progress dots, cost badge, asset count
- `frontend/src/components/pipeline/CostTracker.tsx` — NEW (~60 lines): Running cost vs budget visualization, color-coded bar (green→amber→red), warning messages at 80% and 100%

### Changed
- `frontend/src/lib/types.ts` — Added `CostTracking` interface with totalCost, budgetLimit, breakdown
- `frontend/src/hooks/useSession.ts` — Added `pipelineStages` and `costTracking` state, `pipeline_update` and `cost_update` SSE event handlers, state reset on start/reset
- `frontend/src/app/page.tsx` — Flexbox layout with PipelineSidebar on left, chat area on right; sidebar hidden on topic form; renamed "New Video" → "New Project"

### Tested
- Frontend: `npm run build` passes with zero errors
- All 3 new pipeline components import and render
- SSE event handlers for pipeline_update and cost_update wired up

---

## [Phase 4] — Assembly + Polish + Deliver — 2026-02-09

### Added
- `backend/agent/nodes/assemble.py` — REWRITTEN (~176 lines): Content-type-aware assembly (video concat+audio overlay, graphic pass-through, audio mix), fallback path handling
- `backend/agent/nodes/review_assembly.py` — REWRITTEN: interrupt() for assembled output approval with approve/modify actions
- `backend/agent/nodes/polish.py` — REWRITTEN (~320 lines): Video polish pipeline (caption burn via whisper+FFmpeg, text overlays from blueprint, audio normalization to platform LUFS standards, thumbnail extraction), audio normalization for podcasts, graceful fallback on each step
- `backend/agent/nodes/review_polish.py` — REWRITTEN: interrupt() for polished output approval with approve/modify actions
- `backend/agent/nodes/deliver.py` — REWRITTEN (~213 lines): Claude-generated metadata (title, description, hashtags, SEO tags), cost summary, final artifact emission, platform-optimized delivery message
- `backend/agent/nodes/review_final.py` — REWRITTEN: Final interrupt() for delivery approval, emits complete event

### Technical Details
- Platform loudness standards: TikTok/YouTube/Instagram at -14 LUFS, LinkedIn/Podcast at -16 LUFS
- Default caption styles per platform: TikTok→tiktok, YouTube→youtube, Instagram→bold, LinkedIn→minimal
- Caption pipeline: extract_audio → transcribe_to_word_srt → burn_subtitles (each step independently recoverable)
- Thumbnail: FFmpeg frame extraction at video midpoint
- Metadata: Claude Sonnet 4.5 generates platform-optimized title/description/hashtags with fallback defaults

### Tested
- Backend: All 6 Phase 4 nodes import with callable run() functions
- Graph compiles (17 nodes), all conditional routing functions resolve
- Frontend: `npm run build` passes with zero errors

---

## [Phase 3] — Blueprint + Production Executor — 2026-02-09

### Added
- `backend/agent/prompts/blueprint.py` — Blueprint generation prompt: transforms creative direction into detailed execution specs with model-specific prompting
- `backend/agent/prompts/quality_gate.py` — Two prompts: Gemini vision evaluation criteria (image/video/audio) + Claude prompt optimization
- `backend/agent/nodes/blueprint.py` — Blueprint node: Claude generates freeform execution blueprint from creative brief + production plan
- `backend/agent/nodes/review_blueprint.py` — Blueprint review: interrupt() for user approval, initializes production state
- `backend/agent/nodes/produce.py` — Core production executor (~340 lines): walks production plan, calls capabilities via registry, batch parallel execution (ThreadPoolExecutor), stores results in state, tracks costs, emits SSE artifacts
- `backend/agent/nodes/quality_gate.py` — Quality gate (~300 lines): Gemini vision scores assets 1-10, auto-retry with Claude-optimized prompts up to 3x, escalation on max retries
- `backend/agent/nodes/review_stage.py` — Stage review: interrupt() at stage boundaries, shows production summary with quality scores and costs
- 20 capability functions in `backend/agent/capabilities/`:
  - **Generation**: image_gen, video_gen, voiceover, voice_select, music_gen, sfx_gen, face_reference, first_last_frame
  - **Processing**: audio_mix, video_concat, audio_overlay, caption_burn, text_overlay, image_composite, transcribe
  - **Analysis**: analyze_image, analyze_video, analyze_audio, analyze_video_reference, web_search
- `frontend/src/components/artifacts/BlueprintViewer.tsx` — Dynamic blueprint renderer: specialized UI for scenes, audio map, style guide; collapsible JSON for unknown sections

### Changed
- `frontend/src/components/chat/ChatView.tsx` — Added blueprint artifact rendering

### Tested
- Backend: Graph compiles (17 nodes), all 20 capabilities import with execute() functions
- Registry lazy loading works (get_capability_function → importlib)
- Frontend: `npm run build` passes with zero errors
- Blueprint prompt builds correctly with model context injection
- Quality gate prompts generate evaluation criteria for image/video/audio types

---

## [Phase 2] — Research + Creative Direction — 2026-02-09

### Added
- `backend/agent/prompts/research.py` — Research prompts: query generation (2-4 targeted search queries) + synthesis (trends, recommendations, audience insights)
- `backend/agent/prompts/creative_direction.py` — "Brain" prompt (~150 lines): injects model knowledge + capabilities, generates creative brief + production plan + 3 budget variants with 11 critical rules
- `backend/agent/prompts/model_knowledge.py` — Injectable model/capability context: formatted model cards with costs/strengths/weaknesses, capability list with production plan format, model selection guidance
- `frontend/src/components/artifacts/CreativeBriefCard.tsx` — Expandable card showing concept, visual style, tone, pacing, audio direction, color palette, key messages, references (purple gradient styling)
- `frontend/src/components/artifacts/BudgetSelector.tsx` — 3-column budget tier selector (green/blue/amber), expandable cost breakdowns, confirm button

### Changed
- `backend/agent/nodes/research.py` — REWRITTEN: 3-step process (Claude generates queries → Tavily multi-search → Claude synthesizes findings), graceful fallback on search failure
- `backend/agent/nodes/creative_direction.py` — REWRITTEN: Single Claude call with brain prompt (max_tokens=4096), parses creative_brief + production_plan + budget_variants, emits SSE artifacts
- `backend/agent/nodes/review_direction.py` — REWRITTEN: interrupt() for budget tier approval, applies selected variant's model_selections to production plan, sets budget_limit (1.2x estimate)
- `frontend/src/components/chat/ChatView.tsx` — Added creative_brief and budget_variants artifact rendering cases

### Fixed
- `model_knowledge.py` — Removed reference to non-existent `capabilities` field in MODEL_CARDS (uses strengths/weaknesses/best_for instead)

### Tested
- Backend: Graph compiles (17 nodes), all Phase 2 node imports pass, model context generates correctly
- Frontend: `npm run build` passes with zero errors
- Prompt injection: `get_full_context()` produces formatted model cards + capability list for brain prompt

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
