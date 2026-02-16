# Agentic Content Director — Transformation Plan

> Transform the fixed-pipeline AI Content Maker into an autonomous Content Director agent
> that thinks, plans, and executes like a professional production team.

---

## Table of Contents

1. [Vision & Architecture Shift](#1-vision--architecture-shift)
2. [What Changes, What Stays](#2-what-changes-what-stays)
3. [Preparation Steps (Before Starting)](#3-preparation-steps-before-starting)
4. [Phase 0: Foundation — ReAct Agent Loop](#4-phase-0-foundation--react-agent-loop)
5. [Phase 1: Tool Layer — Convert Services to Tools](#5-phase-1-tool-layer--convert-services-to-tools)
6. [Phase 2: MCP Integration — External Tool Servers](#6-phase-2-mcp-integration--external-tool-servers)
7. [Phase 3: Director Intelligence — System Prompt & Planning](#7-phase-3-director-intelligence--system-prompt--planning)
8. [Phase 3.5: Prompting Intelligence Layer](#8-phase-35-prompting-intelligence-layer)
9. [Phase 4: Human-in-the-Loop — Selective Interrupts](#9-phase-4-human-in-the-loop--selective-interrupts)
10. [Phase 5: Frontend — Conversational UI](#10-phase-5-frontend--conversational-ui)
11. [Phase 6: New Capabilities](#11-phase-6-new-capabilities)
12. [Edge Cases & Failure Modes](#12-edge-cases--failure-modes)
13. [File-by-File Change Map](#13-file-by-file-change-map)
14. [CLAUDE.md for the New Project](#14-claudemd-for-the-new-project)
15. [First Prompt for New Claude Session](#15-first-prompt-for-new-claude-session)

---

## 1. Vision & Architecture Shift

### Current: Fixed Pipeline
```
START → analyze → script → review → scenes → review → images → review → videos → review → voiceover → review → assemble → captions → END
```
The graph is hardcoded. Claude has zero decision-making power. Every request follows the same 14-node sequence regardless of what the user asks for.

### Target: Autonomous Content Director
```
User: "Create a 2-minute TikTok video about sleep tips with upbeat music"

Agent thinks: "This needs a 9:16 aspect ratio, ~500 word script, 10-12 scenes,
              background music, animated captions. Let me start with the script..."
Agent acts:   calls write_script(topic="sleep tips", duration=120, style="energetic")
Agent thinks: "Script approved. Now I need scenes. Given 2 min, I'll plan 10 scenes..."
Agent acts:   calls plan_scenes(script=..., count=10, aspect_ratio="9:16")
...continues autonomously, making creative decisions at each step...
```

### The Fundamental Change

| Aspect | Current (Pipeline) | Target (Agent) |
|--------|-------------------|----------------|
| **Decision maker** | Hardcoded graph edges | Claude (via ReAct loop) |
| **Capabilities** | 14 fixed nodes | ~25+ tools Claude can call in any order |
| **User interaction** | Forced review at every stage | Selective — only for expensive/creative decisions |
| **Format flexibility** | 16:9, ~45s, no music | Any aspect ratio, any duration, music, SFX, thumbnails |
| **Error recovery** | Crash → fail | Agent reasons about errors and retries/adapts |
| **State** | Linear progression | Agent tracks complex production state |
| **Extensibility** | Modify graph code | Add a tool (or MCP server) — agent discovers it |

---

## 2. What Changes, What Stays

### KEEP (reuse as-is or with minor modifications)
- `backend/services/fal_service.py` — wrap functions as tools
- `backend/services/kie_service.py` — wrap functions as tools
- `backend/services/elevenlabs_service.py` — wrap as tool
- `backend/services/ffmpeg_service.py` — wrap individual functions as tools
- `backend/services/whisper_service.py` — wrap as tool
- `backend/services/supabase_service.py` — wrap as tools
- `backend/services/model_registry.py` — keep, extend with new models
- `backend/config.py` — keep, add new API keys
- `backend/api/routes.py` — modify SSE/resume to work with agent loop
- `backend/main.py` — minor changes
- `frontend/src/components/artifacts/*` — keep all artifact renderers
- `frontend/src/components/history/*` — keep all history components
- `frontend/src/app/history/page.tsx` — keep
- `frontend/src/lib/api.ts` — extend
- `frontend/src/components/Header.tsx` — keep

### REPLACE
- `backend/agent/graph.py` — replace fixed StateGraph with ReAct agent loop
- `backend/agent/state.py` — replace VideoState with AgentState (extends MessagesState)
- `backend/agent/nodes/*` — replace 14 node files with ~25 `@tool` functions
- `backend/services/claude_service.py` — replace hardcoded prompts with system prompt engineering
- `backend/agent/modification.py` — no longer needed (agent handles modifications via conversation)
- `frontend/src/hooks/useSession.ts` — rewrite for conversational (non-staged) interaction
- `frontend/src/components/chat/ChatView.tsx` — rewrite for agent message stream
- `frontend/src/components/TopicForm.tsx` — simplify (just a text input, agent asks follow-ups)

### DELETE
- `backend/agent/nodes/` directory — all 14 node files (replaced by tools)
- `backend/services/video_router.py` — agent decides model, not a router function

---

## 3. Preparation Steps (Before Starting)

### 3.1 Copy the Project
```bash
cp -r video-ai-agent video-ai-agent-v2
cd video-ai-agent-v2
```

### 3.2 Install New Dependencies
Add to `backend/pyproject.toml`:
```toml
dependencies = [
    # ... existing deps ...
    "langchain-mcp-adapters>=0.1.0",
    "mcp>=1.0.0",
    "langchain-anthropic>=0.3.0",
    "langgraph>=0.4.0",
    "tavily-python>=0.5.0",            # Web search tool
]
```

### 3.3 API Keys — Verify You Have
The new project will need:
- `ANTHROPIC_API_KEY` (existing) — Claude for the agent brain
- `FAL_KEY` (existing) — fal.ai image/video generation (Seedream, Seedance, Veo, Kling via fal)
- `KIE_AI_API_KEY` (existing) — Kie AI video generation (Veo 3.1, Kling 2.6)
- `ELEVENLABS_API_KEY` (existing) — Voice synthesis, music, SFX
- `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` (existing) — History persistence
- `TAVILY_API_KEY` (**NEW**) — Web search for research/reference gathering

**Provider constraint**: Content generation uses ONLY three providers:
- **fal.ai** — Image generation (Seedream 4.5), video generation (Seedance 1.5, Veo 3.1, Kling 3.0)
- **Kie AI** — Video generation (Veo 3.1 fast, Kling 2.6)
- **ElevenLabs** — TTS voiceover, background music, SFX, voice cloning

No Runway, MiniMax, Sora, or any other content generation providers.

### 3.4 CLAUDE.md Strategy
**Delete the current `CLAUDE.md`** before starting the new conversation. The current CLAUDE.md describes the fixed pipeline architecture which will be misleading. After Phase 0 is complete, run `/init` to have Claude generate a new CLAUDE.md that reflects the new agentic architecture.

However, **keep the global `~/.claude/CLAUDE.md`** as-is (it has your git safety rules and n8n instructions — those are still useful).

### 3.5 Clean Git State
```bash
cd video-ai-agent-v2
git checkout -b agentic-rewrite
git add -A && git commit -m "Starting point: copy of v3 pipeline"
```

---

## 4. Phase 0: Foundation — ReAct Agent Loop

**Goal**: Replace the fixed 14-node StateGraph with a ReAct agent loop. No new capabilities yet — just the same features running through an agent instead of a pipeline.

### 4.1 New State: `backend/agent/state.py`

Replace `VideoState` with `AgentState` that extends LangGraph's `MessagesState`:

```python
import operator
from typing import Annotated, NotRequired, Literal
from typing_extensions import TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage


class Scene(TypedDict):
    scene_number: int
    narration: str
    visual_description: str
    image_prompt: str
    duration: float
    image_url: NotRequired[str]
    image_local_path: NotRequired[str]
    video_local_path: NotRequired[str]


class AgentState(TypedDict):
    # === LangGraph agent core (REQUIRED) ===
    messages: Annotated[list[AnyMessage], add_messages]

    # === Session identity ===
    job_id: str

    # === Production parameters (set early, read by tools) ===
    aspect_ratio: str              # "16:9", "9:16", "1:1", "4:5"
    target_duration: int           # target video length in seconds
    video_model: str               # default video model ID
    concat_enabled: bool           # assemble into single video?

    # === Uploads & references ===
    uploaded_files: NotRequired[list[dict]]
    character_description: NotRequired[str]
    reference_images: NotRequired[list[str]]
    character_sheets: NotRequired[list[dict]]  # Continuity lock sheets for character consistency

    # === Production artifacts (populated by tools) ===
    script: NotRequired[str]
    scenes: NotRequired[list[Scene]]
    voiceover_path: NotRequired[str]
    music_path: NotRequired[str]
    assembled_video_path: NotRequired[str]
    captions_srt_path: NotRequired[str]
    final_video_path: NotRequired[str]
    thumbnail_path: NotRequired[str]

    # === Supabase ===
    project_id: NotRequired[str]
    project_name: NotRequired[str]

    # === Tracking ===
    status: NotRequired[str]
    error: NotRequired[str]
```

**Key differences from VideoState**:
- `messages` field with `add_messages` reducer — this is what makes the ReAct loop work
- `aspect_ratio` and `target_duration` — no longer hardcoded
- `music_path` and `thumbnail_path` — new production artifacts
- Removed `progress_messages` — the agent communicates via messages now
- Removed `generation_plan` and `input_topic` — the agent extracts these from conversation

### 4.2 Tools Directory: `backend/agent/tools/`

Create a new directory `backend/agent/tools/` with one file per tool group. Each tool is a `@tool`-decorated function that wraps the existing service calls.

**File: `backend/agent/tools/__init__.py`**
```python
from .script_tools import write_script, modify_script
from .scene_tools import plan_scenes, modify_scenes
from .image_tools import generate_image, generate_all_images
from .video_tools import generate_video, generate_all_videos
from .audio_tools import generate_voiceover, generate_music
from .assembly_tools import assemble_final_video, add_captions
from .project_tools import create_project, save_media_record, update_project_status
from .utility_tools import get_production_status, get_model_info
from .search_tools import web_search, search_references
from .prompt_tools import format_image_prompt, format_video_prompt, get_model_best_practices

ALL_TOOLS = [
    write_script, modify_script,
    plan_scenes, modify_scenes,
    generate_image, generate_all_images,
    generate_video, generate_all_videos,
    generate_voiceover, generate_music,
    assemble_final_video, add_captions,
    create_project, save_media_record, update_project_status,
    get_production_status, get_model_info,
    web_search, search_references,
    format_image_prompt, format_video_prompt, get_model_best_practices,
]
```

**Example tool: `backend/agent/tools/script_tools.py`**
```python
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing import Annotated
from agent.state import AgentState
from services import claude_service


@tool
def write_script(
    topic: str,
    duration_seconds: int,
    style: str = "engaging and conversational",
    platform: str = "youtube",
    state: Annotated[AgentState, InjectedState] = None,
) -> str:
    """Write a narration script for the video.

    Args:
        topic: The subject of the video
        duration_seconds: Target duration in seconds (determines word count)
        style: Tone and style of the narration (e.g., "energetic", "calm", "professional")
        platform: Target platform (youtube, tiktok, instagram, etc.)

    Returns:
        The complete narration script text.
    """
    word_count = int(duration_seconds * 2.5)  # ~2.5 words/sec for narration

    script = claude_service.generate_script_flexible(
        topic=topic,
        word_count=word_count,
        style=style,
        platform=platform,
    )
    return script
```

**Important design decisions for tools**:

1. **Tools return strings** (tool results are ToolMessage content). For structured data, return JSON strings that the agent can parse.

2. **Tools read state via `InjectedState`** for context (job_id, aspect_ratio, etc.) but do NOT mutate state. State updates happen in a post-tool processing node.

3. **Expensive tools** (image gen, video gen, assembly) will include `interrupt()` calls (Phase 4). Cheap tools (write_script, plan_scenes, get_status) run without interrupts.

4. **Batch tools** exist alongside single-item tools: `generate_image` (one scene) vs `generate_all_images` (all scenes). The agent decides which to use based on context.

### 4.3 New Graph: `backend/agent/graph.py`

Replace the fixed pipeline with a ReAct agent loop:

```python
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from agent.state import AgentState
from agent.tools import ALL_TOOLS
from agent.system_prompt import build_system_prompt


def build_graph():
    model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        temperature=0.7,  # creative tasks benefit from some temperature
    )
    model_with_tools = model.bind_tools(ALL_TOOLS)

    def call_model(state: AgentState):
        system_prompt = build_system_prompt(state)
        messages = [{"role": "system", "content": system_prompt}] + state["messages"]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    def post_tool_update(state: AgentState):
        """After tool execution, parse tool results and update production state."""
        # Check the last message — if it's a ToolMessage with structured data,
        # extract state updates (scenes, script, paths, etc.)
        last_msg = state["messages"][-1]
        updates = {}
        # ... parse tool results and update state fields ...
        return updates

    builder = StateGraph(AgentState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(ALL_TOOLS))
    builder.add_node("post_tool", post_tool_update)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "post_tool")
    builder.add_edge("post_tool", "agent")

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


graph = build_graph()
```

**Key architecture points**:

- **3 nodes instead of 14**: `agent` (LLM), `tools` (execution), `post_tool` (state updates)
- **`tools_condition`**: Routes to `tools` if LLM returned tool_calls, else to `END`
- **`post_tool` node**: Parses tool results and updates AgentState fields (scenes, script, paths). This is necessary because tools return strings, not state dicts.
- **`build_system_prompt(state)`**: Dynamically injects production state into the system prompt so Claude knows what's been done and what's pending.

### 4.4 System Prompt: `backend/agent/system_prompt.py`

This is the **brain** of the agent — the most important file in the new architecture:

```python
from agent.state import AgentState
from services.model_registry import get_model_description_for_llm


def build_system_prompt(state: AgentState) -> str:
    """Build dynamic system prompt with current production state."""

    model_info = get_model_description_for_llm()

    # Build production status summary
    status_parts = []
    if state.get("script"):
        status_parts.append(f"Script: DONE ({len(state['script'].split())} words)")
    if state.get("scenes"):
        n_scenes = len(state["scenes"])
        n_with_images = sum(1 for s in state["scenes"] if s.get("image_url"))
        n_with_videos = sum(1 for s in state["scenes"] if s.get("video_local_path"))
        status_parts.append(f"Scenes: {n_scenes} planned, {n_with_images} images, {n_with_videos} videos")
    if state.get("voiceover_path"):
        status_parts.append("Voiceover: DONE")
    if state.get("music_path"):
        status_parts.append("Music: DONE")
    if state.get("final_video_path"):
        status_parts.append("Final video: DONE")

    production_status = "\n".join(status_parts) if status_parts else "Nothing produced yet."

    return f"""You are an elite AI Content Director — the creative brain behind a professional
video production team. You have a suite of production tools at your disposal and you make
all creative and technical decisions autonomously.

## Your Role
You are NOT a chatbot. You are a director who:
1. Understands the client's vision (ask clarifying questions if needed)
2. Plans the production (script, scenes, visual style, audio)
3. Executes each production step using your tools
4. Reviews your own output and iterates until quality is professional-grade
5. Delivers a polished final product

## Production Pipeline (follow this professional workflow)
1. **Creative Brief**: Understand the request. Ask about: target audience, platform,
   tone/mood, duration, aspect ratio, special requirements. If the user gives a simple
   topic, make smart default choices and tell them what you've decided.
2. **Script Writing**: Write the narration script. Match duration to word count (~2.5 words/sec).
3. **Scene Planning**: Break script into visual scenes with detailed cinematography notes.
4. **Image Generation**: Generate a key frame image for each scene.
5. **Video Generation**: Animate each scene image into a video clip.
6. **Audio Production**: Generate voiceover narration. Optionally generate background music.
7. **Post-Production**: Assemble all clips, overlay audio, add captions.
8. **Delivery**: Present the final video to the client.

You can deviate from this order when it makes sense (e.g., regenerate a single scene's
image without redoing everything else).

## Current Production State
Job ID: {state.get("job_id", "not set")}
Aspect Ratio: {state.get("aspect_ratio", "not set")}
Target Duration: {state.get("target_duration", "not set")}s
Video Model: {state.get("video_model", "not set")}
Concat Enabled: {state.get("concat_enabled", True)}

{production_status}

## Available Models
{model_info}

## Provider Constraint
You may ONLY use these three providers for content generation:
- fal.ai (Seedream 4.5 images, Seedance 1.5 / Veo 3.1 / Kling 3.0 videos)
- Kie AI (Veo 3.1 fast/quality, Kling 2.6 videos)
- ElevenLabs (TTS voiceover, background music, SFX, voice cloning)
Do NOT use Runway, MiniMax, Sora, Midjourney, or any other provider.

## Prompting Rules
- ALWAYS call format_image_prompt / format_video_prompt before generating any media.
  These tools optimize prompts for each model's unique optimal structure and vocabulary.
- ALWAYS call web_search before writing scripts on factual topics to ensure accuracy.
- Use get_model_best_practices to check prompt length/structure before calling a new model.
- Maintain character consistency by using identical description tokens across all scenes.

## Rules
- ALWAYS create a Supabase project first (call create_project) before generating any media.
- After generating images or videos, call save_media_record to persist them.
- When the user approves a step, move forward. When they request changes, use the
  appropriate modification tool.
- For expensive operations (image gen, video gen, assembly), explain what you're about
  to do and why BEFORE calling the tool, so the user can intervene.
- If a tool fails, analyze the error and try an alternative approach.
- Always track costs mentally. If a user's request would cost >$5, warn them.
- Present all generated media to the user for review before moving to the next step.
"""
```

### 4.5 Backend API Changes: `backend/api/routes.py`

The SSE/resume pattern needs to change because the agent loop works differently from fixed nodes:

**Current flow**:
1. POST `/api/sessions` → starts graph, runs until first interrupt
2. GET `/api/sessions/{id}/events` → SSE stream of events
3. POST `/api/sessions/{id}/resume` → resumes graph with user action (approve/modify)

**New flow**:
1. POST `/api/sessions` → creates session, sends initial user message to agent
2. GET `/api/sessions/{id}/events` → SSE stream of agent messages + tool events
3. POST `/api/sessions/{id}/message` → sends user message to agent (replaces /resume)

The key change: instead of `Command(resume={"action": "approve"})`, we send a regular human message like `"Looks great, proceed"` or `"Change scene 2 to be more dramatic"`. The agent interprets this naturally.

For interrupt-based reviews (Phase 4), we still use `Command(resume=...)` but only for explicit approve/reject on expensive operations.

```python
# New endpoint (replaces /resume for conversational messages)
@router.post("/api/sessions/{session_id}/message")
async def send_message(session_id: str, body: dict):
    """Send a user message to the agent."""
    message = body.get("message", "")

    config = {"configurable": {"thread_id": session_id}}

    # Check if there's a pending interrupt (expensive tool awaiting approval)
    state = graph.get_state(config)
    if state.tasks and any(t.interrupts for t in state.tasks):
        # Resume the interrupt with the user's response
        action = body.get("action", "approve")  # approve, reject, or modify
        graph.invoke(
            Command(resume={"action": action, "message": message}),
            config
        )
    else:
        # Regular message — add to conversation and let agent continue
        graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config
        )
```

### 4.6 Streaming Events

The agent loop emits different events than the fixed pipeline. We need to map them:

| Agent Event | Frontend Event | Description |
|------------|----------------|-------------|
| AIMessage (text only) | `message` | Agent's conversational response |
| AIMessage (tool_calls) | `progress` | Agent is about to do something |
| ToolMessage | `artifact` or `progress` | Tool completed, result available |
| interrupt() | `awaiting` | Agent paused for user approval |
| No more tool_calls | `complete` | Agent is done |

Use LangGraph's `astream_events` (v2) to get fine-grained streaming:

```python
async for event in graph.astream_events(input, config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        # Token-by-token streaming of agent's response
        chunk = event["data"]["chunk"]
        if chunk.content:
            yield sse_event("message_token", {"text": chunk.content})

    elif event["event"] == "on_tool_start":
        tool_name = event["name"]
        yield sse_event("progress", {"message": f"Running {tool_name}..."})

    elif event["event"] == "on_tool_end":
        result = event["data"]["output"]
        yield sse_event("artifact", parse_tool_result(tool_name, result))
```

---

## 5. Phase 1: Tool Layer — Convert Services to Tools

### 5.1 Tool Groups

Create these files in `backend/agent/tools/`:

#### `script_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `write_script` | `claude_service.generate_script_flexible()` | Write narration script with configurable duration/style |
| `modify_script` | `claude_service.modify_script()` | Edit script based on feedback |

#### `scene_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `plan_scenes` | `claude_service.plan_scenes_flexible()` | Plan visual scenes from script |
| `modify_scenes` | `claude_service.modify_scenes()` | Edit scene descriptions |

#### `image_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `generate_image` | `fal_service.generate_image()` | Generate single scene image |
| `generate_all_images` | Loop over scenes | Generate images for all scenes |
| `generate_image_flux` | `fal_service.generate_image_flux()` | Image-to-image with FLUX (for references) |

#### `video_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `generate_video` | `fal_service.generate_video()` or `kie_service.*` | Generate single scene video |
| `generate_all_videos` | Loop over scenes | Generate videos for all scenes (sequential or parallel) |

#### `audio_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `generate_voiceover` | `elevenlabs_service.generate_tts()` | Generate TTS voiceover |
| `generate_music` | ElevenLabs MCP `compose_music` | Generate background music |
| `list_voices` | NEW | List available ElevenLabs voices |

#### `assembly_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `assemble_final_video` | `ffmpeg_service.concat_videos()` + `overlay_audio()` | Combine clips + audio |
| `add_captions` | `whisper_service.transcribe_to_srt()` + `ffmpeg_service.burn_subtitles()` | Add captions |
| `mix_audio` | NEW `ffmpeg_service.mix_audio_tracks()` | Mix voiceover + music |

#### `project_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `create_project` | `supabase_service.create_project()` | Create Supabase project folder |
| `save_media_record` | `supabase_service.create_media_record()` | Save generated media to DB |
| `upload_to_storage` | `supabase_service.upload_file()` | Upload file to Supabase Storage |
| `update_project_status` | `supabase_service.update_project()` | Update project status |

#### `utility_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `get_production_status` | Reads AgentState via InjectedState | Returns current production state summary |
| `get_model_info` | `model_registry.get_model_description_for_llm()` | Get available models + costs |
| `estimate_cost` | Calculation based on scene count + model | Estimate total production cost |

#### `search_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `web_search` | `tavily_client.search()` | Search the web for topic research, trends, reference material |
| `search_references` | `tavily_client.search()` + filtering | Search for visual references, style guides, or platform best practices |

#### `prompt_tools.py`
| Tool | Wraps | Description |
|------|-------|-------------|
| `format_image_prompt` | `prompt_engineering.format_for_image_model()` | Format scene description into model-optimized image prompt |
| `format_video_prompt` | `prompt_engineering.format_for_video_model()` | Format scene into model-optimized video prompt with camera/motion |
| `get_model_best_practices` | `prompt_engineering.get_best_practices()` | Get optimal prompt structure, length, and vocabulary for a specific model |

### 5.2 Claude Service Changes: `backend/services/claude_service.py`

The current `claude_service.py` has hardcoded prompts (45s, 120-150 words, 4-6 scenes). Replace with flexible versions:

```python
def generate_script_flexible(
    topic: str,
    word_count: int,
    style: str = "engaging",
    platform: str = "youtube",
    additional_instructions: str = "",
) -> str:
    """Generate a narration script with configurable parameters."""
    prompt = f"""Write a narration script for a {platform} video about: {topic}

Requirements:
- Target length: approximately {word_count} words (~{word_count // 2.5:.0f} seconds when spoken)
- Tone/style: {style}
- Platform: {platform} (optimize for this platform's audience)
- Write ONLY the narration text. No stage directions, no scene descriptions.
- Must flow naturally when read aloud.
{additional_instructions}
"""
    # ... call Claude API ...


def plan_scenes_flexible(
    script: str,
    scene_count: int,
    aspect_ratio: str = "16:9",
    style_notes: str = "",
) -> list[dict]:
    """Plan visual scenes with configurable count and aspect ratio."""
    prompt = f"""Break this script into exactly {scene_count} visual scenes.

Aspect ratio: {aspect_ratio} — frame all compositions for this ratio.
{f"Style notes: {style_notes}" if style_notes else ""}

For each scene, provide:
- narration: the exact script text for this scene
- visual_description: detailed shot description (camera angle, lighting, mood, motion)
- image_prompt: optimized prompt for AI image generation
- duration: seconds (match narration length, ~2.5 words/sec)

Script:
{script}
"""
    # ... call Claude API, return structured scenes ...
```

### 5.3 Service Modifications

**`fal_service.py`** — Add `aspect_ratio` parameter to `generate_image()` and `generate_video()`:
```python
# Map aspect ratios to fal.ai image sizes
ASPECT_RATIO_MAP = {
    "16:9": {"width": 1280, "height": 720},
    "9:16": {"width": 720, "height": 1280},
    "1:1":  {"width": 1024, "height": 1024},
    "4:5":  {"width": 896, "height": 1120},
}
```

**`kie_service.py`** — Already accepts `aspect_ratio` parameter. Just pass it through.

**`ffmpeg_service.py`** — Make `concat_videos()` and `burn_subtitles()` aspect-ratio-aware:
```python
def get_resolution_for_ratio(aspect_ratio: str) -> tuple[int, int]:
    return {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}[aspect_ratio]
```

---

## 6. Phase 2: MCP Integration — External Tool Servers

### 6.1 MCP Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     Agent (LangGraph)                          │
│  ┌───────────┐  ┌───────────────┐  ┌────────────────────────┐│
│  │ Local      │  │ MCP Tools     │  │ MCP Tools              ││
│  │ @tools     │  │ (adapter)     │  │ (adapter)              ││
│  └───────────┘  └──────┬────────┘  └───────────┬────────────┘│
└─────────────────────────┼──────────────────────┼─────────────┘
                          │                      │
                 ┌────────▼────────┐  ┌──────────▼──────────┐
                 │ ElevenLabs      │  │ Custom FastMCP       │
                 │ Official MCP    │  │ Server               │
                 │ (@anthropic/    │  │ (wraps fal.ai +      │
                 │  elevenlabs-mcp)│  │  Kie AI services)    │
                 │ stdio           │  │ stdio                │
                 └─────────────────┘  └─────────────────────┘
```

### 6.2 MCP Strategy — Why NOT Community Servers

**Research findings on community MCP servers**:
- **fal.ai** (`raveenb/fal-ai-mcp-server`): 30 stars, 23 open issues, stale since Jan 2025 — **SKIP**
- **Kie AI** (`felores/kie-ai-mcp-server`): 11 stars, single developer, minimal maintenance — **SKIP**
- **Runway** — Not needed (provider not used)
- **MiniMax** — Not needed (provider not used)

**Decision**: Use ElevenLabs official MCP (1,203 stars, 24 tools, maintained by Anthropic) + build a **custom FastMCP server** that wraps our existing `fal_service.py` and `kie_service.py`. This gives us:
- Full control over error handling, retries, and timeouts
- No dependency on unmaintained community code
- Same API surface as MCP but with our battle-tested service layer underneath

### 6.3 MCP Server Catalog

| Server | Type | Transport | What It Provides |
|--------|------|-----------|-----------------|
| **ElevenLabs** (official) | `@anthropic/elevenlabs-mcp` | stdio | 24 tools: TTS, voice search, SFX, music gen, voice cloning, speech-to-speech, audio isolation |
| **Custom FastMCP** (ours) | `backend/mcp_server/` | stdio | Wraps fal.ai + Kie AI: image gen, video gen, model listing |

### 6.4 ElevenLabs MCP — Full Tool Inventory

The official ElevenLabs MCP (`@anthropic/elevenlabs-mcp`, 1,203 stars) provides:

| Tool | Description | Replaces Local? |
|------|-------------|----------------|
| `text_to_speech` | Convert text to speech with any voice | Yes — replaces `elevenlabs_service.generate_tts()` |
| `search_voices` | Search ElevenLabs voice library | NEW capability |
| `get_voice_info` | Get voice details + preview | NEW capability |
| `voice_clone` | Clone a voice from audio samples | NEW capability |
| `text_to_sound_effects` | Generate SFX from text description | NEW capability |
| `compose_music` | AI music composition | NEW capability |
| `speech_to_speech` | Voice-to-voice conversion | NEW capability |
| `isolate_audio` | Remove background noise | NEW capability |
| `dub_content` | Automatic dubbing/translation | NEW capability |

### 6.5 Custom FastMCP Server: `backend/mcp_server/server.py`

Build a custom MCP server using FastMCP (22,678 stars, ~70% MCP market share):

```python
"""Custom MCP server wrapping fal.ai and Kie AI services."""

from mcp.server.fastmcp import FastMCP
from services import fal_service, kie_service

mcp = FastMCP("content-generation")


@mcp.tool()
def generate_image_seedream(
    prompt: str,
    aspect_ratio: str = "16:9",
    negative_prompt: str = "",
) -> str:
    """Generate an image using Seedream 4.5 (fal.ai).
    Cost: ~$0.04/image. Best for: photorealistic scenes, product shots.
    Optimal prompt: 30-100 words, Subject → Style → Composition → Lighting → Technical.
    """
    result = fal_service.generate_image(prompt, aspect_ratio=aspect_ratio)
    return json.dumps({"image_url": result, "model": "seedream-4.5", "cost": 0.04})


@mcp.tool()
def generate_video_veo3(
    prompt: str,
    image_url: str | None = None,
    aspect_ratio: str = "16:9",
    model: str = "veo3_fast",
) -> str:
    """Generate video using Veo 3.1 via Kie AI.
    Cost: ~$0.08 (fast) / ~$0.25 (quality). Duration: 8s fixed.
    Optimal prompt: 150-300 chars, Shot → Setting → Subject → Action.
    """
    result = kie_service.generate_video_veo3(prompt, image_url=image_url, aspect_ratio=aspect_ratio, model=model)
    return json.dumps({"video_url": result["video"]["url"], "model": f"veo3.1-{model}", "cost": 0.08 if model == "veo3_fast" else 0.25})


@mcp.tool()
def generate_video_kling(
    prompt: str,
    image_url: str | None = None,
    duration: int = 5,
    aspect_ratio: str = "16:9",
) -> str:
    """Generate video using Kling 2.6 via Kie AI.
    Cost: ~$0.15/video. Duration: 5 or 10 seconds.
    Optimal prompt: 4 parts — Scene → Subject → Motion → Style. Supports ++emphasis++.
    """
    result = kie_service.generate_video_kling(prompt, image_url=image_url, duration=duration, aspect_ratio=aspect_ratio)
    return json.dumps({"video_url": result["video"]["url"], "model": "kling-2.6", "cost": 0.15})


@mcp.tool()
def generate_video_seedance(
    prompt: str,
    image_url: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
) -> str:
    """Generate video using Seedance 1.5 via fal.ai.
    Cost: ~$0.26/video. Duration: 5 or 10 seconds. Requires image input.
    Best for: highest motion quality, artistic/cinematic content.
    """
    result = fal_service.generate_video(prompt, image_url=image_url, model="seedance", duration=duration, aspect_ratio=aspect_ratio)
    return json.dumps({"video_path": result, "model": "seedance-1.5", "cost": 0.26})


@mcp.tool()
def list_available_models() -> str:
    """List all available image and video generation models with their costs and capabilities."""
    from services.model_registry import VIDEO_MODELS, IMAGE_MODELS
    return json.dumps({"video_models": VIDEO_MODELS, "image_models": IMAGE_MODELS})
```

### 6.6 MCP Client Setup: `backend/agent/mcp_client.py`

```python
"""MCP client manager — connects to external tool servers."""

from langchain_mcp_adapters.client import MultiServerMCPClient
from config import settings


def get_mcp_config() -> dict:
    """Build MCP server configuration from environment."""
    servers = {}

    # ElevenLabs Official MCP (24 tools: TTS, voice search, SFX, music, cloning)
    if settings.ELEVENLABS_API_KEY:
        servers["elevenlabs"] = {
            "command": "npx",
            "args": ["-y", "@anthropic/elevenlabs-mcp"],
            "transport": "stdio",
            "env": {
                "ELEVENLABS_API_KEY": settings.ELEVENLABS_API_KEY,
            },
        }

    # Custom FastMCP server (wraps fal.ai + Kie AI — our own code, full control)
    servers["content_generation"] = {
        "command": "python",
        "args": ["-m", "mcp_server.server"],
        "transport": "stdio",
        "env": {
            "FAL_KEY": settings.FAL_KEY,
            "KIE_AI_API_KEY": settings.KIE_AI_API_KEY,
        },
    }

    return servers


async def load_mcp_tools() -> list:
    """Load tools from all configured MCP servers."""
    config = get_mcp_config()
    if not config:
        return []

    client = MultiServerMCPClient(config)
    tools = await client.get_tools()
    return tools
```

### 6.7 Combining Local Tools + MCP Tools

In `graph.py`, combine both tool sources:

```python
from agent.tools import ALL_TOOLS as LOCAL_TOOLS
from agent.mcp_client import load_mcp_tools

async def build_graph():
    mcp_tools = await load_mcp_tools()
    all_tools = LOCAL_TOOLS + mcp_tools

    model = ChatAnthropic(model="claude-sonnet-4-5-20250929", max_tokens=8192)
    model_with_tools = model.bind_tools(all_tools)
    # ... rest of graph setup ...
```

### 6.8 MCP vs Local — Decision Matrix

| Capability | Use Local @tool | Use MCP | Why |
|-----------|----------------|---------|-----|
| Script writing | Yes | No | Needs deep state access (InjectedState) |
| Scene planning | Yes | No | Needs state access |
| Prompt formatting | Yes | No | Needs embedded model knowledge |
| Web search (Tavily) | Yes | No | Simple API, no MCP overhead needed |
| Image generation (fal.ai) | No | **Custom MCP** | Unified MCP interface for all generation |
| Video generation (fal.ai) | No | **Custom MCP** | Same custom server |
| Video generation (Kie AI) | No | **Custom MCP** | Same custom server |
| Voiceover (ElevenLabs) | No | **Official MCP** | 24 tools: voice search, SFX, music, cloning |
| Background music | No | **Official MCP** | ElevenLabs `compose_music` tool |
| Sound effects | No | **Official MCP** | ElevenLabs `text_to_sound_effects` tool |
| Voice search/cloning | No | **Official MCP** | ElevenLabs `search_voices`, `voice_clone` |
| FFmpeg operations | Yes | No | Local CLI tool, no API needed |
| Whisper transcription | Yes | No | Local model, no API needed |
| Supabase operations | Yes | No | Direct DB access needed |

**Strategy**: MCP for all external API calls (generation + audio). Local @tools for state management, prompt engineering, search, and local operations (FFmpeg, Whisper, Supabase).

---

## 7. Phase 3: Director Intelligence — System Prompt & Planning

### 7.1 The Director Persona

The system prompt (Section 4.4) is the most critical component. It should encode:

1. **Professional production knowledge**: Camera angles, lighting, pacing, platform-specific best practices
2. **Creative decision-making**: When to use which model, how many scenes for a given duration, when to suggest music
3. **Cost awareness**: Track costs mentally, warn before expensive operations
4. **Self-evaluation**: After generating content, the agent should assess quality and suggest improvements

### 7.2 Production Planning

When a user makes a request, the agent should first create an internal production plan:

```
User: "Make a 2-minute TikTok about morning routines"

Agent thinks:
- Platform: TikTok → 9:16 aspect ratio, fast pacing, hook in first 3 seconds
- Duration: 120s → ~300 words script, 10-12 scenes, 8-10s per scene
- Style: Energetic, quick cuts, trendy
- Video model: Veo 3.1 Fast (best value for TikTok content)
- Audio: Voiceover + upbeat background music
- Estimated cost: 12 images ($0.48) + 12 videos ($1.20) + voiceover ($0.10) ≈ $1.78
```

The agent communicates this plan to the user before starting, giving them a chance to adjust.

### 7.3 Smart Model Selection

Encode model selection logic in the system prompt:

```
PROVIDER CONSTRAINT: You may ONLY use these three providers for content generation:
- fal.ai (Seedream 4.5 images, Seedance 1.5 / Veo 3.1 / Kling 3.0 videos)
- Kie AI (Veo 3.1 fast/quality, Kling 2.6 videos)
- ElevenLabs (TTS voiceover, background music, SFX, voice cloning)
Do NOT use Runway, MiniMax, Sora, Midjourney, or any other provider.

Model selection guidelines:
- TikTok/Reels (9:16, <60s): Veo 3.1 Fast via Kie AI — fast, cheapest, good quality
- YouTube (16:9, 1-5min): Seedance 1.5 via fal.ai — highest motion quality
- Character-focused content: Kling O1 Reference via fal.ai — character consistency support
- Music videos / artistic: Seedance 1.5 via fal.ai — best fluid motion
- Explainer / tutorial: Veo 3.1 Fast via Kie AI — save budget for more scenes
- High detail scenes: Kling 2.6 via Kie AI — best multi-subject handling

ALWAYS call format_image_prompt / format_video_prompt before generating media.
These tools optimize prompts for each specific model's strengths and format.

ALWAYS call web_search before writing a script on any factual topic.
Research ensures accuracy and up-to-date information.
```

### 7.4 Self-Evaluation Loop

After generating content, the agent should evaluate before presenting to the user:

```python
@tool
def evaluate_scene_images(
    state: Annotated[AgentState, InjectedState] = None,
) -> str:
    """Evaluate generated scene images for quality and consistency.
    Returns assessment and suggested improvements."""
    scenes = state.get("scenes", [])
    # Use Claude vision to evaluate images
    # Return structured assessment
```

---

## 8. Phase 3.5: Prompting Intelligence Layer

### 8.1 Why This Matters

Every AI image/video model has a unique "prompt language" — optimal length, structure, vocabulary, and formatting. Sending the same generic prompt to Seedream 4.5, Veo 3.1, and Kling 2.6 leaves 30-50% of quality on the table. The prompting layer converts structured scene data into model-optimized prompts.

### 8.2 Research Findings on Prompt Frameworks

**SEALCaM** (Subject, Environment, Action, Lighting, Camera, Metatokens) — widely shared but NOT an industry standard. It's a ChatGPT GPT Store custom GPT, not peer-reviewed or adopted by model vendors. Useful as a starting vocabulary but not as a framework to follow rigidly.

**Shot Grammar Framework** (TrueFan, 2026) — the most comprehensive scaffold for AI video production:
1. Subject & Action (who, doing what)
2. Emotional Energy (mood, tension, tone)
3. Camera Optics (lens, focal length, depth of field)
4. Motion (camera movement, subject movement)
5. Lighting Physics (direction, quality, color temperature)
6. Style & Color Science (film stock, grade, palette)
7. Audio Targets (soundtrack cues, ambient sound)
8. Continuity Constraints (match previous shots, character consistency)

**Key finding**: "Format doesn't determine quality — clarity does." JSON vs XML vs natural language doesn't matter to models. Use **JSON internally** for structured planning, then **render to model-optimal natural language** for actual prompts.

### 8.3 Model-Specific Prompt Structures

Each model has a documented optimal prompt structure:

#### Seedream 4.5 (fal.ai — Image Generation)
- **Structure**: Subject → Style → Composition → Lighting → Technical
- **Optimal length**: 30-100 words
- **Supports**: Negative prompts (separate field)
- **Tips**: Front-load the subject. Use photographic terms (f/2.8, 85mm lens). Avoid abstract concepts.

#### Veo 3.1 (Kie AI — Video Generation)
- **Structure**: Shot type → Setting → Subject → Action → Dialogue/Sound
- **Optimal length**: 150-300 characters (NOT words — chars)
- **Duration**: Fixed 8 seconds
- **Tips**: Be specific about camera movement. Use one continuous action per prompt. Veo excels at realistic motion.

#### Kling 2.6 (Kie AI — Video Generation)
- **Structure**: Scene → Subject → Motion → Style
- **Optimal length**: 50-200 words
- **Duration**: 5 or 10 seconds
- **Supports**: `++emphasis++` notation for important elements, negative prompts (aggressive — use 3-7 items)
- **Tips**: Describe motion explicitly (direction, speed, acceleration). Kling handles complex multi-subject scenes well.

#### Seedance 1.5 (fal.ai — Video Generation)
- **Structure**: Camera movement → Subject action → Environment → Style
- **Optimal length**: 50-150 words
- **Duration**: 5 or 10 seconds
- **Tips**: Seedance has the best motion quality. Emphasize camera movement and fluid motion in prompts. Always requires an input image.

### 8.4 Cinematography Vocabulary

**Camera terms that reliably work across models**:
- Movements: dolly in/out, pan left/right, tilt up/down, tracking shot, crane shot, arc shot, steadicam, handheld, aerial/drone, push-in, pull-back
- Angles: low angle, high angle, bird's eye, Dutch angle, eye level, over-the-shoulder
- Shots: extreme close-up, close-up, medium close-up, medium shot, medium wide, wide shot, extreme wide, establishing shot

**Lighting terms that work**:
- Natural: golden hour, blue hour, overcast, harsh midday, dappled light
- Studio: Rembrandt lighting, butterfly lighting, split lighting, rim light, backlit, three-point lighting
- Atmospheric: volumetric light, god rays, neon glow, candlelight, firelight
- Technical: high key, low key, chiaroscuro, silhouette

**Style terms that work**:
- Film: anamorphic, film grain, 35mm, 70mm IMAX, Kodak Portra, Fujifilm
- Digital: 8K, hyperrealistic, photorealistic, cinematic color grade
- Artistic: oil painting, watercolor, anime, cel-shaded, vaporwave, cyberpunk

### 8.5 Character Consistency Techniques

Maintaining visual consistency for characters across multiple scenes:

1. **Token Anchoring**: Use the exact same character description (verbatim) in every prompt. Even minor wording changes cause drift.
2. **Reference Images**: Use 2-3 reference images per character. Kling O1 Reference model supports this natively.
3. **Seed Locking**: Where supported, use the same seed value for consistent outputs.
4. **Continuity Lock Sheet**: Maintain a JSON document per character:
```json
{
  "character_id": "narrator_01",
  "description": "A 30-year-old woman with shoulder-length auburn hair, green eyes, wearing a navy blue blazer over a white blouse",
  "locked_tokens": "30-year-old woman, shoulder-length auburn hair, green eyes, navy blue blazer, white blouse",
  "reference_image_urls": ["url1", "url2"],
  "seed": 42
}
```

### 8.6 Negative Prompt Guidelines

| Model | Negative Prompt Support | Recommendations |
|-------|------------------------|-----------------|
| Seedream 4.5 | Dedicated `negative_prompt` field | Use 3-7 items: "blurry, low quality, distorted face, watermark, text overlay" |
| Kling 2.6 | Supports aggressively | Use 3-7 items, be specific: "static camera, frozen motion, jittery, morphing" |
| Veo 3.1 | Dedicated fields available | Minimal — Veo responds better to positive framing |
| Seedance 1.5 | Limited support | Prefer positive framing. Focus on what you WANT, not what to avoid |

### 8.7 New File: `backend/services/prompt_engineering.py`

```python
"""Model-specific prompt engineering and formatting.

Converts structured scene JSON into model-optimized natural language prompts.
Each model has a unique optimal prompt structure, length, and vocabulary.
"""

import json
from typing import Optional


# ── Internal Scene Schema ──────────────────────────────────────────────
# This JSON schema is used internally by the agent to plan scenes.
# It captures all cinematic elements before model-specific formatting.

SCENE_SCHEMA = {
    "scene_number": int,
    "narration": str,                    # Voiceover text for this scene
    "subject": str,                      # Who/what is in the scene
    "action": str,                       # What is happening
    "environment": str,                  # Setting/location
    "camera": {
        "shot_type": str,                # wide, medium, close-up, etc.
        "movement": str,                 # dolly, pan, static, tracking, etc.
        "angle": str,                    # eye level, low angle, high angle, etc.
    },
    "lighting": str,                     # golden hour, studio, neon, etc.
    "mood": str,                         # energetic, calm, dramatic, etc.
    "style": str,                        # photorealistic, cinematic, artistic, etc.
    "duration": float,                   # seconds
    "continuity_notes": str,             # What must match previous scene
    "negative_elements": list[str],      # What to avoid
}


# ── Model Best Practices Database ──────────────────────────────────────

MODEL_BEST_PRACTICES = {
    "seedream-4.5": {
        "provider": "fal.ai",
        "type": "image",
        "optimal_length": "30-100 words",
        "structure": "Subject → Style → Composition → Lighting → Technical",
        "supports_negative": True,
        "tips": [
            "Front-load the subject — first phrase is most influential",
            "Use photographic terms: '85mm lens, f/2.8, shallow depth of field'",
            "Include lighting explicitly — Seedream defaults to flat lighting without guidance",
            "Negative prompt field is separate — use 3-7 specific terms",
            "Avoid abstract concepts — be concrete and visual",
        ],
        "example": "A 30-year-old woman with auburn hair standing in a sunlit cafe, warm golden hour light streaming through windows, medium close-up shot, shallow depth of field, 85mm lens, cinematic color grade, soft bokeh background",
    },
    "veo3.1": {
        "provider": "kie_ai",
        "type": "video",
        "optimal_length": "150-300 characters",
        "duration": "8s (fixed)",
        "structure": "Shot type → Setting → Subject → Action → Sound",
        "supports_negative": True,
        "tips": [
            "Keep prompts SHORT — 150-300 characters optimal, NOT words",
            "One continuous action per prompt — Veo struggles with scene changes mid-clip",
            "Be specific about camera movement direction and speed",
            "Veo excels at realistic human motion and natural environments",
            "Add ambient sound cues for better results: 'birds chirping', 'city traffic'",
        ],
        "example": "Tracking shot through a busy Tokyo street at night, neon signs reflecting on wet pavement, a woman in a red coat walking toward camera, city ambiance",
    },
    "kling-2.6": {
        "provider": "kie_ai",
        "type": "video",
        "optimal_length": "50-200 words",
        "duration": "5 or 10 seconds",
        "structure": "Scene → Subject → Motion → Style",
        "supports_negative": True,
        "supports_emphasis": True,
        "tips": [
            "Use ++double plus++ to emphasize critical elements",
            "Describe motion explicitly: direction, speed, acceleration",
            "Negative prompts work aggressively — use 3-7 items for best results",
            "Handles complex multi-subject scenes better than other models",
            "Specify 'smooth camera movement' to avoid jitter",
        ],
        "example": "A cozy kitchen in morning light. ++A chef in white uniform++ carefully plates a dish, smooth steady hands arranging garnish with precision. Camera slowly dollies in. Warm color palette, cinematic depth of field.",
    },
    "seedance-1.5": {
        "provider": "fal.ai",
        "type": "video",
        "optimal_length": "50-150 words",
        "duration": "5 or 10 seconds",
        "structure": "Camera movement → Subject action → Environment → Style",
        "supports_negative": False,
        "tips": [
            "ALWAYS requires an input image — image-to-video only",
            "Best motion quality of all models — emphasize fluid movement",
            "Lead with camera movement for best results",
            "Avoid static descriptions — everything should imply motion",
            "Positive framing only — describe what you want, not what to avoid",
        ],
        "example": "Slow dolly forward through autumn forest, golden leaves gently falling around the frame, soft morning mist between the trees, a deer pauses and looks toward camera, cinematic shallow depth of field, warm amber tones",
    },
}


def format_for_image_model(
    scene: dict,
    model: str = "seedream-4.5",
    character_sheets: list[dict] | None = None,
) -> dict:
    """Format a scene into a model-optimized image prompt.

    Returns: {"prompt": str, "negative_prompt": str | None}
    """
    practices = MODEL_BEST_PRACTICES.get(model, MODEL_BEST_PRACTICES["seedream-4.5"])

    # Apply character consistency tokens if available
    subject = scene.get("subject", "")
    if character_sheets:
        for char in character_sheets:
            if char["character_id"] in subject.lower() or char["description"][:20] in subject:
                subject = char["locked_tokens"]

    if model == "seedream-4.5":
        parts = [
            subject,
            scene.get("action", ""),
            f"in {scene['environment']}" if scene.get("environment") else "",
            f"{scene['camera']['shot_type']} shot" if scene.get("camera", {}).get("shot_type") else "",
            scene.get("lighting", ""),
            scene.get("style", "cinematic, photorealistic"),
        ]
        prompt = ", ".join(p for p in parts if p)
        negative = ", ".join(scene.get("negative_elements", ["blurry", "low quality", "watermark"]))
        return {"prompt": prompt, "negative_prompt": negative}

    return {"prompt": f"{subject} {scene.get('action', '')} in {scene.get('environment', '')}", "negative_prompt": None}


def format_for_video_model(
    scene: dict,
    model: str = "veo3.1",
    character_sheets: list[dict] | None = None,
) -> dict:
    """Format a scene into a model-optimized video prompt.

    Returns: {"prompt": str, "negative_prompt": str | None}
    """
    practices = MODEL_BEST_PRACTICES.get(model, {})

    subject = scene.get("subject", "")
    if character_sheets:
        for char in character_sheets:
            if char["character_id"] in subject.lower():
                subject = char["locked_tokens"]

    camera = scene.get("camera", {})
    camera_desc = f"{camera.get('movement', 'static')} {camera.get('shot_type', 'medium')} shot"
    if camera.get("angle") and camera["angle"] != "eye level":
        camera_desc += f", {camera['angle']}"

    if model == "veo3.1":
        # Veo wants SHORT prompts (150-300 chars)
        prompt = f"{camera_desc}, {subject} {scene.get('action', '')}"
        if scene.get("environment"):
            prompt += f", {scene['environment']}"
        if scene.get("mood"):
            prompt += f", {scene['mood']} atmosphere"
        # Truncate to 300 chars
        if len(prompt) > 300:
            prompt = prompt[:297] + "..."
        return {"prompt": prompt, "negative_prompt": None}

    elif model == "kling-2.6":
        # Kling wants detailed prompts with ++emphasis++
        parts = [
            scene.get("environment", ""),
            f"++{subject}++ {scene.get('action', '')}",
            f"Camera: {camera_desc}",
            scene.get("style", "cinematic"),
        ]
        prompt = ". ".join(p for p in parts if p) + "."
        negatives = scene.get("negative_elements", ["static camera", "jittery", "morphing"])
        return {"prompt": prompt, "negative_prompt": ", ".join(negatives)}

    elif model == "seedance-1.5":
        # Seedance: camera movement first, positive only
        parts = [
            camera_desc,
            f"{subject} {scene.get('action', '')}",
            scene.get("environment", ""),
            scene.get("style", "cinematic, smooth motion"),
        ]
        prompt = ", ".join(p for p in parts if p)
        return {"prompt": prompt, "negative_prompt": None}

    return {"prompt": f"{subject} {scene.get('action', '')}", "negative_prompt": None}


def get_best_practices(model: str) -> dict:
    """Get the full best practices guide for a specific model."""
    return MODEL_BEST_PRACTICES.get(model, {"error": f"Unknown model: {model}"})
```

### 8.8 Search Tools: `backend/agent/tools/search_tools.py`

The agent needs web search to:
- Research topics before writing scripts (current trends, facts, statistics)
- Find visual references and style inspiration
- Check platform-specific best practices (TikTok trends, YouTube SEO)

```python
"""Web search tools using Tavily API."""

from langchain_core.tools import tool
from tavily import TavilyClient
from config import settings

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return _client


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for information about a topic.

    Use this to research topics before writing scripts, find current trends,
    gather facts and statistics, or check platform best practices.

    Args:
        query: The search query (be specific for better results)
        max_results: Number of results to return (1-10, default 5)

    Returns:
        Search results with titles, URLs, and content snippets.
    """
    client = _get_client()
    results = client.search(query=query, max_results=min(max_results, 10))
    formatted = []
    for r in results.get("results", []):
        formatted.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:500],
        })
    return json.dumps({"query": query, "results": formatted})


@tool
def search_references(
    query: str,
    search_type: str = "visual",
) -> str:
    """Search for visual references, style guides, or platform best practices.

    Args:
        query: What to search for (e.g., "cinematic lighting examples", "TikTok video trends 2026")
        search_type: "visual" for style/reference search, "platform" for platform-specific tips

    Returns:
        Curated search results relevant to video production.
    """
    client = _get_client()

    # Enhance query based on type
    if search_type == "visual":
        enhanced_query = f"{query} cinematography visual reference examples"
    elif search_type == "platform":
        enhanced_query = f"{query} best practices tips 2026"
    else:
        enhanced_query = query

    results = client.search(query=enhanced_query, max_results=5)
    formatted = []
    for r in results.get("results", []):
        formatted.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:500],
        })
    return json.dumps({"query": enhanced_query, "type": search_type, "results": formatted})
```

---

## 9. Phase 4: Human-in-the-Loop — Selective Interrupts

### 9.1 Philosophy

**Current**: Forced review at EVERY stage (5 interrupt points).
**Target**: Interrupt only for expensive/irreversible operations. The agent handles the rest.

### 9.2 Interrupt Points

| Tool | Interrupt? | Reason |
|------|-----------|--------|
| `write_script` | No | Cheap, agent can iterate |
| `plan_scenes` | No | Cheap, agent can iterate |
| `generate_all_images` | **Yes** | Costs ~$0.04/image, user should see before proceeding |
| `generate_all_videos` | **Yes** | Costs ~$0.10-0.56/video, most expensive step |
| `generate_voiceover` | No | Cheap (~$0.03), easy to redo |
| `generate_music` | No | Agent can swap music cheaply |
| `assemble_final_video` | No | Just FFmpeg, free |
| `add_captions` | No | Just FFmpeg + Whisper, free |

### 9.3 Implementation Pattern

Use `interrupt()` inside the expensive tools:

```python
from langgraph.types import interrupt

@tool
def generate_all_images(
    state: Annotated[AgentState, InjectedState] = None,
) -> str:
    """Generate images for all planned scenes."""
    scenes = state.get("scenes", [])
    aspect_ratio = state.get("aspect_ratio", "16:9")
    estimated_cost = len(scenes) * 0.04

    # Interrupt for user approval
    response = interrupt({
        "stage": "image_generation",
        "message": f"Ready to generate {len(scenes)} images (est. ${estimated_cost:.2f}). Proceed?",
        "scenes": [{"number": s["scene_number"], "prompt": s["image_prompt"]} for s in scenes],
        "actions": ["approve", "modify", "cancel"],
    })

    if response.get("action") == "cancel":
        return "Image generation cancelled by user."

    if response.get("action") == "modify":
        return f"User requested changes: {response.get('message')}. Please modify scenes first."

    # Proceed with generation
    results = []
    for scene in scenes:
        url = fal_service.generate_image(scene["image_prompt"], aspect_ratio=aspect_ratio)
        results.append({"scene_number": scene["scene_number"], "image_url": url})

    return json.dumps({"images": results, "cost": estimated_cost})
```

### 9.4 Frontend Handling

When the frontend receives an `awaiting` event (from an interrupt), it shows an approval UI:
- **Approve button**: Sends `POST /message` with `{"action": "approve"}`
- **Modify input**: Sends `POST /message` with `{"action": "modify", "message": "..."}`
- **Cancel button**: Sends `POST /message` with `{"action": "cancel"}`

This is similar to the current approve/modify flow, but the agent also sends conversational messages explaining what it wants to do and why.

---

## 10. Phase 5: Frontend — Conversational UI

### 10.1 Key Changes

The frontend shifts from a "staged pipeline" UI to a "chat with rich artifacts" UI:

| Current | New |
|---------|-----|
| Fixed stages (script → scenes → images → ...) | Free-flowing conversation |
| Dedicated approve/modify buttons per stage | Inline approve buttons for expensive ops |
| TopicForm with model selector, concat toggle | Simple text input, agent asks follow-ups |
| Progress bar tracks pipeline stages | Progress events from tool execution |

### 10.2 `useSession.ts` Rewrite

```typescript
// Simplified hook — conversational instead of staged
function useSession() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null)

  // Start a new session with an initial message
  async function start(initialMessage: string) {
    const { sessionId } = await api.createSession()
    connectSSE(sessionId)
    await api.sendMessage(sessionId, { message: initialMessage })
  }

  // Send a follow-up message
  async function send(message: string) {
    setMessages(prev => [...prev, { role: "user", content: message }])
    await api.sendMessage(sessionId, { message })
  }

  // Approve a pending operation
  async function approve() {
    await api.sendMessage(sessionId, { action: "approve" })
    setPendingApproval(null)
  }

  // Modify a pending operation
  async function modify(feedback: string) {
    await api.sendMessage(sessionId, { action: "modify", message: feedback })
    setPendingApproval(null)
  }
}
```

### 10.3 `TopicForm.tsx` Simplification

Replace the complex form (model selector, concat toggle, aspect ratio) with a simple text input:

```tsx
function TopicForm({ onSubmit }) {
  const [message, setMessage] = useState("")

  return (
    <div className="flex flex-col items-center gap-6 max-w-2xl mx-auto">
      <h1>What would you like to create?</h1>
      <p className="text-gray-400">
        Describe your video idea. I'll ask follow-up questions if needed.
      </p>
      <textarea
        value={message}
        onChange={e => setMessage(e.target.value)}
        placeholder="Make a 2-minute TikTok about morning routines with upbeat music..."
        className="w-full h-32 ..."
      />
      <button onClick={() => onSubmit(message)}>Start Creating</button>
    </div>
  )
}
```

The agent asks about model choice, aspect ratio, and other parameters in the conversation itself, making smart defaults and letting the user override.

### 10.4 ChatView Changes

The ChatView needs to handle:
1. **Agent text messages** — rendered as chat bubbles
2. **Tool execution** — rendered as progress indicators
3. **Tool results** — rendered as rich artifacts (images, videos, scripts, etc.)
4. **Approval requests** — rendered as inline approve/modify UI

Map tool results to existing artifact components:
- `write_script` result → `<ScriptBlock />`
- `generate_image` result → `<ImageGrid />`
- `generate_video` result → `<VideoGrid />`
- `generate_voiceover` result → `<VoiceoverPlayer />`
- `assemble_final_video` result → `<FinalVideo />`

---

## 11. Phase 6: New Capabilities

Once the agent loop is working, adding new capabilities is just adding new tools. No graph changes needed.

### 11.1 Background Music & SFX (via ElevenLabs MCP)
- ElevenLabs MCP provides `compose_music` and `text_to_sound_effects` tools
- Agent can compose background music that matches the video's mood and pacing
- Agent can generate SFX (whooshes, transitions, ambient) for specific scenes
- `mix_audio` local tool combines voiceover + music + SFX at proper levels

### 11.2 Aspect Ratio + Duration
- Already handled in Phase 0-1 (parameterized tools)

### 11.3 Voice Selection & Cloning (via ElevenLabs MCP)
- ElevenLabs MCP provides `search_voices`, `get_voice_info`, `voice_clone` tools
- Agent asks user "What voice do you prefer?" and searches the library
- Users can upload voice samples for cloning

### 11.4 Thumbnail Generation
- New local tool: `generate_thumbnail` → calls fal.ai Seedream 4.5 with thumbnail-optimized prompt
- Agent auto-generates thumbnails optimized for the target platform (YouTube, TikTok, etc.)

### 11.5 Platform Presets
- Encode in system prompt: "When user says TikTok, default to 9:16, 30-60s, fast pacing"
- Platform-specific prompt optimization via `prompt_engineering.py`

### 11.6 Parallel Video Generation
- `generate_all_videos` tool can use `concurrent.futures.ThreadPoolExecutor` internally
- Or agent can call `generate_video` multiple times in a single response (parallel tool_calls)

### 11.7 Web Research Integration
- Agent uses `web_search` to research topics before scripting
- Agent uses `search_references` to find visual style inspiration
- Platform trend research (TikTok trends, YouTube best practices)

---

## 12. Edge Cases & Failure Modes

### 12.1 Agent Loops Infinitely
**Problem**: Agent keeps calling tools without converging.
**Solution**: Add max iterations. In the graph, track iteration count in state:
```python
class AgentState(TypedDict):
    # ...
    iteration_count: Annotated[int, lambda a, b: (a or 0) + 1]
    max_iterations: int  # default 50

def should_continue(state):
    if state.get("iteration_count", 0) >= state.get("max_iterations", 50):
        return END  # Force termination
    return tools_condition(state)
```

### 12.2 Agent Calls Wrong Tools
**Problem**: Agent tries to generate videos before images.
**Solution**: Tools should validate preconditions and return helpful errors:
```python
@tool
def generate_all_videos(state: Annotated[AgentState, InjectedState] = None) -> str:
    scenes = state.get("scenes", [])
    if not scenes:
        return "Error: No scenes planned yet. Call plan_scenes first."
    if not all(s.get("image_url") for s in scenes):
        return "Error: Not all scenes have images. Generate images first."
    # ... proceed ...
```

### 12.3 Tool Execution Fails
**Problem**: fal.ai or Kie AI returns an error.
**Solution**: Tools should catch exceptions and return structured error messages. The agent will reason about the error and try alternatives:
```python
@tool
def generate_video(scene_id: int, prompt: str, model: str = "veo") -> str:
    try:
        result = video_router.route_and_generate(model, prompt, ...)
        return json.dumps({"video_path": result["path"], "cost": result["cost"]})
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "suggestion": "Try a different model or simplify the prompt."
        })
```

### 12.4 State Gets Corrupted
**Problem**: Post-tool state update parses a tool result incorrectly.
**Solution**:
- Make post_tool_update defensive (try/except on every parse)
- Tools return well-defined JSON schemas
- Add `get_production_status` tool so agent can check its own state

### 12.5 MCP Server Crashes
**Problem**: An MCP server process dies mid-session.
**Solution**:
- `langchain-mcp-adapters` creates fresh connections per invocation (stateless by default)
- If a server is completely down, the tool will raise an exception → agent gets an error message → uses fallback
- Log MCP failures prominently

### 12.6 Context Window Overflow
**Problem**: Long conversations with many tool calls can exceed Claude's context window.
**Solution**:
- Use `trim_messages` utility to prune old messages while keeping recent context
- Keep production state in AgentState fields (not just in message history)
- The system prompt injects current state summary so agent doesn't need full history

```python
from langchain_core.messages import trim_messages

def call_model(state: AgentState):
    messages = trim_messages(
        state["messages"],
        max_tokens=150000,
        strategy="last",
        token_counter=model,
        include_system=True,
    )
    # ... invoke model with trimmed messages ...
```

### 12.7 Cost Runaway
**Problem**: Agent generates 50 images without user noticing.
**Solution**:
- `interrupt()` on batch operations (generate_all_images, generate_all_videos)
- Track cumulative cost in state
- System prompt instructs agent to warn when cost > $5

### 12.8 User Uploads Files
**Problem**: User uploads reference images — agent needs to use them.
**Solution**: File upload endpoint stays the same. Uploaded files are stored in state as `uploaded_files`. The system prompt tells the agent to check for uploads and use them appropriately (e.g., FLUX i2i for character reference, Kling O1 for character consistency).

### 12.9 Concurrent Sessions
**Problem**: Multiple users generating content simultaneously.
**Solution**:
- MemorySaver uses `thread_id` per session (same as current)
- Each session gets its own workspace directory
- Tools read `job_id` from state to scope file operations
- MCP servers are spawned per session (stateless)

### 12.10 Resume After Browser Close
**Problem**: User closes browser mid-production, reopens later.
**Solution**:
- MemorySaver persists state (same as current)
- Frontend reconnects SSE on page load if session_id is in URL/localStorage
- Agent can be resumed with a new message

---

## 13. File-by-File Change Map

### New Files (17)
```
backend/agent/tools/__init__.py
backend/agent/tools/script_tools.py
backend/agent/tools/scene_tools.py
backend/agent/tools/image_tools.py
backend/agent/tools/video_tools.py
backend/agent/tools/audio_tools.py
backend/agent/tools/assembly_tools.py
backend/agent/tools/project_tools.py
backend/agent/tools/utility_tools.py
backend/agent/tools/search_tools.py     NEW — Tavily web search + reference search
backend/agent/tools/prompt_tools.py      NEW — Model-specific prompt formatting tools
backend/agent/system_prompt.py
backend/agent/mcp_client.py
backend/services/prompt_engineering.py   NEW — Prompting intelligence layer (model-specific formatters)
backend/mcp_server/__init__.py           NEW — Custom FastMCP server package
backend/mcp_server/server.py             NEW — Custom MCP server wrapping fal.ai + Kie AI
frontend/src/lib/agent-types.ts          (new types for agent messages)
```

### Modified Files (12)
```
backend/agent/graph.py                  REWRITE — ReAct loop instead of pipeline
backend/agent/state.py                  REWRITE — AgentState extending MessagesState
backend/services/claude_service.py      REWRITE — flexible prompts (parameterized duration, style)
backend/services/fal_service.py         MODIFY — add aspect_ratio param
backend/services/kie_service.py         MODIFY — pass aspect_ratio through
backend/services/ffmpeg_service.py      MODIFY — aspect-ratio-aware resolution
backend/services/model_registry.py      MODIFY — add new models
backend/config.py                       MODIFY — add TAVILY_API_KEY, MCP-related config
backend/api/routes.py                   MODIFY — new /message endpoint, streaming changes
backend/main.py                         MODIFY — async graph initialization
frontend/src/hooks/useSession.ts        REWRITE — conversational instead of staged
frontend/src/components/TopicForm.tsx    SIMPLIFY — just a text input
frontend/src/components/chat/ChatView.tsx MODIFY — handle agent message stream
frontend/src/lib/api.ts                 MODIFY — new sendMessage function
frontend/src/lib/types.ts               MODIFY — new event types
backend/pyproject.toml                  MODIFY — add langchain-mcp-adapters, mcp, tavily-python
.env.example                            MODIFY — add TAVILY_API_KEY + document all keys
```

### Deleted Files (16)
```
backend/agent/nodes/analyze_input.py
backend/agent/nodes/write_script.py
backend/agent/nodes/review_script.py
backend/agent/nodes/plan_scenes.py
backend/agent/nodes/review_scenes.py
backend/agent/nodes/generate_images.py
backend/agent/nodes/review_images.py
backend/agent/nodes/generate_videos.py
backend/agent/nodes/review_videos.py
backend/agent/nodes/generate_voiceover.py
backend/agent/nodes/review_voiceover.py
backend/agent/nodes/assemble_video.py
backend/agent/nodes/add_captions.py
backend/agent/nodes/finish_individual.py
backend/agent/nodes/__init__.py
backend/agent/modification.py
backend/services/video_router.py
```

---

## 14. CLAUDE.md for the New Project

**Delete the current `CLAUDE.md` before starting the new conversation.** The current file describes the fixed pipeline which will be confusing and counterproductive.

After Phase 0 is complete (agent loop working), run `/init` to generate a fresh CLAUDE.md. Claude will analyze the new codebase and write an accurate description.

**However**, you may want to create a minimal temporary `CLAUDE.md` for the new conversation to read:

```markdown
# CLAUDE.md — Temporary (replace with /init after Phase 0)

## What This Project Is
AI Content Director — an autonomous agent that plans and produces videos using AI.
The architecture is a LangGraph ReAct agent loop (NOT a fixed pipeline).

## How to Run
Backend: cd backend && source .venv/bin/activate && python main.py
Frontend: cd frontend && npm run dev

## Key Architecture Files
- backend/agent/graph.py — ReAct agent loop (agent → tools → post_tool → agent)
- backend/agent/state.py — AgentState (extends MessagesState)
- backend/agent/tools/ — All production tools
- backend/agent/system_prompt.py — Director persona + dynamic state injection
- backend/agent/mcp_client.py — MCP server connections

## Transformation Plan
See agentic_content_creation_plan.md for the full plan this project is being built from.
```

---

## 15. First Prompt for New Claude Session

Copy-paste this as your first message in the new Claude Code session on the `video-ai-agent-v2` project:

---

```
I'm transforming this project from a fixed LangGraph pipeline into an autonomous ReAct agent.

The full plan is in `agentic_content_creation_plan.md` — read it completely before starting.

CRITICAL CONSTRAINTS:
- Content generation uses ONLY fal.ai, Kie AI, and ElevenLabs. No Runway, MiniMax, or others.
- MCP: ElevenLabs official MCP + custom FastMCP server for fal.ai/Kie AI. No community servers.
- Agent must use Tavily web_search tool to research topics before writing scripts.
- Agent must use prompt_engineering.py to format prompts per model's optimal structure.

Start with **Phase 0** (Foundation — ReAct Agent Loop):

1. Read the current codebase to understand what exists (especially `backend/agent/graph.py`,
   `backend/agent/state.py`, `backend/agent/nodes/`, `backend/services/`, `backend/api/routes.py`,
   `frontend/src/hooks/useSession.ts`)

2. Create the new `AgentState` in `backend/agent/state.py` (extends MessagesState with
   production fields)

3. Create the tools directory `backend/agent/tools/` with tool files that wrap the existing
   services (script_tools, scene_tools, image_tools, video_tools, audio_tools, assembly_tools,
   project_tools, utility_tools, search_tools, prompt_tools)

4. Create `backend/services/prompt_engineering.py` — model-specific prompt formatting,
   cinematography vocabulary, character consistency, negative prompt templates

5. Create `backend/agent/system_prompt.py` with the Content Director system prompt
   (include provider constraints and model selection guidelines)

6. Rewrite `backend/agent/graph.py` as a ReAct loop (agent → tools → post_tool → agent)

7. Update `backend/api/routes.py` to work with the new agent (add /message endpoint,
   update SSE streaming)

8. Update `backend/services/claude_service.py` with flexible prompts (parameterized
   duration, style, scene count)

9. Update the frontend (`useSession.ts`, `ChatView.tsx`, `TopicForm.tsx`) for
   conversational interaction

10. Add `TAVILY_API_KEY` to `backend/config.py` and `.env.example`

Keep the existing services (fal_service, kie_service, elevenlabs_service, ffmpeg_service,
whisper_service, supabase_service) — just wrap their functions as @tool definitions.

Don't add MCP yet — that's Phase 2. Focus on getting the agent loop working with local tools
and the prompting intelligence layer.

After Phase 0 is working, we'll move to Phase 1-6.
```

---

## Implementation Order Summary

```
Phase 0: ReAct agent loop (replace pipeline)           ← START HERE
  └─ state.py, tools/, system_prompt.py, graph.py, routes.py, frontend

Phase 1: Tool layer (wrap all services)
  └─ script_tools, scene_tools, image_tools, video_tools, audio_tools,
     assembly_tools, search_tools, prompt_tools

Phase 2: MCP integration (ElevenLabs official + custom FastMCP)
  └─ mcp_client.py, ElevenLabs official MCP, custom mcp_server/ for fal.ai + Kie AI

Phase 3: Director intelligence (system prompt engineering)
  └─ system_prompt.py refinement, model selection logic, self-evaluation

Phase 3.5: Prompting intelligence layer
  └─ prompt_engineering.py, model-specific formatters, cinematography vocabulary,
     character consistency, negative prompts

Phase 4: Human-in-the-loop (selective interrupts)
  └─ interrupt() in expensive tools, frontend approval UI

Phase 5: Frontend (conversational UI)
  └─ useSession rewrite, TopicForm simplification, ChatView updates

Phase 6: New capabilities (music, SFX, thumbnails, voice selection, web research)
  └─ ElevenLabs MCP tools (music, SFX, cloning), Tavily search, platform presets
```

**Providers**: ONLY fal.ai + Kie AI + ElevenLabs. No Runway, MiniMax, or others.

**Note**: Phases 0+1+4+5 are tightly coupled and should ideally be done together as one big push. Phase 2, 3, 3.5, and 6 are additive and can be done incrementally.

---

## Estimated Complexity

| Phase | Files Changed | Effort | Risk |
|-------|--------------|--------|------|
| Phase 0 | ~15 | High | High — core architecture change |
| Phase 1 | ~10 | Medium | Medium — wrapping existing code + search + prompt tools |
| Phase 2 | ~5 | Medium | Medium — ElevenLabs MCP + custom FastMCP server |
| Phase 3 | ~2 | Low | Low — system prompt refinement |
| Phase 3.5 | ~3 | Medium | Low — prompt engineering layer (well-researched) |
| Phase 4 | ~4 | Medium | Medium — interrupt resumption |
| Phase 5 | ~5 | Medium | Medium — frontend state management |
| Phase 6 | ~6 | Low | Low — additive features |
