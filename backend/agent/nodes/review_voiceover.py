import time
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from services.elevenlabs_service import generate_tts
from agent.modification import modify_script
from agent.state import VideoState


def review(state: VideoState) -> dict:
    """Pause for user to review voiceover. Approve or request changes."""
    writer = get_stream_writer()

    response = interrupt({
        "stage": "voiceover_review",
        "actions": ["approve", "modify"],
    })

    if response.get("action") == "approve":
        return {
            "status": "voiceover_approved",
            "progress_messages": ["Voiceover approved"],
        }

    # User wants modifications - revise narration text, then regenerate TTS
    user_msg = response.get("message", "")
    job_id = state["job_id"]

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": "Adjusting the voiceover..."},
    })
    writer({
        "event": "progress",
        "data": {"stage": "voiceover", "message": "Revising narration text..."},
    })

    full_narration = " ".join(scene["narration"] for scene in state["scenes"])
    revised_narration = modify_script(full_narration, user_msg)

    writer({
        "event": "progress",
        "data": {"stage": "voiceover", "message": "Regenerating voiceover..."},
    })
    voiceover_path = generate_tts(revised_narration, job_id)

    writer({
        "event": "artifact",
        "data": {
            "type": "voiceover",
            "url": f"/api/media/{job_id}/voiceover.mp3?t={int(time.time())}",
        },
    })
    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Here's the updated voiceover. Approve or request more changes.",
        },
    })

    return {
        "voiceover_path": voiceover_path,
        "status": "voiceover_modified",
    }
