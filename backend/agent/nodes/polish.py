"""Polish node — applies finishing touches to the assembled output.

Handles per-content-type polishing:
- Video: captions (transcribe → burn), text overlays, audio normalization, thumbnail
- Graphic: pass through (polish already applied during production)
- Audio: loudness normalization
The creative brief and blueprint drive what polish steps are applied.
"""

import logging
import os

from langgraph.config import get_stream_writer

from agent.state import ProductionState
from utils.file_manager import get_job_path

logger = logging.getLogger(__name__)

# Platform loudness standards (LUFS)
PLATFORM_LOUDNESS = {
    "tiktok": -14,
    "youtube": -14,
    "instagram": -14,
    "linkedin": -16,
    "podcast": -16,
    "custom": -14,
}

# Default caption style per platform
PLATFORM_CAPTION_STYLE = {
    "tiktok": "tiktok",
    "youtube": "youtube",
    "instagram": "bold",
    "linkedin": "minimal",
    "podcast": "none",
    "custom": "youtube",
}


def run(state: ProductionState) -> dict:
    """Apply finishing touches to the assembled output."""
    writer = get_stream_writer()
    job_id = state.get("job_id", "unknown")
    content_type = state.get("content_type", "short_video")
    assembled_path = state.get("assembled_path", "")

    if not assembled_path:
        logger.warning("No assembled path — skipping polish")
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": "No assembled output to polish. Moving forward.",
            },
        })
        return {
            "polished_path": "",
            "status": "polish_complete",
            "progress_messages": ["Polish skipped — no assembled output"],
        }

    writer({
        "event": "progress",
        "data": {"stage": "polish", "message": "Applying finishing touches..."},
    })

    polished_path = assembled_path

    try:
        if content_type in ("short_video", "long_video", "motion_graphics"):
            polished_path = _polish_video(state, polished_path, job_id, writer)
        elif content_type in ("audio", "podcast"):
            polished_path = _polish_audio(polished_path, job_id, state, writer)
        # Graphic content passes through — no post-production polish needed
    except Exception as e:
        logger.error("Polish failed: %s", e)
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Some polish steps had issues: {str(e)[:100]}. Using the best available output.",
            },
        })

    if polished_path and polished_path != assembled_path:
        writer({
            "event": "artifact",
            "data": {"type": "final_video", "url": polished_path},
        })

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Polish complete! Here's the polished output.",
        },
    })

    return {
        "polished_path": polished_path,
        "status": "polish_complete",
        "progress_messages": [f"Polish complete: {polished_path or 'N/A'}"],
    }


def _polish_video(state: dict, video_path: str, job_id: str, writer) -> str:
    """Polish video: captions, text overlays, audio normalization, thumbnail."""
    platform = state.get("target_platform", "youtube")
    creative_brief = state.get("creative_brief", {})
    blueprint = state.get("blueprint", {})

    current_path = video_path

    # Step 1: Captions — transcribe audio and burn subtitles
    caption_style = state.get("caption_style", "")
    if not caption_style:
        # Derive from creative brief or platform default
        if isinstance(creative_brief, dict):
            caption_style = creative_brief.get("caption_style", "")
        if not caption_style:
            caption_style = PLATFORM_CAPTION_STYLE.get(platform, "youtube")

    if caption_style != "none":
        current_path = _burn_captions(current_path, job_id, caption_style, writer)

    # Step 2: Text overlays from blueprint
    overlays = []
    if isinstance(blueprint, dict):
        overlays = blueprint.get("text_overlays", [])
        # Also check style_guide for title card / CTA
        style_guide = blueprint.get("style_guide", {})
        if isinstance(style_guide, dict):
            title_card = style_guide.get("title_card")
            if title_card and isinstance(title_card, dict):
                overlays.insert(0, title_card)

    if overlays:
        current_path = _apply_text_overlays(current_path, overlays, job_id, writer)

    # Step 3: Audio normalization
    current_path = _normalize_audio(current_path, job_id, platform, writer)

    # Step 4: Generate thumbnail (extract frame from midpoint)
    _generate_thumbnail(current_path, job_id, writer)

    return current_path


