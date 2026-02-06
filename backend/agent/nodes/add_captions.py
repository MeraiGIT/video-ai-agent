from langgraph.config import get_stream_writer
from services.whisper_service import transcribe_to_srt
from services.ffmpeg_service import burn_subtitles
from agent.state import VideoState


def run(state: VideoState) -> dict:
    """Add auto-generated captions to the video. Auto-runs, no interrupt."""
    writer = get_stream_writer()
    job_id = state["job_id"]

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

    return {
        "captions_srt_path": srt_path,
        "final_video_path": final_path,
        "status": "completed",
        "progress_messages": ["Video complete with captions!"],
    }
