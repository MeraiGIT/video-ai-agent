import time
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from services.elevenlabs_service import generate_tts
from agent.modification import modify_script
from agent.state import VideoState


def run(state: VideoState) -> dict:
    """Generate voice narration, then pause for user review."""
    writer = get_stream_writer()
    job_id = state["job_id"]

    # Combine all scene narrations
    full_narration = " ".join(scene["narration"] for scene in state["scenes"])

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Generating voiceover with ElevenLabs...",
        },
    })
    writer({
        "event": "progress",
        "data": {"stage": "voiceover", "message": "Generating voiceover..."},
    })

    voiceover_path = generate_tts(full_narration, job_id)

    writer({
        "event": "artifact",
        "data": {
            "type": "voiceover",
            "url": f"/api/media/{job_id}/voiceover.mp3",
        },
    })
    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                "Here's the voiceover. Listen and let me know if you'd like changes "
                "(e.g., 'make it slower', 'more energetic tone', 'shorter sentences')."
            ),
        },
    })

    # Review loop
    while True:
        response = interrupt({
            "stage": "voiceover_review",
            "actions": ["approve", "modify"],
        })

        if response.get("action") == "approve":
            break

        user_msg = response.get("message", "")
        writer({
            "event": "message",
            "data": {"role": "assistant", "content": "Adjusting the voiceover..."},
        })
        writer({
            "event": "progress",
            "data": {"stage": "voiceover", "message": "Revising narration text..."},
        })

        # Use Claude to revise the narration text, then regenerate TTS
        full_narration = modify_script(full_narration, user_msg)

        writer({
            "event": "progress",
            "data": {"stage": "voiceover", "message": "Regenerating voiceover..."},
        })
        voiceover_path = generate_tts(full_narration, job_id)

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
        "status": "voiceover_approved",
        "progress_messages": ["Voiceover approved"],
    }
