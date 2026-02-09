"""Assemble node — combines produced assets into a unified output.

Handles different content types dynamically:
- Video: concat clips with transitions → overlay mixed audio
- Graphic: composite layers → render final image
- Audio: join segments → normalize
The blueprint determines what assembly steps are needed.
"""

import logging

from langgraph.config import get_stream_writer

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Combine produced assets into a single output."""
    writer = get_stream_writer()
    job_id = state.get("job_id", "unknown")
    content_type = state.get("content_type", "short_video")
    blueprint = state.get("blueprint", {})

    writer({
        "event": "progress",
        "data": {"stage": "assembly", "message": "Assembling final output..."},
    })

    try:
        if content_type in ("short_video", "long_video", "motion_graphics"):
            assembled_path = _assemble_video(state, blueprint, job_id, writer)
        elif content_type in ("graphic", "graphic_design", "poster"):
            assembled_path = _assemble_graphic(state, blueprint, job_id, writer)
        elif content_type in ("audio", "podcast"):
            assembled_path = _assemble_audio(state, blueprint, job_id, writer)
        else:
            # Default: try video assembly, fall back to first available asset
            assembled_path = _assemble_video(state, blueprint, job_id, writer)
    except Exception as e:
        logger.error("Assembly failed: %s", e)
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Assembly encountered an issue: {str(e)[:100]}. Using available assets directly.",
            },
        })
        assembled_path = _fallback_path(state)

    if assembled_path:
        writer({
            "event": "artifact",
            "data": {"type": "final_video", "url": assembled_path},
        })

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Assembly complete! Here's the assembled output.",
        },
    })

    return {
        "assembled_path": assembled_path,
        "status": "assembly_complete",
        "progress_messages": [f"Assembly complete: {assembled_path or 'N/A'}"],
    }


def _assemble_video(state, blueprint, job_id, writer):
    """Assemble video content: concat clips + overlay audio."""
    videos = state.get("videos", [])
    if not videos:
        logger.warning("No videos to assemble")
        return ""

    video_paths = [v["local_path"] for v in videos if v.get("local_path")]
    if not video_paths:
        # Try URLs
        video_paths = [v["url"] for v in videos if v.get("url")]

    if not video_paths:
        return ""

    # Determine transition type from blueprint or state
    transition = state.get("transition_type", "fade")
    transition_dur = 0.5

    style_guide = blueprint.get("style_guide", {})
    if isinstance(style_guide, dict):
        transition = style_guide.get("transition", transition)

    from services.ffmpeg_service import download_if_url

    # Ensure all paths are local
    local_paths = []
    for p in video_paths:
        local_paths.append(download_if_url(p, job_id))

    writer({
        "event": "progress",
        "data": {"stage": "assembly", "message": f"Concatenating {len(local_paths)} clips..."},
    })

    # Concatenate
    if len(local_paths) == 1:
        concat_path = local_paths[0]
    else:
        if transition == "cut":
            from services.ffmpeg_service import concat_videos
            concat_path = concat_videos(local_paths, job_id)
        else:
            from services.ffmpeg_service import concat_videos_with_transitions
            concat_path = concat_videos_with_transitions(
                local_paths, job_id, transition=transition, transition_duration=transition_dur,
            )

    # Overlay audio (voiceover or mixed audio)
    audio_path = state.get("mixed_audio_path", state.get("voiceover_path", ""))
    if audio_path:
        writer({
            "event": "progress",
            "data": {"stage": "assembly", "message": "Overlaying audio..."},
        })
        from services.ffmpeg_service import overlay_audio
        concat_path = overlay_audio(concat_path, audio_path, job_id)

    return concat_path


def _assemble_graphic(state, blueprint, job_id, writer):
    """Assemble graphic content: return best image or composite."""
    images = state.get("images", [])
    if not images:
        return ""

    # For simple graphics, just return the best/latest image
    # For complex composites, the produce step already handled image_composite
    if len(images) == 1:
        return images[0].get("url", images[0].get("local_path", ""))

    # Return the last image (most refined)
    return images[-1].get("url", images[-1].get("local_path", ""))


def _assemble_audio(state, blueprint, job_id, writer):
    """Assemble audio content: mix or return voiceover."""
    mixed = state.get("mixed_audio_path", "")
    if mixed:
        return mixed

    voiceover = state.get("voiceover_path", "")
    if voiceover:
        return voiceover

    return ""


def _fallback_path(state):
    """Return any available output path as fallback."""
    for key in ("assembled_path", "polished_path", "voiceover_path", "mixed_audio_path"):
        path = state.get(key, "")
        if path:
            return path
    # Try first video or image
    videos = state.get("videos", [])
    if videos:
        return videos[0].get("local_path", videos[0].get("url", ""))
    images = state.get("images", [])
    if images:
        return images[0].get("url", images[0].get("local_path", ""))
    return ""
