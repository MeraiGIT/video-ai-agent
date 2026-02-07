from langgraph.config import get_stream_writer
from services.ffmpeg_service import concat_videos, overlay_audio
from agent.state import VideoState


def run(state: VideoState) -> dict:
    """Assemble final video: concatenate scenes + overlay voiceover. Auto-runs, no interrupt."""
    writer = get_stream_writer()
    job_id = state["job_id"]

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Assembling your video - concatenating scenes and adding voiceover...",
        },
    })

    try:
        video_paths = [scene["video_local_path"] for scene in state["scenes"]]

        writer({
            "event": "progress",
            "data": {"stage": "assembly", "message": "Concatenating scene videos..."},
        })
        concat_path = concat_videos(video_paths, job_id)

        writer({
            "event": "progress",
            "data": {"stage": "assembly", "message": "Adding voiceover audio..."},
        })
        assembled_path = overlay_audio(concat_path, state["voiceover_path"], job_id)

        return {
            "assembled_video_path": assembled_path,
            "status": "video_assembled",
            "progress_messages": ["Video assembled with voiceover"],
        }
    except Exception as e:
        error_msg = str(e)
        writer({
            "event": "error",
            "data": {"message": f"Video assembly failed: {error_msg}"},
        })
        writer({
            "event": "complete",
            "data": {"error": error_msg},
        })
        return {
            "status": "error",
            "error": error_msg,
            "progress_messages": [f"Assembly failed: {error_msg}"],
        }
