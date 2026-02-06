from langgraph.config import get_stream_writer
from services.claude_service import generate_script
from agent.state import VideoState


def generate(state: VideoState) -> dict:
    """Generate a narration script from the topic."""
    writer = get_stream_writer()

    writer({
        "event": "progress",
        "data": {"stage": "script", "message": "Writing script with Claude..."},
    })

    character_context = state.get("character_description", "")
    script = generate_script(state["input_topic"], character_context=character_context)
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

    return {
        "script": script,
        "status": "script_generated",
        "progress_messages": [f"Script generated ({word_count} words)"],
    }
