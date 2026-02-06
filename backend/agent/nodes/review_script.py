from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from agent.modification import modify_script
from agent.state import VideoState


def review(state: VideoState) -> dict:
    """Pause for user to review the script. Approve or modify."""
    writer = get_stream_writer()

    response = interrupt({
        "stage": "script_review",
        "actions": ["approve", "modify"],
    })

    if response.get("action") == "approve":
        return {
            "status": "script_approved",
            "progress_messages": [f"Script approved ({len(state['script'].split())} words)"],
        }

    # User wants modifications
    user_msg = response.get("message", "")
    writer({
        "event": "message",
        "data": {"role": "assistant", "content": "Revising the script..."},
    })
    writer({
        "event": "progress",
        "data": {"stage": "script", "message": "Revising script..."},
    })

    script = modify_script(state["script"], user_msg)
    word_count = len(script.split())

    writer({
        "event": "artifact",
        "data": {"type": "script", "content": script, "word_count": word_count},
    })
    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                f"Here's the revised script ({word_count} words). "
                "Approve or request more changes."
            ),
        },
    })

    return {
        "script": script,
        "status": "script_modified",
    }
