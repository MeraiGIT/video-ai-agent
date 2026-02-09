import os
import shutil
import time
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

# Auto-cleanup: remove workspace dirs older than this (seconds)
WORKSPACE_MAX_AGE = 2 * 60 * 60  # 2 hours


def get_job_dir(job_id: str) -> str:
    path = os.path.join(settings.WORK_DIR, job_id)
    os.makedirs(path, exist_ok=True)
    return path


def get_job_path(job_id: str, filename: str) -> str:
    job_dir = get_job_dir(job_id)
    return os.path.join(job_dir, filename)


def download_file(url: str, job_id: str, filename: str) -> str:
    """Download a file from URL to the job's workspace directory."""
    local_path = get_job_path(job_id, filename)
    with httpx.Client(timeout=180.0) as client:
        response = client.get(url)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(response.content)
    return local_path


def cleanup_old_workspaces():
    """Remove workspace directories older than WORKSPACE_MAX_AGE.

    Called periodically to prevent disk usage from growing unbounded.
    """
    work_dir = settings.WORK_DIR
    if not os.path.isdir(work_dir):
        return

    now = time.time()
    removed = 0
    for entry in os.listdir(work_dir):
        entry_path = os.path.join(work_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        try:
            mtime = os.path.getmtime(entry_path)
            if now - mtime > WORKSPACE_MAX_AGE:
                shutil.rmtree(entry_path, ignore_errors=True)
                removed += 1
        except OSError:
            continue

    if removed:
        logger.info("Cleaned up %d old workspace(s)", removed)
