# AI Production Studio - System Specification & Implementation Plan

## 1. Vision

An AI production studio that takes ANY creative request and produces professional content. The user says "make me X" and gets back production-quality output — whether that's a 30-second TikTok, a 1-hour film, a poster, or a podcast.

The system acts as a full production team: interviewing the client, researching what works, planning the creative direction with budget options, executing production with automated quality control, and delivering platform-optimized output.

---

## 2. Architecture Overview

### 2.1 The 8-Phase Universal Pipeline

Every project, regardless of content type, flows through 8 phases:

```
INTAKE → RESEARCH → CREATIVE DIRECTION → BLUEPRINT → PRODUCE → ASSEMBLE → POLISH → DELIVER
```

These are LangGraph StateGraph nodes. The phases are always sequential. What changes between content types is what happens INSIDE each phase — driven by the creative brief and production plan in state.

### 2.2 Multi-Agent Pattern: Hybrid

```
Main flow:        Sequential Pipeline (8 phases, always in order)
Production:       Supervisor loop (quality gate controls generation)
Asset generation: Parallel (generate N images/videos simultaneously)
Quality gate:     Evaluator (Gemini Flash) + Optimizer (Claude) pair
```

### 2.3 Dynamic Capability Execution (Option A)

The Creative Direction phase outputs a `production_plan` — a JSON list of capability steps:

```json
{
  "production_plan": [
    {"capability": "face_reference", "params": {"source": "uploaded_photo"}},
    {"capability": "image_gen", "params": {"model": "seedream-4.5", "count": 5}},
    {"capability": "video_gen", "params": {"model": "veo3.1", "count": 5}},
    {"capability": "voice_select", "params": {"gender": "male", "energy": "high"}},
    {"capability": "voiceover", "params": {"model": "elevenlabs"}},
    {"capability": "music", "params": {"mood": "upbeat", "source": "suno"}},
    {"capability": "sfx", "params": {"style": "whoosh_transitions"}},
    {"capability": "audio_mix", "params": {"vo_vol": 1.0, "music_vol": 0.25, "sfx_vol": 0.4}}
  ]
}
```

The PRODUCE phase walks this list and calls each capability in order. The LLM decides the composition; the executor runs it reliably.

### 2.4 Cost: ~$0.05-0.15 per session in LLM calls

