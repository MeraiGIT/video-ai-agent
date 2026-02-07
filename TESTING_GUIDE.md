# AI Content Maker - Testing Guide

## Prerequisites Checklist

Before testing, verify you have these installed:

```bash
# Check all three are installed
ffmpeg -version    # Need FFmpeg (any recent version)
python3 --version  # Need Python 3.12+
node --version     # Need Node.js 18+
```

## Step 1: Set Up API Keys

Create your `.env` file in the project root:

```bash
cd ~/Desktop/video-ai-agent
cp .env.example .env
```

Edit `.env` and fill in your real API keys:

```
ANTHROPIC_API_KEY=sk-ant-...     # Required
FAL_KEY=...                       # Required
KIE_AI_API_KEY=...                # Required (for Veo/Kling via Kie AI)
ELEVENLABS_API_KEY=...            # Required
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb  # Default Rachel voice (optional to change)
WHISPER_MODEL_SIZE=base           # Options: tiny, base, small, medium, large

# Optional: Supabase (enables generation history)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-anon-or-service-key
```

### Where to get keys:
- **Anthropic**: https://console.anthropic.com/ -> API Keys
- **fal.ai**: https://fal.ai/dashboard/keys -> Create Key
- **Kie AI**: https://kie.ai/ -> Dashboard -> API Keys
- **ElevenLabs**: https://elevenlabs.io/ -> Profile -> API Keys
- **Supabase**: https://supabase.com/dashboard -> Project Settings -> API

### Cost estimate per video (3 scenes):
| Service | Cost |
|---------|------|
| Claude (script + scenes) | ~$0.02 |
| Seedream 4.5 images | ~$0.12 (3 images x $0.04) |
| Video gen (Seedance 1.5) | ~$0.78 (3 videos x $0.26) |
| Video gen (Veo 3.1 Fast) | ~$0.30 (3 videos x $0.10) |
| Video gen (Kling 2.6) | ~$0.45 (3 videos x $0.15) |
| ElevenLabs TTS | ~$0.03 |
| **Total per video** | **~$0.50-1.00** |

## Step 2: Start the Backend

```bash
cd ~/Desktop/video-ai-agent/backend

# Activate the virtual environment
source .venv/bin/activate

# Start the server
python main.py
```

You should see:
```
INFO:     FFmpeg found: ffmpeg version 7.x ...
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Quick API test (in another terminal):
```bash
# Check the server is running
curl http://localhost:8000/api/projects
# Should return: {"projects":[]}

# Create a session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"topic": "test", "video_model": "seedance", "concat_enabled": false}'
# Should return: {"session_id": "some-uuid-here"}
```

## Step 3: Start the Frontend

In a **new terminal**:

```bash
cd ~/Desktop/video-ai-agent/frontend
npm run dev
```

You should see:
```
> next dev --turbopack
  - Local: http://localhost:3000
```

## Step 4: Create a Video (Interactive Pipeline)

1. Open http://localhost:3000 in your browser
2. Type a topic, e.g.: **"3 tips for better sleep"**
3. Select a video model:
   - **Seedance 1.5 Pro** (fal.ai) - highest quality, ~$0.26/scene
   - **Veo 3.1 Fast** (Kie AI) - best value, ~$0.10/scene
   - **Kling 2.6** (Kie AI) - good quality, ~$0.15/scene
   - **Kling O1 Character Ref** (fal.ai) - character consistency, ~$0.56/scene
4. Toggle **"Assemble into single video"** on/off
5. Click **"Start Creating"**

### Pipeline Steps (Human-in-the-Loop)

At each stage, you can **review**, **modify**, or **approve**:

| Step | What Happens | Review Options |
|------|-------------|----------------|
| 1. Analyze | AI analyzes your topic, detects characters | Auto |
| 2. Script | Generates narration script | Modify text, approve |
| 3. Scene Plan | Plans visual scenes with descriptions | Modify scenes, approve |
| 4. Images | Generates images with Seedream 4.5 | Regenerate specific scenes, approve |
| 5. Videos | Generates videos from images | Regenerate specific scenes, approve |
| 6. Voiceover | Generates TTS with ElevenLabs | Re-record, approve |
| 7a. Assembly | Concatenates + overlays audio (if enabled) | Auto |
| 7b. Captions | Burns SRT subtitles (if enabled) | Auto |

**Modification examples:**
- Script: "Make it shorter", "Add a joke", "More formal tone"
- Scenes: "Reduce to 3 scenes", "Combine scenes 1 and 2"
- Images: Type scene numbers (e.g., "1,3") to regenerate specific ones
- Videos: Same scene-number regeneration

**Expected total time: 5-15 minutes** (mostly waiting for video generation)

## Step 5: Check Generation History

If Supabase is configured:

1. Click **"History"** in the top navigation
2. You should see project cards with thumbnails and status badges
3. Click a project to open the gallery view with:
   - Script text
   - Image grid with "Open" links
   - Video players with "Open" links (Supabase Storage)
   - Voiceover audio player
4. Delete individual media items or entire projects

### History API endpoints:
```bash
# List all projects
curl http://localhost:8000/api/projects

