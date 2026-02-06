from langgraph.config import get_stream_writer
from agent.state import VideoState


def run(state: VideoState) -> dict:
    """Parse and validate the user's input topic."""
    writer = get_stream_writer()
    topic = state["input_topic"].strip()

    if not topic:
        raise ValueError("Input topic cannot be empty")

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                f"Great topic! I'll create a video about "
                f'"{topic[:80]}{"..." if len(topic) > 80 else ""}". '
                "Let me start by writing a script..."
            ),
        },
    })

    return {
        "input_topic": topic,
        "status": "input_analyzed",
        "progress_messages": [f"Topic: {topic[:80]}"],
    }
