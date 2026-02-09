# AI Production Studio - Detailed Building Plan

This is the file-by-file, step-by-step building plan for transforming the current v1 codebase (at `/Users/yosifmerman/Desktop/video-ai-agent/`) into the universal AI Production Studio described in SYSTEM_SPEC.md.

**We are building IN the existing v1 codebase.** Not a new directory. We modify/replace/add files within the current project structure. v2 code (at `../video-ai-agent-v2/`) is referenced for copying patterns and files, but all work happens here.

**Key principles this plan follows:**
- Nothing is hardcoded per content type — the LLM dynamically generates everything
- The capability registry defines what the system CAN do
- The LLM chooses WHAT to do and in WHAT order via the production plan
- The blueprint is freeform creative context, NOT a fixed schema — the LLM decides what structure to generate based on the task and available capabilities
- Gemini uses vision/multimodal mode to actually SEE images, WATCH videos, and LISTEN to audio for quality evaluation
- Quality gate runs autonomously; user is only interrupted at stage boundaries or for model upgrades
- The agent can recreate content from reference videos (Gemini vision analyzes the video) and create motion graphics (Nano Banana first/last frame + video gen)
- For long-form content (>5 min), the pipeline processes in 5-minute chunks with inter-chunk context passing

---

## Target File Structure

```
backend/
├── config.py                          # MODIFY (v1) — add new API keys
├── main.py                            # MODIFY (v1) — add Gemini init, Tavily init
├── agent/
│   ├── __init__.py
│   ├── state.py                       # REWRITE — universal ProductionState
│   ├── graph.py                       # REWRITE — 8-phase graph with conditional edges
│   ├── session_store.py               # MODIFY (v1) — add project_id tracking
│   ├── prompts/                       # NEW DIRECTORY — all LLM prompt templates
│   │   ├── __init__.py
│   │   ├── intake.py                  # NEW — intake classification prompt
│   │   ├── interview.py              # NEW — smart follow-up questions
│   │   ├── research.py               # NEW — research analysis prompt
│   │   ├── creative_direction.py     # NEW — creative brief + plan + budget
│   │   ├── blueprint.py              # NEW — dynamic blueprint generation
│   │   ├── quality_gate.py           # NEW — Gemini evaluation + Claude optimization
│   │   └── model_knowledge.py        # NEW — model cards as injectable context
│   ├── nodes/                         # REWRITE — 16 nodes for 8 phases
│   │   ├── __init__.py
│   │   ├── intake.py                  # NEW — parse + classify request
│   │   ├── interview.py              # NEW — smart follow-up (interrupt)
│   │   ├── research.py               # NEW — web search + trend analysis
│   │   ├── creative_direction.py     # NEW — brief + plan + budget variants
│   │   ├── review_direction.py       # NEW — user reviews direction (interrupt)
│   │   ├── blueprint.py              # NEW — LLM generates dynamic blueprint
│   │   ├── review_blueprint.py       # NEW — user reviews blueprint (interrupt)
│   │   ├── produce.py                # NEW — dynamic capability executor
│   │   ├── quality_gate.py           # NEW — Gemini vision evaluate + Claude optimize
│   │   ├── review_stage.py           # NEW — user reviews stage output (interrupt)
│   │   ├── assemble.py               # NEW — combine assets per blueprint
│   │   ├── review_assembly.py        # NEW — user reviews assembly (interrupt)
│   │   ├── polish.py                 # NEW — captions, audio norm, overlays
│   │   ├── review_polish.py          # NEW — user reviews polish (interrupt)
│   │   ├── deliver.py                # NEW — platform export + metadata
│   │   └── review_final.py           # NEW — final user review (interrupt)
│   └── capabilities/                  # NEW DIRECTORY — capability functions
│       ├── __init__.py
│       ├── registry.py                # NEW — capability registry + model cards
│       ├── image_gen.py               # NEW — wraps fal_service
│       ├── video_gen.py               # NEW — wraps video_router
│       ├── voiceover.py               # NEW — wraps elevenlabs_service
│       ├── voice_select.py            # NEW — voice search/clone
│       ├── music_gen.py               # NEW — music generation
│       ├── sfx_gen.py                 # NEW — SFX generation
│       ├── face_reference.py          # NEW — Gemini face analysis
│       ├── audio_mix.py               # NEW — wraps ffmpeg audio mix
│       ├── video_concat.py            # NEW — wraps ffmpeg concat
│       ├── audio_overlay.py           # NEW — wraps ffmpeg overlay
│       ├── caption_burn.py            # NEW — whisper + ffmpeg captions
│       ├── text_overlay.py            # NEW — ffmpeg text overlay
│       ├── image_composite.py         # NEW — pillow/ffmpeg compositing
│       ├── transcribe.py              # NEW — wraps whisper_service
│       ├── analyze_image.py           # NEW — Gemini vision for images
│       ├── analyze_video.py           # NEW — Gemini vision for video quality evaluation
│       ├── analyze_video_reference.py # NEW — Gemini vision to understand/deconstruct existing videos for recreation
│       ├── analyze_audio.py           # NEW — Gemini for audio quality evaluation
│       ├── first_last_frame.py        # NEW — Nano Banana Pro: generate keyframe pairs for motion graphics
│       ├── web_search.py              # NEW — wraps tavily_service
│       └── prompt_engineering.py       # COPY+MODIFY (v2) — model-specific formatting
├── services/                          # External API wrappers
│   ├── claude_service.py              # MODIFY (v1+v2) — add new prompt types
│   ├── gemini_service.py              # NEW — Gemini 2.5 Flash vision/multimodal
│   ├── fal_service.py                 # KEEP (v1) — works well
│   ├── kie_service.py                 # KEEP (v1) — works well
│   ├── elevenlabs_service.py          # KEEP (v1) — works well
│   ├── ffmpeg_service.py              # COPY (v2) — has transitions, audio mix, text overlay
│   ├── whisper_service.py             # COPY (v2) — has word-level SRT
│   ├── tavily_service.py              # NEW — web search service
│   ├── nanana_service.py              # NEW — Nano Banana Pro integration
│   ├── model_registry.py              # MODIFY (v2) — extend with full model cards
│   ├── video_router.py                # KEEP (v1) — works well
│   ├── caption_styles.py              # COPY (v2) — 7 preset styles, production-ready
│   └── supabase_service.py            # MODIFY (v1) — extend schema for universal projects
├── api/
│   ├── routes.py                      # MODIFY (v1) — add upload, enhance SSE events
│   └── schemas.py                     # MODIFY (v1) — add new request/response types
└── utils/
    ├── file_manager.py                # KEEP (v1) — works well
    └── srt.py                         # KEEP (v1) — works well

frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx                 # MODIFY (v1) — add sidebar layout
│   │   ├── page.tsx                   # MODIFY (v1) — integrate PipelineSidebar
│   │   └── history/page.tsx           # MODIFY (v1) — enhanced project gallery
│   ├── hooks/
│   │   └── useSession.ts              # REWRITE (v1 base) — universal session manager
│   ├── lib/
│   │   ├── types.ts                   # REWRITE — universal type definitions
│   │   └── api.ts                     # MODIFY (v1) — add upload, new endpoints
│   └── components/
│       ├── Header.tsx                 # MODIFY (v1) — updated branding
│       ├── TopicForm.tsx              # MODIFY (v1) — universal intake form + file upload
│       ├── pipeline/                  # NEW DIRECTORY
│       │   ├── PipelineSidebar.tsx    # NEW — visual progress through phases
│       │   ├── StageCard.tsx          # NEW — individual phase card
│       │   └── CostTracker.tsx        # NEW — running cost vs estimate
│       ├── chat/
│       │   ├── ChatView.tsx           # MODIFY (v1) — handle new artifact types
│       │   └── MessageBubble.tsx      # KEEP (v1)
│       ├── input/
│       │   └── InputBar.tsx           # MODIFY (v1) — new action types
│       ├── artifacts/
│       │   ├── ScriptBlock.tsx        # KEEP (v1)
│       │   ├── SceneCards.tsx         # KEEP (v1)
│       │   ├── ImageGrid.tsx          # KEEP (v1)
│       │   ├── VideoGrid.tsx          # KEEP (v1)
│       │   ├── VoiceoverPlayer.tsx    # KEEP (v1)
│       │   ├── FinalVideo.tsx         # KEEP (v1)
│       │   ├── ProgressIndicator.tsx  # KEEP (v1)
│       │   ├── BudgetSelector.tsx     # NEW — 3-tier budget variant cards
│       │   ├── BlueprintViewer.tsx    # NEW — dynamic blueprint display
│       │   ├── CreativeBriefCard.tsx  # NEW — creative brief display
│       │   └── QualityGateIndicator.tsx # NEW — quality evaluation status
│       └── history/
│           ├── ProjectCard.tsx        # KEEP (v1)
│           └── ProjectGallery.tsx     # MODIFY (v1) — universal project types
```

