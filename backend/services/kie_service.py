"""
Kie AI provider — video generation via Veo 3.1 and Kling 2.6.

Kie AI uses an async task model:
  1. Submit a generation request → get taskId
  2. Poll for completion → get result URLs
  3. Download result (URLs expire after ~24h)
"""

import json
import time
import logging
import requests
from config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.kie.ai/api/v1"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.KIE_AI_API_KEY}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Veo 3.1
# ---------------------------------------------------------------------------

def generate_video_veo3(
    prompt: str,
    image_url: str | None = None,
    end_image_url: str | None = None,
    aspect_ratio: str = "16:9",
    model: str = "veo3_fast",
) -> dict:
    """Generate video with Google Veo 3.1 via Kie AI.

    model: "veo3" (quality) or "veo3_fast" (cost-efficient, recommended)
    image_url: optional start frame image
    end_image_url: optional end frame image (for first-last-frame mode)
    Returns: {"video": {"url": str}}
    """
    body: dict = {
        "prompt": prompt,
        "model": model,
        "aspectRatio": aspect_ratio,
    }

    # Image-to-video: 1 image = start frame, 2 images = first+last frame
    if image_url:
        image_urls = [image_url]
        if end_image_url:
            image_urls.append(end_image_url)
        body["imageUrls"] = image_urls

    logger.info(f"[kie/veo3] Submitting task: model={model}")
    resp = requests.post(f"{BASE_URL}/veo/generate", json=body, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 200:
        raise RuntimeError(f"Kie AI Veo3 submit failed: {data}")

    task_id = data["data"]["taskId"]
    logger.info(f"[kie/veo3] Task submitted: {task_id}")

    # Poll until complete
    video_url = _poll_veo3(task_id)
    return {"video": {"url": video_url}}


def _poll_veo3(task_id: str, timeout: int = 600, interval: int = 5) -> str:
    """Poll Veo3 task until success. Returns video URL."""
    deadline = time.time() + timeout

    while time.time() < deadline:
        time.sleep(interval)
        resp = requests.get(
            f"{BASE_URL}/veo/record-info",
            params={"taskId": task_id},
            headers=_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 200:
            logger.warning(f"[kie/veo3] Unexpected response: {data}")
            continue

        record = data.get("data", {})
        flag = record.get("successFlag", 0)

        if flag == 1:
            # Success — parse result URLs (may be at top level or nested in "response")
            urls_raw = record.get("resultUrls") or (
                record.get("response", {}) or {}
            ).get("resultUrls")
            if urls_raw is None:
                urls_raw = "[]"
            urls = json.loads(urls_raw) if isinstance(urls_raw, str) else urls_raw
            if urls:
                logger.info(f"[kie/veo3] Task {task_id} completed")
                return urls[0]
            raise RuntimeError(f"Veo3 succeeded but no URLs: {record}")

        if flag in (2, 3):
            raise RuntimeError(f"Veo3 task failed (flag={flag}): {record}")

        logger.info(f"[kie/veo3] Task {task_id} processing (flag={flag})...")

    raise TimeoutError(f"Veo3 task {task_id} timed out after {timeout}s")


# ---------------------------------------------------------------------------
# Kling 2.6 (via Market/Jobs API)
# ---------------------------------------------------------------------------

def generate_video_kling(
    prompt: str,
    image_url: str | None = None,
    duration: float = 5,
    aspect_ratio: str = "16:9",
) -> dict:
    """Generate video with Kling 2.6 via Kie AI Market API.

    Returns: {"video": {"url": str}}
    """
    dur = int(min(max(duration, 5), 10))

    body: dict = {
        "prompt": prompt,
        "duration": dur,
        "aspectRatio": aspect_ratio,
        "model": "kling-2.6",
    }

    if image_url:
        body["imageUrl"] = image_url

    logger.info(f"[kie/kling] Submitting task: duration={dur}s")
    resp = requests.post(f"{BASE_URL}/jobs/createTask", json=body, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 200:
        raise RuntimeError(f"Kie AI Kling submit failed: {data}")

    task_id = data["data"]["taskId"]
    logger.info(f"[kie/kling] Task submitted: {task_id}")

    # Poll until complete
    video_url = _poll_market(task_id)
    return {"video": {"url": video_url}}


def _poll_market(task_id: str, timeout: int = 600, interval: int = 5) -> str:
    """Poll Market/Jobs task until success. Returns result URL."""
    deadline = time.time() + timeout

    while time.time() < deadline:
        time.sleep(interval)
        resp = requests.get(
            f"{BASE_URL}/jobs/recordInfo",
            params={"taskId": task_id},
            headers=_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        record = data.get("data", {})
        state = record.get("state", "waiting")

        if state == "success":
            result_json = record.get("resultJson", "{}")
            parsed = json.loads(result_json) if isinstance(result_json, str) else result_json
            urls = parsed.get("resultUrls", [])
            if urls:
                logger.info(f"[kie/market] Task {task_id} completed")
                return urls[0]
            raise RuntimeError(f"Market task succeeded but no URLs: {record}")

        if state == "fail":
            fail_msg = record.get("failMsg", "Unknown error")
            raise RuntimeError(f"Market task failed: {fail_msg}")

        logger.info(f"[kie/market] Task {task_id} state={state}...")

    raise TimeoutError(f"Market task {task_id} timed out after {timeout}s")
