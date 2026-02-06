import os
import httpx
from config import settings


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
