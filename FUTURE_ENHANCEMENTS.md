# Future Enhancements — AI Content Director Agent

> Assessment date: February 2026
> Vision: Replace a professional content production team with an autonomous AI agent

---

## Current State Summary

The agent has a solid foundation:
- LangGraph pipeline with human-in-the-loop at every stage
- Multi-provider video generation (fal.ai + Kie AI)
- Character consistency via reference images (FLUX i2i + Kling O1)
- Auto-assembly with FFmpeg (concat + voiceover overlay + captions)
- Supabase persistence for generation history
- SSE streaming with real-time progress

**But it produces "first draft" content, not "final cut" quality.** The biggest gaps are post-production polish, format flexibility, and smarter AI direction.

---

## Gap Analysis: Current vs. Professional-Grade

### What Fails Today

| User Request | What Happens | Why |
|---|---|---|
| "Make a 2-minute video" | Produces ~45s video | Script prompt hardcoded to "120-150 words" (~45s) |
| "9:16 for TikTok" | Produces 16:9 | Aspect ratio hardcoded everywhere (fal, kie, ffmpeg) |
| "Add background music" | No music | Only voiceover, no audio layering |
| "Make it cinematic" | Generic output | No camera movement/lighting/mood in scene prompts |
| "Generate a thumbnail" | Nothing | Feature doesn't exist |
| "Different voice" | Same voice | Single hardcoded ElevenLabs voice ID |

### Pipeline vs. Professional Production Team

| Production Stage | Current Capability | Gap |
|---|---|---|
| Creative brief | User types a topic | No tone, audience, platform, style controls |
| Script writing | Generic 45s script | No length/format flexibility, no platform optimization |
| Storyboarding | 4-6 scenes, basic descriptions | No cinematography (camera, lighting, transitions) |
| Image generation | Seedream 4.5 / FLUX i2i | No FLUX.2 multi-reference, no GPT Image 1.5 |
| Video generation | 4 models, sequential | No Kling 3.0 multi-shot, no Runway Gen-4.5, no parallel gen |
| Sound design | Voiceover only | No background music, no SFX, no audio layering |
| Color grading | None | AI color grading exists (fylm.ai, Colourlab) |
| Captions | Basic white text, fixed style | No animated captions, no platform-specific styles |
| Motion graphics | None | No titles, lower-thirds, end screens |
| Thumbnails | None | AI thumbnail generation is mature |
| Multi-format export | 16:9 MP4 only | No 9:16, 1:1, platform-optimized exports |
| Distribution | None | No metadata, hashtags, scheduling |

---

## Phase 1 — Core Upgrades (Highest Impact)

### 1.1 Aspect Ratio Control

**Problem**: Everything hardcoded to 16:9.

**Solution**: Add `aspect_ratio` to session state and propagate through entire pipeline.

- State: `aspect_ratio: Literal["16:9", "9:16", "1:1", "4:5"]`
- Frontend: Aspect ratio selector in TopicForm
- Image gen: Map to fal.ai size params (`portrait_16_9`, `square`, etc.)
- Video gen: Pass to all providers (Kie, fal.ai all support aspect ratio param)
- FFmpeg: Dynamic output resolution based on ratio
- Captions: Adjust font size and position per ratio

**Impact**: Doubles addressable use cases (TikTok, Reels, Shorts, Instagram feed).

### 1.2 Flexible Video Duration

**Problem**: Script locked to ~45s / 120-150 words. No duration parameter.

**Solution**: Add `target_duration` to state, adjust script prompt and scene planning dynamically.

- State: `target_duration: int` (seconds, 15-300)
- Script prompt: Calculate word count from duration (~2.5 words/sec for narration)
- Scene planning: Scale scene count with duration (e.g., 15s = 2 scenes, 120s = 12 scenes)
- Frontend: Duration selector or free input

**Impact**: Supports everything from 15s TikTok to 5-min YouTube explainer.

### 1.3 Background Music

**Problem**: Only voiceover, no music layer.

