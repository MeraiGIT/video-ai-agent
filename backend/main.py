import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import settings
from services.ffmpeg_service import check_ffmpeg_available

logger = logging.getLogger(__name__)


async def _cleanup_old_jobs():
    """Periodically delete job workspace directories older than 2 hours."""
    from utils.file_manager import cleanup_old_workspaces

    while True:
        await asyncio.sleep(600)  # Check every 10 minutes
        try:
            cleanup_old_workspaces()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check FFmpeg availability
    ffmpeg_ok, ffmpeg_version = check_ffmpeg_available()
    if ffmpeg_ok:
        logger.info(f"FFmpeg found: {ffmpeg_version}")
    else:
        logger.warning(
            "FFmpeg not found! Video assembly and captions will not work. "
            "Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
        )
    # Log service availability
    services = {
        "Anthropic (Claude)": bool(settings.ANTHROPIC_API_KEY),
        "fal.ai": bool(settings.FAL_KEY),
        "ElevenLabs": bool(settings.ELEVENLABS_API_KEY),
        "Gemini": bool(settings.GOOGLE_API_KEY),
        "Tavily": bool(settings.TAVILY_API_KEY),
        "Nanana": bool(settings.NANANA_API_KEY),
    }
    for name, available in services.items():
        status = "available" if available else "not configured"
        logger.info(f"Service {name}: {status}")

    # Ensure workspace directory exists
    os.makedirs(settings.WORK_DIR, exist_ok=True)
    # Start cleanup task
    cleanup_task = asyncio.create_task(_cleanup_old_jobs())
    yield
    # Shutdown
    cleanup_task.cancel()


app = FastAPI(
    title="AI Production Studio",
    description="Universal AI content creation agent — any creative request, professional output",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3111",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3111",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
