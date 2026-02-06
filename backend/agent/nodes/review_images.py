from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from agent.modification import interpret_regeneration_request
from agent.state import VideoState


def review(state: VideoState) -> dict:
    """Pause for user to review images. Approve or request regeneration."""
    writer = get_stream_writer()

    response = interrupt({
        "stage": "images_review",
        "actions": ["approve", "modify", "regenerate"],
    })

    if response.get("action") == "approve":
        return {
            "status": "images_approved",
            "progress_messages": [f"Images approved ({len(state['scenes'])} images)"],
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
                    "I couldn't determine which images to change. "
                    "Try 'regenerate scene 2' or 'redo the first and third images'."
                ),
            },
        })
        # Return without changing status so we loop back to review again
        return {"status": "images_review_unclear"}

    # Clear image_url for scenes that need regeneration
    for i in indices:
        if 0 <= i < len(scenes):
            scenes[i].pop("image_url", None)
            scenes[i].pop("image_local_path", None)

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": f"Regenerating {len(indices)} image(s)...",
        },
    })

    return {
        "scenes": scenes,
        "status": "images_regenerating",
    }