**Solution**: Add music generation step after voiceover, mix in FFmpeg.

- New node: `generate_music` (after voiceover, before assembly)
- Options:
  - **Suno API**: Full song generation from prompt + genre ($10/mo unlimited)
  - **ElevenLabs Music**: Leverages existing API key
  - **Mubert API**: Real-time background music via API
- FFmpeg: Mix music track at reduced volume (-15dB) under voiceover
- Review node: Let user approve/swap music
- State: `music_path`, `music_style`, `music_volume`

**Impact**: Transforms amateur-sounding output to professional quality.

### 1.4 Parallel Scene Generation

**Problem**: Scenes generated sequentially. 6 scenes = 6x wait time.

**Solution**: Use `concurrent.futures.ThreadPoolExecutor` for parallel API calls.

- Images: Generate all scenes concurrently (fal.ai handles concurrent requests)
- Videos: Generate all scenes concurrently (Kie AI and fal.ai both support)
- Progress: Update per-scene as each completes
- Fallback: If one scene fails, retry it without blocking others

**Impact**: 3-5x faster generation (most time is API wait, not compute).

### 1.5 New Video Models

**Kling 3.0** (game-changer):
- Multi-shot: Up to 6 camera cuts in one generation
- Native 4K/60fps
- AI Director: Automatic camera angle scheduling
- Native audio: Dialogue with lip-sync, SFX, ambient
- Voice binding per character
- ~$0.10/sec via third-party APIs
- Could potentially replace concat pipeline for shorter videos

**Runway Gen-4.5**:
- #1 visual quality (Elo 1,247 on Artificial Analysis)
- Best photorealistic rendering and physics
- 1080p, 5-10s, all aspect ratios
- ~$0.30-0.50/video

**Sora 2** (via fal.ai):
- Up to 25s per clip (longest available)
- Native audio
- ~$0.10/sec standard

**Wan 2.6** (budget option):
- Open-source, cheapest at ~$0.05/sec
- Character R2V (reference-to-video)
- 15s, native audio

### 1.6 Voice Selection UI

**Problem**: Single hardcoded ElevenLabs voice.

**Solution**: Expose voice library in frontend.

- Fetch voices from ElevenLabs API at session start
- Voice picker component with preview samples
- Store selected `voice_id` in state
- Pass to `generate_tts()` call

**Impact**: Personalization, gender/accent matching to content.

---

## Phase 2 — Professional Polish

### 2.1 Enhanced Prompts (Cinematography)

Current scene planning gives basic visual descriptions. Upgrade to include:

```
For each scene, specify:
- Camera: wide/medium/close-up/extreme-close-up
- Movement: static/pan-left/pan-right/tilt-up/zoom-in/dolly/tracking
- Lighting: bright/moody/dramatic/golden-hour/neon/silhouette
- Mood: energetic/calm/mysterious/playful/intense
- Transition to next: cut/fade/dissolve/match-cut
```

This metadata can be:
- Embedded in video generation prompts (models understand camera terms)
- Used by FFmpeg for transition effects between scenes
- Displayed in scene cards for user review

### 2.2 Animated Captions

Replace fixed white-text captions with platform-specific styles:

- **TikTok style**: Word-by-word highlight, bold colors, bouncy animations
- **YouTube style**: Clean lower-third, semi-transparent background
- **Instagram style**: Centered, minimalist, story-friendly
- **Custom**: Font, color, position, animation configurable

Implementation: ASS subtitle format supports all of this. Generate styled `.ass` files based on platform preset.

### 2.3 AI Thumbnail Generation

Add a `generate_thumbnail` node after final video:

- Extract key frame from video OR generate standalone image
- Use GPT Image 1.5 (best text rendering) or Seedream for the visual
- Overlay text (title, hook) using FFmpeg or Pillow
- Generate 3 variants for A/B testing
- Store in Supabase as media type `thumbnail`

### 2.4 Sound Effects Layer

