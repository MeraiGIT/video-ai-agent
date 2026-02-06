from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from agent.modification import modify_scenes
from agent.state import VideoState


def review(state: VideoState) -> dict:
    """Pause for user to review the scene plan. Approve or modify."""
    writer = get_stream_writer()

    response = interrupt({
        "stage": "scenes_review",
        "actions": ["approve", "modify"],
    })

    if response.get("action") == "approve":
        return {
            "status": "scenes_approved",
            "progress_messages": [f"Scenes approved ({len(state['scenes'])} scenes)"],
        }

    # User wants modifications
    user_msg = response.get("message", "")
    writer({
        "event": "message",
        "data": {"role": "assistant", "content": "Updating the scene plan..."},
    })
    writer({
        "event": "progress",
        "data": {"stage": "scenes", "message": "Revising scenes..."},
    })

    scenes = modify_scenes(state["scenes"], user_msg)
    total_duration = sum(s["duration"] for s in scenes)

    writer({
        "event": "artifact",
        "data": {
            "type": "scenes",
            "content": scenes,
            "count": len(scenes),
            "total_duration": total_duration,
        },
    })
    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                f"Updated to {len(scenes)} scenes ({total_duration:.0f}s). "
                "Approve or request more changes."
            ),
        },
    })

    return {
        "scenes": scenes,
        "status": "scenes_modified",
    }
