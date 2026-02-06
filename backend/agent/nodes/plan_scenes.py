from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from services.claude_service import plan_scenes_from_script
from agent.modification import modify_scenes
from agent.state import VideoState


def run(state: VideoState) -> dict:
    """Break script into visual scenes, then pause for user review."""
    writer = get_stream_writer()

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": "Planning visual scenes from your script..."},
    })
    writer({
        "event": "progress",
        "data": {"stage": "scenes", "message": "Planning scenes with Claude..."},
    })

    scenes = plan_scenes_from_script(state["script"])
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
                f"Planned {len(scenes)} scenes ({total_duration:.0f}s total). "
                "Review the scene breakdown, then approve or request changes."
            ),
        },
    })

    # Review loop
    while True:
        response = interrupt({
            "stage": "scenes_review",
            "actions": ["approve", "modify"],
        })

        if response.get("action") == "approve":
            break

        user_msg = response.get("message", "")
        writer({
            "event": "message",
            "data": {"role": "assistant", "content": "Updating the scene plan..."},
        })
        writer({
            "event": "progress",
            "data": {"stage": "scenes", "message": "Revising scenes..."},
        })

        scenes = modify_scenes(scenes, user_msg)
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
        "status": "scenes_approved",
        "progress_messages": [f"Scenes approved ({len(scenes)} scenes)"],
    }