def _burn_captions(video_path: str, job_id: str, style_name: str, writer) -> str:
    """Transcribe audio and burn captions onto the video."""
    writer({
        "event": "progress",
        "data": {"stage": "polish", "message": "Adding captions..."},
    })

    try:
        from services.ffmpeg_service import extract_audio
        audio_path = extract_audio(video_path, job_id)
    except Exception as e:
        logger.warning("Audio extraction failed, skipping captions: %s", e)
        return video_path

    try:
        from services.whisper_service import transcribe_to_word_srt
        srt_path = transcribe_to_word_srt(audio_path, job_id)
    except Exception as e:
        logger.warning("Transcription failed, skipping captions: %s", e)
        return video_path

    try:
        from services.ffmpeg_service import burn_subtitles
        captioned_path = burn_subtitles(video_path, srt_path, job_id, style_name=style_name)
        return captioned_path
    except Exception as e:
        logger.warning("Caption burn failed: %s", e)
        return video_path


def _apply_text_overlays(video_path: str, overlays: list, job_id: str, writer) -> str:
    """Apply text overlays (title cards, CTAs) to the video."""
    from services.ffmpeg_service import add_text_overlay_to_video

    writer({
        "event": "progress",
        "data": {"stage": "polish", "message": f"Adding {len(overlays)} text overlay(s)..."},
    })

    current_path = video_path
    for i, overlay in enumerate(overlays):
        if not isinstance(overlay, dict) or "text" not in overlay:
            continue
        try:
            current_path = add_text_overlay_to_video(
                video_path=current_path,
                text=overlay["text"],
                job_id=job_id,
                position=overlay.get("position", "bottom"),
                font_size=overlay.get("font_size", 48),
                font_color=overlay.get("font_color", "white"),
                start_time=overlay.get("start_time", 0.0),
                end_time=overlay.get("end_time"),
                output_filename=f"overlay_{i}.mp4",
            )
        except Exception as e:
            logger.warning("Text overlay %d failed: %s", i, e)

    return current_path


def _normalize_audio(video_path: str, job_id: str, platform: str, writer) -> str:
    """Normalize audio to platform loudness standard using FFmpeg loudnorm."""
    import subprocess

    writer({
        "event": "progress",
        "data": {"stage": "polish", "message": "Normalizing audio levels..."},
    })

    target_lufs = PLATFORM_LOUDNESS.get(platform, -14)
    output_path = get_job_path(job_id, "normalized.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.warning("Audio normalization failed, using original: %s", result.stderr[-200:])
            return video_path
        return output_path
    except Exception as e:
        logger.warning("Audio normalization error: %s", e)
        return video_path


def _generate_thumbnail(video_path: str, job_id: str, writer) -> str:
    """Extract a frame from the video midpoint as a thumbnail."""
    import subprocess

    thumbnail_path = get_job_path(job_id, "thumbnail.jpg")

    # Probe duration to pick midpoint
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        duration = float(result.stdout.strip())
        midpoint = duration / 2
    except Exception:
        midpoint = 2.0

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(midpoint),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        thumbnail_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if os.path.exists(thumbnail_path):
            writer({
                "event": "artifact",
                "data": {"type": "image", "url": thumbnail_path, "scene_index": -1, "total_scenes": 0},
            })
            return thumbnail_path
    except Exception as e:
        logger.warning("Thumbnail generation failed: %s", e)

    return ""


def _polish_audio(audio_path: str, job_id: str, state: dict, writer) -> str:
    """Polish audio content: loudness normalization."""
    import subprocess

    platform = state.get("target_platform", "podcast")
    target_lufs = PLATFORM_LOUDNESS.get(platform, -16)
    output_path = get_job_path(job_id, "polished_audio.mp3")

    writer({
        "event": "progress",
        "data": {"stage": "polish", "message": "Normalizing audio levels..."},
    })

    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.warning("Audio normalization failed: %s", result.stderr[-200:])
            return audio_path
        return output_path
    except Exception as e:
        logger.warning("Audio polish error: %s", e)
        return audio_path
