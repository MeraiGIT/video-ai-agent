from langgraph.config import get_stream_writer
from agent.state import VideoState


def run(state: VideoState) -> dict:
    """Skip assembly - show individual scene videos as final output."""
    writer = get_stream_writer()
    job_id = state["job_id"]
    scenes = state["scenes"]

    urls = [f"/api/media/{job_id}/scene_{i + 1}.mp4" for i in range(len(scenes))]

    writer({
        "event": "artifact",
        "data": {"type": "individual_videos", "urls": urls},
    })
    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                f"Your {len(scenes)} scene videos are ready for download! "
                "Each scene is available individually."
            ),
        },
    })
    writer({
        "event": "complete",
        "data": {"type": "individual", "urls": urls},
    })

    return {
        "status": "completed",
        "progress_messages": ["Individual scene videos ready"],
    }