**File count summary:**
- Backend: ~45 files (16 new, 10 modify, 12 keep/copy, 7 rewrite)
- Frontend: ~27 files (7 new, 9 modify, 11 keep)
- Total: ~72 files

---

## Phase 0: Foundation (Estimated: 2 sessions)

**Goal**: Universal state, graph skeleton, capability registry, enhanced services. Everything compiles and the graph runs with stub nodes.

### Step 0.1: Update config

**File**: `backend/config.py`
**Action**: MODIFY
**Source**: v1 `config.py` (27 lines)
**Changes**: Add `GOOGLE_API_KEY` (Gemini), `TAVILY_API_KEY` (web search), `NANANA_API_KEY` (Nano Banana). Keep all existing keys.

```python
# Add these fields to Settings class:
GOOGLE_API_KEY: str = ""
TAVILY_API_KEY: str = ""
NANANA_API_KEY: str = ""
```

### Step 0.2: Universal State

**File**: `backend/agent/state.py`
**Action**: REWRITE
**Source**: v1 `state.py` (45 lines) as starting point
**What it becomes**: ~120 lines. The `ProductionState` TypedDict from SYSTEM_SPEC.md Section 4, plus supporting types (`Scene`, `UploadedFile`, `PipelineStage`, `ImageAsset`, `VideoAsset`).

Key design: all fields are optional (default to empty/None/0) so the state works for ANY content type. The LLM populates only the fields relevant to the current project.

### Step 0.3: Capability Registry + Model Cards

**File**: `backend/agent/capabilities/registry.py`
**Action**: NEW (~200 lines)
**Source**: v2 `model_registry.py` (115 lines) + v2 `prompt_engineering.py` (352 lines) for model knowledge
**What it does**:
- `CAPABILITY_REGISTRY`: dict mapping capability_id → {function, description, input_schema, output_type}
- `MODEL_CARDS`: dict with full model metadata (from SYSTEM_SPEC.md Section 7.4) — cost, strengths, weaknesses, best_for, prompt_structure, duration_format
- `get_capability(id)` → returns capability function
- `get_model_card(model_id)` → returns model metadata
- `get_all_capabilities_for_llm()` → returns formatted string for LLM context injection
- `get_all_model_cards_for_llm()` → returns formatted string for LLM context injection
- `get_models_by_type(type)` → filter models by image/video/audio

### Step 0.4: Graph Skeleton

**File**: `backend/agent/graph.py`
**Action**: REWRITE
**Source**: v1 `graph.py` (109 lines) for pattern
**What it becomes**: ~150 lines. The StateGraph from SYSTEM_SPEC.md Section 3 with all 16 nodes, all conditional edges, all routing functions. Nodes start as stubs that just pass state through.

```python
def build_graph():
    sg = StateGraph(ProductionState)
    # Add all 16 nodes...
    # Add all edges and conditional edges...
    # Compile with MemorySaver
    return sg.compile(checkpointer=MemorySaver())
```

### Step 0.5: Stub Nodes

