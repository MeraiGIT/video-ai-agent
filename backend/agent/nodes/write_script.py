from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from services.claude_service import generate_script
from agent.modification import modify_script
from agent.state import VideoState


def run(state: VideoState) -> dict:
    """Generate a narration script, then pause for user review."""
    writer = get_stream_writer()

    writer({
        "event": "progress",
        "data": {"stage": "script", "message": "Writing script with Claude..."},
    })

    script = generate_script(state["input_topic"])
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
                f"Here's your script ({word_count} words, ~45 seconds). "
                "You can approve it or tell me what to change."
            ),
        },
    })

    # Review loop - pauses graph until user responds
    while True:
        response = interrupt({
            "stage": "script_review",
            "actions": ["approve", "modify"],
        })

        if response.get("action") == "approve":
            break

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

        script = modify_script(script, user_msg)
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
        "status": "script_approved",
        "progress_messages": [f"Script approved ({word_count} words)"],
    }
