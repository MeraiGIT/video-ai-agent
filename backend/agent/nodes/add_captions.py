from langgraph.config import get_stream_writer
from services.whisper_service import transcribe_to_srt
from services.ffmpeg_service import burn_subtitles
from services import supabase_service
from agent.state import VideoState


def run(state: VideoState) -> dict:
    """Add auto-generated captions to the video. Auto-runs, no interrupt."""
    writer = get_stream_writer()
    job_id = state["job_id"]

    if state.get("status") == "error":
        return {"status": "error", "progress_messages": ["Skipped captions due to assembly error"]}

    try:
        writer({
            "event": "progress",
            "data": {"stage": "assembly", "message": "Transcribing voiceover with Whisper..."},
        })
        srt_path = transcribe_to_srt(state["voiceover_path"], job_id)

        writer({
            "event": "progress",
            "data": {"stage": "assembly", "message": "Burning subtitles into video..."},
        })
        final_path = burn_subtitles(state["assembled_video_path"], srt_path, job_id)

        writer({
            "event": "artifact",
            "data": {
                "type": "final_video",
                "url": f"/api/media/{job_id}/final.mp4",
            },
        })
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": "Your video is complete with captions! Download it or create another.",
            },
        })
        writer({
            "event": "complete",
            "data": {"video_url": f"/api/media/{job_id}/final.mp4"},
        })

        # Upload final video to Supabase + mark project complete
        project_id = state.get("project_id")
        if project_id:
            storage_path = f"{project_id}/final.mp4"
            public_url = supabase_service.upload_file(
                final_path, storage_path, content_type="video/mp4"
            )
            supabase_service.create_media_record(
                project_id=project_id,
                media_type="final_video",
                public_url=public_url,
                storage_path=storage_path,
                filename="final.mp4",
            )
            supabase_service.update_project(project_id, {
                "status": "completed",
                "completed_at": "now()",
            })

        return {
            "captions_srt_path": srt_path,
            "final_video_path": final_path,
            "status": "completed",
            "progress_messages": ["Video complete with captions!"],
        }
    except Exception as e:
        error_msg = str(e)
        writer({
            "event": "error",
            "data": {"message": f"Caption generation failed: {error_msg}"},
        })
        writer({
            "event": "complete",
            "data": {"error": error_msg},
        })
        return {
            "status": "error",
            "error": error_msg,
            "progress_messages": [f"Captions failed: {error_msg}"],
        }