**Files**: All 16 files in `backend/agent/nodes/`
**Action**: NEW (stubs, ~15 lines each)
**What they do**: Each stub node logs that it was called and passes state through. Review nodes call `interrupt()` and return state. This lets us test the full graph flow before implementing real logic.

### Step 0.6: Copy Enhanced Services from v2

**Files**:
- `backend/services/ffmpeg_service.py` — COPY from v2 (517 lines). Has transitions, text overlay, audio mix, everything we need.
- `backend/services/whisper_service.py` — COPY from v2 (43 lines). Has word-level SRT.
- `backend/services/caption_styles.py` — COPY from v2 (175 lines). 7 preset styles, production-ready.

These replace the v1 versions which are less capable.

### Step 0.7: New Services

**File**: `backend/services/gemini_service.py`
**Action**: NEW (~80 lines)
**Source**: v2 `visual_qa_tools.py` (235 lines) for Gemini integration pattern
**What it does**:
- `analyze_image(image_url, prompt)` — Gemini 2.5 Flash vision: sends image + text prompt, returns analysis
- `analyze_video(video_url_or_path, prompt)` — Gemini vision: sends video frames + text prompt, returns analysis
- `analyze_audio(audio_path, prompt)` — Gemini: sends audio + text prompt, returns analysis
- All use `google.generativeai` SDK with `gemini-2.5-flash` model

**File**: `backend/services/tavily_service.py`
**Action**: NEW (~40 lines)
**Source**: v2 `search_tools.py` (129 lines) for pattern
**What it does**:
- `search(query, max_results=5)` → returns list of {title, url, content}
- `search_and_summarize(query, context)` → returns AI-summarized insights

**File**: `backend/services/nanana_service.py`
**Action**: NEW (~30 lines)
**What it does**:
- `generate_image(prompt)` → calls Nanana AI MCP for image generation
- Used for Nano Banana Pro model (motion graphics frames, stylized content)

### Step 0.8: Update model_registry with full model cards

**File**: `backend/services/model_registry.py`
**Action**: MODIFY
**Source**: v2 `model_registry.py` (115 lines)
**Changes**: Extend VIDEO_MODELS and IMAGE_MODELS with full knowledge card data (strengths, weaknesses, best_for, prompt_structure, optimal_length). Add Nano Banana Pro. This becomes the single source of truth referenced by the capability registry.

### Step 0.9: Prompt Engineering (capabilities layer)

**File**: `backend/agent/capabilities/prompt_engineering.py`
**Action**: COPY+MODIFY from v2 `services/prompt_engineering.py` (352 lines)
**Changes**: Same core logic — `format_for_image_model()`, `format_for_video_model()`, `get_best_practices()`. Add Nano Banana Pro formatting. Add character consistency token injection from v2. This is called by capability functions, not directly by nodes.

### Step 0.10: Verify Everything Compiles

**Test**: Run `python -c "from agent.graph import build_graph; g = build_graph(); print('OK')"` — should compile the graph with all stub nodes.

**Checkpoint**: The graph runs end-to-end with stubs. All services import. No errors.

---

## Phase 1: Intake + Interview (Estimated: 1-2 sessions)

**Goal**: User can submit any request (text + optional files) and the system classifies it, asks smart follow-ups, and decides if research is needed.

### Step 1.1: Intake Prompt

**File**: `backend/agent/prompts/intake.py`
**Action**: NEW (~80 lines)
**What it does**: Contains the prompt template for classifying any user request. The prompt tells Claude:
- Parse the request into: content_type, target_platform, target_audience, constraints, reference_materials
- Identify what kind of content is being requested
- List what information would help produce better results
- Decide: do we need to interview the user, or is the request clear enough?
- The prompt injects the full capability registry so Claude knows what the system can do

### Step 1.2: Interview Prompt

**File**: `backend/agent/prompts/interview.py`
**Action**: NEW (~60 lines)
**What it does**: Prompt for smart follow-up questions. Tells Claude to act like a production team interviewing a client:
- Ask about audience, platform, tone, style, references
- Be smart — don't ask obvious questions, ask questions that will actually improve the output
- If the user says "just figure it out" — respect that and use best judgment
- Maximum 3-5 questions, prioritized by impact

### Step 1.3: Intake Node

**File**: `backend/agent/nodes/intake.py`
**Action**: NEW (~60 lines)
**Source**: v1 `analyze_input.py` (136 lines) for pattern
**What it does**:
1. Reads user_request and uploaded_files from state
2. If uploaded files: sends them to Gemini vision for analysis:
   - **Images**: Gemini sees the image → extracts character description, style, objects, setting
   - **Videos**: Gemini watches the video → extracts scene breakdown, style, pacing, transitions, mood (this enables "recreate this video" requests)
   - **Audio**: Gemini listens → extracts tone, pacing, content description
3. Calls Claude with intake prompt + user request + file analyses
4. Parses response into structured fields: content_type, platform, audience, constraints, reference_materials
5. Sets `interview_complete = False` if follow-up questions are needed
6. Emits SSE event: `{event: "message", data: {role: "assistant", content: "I understand you want..."}}`

### Step 1.4: Interview Node

**File**: `backend/agent/nodes/interview.py`
**Action**: NEW (~50 lines)
**What it does**:
1. If `interview_complete` is already True → pass through (no interview needed)
2. Calls Claude with interview prompt + parsed request
3. Claude generates follow-up questions
4. Emits SSE event with questions
5. `interrupt()` — waits for user response
6. On resume: updates state with user's answers, sets `interview_complete = True`
7. Also decides: does this project need web research? Sets `research_needed`

### Step 1.5: Routing after Interview

**In**: `backend/agent/graph.py`
**Function**: `route_after_interview(state)`
- If `research_needed` → "research"
- Else → "creative_direction"

### Step 1.6: Frontend — Enhanced TopicForm

