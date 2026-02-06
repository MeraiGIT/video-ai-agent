from langgraph.config import get_stream_writer
from services.claude_service import plan_scenes_from_script
from agent.state import VideoState


def generate(state: VideoState) -> dict:
    """Break script into visual scenes."""
    writer = get_stream_writer()

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": "Planning visual scenes from your script..."},
    })
    writer({
        "event": "progress",
        "data": {"stage": "scenes", "message": "Planning scenes with Claude..."},
    })

    character_desc = state.get("character_description", "")
    scenes = plan_scenes_from_script(state["script"], character_description=character_desc)
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

    return {
        "scenes": scenes,
        "status": "scenes_generated",
        "progress_messages": [f"Scenes planned ({len(scenes)} scenes)"],
    }
