from langgraph.config import get_stream_writer
from services.fal_service import generate_image, generate_video
from utils.file_manager import download_file
from agent.state import VideoState

MODEL_DISPLAY_NAMES = {
    "seedance": "Seedance 1.5 Pro",
    "veo": "Google Veo 3.1",
    "kling": "Kling 3.0",
}


def generate(state: VideoState) -> dict:
    """Generate videos for each scene. Skips scenes that already have videos."""
    writer = get_stream_writer()
    scenes = [dict(s) for s in state["scenes"]]
    model = state["video_model"]
    job_id = state["job_id"]
    display_name = MODEL_DISPLAY_NAMES.get(model, model)

    # Determine which scenes need videos
    to_generate = [i for i, s in enumerate(scenes) if not s.get("video_local_path")]

    if len(to_generate) == len(scenes):
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": (
                    f"Generating {len(scenes)} videos with {display_name}... "
                    "This takes a few minutes per scene."
                ),
            },
        })
    elif to_generate:
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Regenerating {len(to_generate)} video(s) with {display_name}...",
            },
        })

    for idx, i in enumerate(to_generate):
        scene = scenes[i]
        writer({
            "event": "progress",
            "data": {
                "stage": "videos",
                "current": idx + 1,
                "total": len(to_generate),
                "message": f"Generating video {idx + 1} of {len(to_generate)} with {display_name}...",
            },
        })

        # If scene lost its image (from regeneration), regenerate image first
        if not scene.get("image_url"):
            img_result = generate_image(scene["image_prompt"])
            scene["image_url"] = img_result["images"][0]["url"]
            scene["image_local_path"] = download_file(
                scene["image_url"], job_id, f"scene_{i + 1}.png"
            )

        result = generate_video(
            model=model,
            image_url=scene["image_url"],
            prompt=f"Cinematic motion, {scene['visual_description']}",
            duration=scene["duration"],
        )

        video_url = result["video"]["url"]
        scene["video_local_path"] = download_file(
            video_url, job_id, f"scene_{i + 1}.mp4"
        )

        writer({
            "event": "artifact",
            "data": {
                "type": "video",
                "scene_index": i,
                "url": f"/api/media/{job_id}/scene_{i + 1}.mp4",
            },
        })

    # Emit artifacts for already-existing videos (so frontend has full set)
    for i, scene in enumerate(scenes):
        if i not in to_generate and scene.get("video_local_path"):
            writer({
                "event": "artifact",
                "data": {
                    "type": "video",
                    "scene_index": i,
                    "url": f"/api/media/{job_id}/scene_{i + 1}.mp4",
                },
            })

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                f"All {len(scenes)} scene videos are ready! "
                "Review them, or ask me to regenerate any scene."
            ),
        },
    })

    return {
        "scenes": scenes,
        "status": "videos_generated",
        "progress_messages": [f"Videos generated ({len(scenes)} videos)"],
    }