**File**: `frontend/src/components/TopicForm.tsx`
**Action**: MODIFY
**Source**: v1 `TopicForm.tsx` (215 lines)
**Changes**:
- Remove video model selector (the agent chooses this now)
- Remove concat toggle (the agent decides)
- Keep text input but make it bigger — this is a universal creative brief input
- Keep file upload (drag-drop)
- Add placeholder text: "Describe what you want to create. Be as specific as you want — I'll ask if I need more info."

### Step 1.7: Frontend — Universal Types

**File**: `frontend/src/lib/types.ts`
**Action**: REWRITE
**Source**: v1 `types.ts` (91 lines)
**Changes**: Remove `VideoModel` enum (agent chooses). Add new types: `PipelineStage`, `BudgetVariant`, `CreativeBrief`. Keep `ChatItem`, `ChatMessage`, `ChatArtifact`, add new artifact types: `creative_brief`, `budget_variants`, `blueprint`, `quality_report`.

**Checkpoint**: User can type any request, the system classifies it and asks smart follow-ups.

---

## Phase 2: Research + Creative Direction (Estimated: 2 sessions)

**Goal**: Web research when needed, creative brief generation with budget variants, user approval.

### Step 2.1: Research Prompt

**File**: `backend/agent/prompts/research.py`
**Action**: NEW (~60 lines)
**What it does**: Prompt template that tells Claude what to research based on the project:
- What's performing well in this format/niche right now
- Platform-specific best practices and specs
- Trending styles, sounds, formats
- Competitor/reference analysis

### Step 2.2: Research Node

**File**: `backend/agent/nodes/research.py`
**Action**: NEW (~70 lines)
**Source**: v2 `search_tools.py` (129 lines) for Tavily pattern
**What it does**:
1. Uses Claude to generate 2-4 targeted search queries based on the project
2. Calls `tavily_service.search()` for each query in parallel
3. Sends results back to Claude for synthesis
4. Stores structured insights in `state.research_insights`
5. Emits SSE event showing research findings to user

### Step 2.3: Creative Direction Prompt

**File**: `backend/agent/prompts/creative_direction.py`
**Action**: NEW (~150 lines) — this is the "brain" prompt
**What it does**: The most important prompt in the system. Tells Claude:
- You are a senior creative director at a top production studio
- Here is the project brief, audience, platform, constraints, references, research insights
- Here are ALL available capabilities and their costs: [inject capability registry]
- Here are ALL available models with strengths/weaknesses/costs: [inject model cards]
- **FIRST**: Honestly assess — can we achieve what the user wants with the available capabilities? If something is truly impossible (e.g., real-time 3D rendering, live action capture), tell the user clearly and suggest the closest achievable alternative. If it's achievable but with tradeoffs, explain them.
- **THEN** generate:
  1. A creative brief (concept, visual style, pacing, audio direction, etc.)
  2. A production plan (ordered JSON list of capabilities to execute)
  3. Three budget variants (budget/standard/premium) with specific model selections and itemized cost estimates
- The production plan uses ONLY capabilities from the registry — the LLM decides which ones, how many times, and in what order
- Each budget variant should have different model choices, not just fewer steps
- Explain the quality/cost tradeoffs for each variant
- For motion graphics: use first_last_frame (Nano Banana) + video_gen with first/last frame support
- For video recreation: use analyze_video_reference output to inform the creative brief

### Step 2.4: Creative Direction Node

**File**: `backend/agent/nodes/creative_direction.py`
**Action**: NEW (~80 lines)
**What it does**:
1. Builds the creative direction prompt with all context injected
2. One Claude call (this is the "brain" call — most important in the pipeline)
3. Parses response: creative_brief, production_plan, budget_variants
4. Stores all three in state
5. Emits SSE events: creative brief card + budget variant selector

### Step 2.5: Review Direction Node

**File**: `backend/agent/nodes/review_direction.py`
**Action**: NEW (~45 lines)
**What it does**:
1. `interrupt()` — presents creative brief + budget variants to user
2. User can: approve (with budget selection), modify (chat feedback), or reject
3. On approve: set `selected_variant`, copy selected model assignments into production_plan
4. On modify: pass feedback back to creative_direction node for revision

### Step 2.6: Model Knowledge Prompt Context

**File**: `backend/agent/prompts/model_knowledge.py`
**Action**: NEW (~100 lines)
**What it does**: Generates injectable context strings for LLM prompts:
- `get_model_cards_context()` → formatted text block describing all models
- `get_capability_context()` → formatted text block describing all capabilities
- Used by creative_direction, blueprint, and quality_gate prompts

### Step 2.7: Frontend — BudgetSelector

**File**: `frontend/src/components/artifacts/BudgetSelector.tsx`
**Action**: NEW (~120 lines)
**What it does**: Renders 3 budget variant cards side by side:
- Each card shows: tier name, total estimate, model selections, cost breakdown, tradeoffs
- User clicks to select one
- Highlighted card shows which is selected
- "Approve" button sends selection back

### Step 2.8: Frontend — CreativeBriefCard

**File**: `frontend/src/components/artifacts/CreativeBriefCard.tsx`
**Action**: NEW (~80 lines)
**What it does**: Renders the creative brief as a styled card:
- Concept, visual style, pacing, audio direction
- Collapsible sections for detail
- Shows platform specs

**Checkpoint**: Full pre-production pipeline works. User submits request → optional interview → optional research → creative direction with budget variants → user approves.

---

## Phase 3: Blueprint + Production Executor (Estimated: 3 sessions)

**Goal**: Dynamic blueprint generation, the core production executor that walks the capability list, and all capability functions.

### Step 3.1: Blueprint Prompt