# Get project with media
curl http://localhost:8000/api/projects/{project_id}

# Delete a project (cascading)
curl -X DELETE http://localhost:8000/api/projects/{project_id}

# Delete a single media item
curl -X DELETE http://localhost:8000/api/media-items/{media_id}
```

## Step 6: Test Each Video Model

Try the same topic with each model to compare quality:

| Model | Provider | Strengths | Duration Range |
|-------|----------|-----------|----------------|
| Seedance 1.5 Pro | fal.ai | Best quality, natural motion | 4-12 seconds |
| Veo 3.1 Fast | Kie AI | Best value, fast generation | 5-8 seconds |
| Kling 2.6 | Kie AI | Good quality, extended duration | 5-10 seconds |
| Kling O1 (Char Ref) | fal.ai | Character consistency | 5-10 seconds |

## Supabase Setup (Optional)

To enable generation history persistence:

1. Create a Supabase project at https://supabase.com
2. Run the migration to create tables:
   - `projects` table (id, name, topic, status, thumbnail_url, etc.)
   - `media` table (id, project_id, type, public_url, storage_path, etc.)
3. Create a `media` storage bucket (public)
4. Set permissive RLS policies on both tables and storage
5. Add `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` to your `.env`

The app works without Supabase - history just won't persist.

## Troubleshooting

### "Connection lost" error in frontend
- Check the backend terminal for error messages
- Most likely an API key is invalid or missing

### Backend crashes on startup
- Make sure `.env` exists in the project root (not in `backend/`)
- Verify all required API keys are set

### "FFmpeg not found" warning on startup
- Install FFmpeg: `brew install ffmpeg`
- Without FFmpeg, assembly + captions steps will fail gracefully

### Video generation takes too long / times out
- fal.ai and Kie AI queues can be slow during peak times
- The retry logic attempts 3 times with exponential backoff
- If it keeps failing, try a different video model

### Supabase upload fails with 403
- Check that storage bucket RLS policies allow INSERT/UPDATE/DELETE
- If using anon key, policies must use `USING (true)` not `auth.role() = 'service_role'`

### Subtitles not appearing
- Check that FFmpeg has `libass` support: `ffmpeg -filters | grep subtitles`
- Homebrew FFmpeg includes this by default

### Want to inspect intermediate files?
All generated files for each job are stored in:
```
backend/workspace/{job_id}/
├── scene_1.png, scene_2.png, ...    # Generated images
├── scene_1.mp4, scene_2.mp4, ...    # Generated videos
├── voiceover.mp3                      # ElevenLabs audio
├── concatenated.mp4                   # Joined scenes (concat mode)
├── assembled.mp4                      # With voiceover (concat mode)
├── captions.srt                       # Subtitle file (concat mode)
└── final.mp4                          # Final output (concat mode)
```

Files auto-delete after 2 hours. If Supabase is configured, videos and audio are uploaded to Supabase Storage for permanent access.

## Testing Checklist

### Core Pipeline
- [ ] Backend starts without errors on port 8000
- [ ] Frontend starts without errors on port 3000
- [ ] Topic form submits and creates a session
- [ ] SSE stream shows progress events in browser
- [ ] Script generation works (Claude)
- [ ] Script modification works (e.g., "make it shorter")
- [ ] Scene planning works (Claude)
- [ ] Scene modification works (e.g., "reduce to 3 scenes")
- [ ] Image generation works (Seedream 4.5)
- [ ] Image regeneration works (specific scenes)
- [ ] Video generation works (test at least one model)
- [ ] Voiceover generates properly (ElevenLabs)
- [ ] "Approve & Continue" advances to next stage

### Assembly (Concat Mode)
- [ ] Video concatenation works (FFmpeg)
- [ ] Audio overlay works
- [ ] Caption burning works
- [ ] Final video plays in browser
- [ ] Download button works

### Individual Mode (Concat Off)
- [ ] Individual scene videos are downloadable
- [ ] Pipeline completes without assembly step

### History (Supabase)
- [ ] Project created on analyze_input
- [ ] Script saved as media record
- [ ] Images saved with fal.ai CDN URLs
- [ ] Videos uploaded to Supabase Storage
- [ ] Voiceover uploaded to Supabase Storage
- [ ] Project marked completed on finish
- [ ] History page shows project cards
- [ ] Gallery view shows all media
- [ ] Delete project works (cascading)
- [ ] Delete individual media works

### Navigation
- [ ] Header shows "Create" and "History" tabs
- [ ] Active tab is highlighted
- [ ] "New Video" button resets the form
- [ ] "Create Another" button works after completion