- Use **ElevenLabs SFX API** (already have the key) to generate scene-specific sounds
- Claude generates SFX descriptions per scene during planning
- Mix SFX at appropriate timestamps in FFmpeg
- State: `sound_effects: list[{timestamp, description, path}]`

### 2.5 Content Format Presets

Instead of generic "topic", offer format templates:

| Format | Script Structure | Scenes | Duration | Aspect |
|---|---|---|---|---|
| TikTok/Reel | Hook → value → CTA | 3-4 | 15-60s | 9:16 |
| YouTube Explainer | Hook → thesis → evidence → payoff | 8-15 | 2-5min | 16:9 |
| Product Demo | Problem → solution → features → CTA | 4-6 | 30-90s | 16:9 |
| Tutorial | Intro → steps → summary | 5-10 | 1-3min | 16:9 |
| Ad/Promo | Attention → interest → desire → action | 3-4 | 15-30s | 9:16 or 1:1 |
| Story/Narrative | Setup → conflict → resolution | 5-8 | 1-3min | 16:9 |

### 2.6 Image Model Upgrades

- **FLUX.2 Multi-Reference**: Up to 10 reference images, zero training, eliminates character drift
- **GPT Image 1.5**: Best text rendering for title cards, infographics
- Smart routing: Use FLUX.2 for character scenes, Seedream for landscapes, GPT Image for text-heavy

---

## Phase 3 — Agent Intelligence

### 3.1 MCP Client Integration

Build an MCP client into the backend so the agent can use external tools:

**High-value MCP servers to integrate**:
- Web search (trend research before scripting)
- ElevenLabs MCP (voice library, SFX generation)
- fal.ai MCP (if available — model discovery, generation)
- Social media APIs (direct publishing)
- Analytics platforms (performance tracking)

**Architecture**: MCP client in Python using the `mcp` SDK. Connect at agent startup, discover tools, make them available to Claude during `analyze_input` and planning nodes.

### 3.2 Per-Scene Model Routing

Instead of one model for all scenes, let the agent choose per scene:

- Hero/establishing shot → Runway Gen-4.5 (highest quality)
- Action/motion → Kling 3.0 (multi-shot, 4K)
- Simple/static → Wan 2.6 (cheapest)
- Character close-up → Kling O1 Ref (consistency)

Claude decides during scene planning based on visual complexity and budget.

### 3.3 Self-Evaluation Loop

Before showing output to user, agent judges its own work:

- After image generation: Claude evaluates each image against the prompt
- After video generation: Check for artifacts, consistency issues
- After assembly: Review pacing, audio sync, caption accuracy
- Auto-regenerate if quality below threshold

### 3.4 Content Repurposing

From one generation, produce multiple format outputs:

- 16:9 YouTube version (full)
- 9:16 TikTok version (re-cropped, re-paced)
- 1:1 Instagram version (center-cropped)
- Thumbnail set (3 variants)
- Caption/description text for each platform
- Hashtag suggestions

### 3.5 Platform Metadata Generation

After video completion, generate:

- SEO-optimized title (platform-specific length limits)
- Description with keywords
- Hashtag set (trending + niche)
- Best posting time suggestion
- Content category tags

---

## Phase 4 — Advanced Features (Future)

### 4.1 Kling 3.0 Multi-Shot Pipeline

Kling 3.0's multi-shot could replace the entire image→video→concat pipeline:

- Write scene descriptions with camera directions
- Single API call generates multi-angle video with native audio
- AI Director handles transitions automatically
- Skip image generation, video concat, and separate voiceover

This would be a fundamental architecture shift — the current sequential pipeline becomes a single-call generation for videos under 15s.

### 4.2 Real-Time Collaboration

- WebSocket-based live editing (multiple users)
- Shared project workspaces
- Comment/annotation system on media

### 4.3 Template Library

- Save successful generations as templates
- Community template sharing
- One-click clone and customize

### 4.4 Brand Kits

- Upload brand colors, fonts, logo
- Auto-apply to thumbnails, captions, overlays
- Consistent visual identity across all generations