**File**: `backend/agent/prompts/blueprint.py`
**Action**: NEW (~100 lines)
**What it does**: Tells Claude to generate a detailed execution blueprint:
- You are given the creative brief, production plan, and selected budget variant
- Generate whatever detailed specifications each production step needs
- For video content: script, storyboard, audio map (but don't hardcode this — Claude decides)
- For graphic content: layout, elements, typography (Claude decides)
- For anything else: Claude generates appropriate structure
- Include model-specific prompting notes from the model knowledge cards
- This should be professional-grade — the kind of document a creative director hands their team

### Step 3.2: Blueprint Node

**File**: `backend/agent/nodes/blueprint.py`
**Action**: NEW (~70 lines)
**What it does**:
1. Builds blueprint prompt with creative brief + production plan + model cards
2. One Claude call → generates freeform blueprint JSON
3. Stores in `state.blueprint`
4. Emits SSE event with blueprint content

### Step 3.3: Review Blueprint Node

**File**: `backend/agent/nodes/review_blueprint.py`
**Action**: NEW (~45 lines)
**What it does**: Same pattern as review_direction — interrupt, user approves/modifies/rejects.

### Step 3.4: Frontend — BlueprintViewer

**File**: `frontend/src/components/artifacts/BlueprintViewer.tsx`
**Action**: NEW (~150 lines)
**What it does**: Renders the dynamic blueprint. Since the blueprint structure varies:
- Detect common sections (script, scenes, layout, audio_map) and render them with specialized UI
- For unknown sections: render as formatted JSON/markdown
- Script section → ScriptBlock component
- Scenes section → SceneCards component
- Everything else → collapsible JSON viewer with syntax highlighting

### Step 3.5: Capability Functions (the shared layer)

Each capability is a standalone function that does ONE thing. The produce node calls them.

**File**: `backend/agent/capabilities/image_gen.py`
**Action**: NEW (~50 lines)
**Source**: v1 `fal_service.generate_image()` + v2 `prompt_engineering.format_for_image_model()`
**Function**: `execute(params, state, blueprint_context) → ImageAsset`
- Reads model from params, formats prompt using prompt_engineering
- Calls fal_service or nanana_service based on model
- Returns {url, local_path, model, cost}

**File**: `backend/agent/capabilities/video_gen.py`
**Action**: NEW (~60 lines)
**Source**: v1 `video_router.generate_video()` + v2 `prompt_engineering.format_for_video_model()`
**Function**: `execute(params, state, blueprint_context) → VideoAsset`
- Routes to correct provider (fal/kie) based on model
- Handles duration format per model (Veo="8s", Seedance=int, Kling=str)
- Returns {url, local_path, model, cost, duration}

**File**: `backend/agent/capabilities/voiceover.py`
**Action**: NEW (~30 lines)
**Source**: v1 `elevenlabs_service.generate_tts()`
**Function**: `execute(params, state, blueprint_context) → str (audio path)`

**File**: `backend/agent/capabilities/voice_select.py`
**Action**: NEW (~40 lines)
**Function**: `execute(params, state, blueprint_context) → str (voice_id)`
- Calls ElevenLabs voice search API based on criteria (gender, age, energy)

**File**: `backend/agent/capabilities/music_gen.py`
**Action**: NEW (~40 lines)
**Function**: `execute(params, state, blueprint_context) → str (audio path)`
- Calls music generation (Suno via API or ElevenLabs)

**File**: `backend/agent/capabilities/sfx_gen.py`
**Action**: NEW (~30 lines)
**Function**: `execute(params, state, blueprint_context) → str (audio path)`
- Calls ElevenLabs SFX generation

**File**: `backend/agent/capabilities/face_reference.py`
**Action**: NEW (~50 lines)
**Source**: v2 `visual_qa_tools.py` `analyze_reference_image()` pattern
**Function**: `execute(params, state, blueprint_context) → dict (character_sheet)`
- Sends reference image to Gemini vision for character extraction
- Returns structured character description for prompt injection

**File**: `backend/agent/capabilities/audio_mix.py`
**Action**: NEW (~30 lines)
**Source**: v2 `ffmpeg_service.mix_audio_layers()`
**Function**: `execute(params, state, blueprint_context) → str (mixed audio path)`

**File**: `backend/agent/capabilities/video_concat.py`
**Action**: NEW (~30 lines)
**Source**: v2 `ffmpeg_service.concat_videos_with_transitions()`
**Function**: `execute(params, state, blueprint_context) → str (concat path)`

**File**: `backend/agent/capabilities/audio_overlay.py`
**Action**: NEW (~20 lines)
**Source**: v2 `ffmpeg_service.overlay_audio()`
**Function**: `execute(params, state, blueprint_context) → str (video path)`

**File**: `backend/agent/capabilities/caption_burn.py`
**Action**: NEW (~40 lines)
**Source**: v2 `ffmpeg_service.burn_subtitles()` + `caption_styles.py`
**Function**: `execute(params, state, blueprint_context) → str (captioned video path)`

**File**: `backend/agent/capabilities/text_overlay.py`
**Action**: NEW (~30 lines)
**Source**: v2 `ffmpeg_service.add_text_overlay_to_video()`
**Function**: `execute(params, state, blueprint_context) → str (video path)`

**File**: `backend/agent/capabilities/transcribe.py`
**Action**: NEW (~20 lines)
**Source**: v2 `whisper_service.transcribe_to_word_srt()`
**Function**: `execute(params, state, blueprint_context) → str (SRT path)`

**File**: `backend/agent/capabilities/analyze_image.py`
**Action**: NEW (~40 lines)
**Function**: `execute(image_url, criteria, creative_brief) → dict (score + notes)`
- Sends image to Gemini vision with evaluation criteria
- Returns {score, issues, suggestions}

**File**: `backend/agent/capabilities/analyze_video.py`
**Action**: NEW (~40 lines)
**Function**: `execute(video_path, criteria, creative_brief) → dict (score + notes)`
- Sends video frames to Gemini vision
- Returns {score, issues, suggestions}

**File**: `backend/agent/capabilities/analyze_audio.py`
**Action**: NEW (~30 lines)
**Function**: `execute(audio_path, criteria, creative_brief) → dict (score + notes)`
- Sends audio to Gemini for quality evaluation (clarity, pronunciation, pacing)

**File**: `backend/agent/capabilities/analyze_video_reference.py`
**Action**: NEW (~50 lines)
**What it does**: Gemini vision mode to UNDERSTAND an existing video for recreation/inspiration.
**Function**: `execute(video_url, analysis_prompt) → dict`
- Sends video to Gemini 2.5 Flash vision
- Returns: scene-by-scene breakdown, visual style analysis, timing/pacing, transitions used, mood/tone, camera movements, text overlays detected
- This is how the agent handles "recreate this video" or "make something like this" requests
- The output feeds into creative_direction and blueprint nodes so the LLM can plan a recreation

**File**: `backend/agent/capabilities/first_last_frame.py`
**Action**: NEW (~40 lines)
**What it does**: Generate first + last keyframe images for motion graphics using Nano Banana Pro.
**Function**: `execute(params, state, blueprint_context) → dict (two image URLs)`
- Generates start frame image based on prompt
- Generates end frame image based on prompt
- Returns {first_frame_url, last_frame_url}
- These get passed to video_gen models that support first/last frame (Veo 3.1) to create smooth motion graphics transitions

**File**: `backend/agent/capabilities/web_search.py`
**Action**: NEW (~20 lines)
**Function**: `execute(params, state, blueprint_context) → dict (search results)`
- Wraps tavily_service.search()

**File**: `backend/agent/capabilities/image_composite.py`
**Action**: NEW (~40 lines)
**Function**: `execute(params, state, blueprint_context) → str (composite image path)`
- Uses Pillow for layer compositing (graphic design)

### Step 3.6: Production Executor (the core engine)

**File**: `backend/agent/nodes/produce.py`
**Action**: NEW (~120 lines) — most complex node
**What it does**:
1. Reads `production_plan` from state (ordered list of capability steps)
2. Reads `current_stage_index` to know where we are
3. Gets current capability step: `plan[stage_index]`
4. Looks up capability function from registry
5. Extracts relevant blueprint context for this step
6. Executes the capability (may execute multiple in parallel for batch operations like "generate 5 images")
7. Stores result in appropriate state field (images, videos, voiceover, etc.)
8. Updates cost tracking
9. Updates pipeline visualization
10. Routes to quality_gate for evaluation

**Stage grouping logic**: The production plan might have:
```json
[
  {"capability": "face_reference", ...},
  {"capability": "image_gen", "count": 5, ...},    ← these are one "stage"
  {"capability": "video_gen", "count": 5, ...},    ← this is another "stage"
  {"capability": "voiceover", ...},                 ← another "stage"
  {"capability": "music_gen", ...},
  {"capability": "audio_mix", ...}
]
```
After each "stage" completes (all items in a batch), the user reviews. Between individual items within a stage, the quality gate runs autonomously.

### Step 3.7: Quality Gate Node

**File**: `backend/agent/nodes/quality_gate.py`
**Action**: NEW (~100 lines)
**Source**: v2 `visual_qa_tools.py` for Gemini evaluation pattern
**What it does**:
1. Gets the just-produced asset from state
2. Determines asset type (image/video/audio)
3. Calls appropriate analyze capability (Gemini vision mode)
4. Sends: the actual asset + creative brief + original prompt
5. Receives: score (1-10) + written analysis
6. If score >= 7: PASS → route back to produce for next item
7. If score < 7 and retry < 3:
   - Send Gemini's analysis to Claude
   - Claude generates optimized prompt
   - Route back to produce with new prompt
8. If retry >= 3:
   - Propose model upgrade → interrupt user
   - User approves → update model in plan, reset retries
   - User declines → keep best attempt, move on
9. If expensive model also fails 2x: escalate to user with all attempts

### Step 3.8: Quality Gate Prompt

**File**: `backend/agent/prompts/quality_gate.py`
**Action**: NEW (~80 lines)
**Contains two prompts**:
1. **Gemini evaluation prompt**: "You are a quality control expert. Analyze this [image/video/audio]. Score it 1-10 on these criteria. If below 7, explain specifically what's wrong and what would fix it."
2. **Claude optimization prompt**: "Gemini found these issues: [analysis]. The original prompt was: [prompt]. Generate an improved prompt that fixes these specific issues while maintaining the creative brief."

### Step 3.9: Review Stage Node

**File**: `backend/agent/nodes/review_stage.py`
**Action**: NEW (~50 lines)
**What it does**:
1. Called after a complete stage (e.g., all 5 images generated and quality-checked)
2. Presents all assets from this stage to user
3. `interrupt()` — "Here are the results. Approve to move to next stage?"
4. On approve: increment stage_index, route back to produce
5. On modify: route back to produce with feedback for regeneration
6. If all stages complete: route to assemble

**Checkpoint**: The full production engine works. Capabilities execute, quality gate evaluates with Gemini vision, auto-retries, model upgrade proposals, stage-level user approval.

---

## Phase 4: Assembly + Polish + Deliver (Estimated: 2 sessions)

**Goal**: Post-production pipeline that combines all assets and delivers platform-optimized output.

### Step 4.1: Assemble Node

**File**: `backend/agent/nodes/assemble.py`
**Action**: NEW (~70 lines)
**Source**: v2 `assembly_tools.py` (452 lines) for pattern
**What it does**:
1. Reads blueprint for assembly instructions (transitions, timing, etc.)
2. For video: concat clips with transitions → overlay mixed audio
3. For graphic: composite layers → render final image
4. For audio: join segments → normalize
5. Stores assembled output in `state.assembled_path`

### Step 4.2: Review Assembly Node

**File**: `backend/agent/nodes/review_assembly.py`
**Action**: NEW (~40 lines)
**What it does**: Interrupt, show assembled output, user approves/requests changes.

### Step 4.3: Polish Node

**File**: `backend/agent/nodes/polish.py`
**Action**: NEW (~80 lines)
**Source**: v2 `ffmpeg_service.py` for captions, text overlays
**What it does**:
1. Reads creative brief for polish specifications
2. Applies caption style (from 7 presets in caption_styles.py)
3. Transcribes audio → SRT → burn captions
4. Add text overlays (title cards, CTAs) if specified in blueprint
5. Audio normalization to platform loudness standards
6. Generate thumbnail (if video content)
7. Stores in `state.polished_path`

### Step 4.4: Review Polish Node

**File**: `backend/agent/nodes/review_polish.py`
**Action**: NEW (~40 lines)

### Step 4.5: Deliver Node

**File**: `backend/agent/nodes/deliver.py`
**Action**: NEW (~60 lines)
**What it does**:
1. Platform-specific export (aspect ratio, resolution, codec)
2. Generate metadata: title, description, hashtags (Claude call)
3. Store final output in `state.final_output_path`
4. Save everything to Supabase (project, media records, chat history)
5. Emit download link

### Step 4.6: Review Final Node

**File**: `backend/agent/nodes/review_final.py`
**Action**: NEW (~30 lines)
**What it does**: Final interrupt showing the output + metadata. User approves → END.

**Checkpoint**: Complete pipeline works end-to-end. User can go from "make me a viral TikTok" to getting a polished video with captions, music, and platform metadata.

---

## Phase 5: Frontend — Pipeline Sidebar + Cost Tracking (Estimated: 1-2 sessions)

**Goal**: Real-time visual progress and cost tracking in the UI.

### Step 5.1: PipelineSidebar

**File**: `frontend/src/components/pipeline/PipelineSidebar.tsx`
**Action**: NEW (~150 lines)
**What it does**:
- Vertical list of phase cards (Intake, Research, Creative Direction, Blueprint, Produce, Assemble, Polish, Deliver)
- Each card shows: status icon (pending/active/done/failed), substep progress (e.g., "3/5 images"), cost for this phase
- Active phase highlighted with animation
- Click completed phase → scroll to that point in chat
- Receives pipeline state via SSE events

### Step 5.2: StageCard

**File**: `frontend/src/components/pipeline/StageCard.tsx`
**Action**: NEW (~60 lines)
**What it does**: Individual phase card with status icon, progress dots, cost display, click handler.

### Step 5.3: CostTracker

**File**: `frontend/src/components/pipeline/CostTracker.tsx`
**Action**: NEW (~50 lines)
**What it does**: Shows running cost vs budget estimate. Bar visualization. Red warning if approaching limit.

### Step 5.4: Frontend — Enhanced Page Layout

**File**: `frontend/src/app/page.tsx`
**Action**: MODIFY
**Changes**: Add PipelineSidebar to left side of page. Main chat area takes remaining width. Sidebar shows during active sessions, hidden on topic form.

### Step 5.5: SSE Events for Pipeline Updates

**Backend**: Add new SSE event type `pipeline_update` in routes.py
**Frontend**: Handle `pipeline_update` events in `useSession.ts` to update sidebar state

**Checkpoint**: Users can see exactly where they are in the pipeline, what's happening, and what it's costing in real time.

---

## Phase 6: Long-Form Chunking (Estimated: 1 session)

**Goal**: Support content longer than 5 minutes by processing in chunks.

### Step 6.1: Chunking Logic in Blueprint Node

**Modify**: `backend/agent/nodes/blueprint.py`
**Changes**: If estimated duration > 5 minutes, the blueprint prompt tells Claude to divide into chapters (~5 min each). Blueprint output includes `chapters` array with per-chapter specifications.

### Step 6.2: Chunking Logic in Produce Node

**Modify**: `backend/agent/nodes/produce.py`
**Changes**: If `state.total_chunks > 1`, process one chunk at a time. After each chunk → review_stage → user approves → next chunk. Pass inter-chunk context (character sheets, style decisions, continuity notes) between chunks.

### Step 6.3: Frontend — ChunkProgress

**File**: `frontend/src/components/artifacts/ChunkProgress.tsx` (optional — could be in PipelineSidebar)
**Action**: NEW (~40 lines)
**What it does**: Shows "Chapter 3 of 12" with progress bar.

**Checkpoint**: System can handle 1-hour films by processing in 5-minute chunks.

---

## Phase 7: History + Persistence (Estimated: 1-2 sessions)

**Goal**: Full project history with media gallery and chat resume.

### Step 7.1: Extended Supabase Schema

**Modify**: `backend/services/supabase_service.py`
**Changes**: Update schema to match SYSTEM_SPEC.md Section 11.1. Add fields: content_type, creative_brief (JSONB), production_plan (JSONB), blueprint (JSONB), pipeline_stages (JSONB), cost_breakdown (JSONB). Project name chosen by LLM.

### Step 7.2: Auto-Save at Phase Boundaries

**Modify**: Each review node
**Changes**: After user approves at any review point, auto-save project state to Supabase. This means if the user leaves and comes back, they can see their project in history.

### Step 7.3: Media Records

**Modify**: Capability functions
**Changes**: After each successful generation, create a media record in Supabase with: project_id, media_type, stage, model_used, cost, public_url.

### Step 7.4: Chat History Persistence

**Modify**: `backend/api/routes.py`
**Changes**: Save chat messages to Supabase `chat_messages` table. On project resume, reload chat history.

### Step 7.5: Frontend — Enhanced History

**Modify**: `frontend/src/app/history/page.tsx`
**Changes**: Show universal project types (not just "video"). Display content_type badge, total cost, pipeline progress. Click project → resume session with full chat history.

**Checkpoint**: Users can see all their projects, organized by type, with full media galleries and chat history. Can click to resume.

---

## Phase 8: API Routes + Session Management (Estimated: 1 session)

**Goal**: Updated API to support all new features.

### Step 8.1: Enhanced Routes

**Modify**: `backend/api/routes.py`
**Source**: v1 routes (286 lines) + v2 patterns
**Changes**:
- Keep POST `/api/sessions` — create session (now sends universal request, not just topic)
- Keep POST `/api/sessions/{id}/resume` — resume graph
- Keep GET `/api/sessions/{id}/events` — SSE stream
- Keep GET `/api/media/{id}/{filename}` — serve media
- Add POST `/api/upload` — file upload (from v2, 50MB limit)
- Keep project CRUD endpoints
- Add new SSE event types: `pipeline_update`, `cost_update`, `quality_gate`, `budget_variants`, `creative_brief`, `blueprint`

### Step 8.2: Enhanced useSession Hook

**Modify**: `frontend/src/hooks/useSession.ts`
**Source**: v1 (194 lines) as base
**Changes**:
- Add `pipelineStages` state for sidebar
- Add `costTracking` state
- Add `budgetVariants` state
- Handle new SSE event types
- Add `selectBudget()`, `approveDirection()`, `approveBlueprint()` actions
- Keep existing: `approve()`, `modify()`, `regenerate()`, `reset()`

### Step 8.3: Enhanced ChatView

**Modify**: `frontend/src/components/chat/ChatView.tsx`
**Source**: v1 (186 lines)
**Changes**: Handle new artifact types (creative_brief, budget_variants, blueprint, quality_report). Route to new renderers.

**Checkpoint**: Full API and frontend integration complete.

---

## Phase 9: Testing + Polish (Estimated: 2 sessions)

### Step 9.1: End-to-End Tests

1. **Short video from topic**: "Make me a viral TikTok about AI replacing jobs" → full pipeline → polished video with captions
2. **Video with face reference**: Upload photo + "Make a personal branding video with me" → character consistency → polished video
3. **Graphic design**: "Create an Instagram story ad for 50% off sale" → image generation → compositing
4. **Long-form**: "Create a 3-minute explainer video about quantum computing" → chunked processing
5. **Open-ended**: "Create something amazing about space exploration" → agent interviews, researches, decides content type

### Step 9.2: Error Handling

- Graceful degradation when services fail (Gemini down → skip quality gate, continue)
- Budget enforcement (stop if cost exceeds 1.5x estimate)
- Timeout handling for long generations

### Step 9.3: Performance

- Parallel image/video generation within a stage
- Caching of model cards and capability registry
- SSE event batching for fast updates

---

## Dependency Graph (Build Order)

```
Phase 0 (Foundation)
├── config.py ← no deps
├── state.py ← no deps
├── capabilities/registry.py ← state.py, model_registry.py
├── model_registry.py ← no deps
├── capabilities/prompt_engineering.py ← model_registry.py
├── graph.py ← state.py, all nodes
├── all stub nodes ← state.py
├── ffmpeg_service.py (copy v2) ← no deps
├── whisper_service.py (copy v2) ← no deps
├── caption_styles.py (copy v2) ← no deps
├── gemini_service.py ← config.py
├── tavily_service.py ← config.py
└── nanana_service.py ← config.py

Phase 1 (Intake) ← Phase 0
├── prompts/intake.py ← capabilities/registry.py
├── prompts/interview.py ← no deps
├── nodes/intake.py ← prompts/intake.py, gemini_service.py, claude_service.py
├── nodes/interview.py ← prompts/interview.py, claude_service.py
└── Frontend: TopicForm, types.ts ← no backend deps

Phase 2 (Creative Direction) ← Phase 1
├── prompts/model_knowledge.py ← capabilities/registry.py
├── prompts/creative_direction.py ← prompts/model_knowledge.py
├── prompts/research.py ← no deps
├── nodes/research.py ← tavily_service.py
├── nodes/creative_direction.py ← prompts/creative_direction.py, claude_service.py
├── nodes/review_direction.py ← no deps (interrupt only)
└── Frontend: BudgetSelector, CreativeBriefCard ← no backend deps

Phase 3 (Blueprint + Production) ← Phase 2
├── prompts/blueprint.py ← prompts/model_knowledge.py
├── prompts/quality_gate.py ← no deps
├── nodes/blueprint.py ← prompts/blueprint.py, claude_service.py
├── nodes/review_blueprint.py ← no deps
├── ALL capability functions ← respective services
├── nodes/produce.py ← capabilities/registry.py, all capabilities
├── nodes/quality_gate.py ← gemini_service.py, claude_service.py
├── nodes/review_stage.py ← no deps
└── Frontend: BlueprintViewer, QualityGateIndicator ← no backend deps

Phase 4 (Post-Production) ← Phase 3
├── nodes/assemble.py ← ffmpeg_service.py
├── nodes/review_assembly.py ← no deps
├── nodes/polish.py ← ffmpeg_service.py, whisper_service.py, caption_styles.py
├── nodes/review_polish.py ← no deps
├── nodes/deliver.py ← supabase_service.py
└── nodes/review_final.py ← no deps

Phase 5 (Frontend Sidebar) ← Phase 4
├── PipelineSidebar.tsx ← types.ts
├── StageCard.tsx ← types.ts
├── CostTracker.tsx ← types.ts
└── page.tsx updates ← PipelineSidebar

Phase 6 (Chunking) ← Phase 3
├── blueprint.py updates ← no new deps
└── produce.py updates ← no new deps

Phase 7 (History) ← Phase 4
├── supabase_service.py updates ← no new deps
├── review nodes updates ← supabase_service.py
└── history/page.tsx updates ← api.ts

Phase 8 (API) ← Phase 4
├── routes.py updates ← all nodes
├── useSession.ts updates ← types.ts
└── ChatView.tsx updates ← all artifact components

Phase 9 (Testing) ← ALL
```

---

## Files by Action Type (Summary)

| Action | Count | Description |
|--------|-------|-------------|
| **NEW** | 38 | Brand new files (nodes, capabilities, prompts, services, frontend components) |
| **REWRITE** | 4 | Complete rewrites (state.py, graph.py, types.ts, useSession.ts) |
| **MODIFY** | 15 | Existing files with targeted changes |
| **COPY from v2** | 4 | Direct copies (ffmpeg_service, whisper_service, caption_styles, prompt_engineering) |
| **KEEP** | 16 | Untouched v1 files that work as-is |
| **Total** | ~77 | |

---

## What We Are NOT Building (Scope Boundaries)

To keep focus, these are explicitly deferred:
- **Re-entry**: Once a phase is approved, no going back (per our discussion)
- **Version control within projects**: No undo/redo within a session
- **Multi-user**: Single user system
- **Deployment/hosting**: Local dev only
- **Custom model training**: Use existing models only
- **Real-time collaboration**: Single session at a time
