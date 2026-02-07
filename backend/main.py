import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import settings
from services.ffmpeg_service import check_ffmpeg_available

logger = logging.getLogger(__name__)


async def _cleanup_old_jobs():
    """Periodically delete job workspace directories older than 2 hours."""
    while True:
        await asyncio.sleep(600)  # Check every 10 minutes
        try:
            if not os.path.exists(settings.WORK_DIR):
                continue
            cutoff = time.time() - 7200  # 2 hours ago
            for entry in os.scandir(settings.WORK_DIR):
                if entry.is_dir() and entry.stat().st_mtime < cutoff:
                    import shutil

                    shutil.rmtree(entry.path, ignore_errors=True)
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
    # Ensure workspace directory exists
    os.makedirs(settings.WORK_DIR, exist_ok=True)
    # Start cleanup task
    cleanup_task = asyncio.create_task(_cleanup_old_jobs())
    yield
    # Shutdown
    cleanup_task.cancel()


app = FastAPI(
    title="AI Content Maker",
    description="Autonomous video creation agent",
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