### 4.5 Analytics Dashboard

- Track generation costs per project
- API usage and model performance stats
- Content performance metrics (if publishing integration exists)

---

## Model Landscape Reference (Early 2026)

### Video Generation Models

| Model | Provider | Cost/sec | Resolution | Duration | Key Feature |
|---|---|---|---|---|---|
| Wan 2.6 | Alibaba (fal.ai) | $0.05 | 1080p | 15s | Cheapest, open-source, R2V |
| Kling 2.6 Pro | Kie AI | $0.07 | 1080p | 10s | Good value |
| Kling 3.0 | Kie AI / fal.ai | $0.10 | 4K/60fps | 15s | Multi-shot + native audio |
| Veo 3.1 Fast | Google (Kie AI) | $0.10 | 1080p | 8s+ | Native audio, strong prompts |
| Sora 2 | OpenAI (fal.ai) | $0.10 | 720p | 25s | Longest clips, native audio |
| Hailuo 2.3 | MiniMax | $0.15 | 1080p | 10s | Best for stylized content |
| Seedance 1.5 | fal.ai | $0.03/s | 720p | 12s | Current default |
| Runway Gen-4.5 | Runway | $0.30-0.50 | 1080p | 10s | #1 visual quality |
| Luma Ray3 | Luma | varies | 1080p/4K HDR | 10s | HDR, reasoning-driven |

### Image Generation Models

| Model | Provider | Cost | Key Feature |
|---|---|---|---|
| Seedream 4.5 | fal.ai | $0.04 | Fast, affordable (current default) |
| FLUX.2 Multi-Ref | fal.ai | ~$0.05 | 10 reference images, zero training |
| GPT Image 1.5 | OpenAI | ~$0.02-0.08 | Best text rendering |
| FLUX Dev i2i | fal.ai | $0.03 | Image-to-image (current reference) |

### Audio

| Service | Type | Pricing | Key Feature |
|---|---|---|---|
| ElevenLabs | TTS | $5-330/mo | Best emotional depth (current) |
| ElevenLabs SFX | Sound effects | included | Text-to-SFX |
| ElevenLabs Music | Music gen | included | New entrant |
| Suno v4.5 | Music gen | $10/mo | Full songs from prompts |
| Udio | Music gen | varies | Professional stem control |
| Fish Audio S1 | TTS | varies | #1 on TTS-Arena |

---

## MCP Server Availability

> Researched February 2026

### Summary

