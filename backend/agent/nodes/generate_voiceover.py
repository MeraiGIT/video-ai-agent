from langgraph.config import get_stream_writer
from services.elevenlabs_service import generate_tts
from services import supabase_service
from agent.state import VideoState


def generate(state: VideoState) -> dict:
    """Generate voice narration from scene narrations."""
    writer = get_stream_writer()
    job_id = state["job_id"]

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

    # Upload voiceover to Supabase Storage
    project_id = state.get("project_id")
    if project_id:
        storage_path = f"{project_id}/voiceover.mp3"
        public_url = supabase_service.upload_file(
            voiceover_path, storage_path, content_type="audio/mpeg"
        )
        supabase_service.create_media_record(
            project_id=project_id,
            media_type="voiceover",
            public_url=public_url,
            storage_path=storage_path,
            filename="voiceover.mp3",
        )

    return {
        "voiceover_path": voiceover_path,
        "status": "voiceover_generated",
        "progress_messages": ["Voiceover generated"],
    }