- Phase 1-4 (Intake through Blueprint): 4-6 focused LLM calls (~$0.03-0.08)
- Phase 5 (Production): Quality gate calls use Gemini Flash (~$0.01-0.02 each)
- Phase 6-8 (Post-production): Mostly automated, 0-2 LLM calls (~$0.01-0.02)
- Total LLM cost: ~$0.05-0.15 per project (vs $1-5 for v2's ReAct loop)
- Media generation costs are separate (model-dependent, shown in budget variants)

---

## 3. Graph Structure (LangGraph)

```python
# Main graph nodes
StateGraph(ProductionState)

# Phase 1: INTAKE
add_node("intake", intake_node)           # Parse request, classify content type
add_node("interview", interview_node)     # Smart follow-up questions (optional)

# Phase 2: RESEARCH
add_node("research", research_node)       # Web search + trend analysis (conditional)

# Phase 3: CREATIVE DIRECTION
add_node("creative_direction", creative_direction_node)  # Brief + plan + budget variants
add_node("review_direction", review_direction_node)      # USER REVIEWS (interrupt)

# Phase 4: BLUEPRINT
add_node("blueprint", blueprint_node)     # Detailed execution plan
add_node("review_blueprint", review_blueprint_node)      # USER REVIEWS (interrupt)

# Phase 5: PRODUCE (dynamic capability executor)
add_node("produce", produce_node)         # Walks production_plan, calls capabilities
add_node("quality_gate", quality_gate_node)              # Gemini evaluates output
add_node("review_stage", review_stage_node)              # USER REVIEWS at stage boundaries (interrupt)

# Phase 6: ASSEMBLE
add_node("assemble", assemble_node)       # Combine assets per blueprint
add_node("review_assembly", review_assembly_node)        # USER REVIEWS (interrupt)

# Phase 7: POLISH
add_node("polish", polish_node)           # Captions, color, audio norm
add_node("review_polish", review_polish_node)            # USER REVIEWS (interrupt)

# Phase 8: DELIVER
add_node("deliver", deliver_node)         # Platform export + metadata
add_node("review_final", review_final_node)              # USER REVIEWS final (interrupt)

# Edges
add_edge(START, "intake")
add_edge("intake", "interview")
add_conditional_edges("interview", route_after_interview)  # → research or creative_direction
add_edge("research", "creative_direction")
add_edge("creative_direction", "review_direction")
add_conditional_edges("review_direction", route_after_direction_review)  # → back or blueprint
add_edge("blueprint", "review_blueprint")
add_conditional_edges("review_blueprint", route_after_blueprint_review)  # → back or produce
add_conditional_edges("produce", route_after_produce)      # → quality_gate or review_stage
add_conditional_edges("quality_gate", route_after_quality_gate)  # → produce (retry) or review_stage
add_conditional_edges("review_stage", route_after_stage_review)  # → produce (next stage) or assemble
add_edge("assemble", "review_assembly")
add_conditional_edges("review_assembly", route_after_assembly_review)
add_edge("polish", "review_polish")
add_conditional_edges("review_polish", route_after_polish_review)
add_edge("deliver", "review_final")
add_edge("review_final", END)
```

### 3.1 Key Conditional Routing

**After Interview**: If the agent determined it needs web research → research node. Otherwise → creative_direction directly.

**After Direction Review**: User approves → blueprint. User modifies → back to creative_direction with feedback.

**After Blueprint Review**: User approves → produce. User modifies → back to blueprint with feedback.

**After Produce**: Each capability step completion → quality_gate. After all steps in a stage (e.g., all images) → review_stage for user approval.

**After Quality Gate**:
1. Quality passes → continue to next capability step
2. Quality fails, retry < 3 → optimize prompt, re-run same capability
3. Quality fails, retries exhausted → propose model upgrade to user (interrupt)
4. Model upgrade fails 2x → escalate to user with options

**After Stage Review**: User approves → next production stage. All stages done → assemble.

**Long-form chunking**: If content > 5 minutes, the produce node processes in 5-minute chunks. After each chunk, user reviews. State tracks `current_chunk` and `total_chunks`.

---

## 4. Universal State Shape

```python
class ProductionState(TypedDict):
    # === Identity ===
    job_id: str
    project_id: str                    # Supabase project ID

    # === User Input ===
    user_request: str                  # Raw user input
    uploaded_files: list[UploadedFile] # {url, type, filename}

    # === Phase 1: Intake ===
    content_type: str                  # "short_video" | "long_video" | "graphic" | "audio" | "presentation"
    target_platform: str               # "tiktok" | "youtube" | "instagram" | "linkedin" | "custom"
    target_audience: str
    constraints: dict                  # {duration, aspect_ratio, dimensions, style, etc.}
    reference_materials: list[dict]    # Processed references {type, url, analysis}
    interview_complete: bool

    # === Phase 2: Research ===
    research_needed: bool
    research_insights: dict            # {trends, references, specs, recommendations}

    # === Phase 3: Creative Direction ===
    creative_brief: dict               # Full creative brief (see section 5)
    production_plan: list[dict]        # Ordered capability steps (see section 2.3)
    budget_variants: list[dict]        # 3 variants: budget, standard, premium
    selected_variant: str              # Which budget variant user chose

    # === Phase 4: Blueprint ===
    blueprint: dict                    # Content-type-specific execution plan (see section 6)

    # === Phase 5: Production ===
    current_stage_index: int           # Which production_plan step we're on
    current_chunk: int                 # For long-form: which chunk (0-based)
    total_chunks: int                  # For long-form: total chunks

    # Production artifacts (populated during produce phase)
    script: str
    scenes: list[Scene]                # {narration, visual_description, image_prompt, camera, duration, ...}
    character_sheets: list[dict]       # Face consistency data
    images: list[ImageAsset]           # {scene_index, url, local_path, model, cost}
    videos: list[VideoAsset]           # {scene_index, url, local_path, model, cost, duration}
    voiceover_path: str
    music_path: str
    sfx_paths: list[str]
    mixed_audio_path: str

    # Quality tracking
    quality_results: list[dict]        # Per-asset quality evaluations
    retry_count: int                   # Current retry count for quality loop

    # === Phase 6-8: Post-production ===
    assembled_path: str
    polished_path: str
    final_output_path: str
    caption_style: str
    transition_type: str

    # === Cost Tracking ===
    total_cost: float                  # Running total
    cost_breakdown: list[dict]         # [{step, model, count, unit_cost, total}]
    budget_limit: float                # From selected variant

    # === Pipeline Visualization ===
    pipeline_stages: list[PipelineStage]  # For UI visualization
    # Each: {name, status: "pending"|"active"|"completed"|"failed", cost, assets_count}

    # === Meta ===
    status: str
    error: str
    progress_messages: Annotated[list[str], operator.add]
```

### 4.1 Supporting Types

```python
class Scene(TypedDict):
    scene_number: int
    narration: str
    visual_description: str
    image_prompt: str
    video_prompt: str
    camera: dict                  # {shot_type, movement, angle}
    duration: float
    transition_to_next: str       # "cut" | "fade" | "dissolve" | etc.
    text_overlay: str             # Optional on-screen text
    sfx_cue: str                  # Optional SFX description
    image_url: str                # Populated during production
    image_local_path: str
    video_url: str
    video_local_path: str

class UploadedFile(TypedDict):
    url: str
    type: str                     # "image" | "video" | "audio" | "document"
    filename: str
    analysis: str                 # Gemini analysis of the file

class PipelineStage(TypedDict):
    name: str
    status: str                   # "pending" | "active" | "completed" | "failed"
    cost: float
    assets_count: int
    substeps: list[dict]          # For detailed progress
```

---

## 5. Creative Brief Structure

The creative_direction node outputs this into state:

```json
{
  "concept": "A high-energy TikTok showing...",
  "narrative_approach": "Hook → Problem → Solution → CTA",
  "hook_strategy": "Open with a surprising visual of...",

  "visual_style": {
    "mood": "energetic, bold",
    "color_palette": ["#FF6B35", "#004E89", "#FFFFFF"],
    "reference_description": "Think Casey Neistat meets Mr. Beast",
    "shot_variety": ["close-up", "wide", "POV", "overhead"]
  },

  "pacing": {
    "overall": "fast",
    "scene_duration_avg": 3.0,
    "cut_rhythm": "match music beats",
    "pattern_interrupts": "every 3-5 seconds"
  },

  "audio_direction": {
    "voiceover_style": "energetic male, conversational",
    "music_mood": "upbeat electronic",
    "music_volume": 0.3,
    "sfx_approach": "whoosh on transitions, impact on reveals"
  },

  "caption_style": "tiktok",
  "caption_options": {
    "word_by_word": true,
    "highlight_color": "#FF6B35"
  },

  "transition_style": "none",
  "transition_duration": 0,

  "platform_specs": {
    "aspect_ratio": "9:16",
    "target_duration": 45,
    "max_duration": 60,
    "resolution": "1080x1920"
  }
}
```

---

## 6. Blueprint Structure (LLM-Generated, NOT Hardcoded)

### 6.1 Core Principle

The blueprint is **NOT** a fixed schema per content type. The LLM dynamically generates whatever blueprint structure is needed based on:
1. The task (from intake)
2. The creative brief (from creative direction)
3. The available capabilities (from the capability registry)
4. The selected production plan and budget variant

The blueprint is a **freeform creative document** — the LLM decides what structure makes sense for each unique project. A video blueprint will look nothing like a graphic design blueprint, which will look nothing like a podcast blueprint. And that's by design.

### 6.2 What the Blueprint Contains

The blueprint prompt tells the LLM:
> "Given this creative brief, task description, and available capabilities, generate a detailed execution blueprint. Include whatever creative specifications each production step needs to produce exceptional output. Reference the model knowledge cards for optimal prompting. The blueprint should be professional-grade — the kind of document a senior creative director would hand to their production team."

The LLM generates a JSON document with sections it deems necessary. Examples of what it MIGHT generate (these are examples, not schemas):

- For a viral TikTok: script with hook/body/CTA timing, scene-by-scene storyboard with camera movements, audio map with music energy curve and SFX cue points
- For a 1-hour film: chapter/act breakdown, per-chapter scene storyboards, character consistency notes, continuity plan, dialogue timing
- For a poster: layout wireframe with element positions and hierarchy, typography plan, color scheme application
- For a podcast: segment breakdown with speaker notes, music bed cues, intro/outro scripts
- For motion graphics: keyframe descriptions, first/last frame specifications, transition choreography

### 6.3 How the Blueprint Gets Used

The blueprint is **context** injected into capability prompts during the PRODUCE phase. It does NOT drive execution — the `production_plan` (JSON capability list) drives execution. The blueprint makes each capability step produce better output by providing rich creative context.

```
production_plan → WHAT to execute (ordered capability list)
blueprint       → HOW to execute each step (creative context for prompts)
```

The produce node reads the production_plan step by step, and for each capability call, it extracts the relevant section of the blueprint to inject into the prompt.

---

## 7. Capability Registry

Each capability is a well-tested function that the production executor can call.

### 7.1 Generation Capabilities

| Capability ID | Function | Models | Cost Range | Input | Output |
|---|---|---|---|---|---|
| `image_gen` | Generate scene image | Seedream 4.5, FLUX Dev, Nano Banana Pro | $0.02-0.08 | prompt, neg_prompt, size | image URL |
| `video_gen` | Generate video from image | Veo 3.1, Seedance 1.5, Kling 3.0, Kling O1 Ref | $0.10-0.56 | image_url, prompt, duration | video URL |
| `voiceover` | Text-to-speech | ElevenLabs | ~$0.03 | text, voice_id | audio path |
| `voice_select` | Search/select voice | ElevenLabs | free | criteria (gender, age, energy) | voice_id |
| `voice_clone` | Clone voice from sample | ElevenLabs | free | audio_url | voice_id |
| `music_gen` | Generate background music | Suno (via Kie AI), ElevenLabs | $0.05-0.20 | mood, duration, genre | audio path |
| `sfx_gen` | Generate sound effects | ElevenLabs | ~$0.01 | description | audio path |
| `face_reference` | Process face for consistency | Gemini Flash + internal | ~$0.02 | image_url | character_sheet |
| `first_last_frame` | Generate keyframe pair for motion graphics | Nano Banana Pro | ~$0.06 | prompt for start frame, prompt for end frame | two image URLs (first + last frame for video gen) |

### 7.2 Processing Capabilities

| Capability ID | Function | Tool | Cost | Input | Output |
|---|---|---|---|---|---|
| `audio_mix` | Mix VO + music + SFX | FFmpeg | free | audio paths, volumes | mixed audio path |
| `video_concat` | Concatenate clips | FFmpeg | free | video paths, transitions | concat path |
| `audio_overlay` | Add audio to video | FFmpeg | free | video + audio paths | video path |
| `caption_burn` | Burn captions into video | Whisper + FFmpeg | free | video, style | video path |
| `text_overlay` | Add text to video | FFmpeg | free | video, text, position, timing | video path |
| `image_composite` | Layer images | Pillow/FFmpeg | free | image layers, positions | image path |
| `transcribe` | Audio to text/SRT | faster-whisper | free | audio path | SRT path |

### 7.3 Analysis Capabilities

| Capability ID | Function | Model | Cost | Input | Output |
|---|---|---|---|---|---|
| `analyze_image` | Evaluate image quality | Gemini 2.5 Flash | ~$0.01 | image_url, criteria | score + notes |
| `analyze_video` | Evaluate video quality | Gemini 2.5 Flash | ~$0.02 | video_url, criteria | score + notes |
| `analyze_reference` | Extract visual description from image | Gemini 2.5 Flash (vision) | ~$0.01 | image_url | structured description |
| `analyze_video_reference` | Understand existing video (for recreation/inspiration) | Gemini 2.5 Flash (vision) | ~$0.03 | video_url | scene breakdown, style analysis, timing, transitions, mood |
| `check_consistency` | Compare images for character consistency | Gemini 2.5 Flash (vision) | ~$0.02 | image_urls[], ref | consistency scores |
| `web_search` | Research topic/trends | Tavily | ~$0.01 | query | results |

### 7.4 Model Knowledge Cards

Each model has a knowledge card used by the Creative Direction and Blueprint nodes:

```python
MODEL_CARDS = {
    "seedream-4.5": {
        "type": "image",
        "provider": "fal",
        "endpoint": "fal-ai/bytedance/seedream/v4.5/text-to-image",
        "cost": 0.04,
        "strengths": ["photorealistic faces", "consistent style", "good text rendering"],
        "weaknesses": ["complex multi-character scenes"],
        "best_for": ["portraits", "product shots", "single-subject scenes"],
        "prompt_structure": "Subject → Style → Composition → Lighting → Technical",
        "optimal_length": "30-100 words",
        "supports_negative": True,
        "aspect_ratios": ["16:9", "9:16", "1:1", "4:5"],
        "max_resolution": "1024x1024",
    },
    "veo3.1": {
        "type": "video",
        "provider": "kie",
        "endpoint": "veo3_fast",
        "cost": 0.10,
        "strengths": ["fast generation", "good motion", "cheapest option"],
        "weaknesses": ["shorter clips only", "less detail than premium"],
        "best_for": ["TikTok/Reels", "explainers", "budget projects"],
        "prompt_structure": "Shot → Setting → Subject → Action → Sound",
        "optimal_length": "150-300 characters (short!)",
        "supports_negative": False,
        "duration_range": [4, 8],
        "duration_format": "Xs",  # "8s"
        "supports_first_last_frame": True,
    },
    "seedance-1.5": {
        "type": "video",
        "provider": "fal",
        "endpoint": "fal-ai/bytedance/seedance/v1.5/pro/image-to-video",
        "cost": 0.26,
        "strengths": ["highest motion quality", "fluid motion", "artistic"],
        "weaknesses": ["more expensive", "slower"],
        "best_for": ["YouTube", "music videos", "premium content"],
        "prompt_structure": "Camera → Subject → Environment → Style",
        "optimal_length": "50-150 words",
        "supports_negative": False,
        "duration_range": [4, 12],
        "duration_format": "int",
    },
    "kling-3.0": {
        "type": "video",
        "provider": "fal",
        "endpoint": "fal-ai/kling-video/o3/standard/image-to-video",
        "cost": 0.15,
        "strengths": ["good detail", "multi-subject handling"],
        "weaknesses": ["slower than Veo"],
        "best_for": ["detailed scenes", "multi-subject"],
        "prompt_structure": "Scene → ++Subject++ → Motion → Style (uses ++emphasis++)",
        "optimal_length": "50-200 words",
        "supports_negative": True,
        "duration_range": [5, 10],
        "duration_format": "str_int",
    },
    "kling-o1-ref": {
        "type": "video",
        "provider": "fal",
        "endpoint": "fal-ai/kling-video/o1/reference-to-video",
        "cost": 0.56,
        "strengths": ["character consistency", "face preservation"],
        "weaknesses": ["most expensive", "requires reference images"],
        "best_for": ["character-focused content", "personal branding"],
        "prompt_structure": "Same as Kling 3.0",
        "optimal_length": "50-200 words",
        "supports_negative": True,
        "duration_range": [5, 10],
        "duration_format": "int",
        "requires_reference": True,
    },
    # Nano Banana Pro - for first/last frame generation, motion graphics
    "nano-banana-pro": {
        "type": "image",
        "provider": "nanana",
        "cost": 0.03,
        "strengths": ["fast", "creative", "good for motion graphics frames"],
        "weaknesses": ["less photorealistic than Seedream"],
        "best_for": ["motion graphics", "stylized content", "first/last frames"],
    },
}
```

---

## 8. Quality Gate Protocol

The quality gate runs after every generation step in the PRODUCE phase.

### 8.1 How Gemini Evaluates (Vision/Multimodal Mode)

Gemini 2.5 Flash is used in **vision/multimodal mode** — it doesn't just read metadata, it actually LOOKS at the generated content:

- **Images**: Gemini receives the image directly via its vision API. It sees the actual pixels — can detect deformed faces, extra limbs, style mismatches, composition issues, text rendering problems.
- **Videos**: Gemini receives video frames (or the video file directly if supported). It watches the motion — can detect morphing artifacts, unnatural movement, subject distortion, camera mismatch.
- **Audio**: Gemini receives the audio file. It listens — can assess clarity, pronunciation, pacing, emotional tone, background noise.

For each evaluation, Gemini also receives the creative brief and the specific prompt that generated the content, so it can judge whether the output matches the intent.

### 8.2 Flow

```
Generate asset (image/video/audio)
    ↓
Gemini 2.5 Flash SEES/HEARS the output (vision mode)
    + receives creative brief + original prompt
    ↓
Score: 1-10 on relevant criteria + written analysis of issues
    ↓
├── Score >= 7: PASS → next asset
├── Score < 7, retry < 3:
│     Gemini's written analysis → sent to Claude
│     Claude reads what Gemini saw wrong
│     Claude generates optimized prompt to fix those specific issues
│     Re-generate with better prompt
│     → back to Gemini visual evaluation
├── Score < 7, retry >= 3:
│     Propose model upgrade to user (interrupt)
│     User approves → switch model, retry
│     User declines → keep best attempt
└── Model upgrade failed 2x:
      Show user all attempts
      Options: keep best, change brief, skip this asset
```

### 8.3 Evaluation Criteria by Asset Type

Gemini evaluates using vision mode with these criteria (but is not limited to them — it can flag any issue it sees):

**Images** (Gemini sees the actual image):
- Face match to reference (if applicable): 1-10
- Style consistency with creative brief: 1-10
- Composition quality: 1-10
- Artifact-free (no deformities, extra limbs, weird hands): 1-10
- Text rendering quality (if text in image): 1-10
- Overall: weighted average + written notes on what's wrong

**Videos** (Gemini watches the actual video frames):
- Motion quality (smooth, natural, no jitter): 1-10
- Subject integrity (no morphing/distortion/melting): 1-10
- Visual coherence with source image: 1-10
- Camera movement matches prompt: 1-10
- Temporal consistency (no flickering, no sudden changes): 1-10
- Overall: weighted average + written notes on what's wrong

**Audio** (Gemini listens to the actual audio):
- Clarity and pronunciation: 1-10
- Emotional match to brief: 1-10
- Pacing match to timing plan: 1-10
- Background noise/artifacts: 1-10
- Overall: weighted average + written notes on what's wrong

### 8.4 User Interruption Rules

The quality gate does NOT interrupt the user for every asset. It interrupts ONLY when:
1. It needs permission to switch to a more expensive model
2. It has exhausted all retries and needs user decision
3. A stage is complete (all images done, all videos done, etc.)

Between these points, it generates, evaluates, and retries autonomously.

---

## 9. Budget Variant System

The Creative Direction node generates 3 budget variants:

```json
{
  "budget_variants": [
    {
      "tier": "budget",
      "label": "Fast & Affordable",
      "total_estimate": "$1.50",
      "breakdown": {
        "images": {"model": "seedream-4.5", "count": 5, "cost": "$0.20"},
        "videos": {"model": "veo3.1", "count": 5, "cost": "$0.50"},
        "voiceover": {"model": "elevenlabs", "cost": "$0.03"},
        "music": {"source": "stock", "cost": "$0.00"},
        "llm": {"cost": "$0.10"}
      },
      "tradeoffs": "Faster generation, good for most content. Shorter video clips (max 8s)."
    },
    {
      "tier": "standard",
      "label": "Balanced Quality",
      "total_estimate": "$3.20",
      "breakdown": {
        "images": {"model": "seedream-4.5", "count": 5, "cost": "$0.20"},
        "videos": {"model": "seedance-1.5", "count": 5, "cost": "$1.30"},
        "voiceover": {"model": "elevenlabs", "cost": "$0.03"},
        "music": {"source": "suno", "cost": "$0.10"},
        "sfx": {"source": "elevenlabs", "cost": "$0.05"},
        "llm": {"cost": "$0.10"}
      },
      "tradeoffs": "Best motion quality, longer clips (up to 12s). Recommended for YouTube."
    },
    {
      "tier": "premium",
      "label": "Maximum Quality",
      "total_estimate": "$5.80",
      "breakdown": {
        "images": {"model": "seedream-4.5", "count": 5, "cost": "$0.20"},
        "videos": {"model": "kling-o1-ref", "count": 5, "cost": "$2.80"},
        "voiceover": {"model": "elevenlabs", "cost": "$0.03"},
        "music": {"source": "suno", "cost": "$0.10"},
        "sfx": {"source": "elevenlabs", "cost": "$0.10"},
        "llm": {"cost": "$0.10"}
      },
      "tradeoffs": "Character-consistent video with face reference. Best for personal branding."
    }
  ]
}
```

---

## 10. Long-Form Content Chunking

For content longer than 5 minutes (e.g., a 1-hour film):

1. Blueprint divides content into **chapters** (~5 min each)
2. Each chapter = one full production pipeline pass
3. State tracks `current_chunk` and `total_chunks`
4. After each chunk: user reviews, approves, provides feedback for next
5. Between chunks: the system passes all relevant context (character sheets, style decisions, continuity notes)
6. Final assembly joins all chunks with chapter transitions

```
Chapter 1: blueprint → produce (images → videos → audio) → user review
Chapter 2: blueprint → produce → user review
...
Chapter N: blueprint → produce → user review
→ Full assembly (all chapters) → polish → deliver
```

---

## 11. Project History & Storage

### 11.1 Supabase Schema

```sql
-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    content_type TEXT NOT NULL,  -- "short_video", "long_video", "graphic", etc.
    user_request TEXT,
    creative_brief JSONB,
    production_plan JSONB,
    blueprint JSONB,
    pipeline_stages JSONB,       -- For visualization
    cost_breakdown JSONB,
    total_cost NUMERIC(10,2) DEFAULT 0,
    status TEXT DEFAULT 'active',
    thumbnail_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- Media assets
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    media_type TEXT NOT NULL,    -- "image", "video", "audio", "voiceover", "music", "sfx", "final"
    stage TEXT,                  -- Which production stage created this
    public_url TEXT,
    storage_path TEXT,
    filename TEXT,
    scene_number INT,
    model_used TEXT,
    cost NUMERIC(10,4),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Chat history
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    role TEXT NOT NULL,          -- "user" | "assistant" | "system"
    content TEXT,
    artifacts JSONB,            -- Any attached artifacts
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 11.2 File Structure

```
workspace/{job_id}/
├── uploads/                    # User-uploaded files
├── images/                     # Generated images
│   ├── scene_1.png
│   └── scene_2.png
├── videos/                     # Generated videos
│   ├── scene_1.mp4
│   └── scene_2.mp4
├── audio/
│   ├── voiceover.mp3
│   ├── music.mp3
│   ├── sfx_1.mp3
│   └── mixed.mp3
├── assembly/
│   ├── concatenated.mp4
│   ├── assembled.mp4           # With audio
│   └── polished.mp4            # With captions etc.
└── output/
    ├── final.mp4               # Final output
    └── thumbnail.png
```

---

## 12. Frontend Design

### 12.1 Main Layout

```
┌──────────────────────────────────────────────────────┐
│  Header: AI Production Studio          [History] [+] │
├──────────────┬───────────────────────────────────────┤
│              │                                       │
│  Pipeline    │         Chat / Conversation           │
│  Sidebar     │                                       │
│              │  [Assistant messages]                  │
│  ┌────────┐  │  [Artifact cards]                     │
│  │ Intake │  │  [Image/Video grids]                  │
│  │   ✓    │  │  [Audio players]                      │
│  ├────────┤  │                                       │
│  │Research│  │                                       │
│  │   ✓    │  │                                       │
│  ├────────┤  │                                       │
│  │Creative│  │                                       │
│  │   ✓    │  │                                       │
│  ├────────┤  │                                       │
│  │ Blue-  │  │                                       │
│  │ print  │  │                                       │
│  │   ✓    │  │                                       │
│  ├────────┤  │                                       │
│  │Produce │  │                                       │
│  │ ●●●○○  │  │  ← Progress dots per substep         │
│  │$2.34   │  │  ← Running cost                       │
│  ├────────┤  │                                       │
│  │Assemble│  │                                       │
│  │   ○    │  │                                       │
│  ├────────┤  │                                       │
│  │ Polish │  │                                       │
│  │   ○    │  │                                       │
│  ├────────┤  │                                       │
│  │Deliver │  │                                       │
│  │   ○    │  │                                       │
│  └────────┘  │                                       │
│              │                                       │
│ Total: $2.34 │  [Input bar: type message / approve]  │
│ Est:   $3.20 │                                       │
└──────────────┴───────────────────────────────────────┘
```

### 12.2 Pipeline Sidebar

Visual "snake" showing progress through phases:
- Each phase is a card with status icon (pending ○, active ●, done ✓, failed ✗)
- Active phase shows substeps with dots (●●●○○ = 3/5 images done)
- Running cost per phase and total
- Estimated vs actual cost comparison
- Click a completed phase to scroll to that point in the chat

### 12.3 Key UI Components

**New/Enhanced from v1+v2:**
- `PipelineSidebar` — Visual pipeline progress + cost tracker
- `BudgetSelector` — 3-tier budget variant cards during creative direction
- `BlueprintViewer` — Rich blueprint display (script + storyboard + audio map)
- `QualityGateIndicator` — Shows when quality gate is evaluating/retrying
- `ChunkProgress` — For long-form: "Chapter 3 of 12" progress
- `CostTracker` — Running cost vs estimate bar

**Reuse from v1/v2:**
- `ChatView` (enhanced) — Message + artifact rendering
- `ImageGrid`, `VideoGrid` — Asset grids with regenerate controls
- `ScriptBlock`, `SceneCards` — Blueprint display
- `VoiceoverPlayer`, `FinalVideo` — Media players
- `InputBar` — Approve/modify/regenerate controls
- `TopicForm` (enhanced) — Universal intake form with file upload

---

## 13. Implementation Plan

### Phase 0: Foundation (Days 1-2)

**Goal**: Set up the new project structure, universal state, and basic graph skeleton.

**Tasks**:
1. Create new branch `v3-production-studio`
2. Set up universal `ProductionState` in `backend/agent/state.py`
3. Create graph skeleton with all 8 phases as stub nodes
4. Set up capability registry (`backend/capabilities/registry.py`)
5. Migrate and enhance model cards from v2's `model_registry.py` + `prompt_engineering.py`
6. Set up new API routes (keep v1's SSE pattern, add v2's upload + history endpoints)
7. Update frontend layout with pipeline sidebar placeholder

**Reuse**:
- v1: `config.py`, `main.py`, SSE architecture, session management
- v2: `model_registry.py`, `prompt_engineering.py`, `caption_styles.py`

### Phase 1: Intake + Interview (Days 3-4)

**Goal**: Smart intake that classifies any request and asks intelligent follow-up questions.

**Tasks**:
1. Build `intake_node` — Claude call to parse request into structured project
2. Build `interview_node` — Claude asks follow-up questions (if needed)
3. Add Gemini Flash integration for analyzing uploaded files (images, videos)
4. Build routing logic: needs_research → research, else → creative_direction
5. Frontend: Enhanced `TopicForm` with file upload, rich text input

**Reuse**:
- v2: `visual_qa_tools.py` (Gemini integration pattern)
- v1: `analyze_input.py` node (basic parsing logic)

### Phase 2: Research + Creative Direction (Days 5-7)

**Goal**: Web research, creative brief generation, budget variants.

**Tasks**:
1. Build `research_node` — Tavily web search, trend analysis
2. Build `creative_direction_node` — One sophisticated Claude call that outputs:
   - Creative brief
   - Production plan (JSON capability list)
   - 3 budget variants with model selections and cost estimates
3. Build `review_direction_node` — User reviews brief + selects variant
4. Frontend: `BudgetSelector` component, creative brief display

**Reuse**:
- v2: `search_tools.py` (Tavily integration), `system_prompt.py` (creative direction guidelines, platform presets, content-to-style mapping)

### Phase 3: Blueprint (Days 8-9)

**Goal**: Detailed execution plan generation with model-specific prompting.

**Tasks**:
1. Build `blueprint_node` — Claude generates content-type-specific blueprint
   - For video: script + storyboard + audio map
   - For graphic: layout + elements
   - For audio: script + segment breakdown
2. Integrate v2's prompt engineering for model-specific prompt formatting
3. Build `review_blueprint_node` — User reviews full blueprint
4. Frontend: `BlueprintViewer` component (script, scene cards, audio timeline)

**Reuse**:
- v2: `prompt_engineering.py` (model-specific formatting), `format_for_image_model()`, `format_for_video_model()`
- v1: `claude_service.py` (`generate_script`, `plan_scenes_from_script` — enhanced)

### Phase 4: Production Executor + Quality Gate (Days 10-14)

**Goal**: The core production engine that walks the capability list with quality control.

**Tasks**:
1. Build capability executor — walks `production_plan`, calls capability functions in order
2. Build each capability function wrapping existing services:
   - `image_gen` → `fal_service.generate_image()` with prompt engineering
   - `video_gen` → `video_router.generate_video()` with model-specific formatting
   - `voiceover` → `elevenlabs_service.generate_tts()`
   - `music_gen` → Suno via Kie AI MCP or ElevenLabs
   - `sfx_gen` → ElevenLabs SFX
   - `audio_mix` → `ffmpeg_service` new mix function
   - `face_reference` → Gemini analysis + character sheet
3. Build quality gate node:
   - Gemini Flash evaluation call
   - Prompt optimization with Claude on failure
   - Model escalation logic
   - Retry counting and budget tracking
4. Build `review_stage_node` — User approves at stage boundaries
5. Parallel execution for independent assets (e.g., 5 images simultaneously)
6. Frontend: Progress updates per asset, quality gate indicator

**Reuse**:
- v1: All service files (`fal_service`, `kie_service`, `elevenlabs_service`, `ffmpeg_service`, `whisper_service`, `video_router`)
- v2: `visual_qa_tools.py` (quality evaluation), `video_tools.py` (generate_video pattern), `image_tools.py` (batch generation pattern)
- v2: `audio_tools.py` (extract_audio, replace_audio, mix_audio_layers)

### Phase 5: Assembly + Polish + Deliver (Days 15-17)

**Goal**: Post-production pipeline with transitions, captions, and platform export.

**Tasks**:
1. Build `assemble_node` — FFmpeg concat with transitions from blueprint
2. Build `polish_node`:
   - Caption burning (7 styles from v2)
   - Text overlays (title cards, CTAs)
   - Audio normalization
   - Thumbnail generation
3. Build `deliver_node` — Platform-specific export + metadata
4. User review at assembly and final stages
5. Frontend: Final video player, download button, platform metadata display

**Reuse**:
- v2: `ffmpeg_service.py` (transitions, text overlays, concat_with_transitions)
- v2: `caption_styles.py` (7 preset styles)
- v2: `assembly_tools.py` (assemble_final_video logic)
- v1: `whisper_service.py`, `ffmpeg_service.burn_subtitles()`

### Phase 6: Pipeline Visualization + Cost Tracking (Days 18-19)

**Goal**: Real-time pipeline visualization and cost tracking in the UI.

**Tasks**:
1. Build `PipelineSidebar` component — visual progress through phases
2. Build `CostTracker` — running cost vs estimate comparison
3. SSE events for pipeline stage updates
4. Click-to-scroll from sidebar to chat position
5. Cost breakdown display per stage

### Phase 7: Long-Form Chunking (Days 20-21)

**Goal**: Support for content longer than 5 minutes.

**Tasks**:
1. Blueprint node detects long-form → generates chapter structure
2. Produce node processes chapters sequentially
3. Inter-chunk context passing (character sheets, style, continuity)
4. User review between chunks
5. Final assembly joins all chunks
6. Frontend: Chapter progress indicator

### Phase 8: History + Persistence (Days 22-23)

**Goal**: Full project history with chat linkback.

**Tasks**:
1. Supabase schema (projects, media, chat_messages)
2. Auto-save at each phase boundary
3. History page with project gallery
4. Click project → resume chat session
5. Media gallery per project (all generated assets organized by stage)

**Reuse**:
- v2: `supabase_service.py` (patterns), history page components
- v1: Supabase integration patterns

### Phase 9: Testing + Polish (Days 24-25)

**Tasks**:
1. End-to-end test: TikTok video from topic
2. End-to-end test: YouTube video with face reference
3. End-to-end test: Graphic design (poster)
4. End-to-end test: Long-form (2-3 minute video in chunks)
5. Bug fixes from testing
6. Performance optimization (parallel generation, caching)
7. Error handling and graceful degradation

---

## 14. What We're Reusing (Summary)

### From v1 (~60% of backend services):
- SSE + REST architecture (routes, session management, event queue)
- All service wrappers (fal, kie, elevenlabs, ffmpeg, whisper)
- Model registry and video router
- File management and workspace cleanup
- Config + environment management
- Frontend: ChatView, artifact renderers, InputBar, useSession hook pattern

### From v2 (~40% of intelligence layer):
- Model knowledge cards and prompt engineering (300+ lines)
- Caption styles (7 presets)
- Creative direction guidelines (content-to-style mapping, platform presets)
- Visual QA with Gemini Flash (3 evaluation tools)
- System prompt builder pattern (dynamic state injection)
- Assembly with transitions (14 transition types)
- Audio tools (extract, replace, mix)
- Tool definitions (adapted as capability functions)
- MCP client pattern (for ElevenLabs, fal.ai, Kie AI)

### New code (~40% of total):
- Universal state shape
- 8-phase graph structure with conditional routing
- Intake + interview nodes
- Creative direction with budget variants
- Blueprint generation (content-type-specific)
- Production executor (dynamic capability walking)
- Quality gate supervisor loop
- Long-form chunking
- Pipeline visualization sidebar
- Cost tracking UI
- Enhanced history system

---

## 15. Resolved Questions

1. **MCP vs Direct Service Calls** → **Direct service calls.** Simpler, no subprocess management, lower latency. All generation calls go through our own service wrappers (fal_service, kie_service, elevenlabs_service, etc.).

2. **Gemini model** → **Gemini 2.5 Pro** (`gemini-2.5-pro`). The most advanced model for multimodal analysis. Supports image, video, and audio input via vision mode. State-of-the-art video understanding. Cost: ~$0.03 per quality evaluation (input $1.25/M tokens, output $10.00/M tokens). Used for all quality gate evaluations — this is the "eyes and ears" of the system.

3. **Nano Banana** → Available via Nanana AI MCP tool (`mcp__nanana__text_to_image`). Used for first/last frame generation for motion graphics. ~$0.03/image. Integration via `nanana_service.py`.

4. **Music generation** → Defer to model research session. After skeleton is built, we'll research all available music gen models (Suno, ElevenLabs, others) and find the best quality/cost ratio.

5. **Frontend framework** → **Keep Next.js + Tailwind.** Working v1 frontend with SSE, chat, artifacts. No reason to switch.

## 16. Planned: Model Research Session

After the skeleton is built and the full flow works, we will have a dedicated session to:
- Research every available image/video/audio model across fal.ai, Kie AI, WaveSpeed, and other providers
- Find the cheapest API for each model (same model, different providers)
- Rate each model on quality, speed, and cost
- Document best prompting techniques per model
- Build comprehensive model knowledge cards for the capability registry
- This will update the MODEL_CARDS in the capability registry with real, researched data