| Service | Official MCP? | Best Option | GitHub |
|---------|:---:|-------------|--------|
| **ElevenLabs** | **Yes** | elevenlabs/elevenlabs-mcp | [github.com/elevenlabs/elevenlabs-mcp](https://github.com/elevenlabs/elevenlabs-mcp) |
| **Runway** | **Yes** | runwayml/runway-api-mcp-server | [github.com/runwayml/runway-api-mcp-server](https://github.com/runwayml/runway-api-mcp-server) |
| **fal.ai** | No | raveenb/fal-mcp-server | [github.com/raveenb/fal-mcp-server](https://github.com/raveenb/fal-mcp-server) |
| **Kie AI** | No | felores/kie-ai-mcp-server | [github.com/felores/kie-ai-mcp-server](https://github.com/felores/kie-ai-mcp-server) |
| **Suno AI** | No | CodeKeanu/suno-mcp | [github.com/CodeKeanu/suno-mcp](https://github.com/CodeKeanu/suno-mcp) |
| **Multi-provider** | No | h2a-dev/video-gen-mcp-monolithic | [github.com/h2a-dev/video-gen-mcp-monolithic](https://github.com/h2a-dev/video-gen-mcp-monolithic) |

### ElevenLabs MCP (Official)

The most mature option. Maintained by ElevenLabs, Docker image at `mcp/elevenlabs`.

**Tools:** `text_to_speech`, `search_voices`, `generate_sound_effects`, `generate_music`, `voice_design`, `voice_clone`, `audio_isolation`, `voice_conversion`, `transcription`, `create_agent`, `make_outbound_call`, `get_conversations`.

This is highly relevant — it exposes voice search, SFX generation, and music generation that our agent currently lacks.

### Runway MCP (Official)

Maintained by RunwayML. Supports Gen-4 Turbo (2-10s) and Veo 3.1.

**Tools:** Video generation (text-to-video, image-to-video), keyframe support, reference-to-video, 1080p output, flexible duration. Also integrates ElevenLabs TTS (29 languages).

### fal.ai MCP (Community)

`raveenb/fal-mcp-server` is the most comprehensive. Supports 600+ fal.ai models with dynamic discovery. Docker + pip, dual-mode (STDIO + HTTP/SSE).

**Tools:** `list_models`, `generate_image` (flux_schnell/dev, sdxl), `generate_video` (svd, animatediff), `generate_audio` (musicgen), `text_to_speech` (bark), `transcribe` (whisper), `upscale_image`, `image_to_image`.

### Kie AI MCP (Community)

`felores/kie-ai-mcp-server` is the more complete option. Aggregates multiple providers through Kie.ai API.

**Tools:** 8 image tools (Nano Banana, Seedream, Flux Kontext, Midjourney), 9 video tools (Veo3, Runway Aleph, Seedance, Wan), 3 audio tools (Suno V5 music, ElevenLabs TTS). Smart intent detection with automatic cost/quality optimization.

Notable: This single MCP server provides access to most providers we'd want, through one API key.

### Suno MCP (Community)

`CodeKeanu/suno-mcp` supports v3.5 through v5, Docker images via GitHub Actions.

**Tools:** `generate_music`, `get_track_info`, `check_credits`, `convert_mp3_to_wav`.

**Caveat:** Uses unofficial Suno API wrappers (Suno has no public API). May break.

### Multi-Provider Video MCP

`h2a-dev/video-gen-mcp-monolithic` — full video production via fal.ai with platform-optimized presets (YouTube, TikTok, Instagram), cost tracking, and YouTube OAuth2 upload.

### Integration Strategy

For our agent, the most valuable MCP integration path would be:

1. **ElevenLabs MCP (official)** — Immediately adds voice search, SFX, and music generation
2. **felores/kie-ai-mcp-server** — Single server gives access to Veo3, Runway, Suno, ElevenLabs, Seedance, Seedream, Wan, Midjourney through Kie.ai API
3. **Runway MCP (official)** — For highest-quality video (Gen-4.5) if budget allows

Rather than building MCP clients into our Python backend, these could also be used by Claude Code during development, or we could build an MCP client layer that lets the LangGraph agent dynamically discover and use tools at runtime.

---

## Implementation Priority Matrix

| Enhancement | Impact | Effort | Priority |
|---|---|---|---|
| Aspect ratio control | High | Medium | P0 |
| Flexible duration | High | Medium | P0 |
| Background music | High | Medium | P0 |
| Parallel generation | High | Low | P0 |
| Kling 3.0 support | High | Medium | P0 |
| Voice selection UI | Medium | Low | P1 |
| Enhanced prompts (cinematography) | Medium | Low | P1 |
| Animated captions | Medium | Medium | P1 |
| Content format presets | Medium | Medium | P1 |
| AI thumbnail generation | Medium | Medium | P1 |
| Sound effects layer | Medium | Medium | P1 |
| Runway Gen-4.5 / Sora 2 / Wan 2.6 | Medium | Medium | P1 |
| FLUX.2 multi-reference | Medium | Low | P1 |
| MCP client integration | High | High | P2 |
| Per-scene model routing | Medium | Medium | P2 |
| Self-evaluation loop | Medium | Medium | P2 |
| Content repurposing | High | High | P2 |
| Platform metadata | Medium | Low | P2 |
| Kling 3.0 multi-shot pipeline | High | High | P3 |
| Brand kits | Medium | Medium | P3 |
| Template library | Medium | High | P3 |
| Analytics dashboard | Low | High | P3 |
