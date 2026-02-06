# AI Content Maker

A conversational AI agent that transforms any topic into a professional short-form video. Built with LangGraph, FastAPI, and Next.js.

The agent guides you through each stage — script writing, scene planning, image generation, video synthesis, and voiceover — letting you review, modify, and approve at every step before proceeding.

## How It Works

1. **Enter a topic** — e.g. "3 tips for better sleep"
2. **Review the script** — AI writes a 45-second narration; chat to refine it
3. **Review scene plan** — 4-6 scenes with visual descriptions; modify as needed
4. **Review images** — Generated scene images; regenerate specific ones
5. **Review videos** — Scene videos from your chosen model; regenerate any
6. **Review voiceover** — Listen to the TTS narration; request adjustments
7. **Final assembly** — Auto-concatenates, overlays audio, burns captions

At each stage you can **approve** to continue, **modify** via chat (e.g. "make it funnier"), or **regenerate** specific scenes.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Orchestration | LangGraph (StateGraph + interrupt/resume) |
| Backend | Python, FastAPI, SSE |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Script & Scenes | Claude Sonnet 4.5 (Anthropic) |
| Images | Seedream 4.5 via fal.ai |
| Videos | Seedance 1.5 / Veo 3.1 / Kling 3.0 via fal.ai |
| Voiceover | ElevenLabs TTS |
| Captions | faster-whisper transcription + FFmpeg subtitle burn |
| Video Assembly | FFmpeg |

## Prerequisites

- Python 3.12+
- Node.js 18+
- FFmpeg installed and on PATH
- API keys for: [Anthropic](https://console.anthropic.com/), [fal.ai](https://fal.ai/), [ElevenLabs](https://elevenlabs.io/)

## Setup

### 1. Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```
ANTHROPIC_API_KEY=sk-ant-...
FAL_KEY=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb   # Optional, defaults to Rachel
WHISPER_MODEL_SIZE=base                       # Optional, defaults to base
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python main.py
```

The API starts on `http://localhost:8000`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI starts on `http://localhost:3000`.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                 │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ TopicForm │→ │ ChatView │→ │ Artifact Cards   │ │
│  └───────────┘  └──────────┘  │ (Script, Images, │ │
│                     ↑ SSE     │  Videos, Audio)   │ │
│                     │         └──────────────────┘ │
└─────────────────────┼──────────────────────────────┘
                      │
              POST /resume  GET /events
                      │         │
┌─────────────────────┼─────────┼────────────────────┐
│  Backend (FastAPI)   │         │                    │
│  ┌───────────────────┴─────────┴──────────────────┐│
│  │            LangGraph Pipeline                  ││
│  │  analyze → script → scenes → images → videos   ││
│  │    → voiceover → [assemble → captions | finish]││
│  │         interrupt() at each review stage        ││
│  └────────────────────────────────────────────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │ Claude   │ │ fal.ai   │ │ElevenLabs│ │FFmpeg │ │
│  │ Service  │ │ Service  │ │ Service  │ │Service│ │
│  └──────────┘ └──────────┘ └──────────┘ └───────┘ │
└────────────────────────────────────────────────────┘
```

The pipeline uses LangGraph's `interrupt()` to pause at each review stage. The frontend connects via SSE to receive real-time events (artifacts, progress, chat messages). User actions (approve/modify/regenerate) resume the graph via REST.

## Video Models

| Model | Provider | Cost/Scene | Duration |
|-------|----------|-----------|----------|
| **Seedance 1.5 Pro** | ByteDance | ~$0.26 | 4-12s |
| **Veo 3.1** | Google DeepMind | ~$0.25 | 4-8s |
| **Kling 3.0** | Kuaishou | ~$0.30 | 3-15s |

Total cost per video: ~$1.50-1.60 (5 scenes with images + voiceover).

## Options

- **Video Model**: Choose between Seedance, Veo, or Kling at the start
- **Concat Toggle**: Assemble all scenes into one video with voiceover and captions, or keep individual scene clips

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/sessions` | Create session (topic, model, concat) |
| `POST` | `/api/sessions/{id}/resume` | Resume with action (approve/modify/regenerate) |
| `GET` | `/api/sessions/{id}/events` | SSE event stream |
| `GET` | `/api/media/{id}/{filename}` | Serve generated media |

## License

MIT
