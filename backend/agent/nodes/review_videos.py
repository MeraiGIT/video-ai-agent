from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from agent.modification import interpret_regeneration_request
from agent.state import VideoState


def review(state: VideoState) -> dict:
    """Pause for user to review videos. Approve or request regeneration."""
    writer = get_stream_writer()

    response = interrupt({
        "stage": "videos_review",
        "actions": ["approve", "modify", "regenerate"],
    })

    if response.get("action") == "approve":
        return {
            "status": "videos_approved",
            "progress_messages": [f"Videos approved ({len(state['scenes'])} videos)"],
        }

    # Determine which scenes to regenerate
    scenes = [dict(s) for s in state["scenes"]]
    indices = response.get("indices", [])
    if response.get("action") == "modify" and not indices:
        user_msg = response.get("message", "")
        indices = interpret_regeneration_request(user_msg, scenes)

    if not indices:
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": (
                    "I couldn't determine which videos to change. "
                    "Try 'regenerate scene 2' or 'redo the last video'."
                ),
            },
        })
        return {"status": "videos_review_unclear"}

    # Clear video + image paths for scenes that need regeneration
    for i in indices:
        if 0 <= i < len(scenes):
            scenes[i].pop("video_local_path", None)
            scenes[i].pop("image_url", None)
            scenes[i].pop("image_local_path", None)

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": f"Regenerating {len(indices)} video(s)...",
        },
    })

    return {
        "scenes": scenes,
        "status": "videos_regenerating",
    }
