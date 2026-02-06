import time
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from services.fal_service import generate_image, generate_video
from utils.file_manager import download_file
from agent.modification import interpret_regeneration_request
from agent.state import VideoState

MODEL_DISPLAY_NAMES = {
    "seedance": "Seedance 1.5 Pro",
    "veo": "Google Veo 3.1",
    "kling": "Kling 3.0",
}


def run(state: VideoState) -> dict:
    """Generate videos for each scene, then pause for user review."""
    writer = get_stream_writer()
    scenes = list(state["scenes"])
    model = state["video_model"]
    job_id = state["job_id"]
    display_name = MODEL_DISPLAY_NAMES.get(model, model)

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

    # Generate all videos
    for i, scene in enumerate(scenes):
        writer({
            "event": "progress",
            "data": {
                "stage": "videos",
                "current": i + 1,
                "total": len(scenes),
                "message": f"Generating video {i + 1} of {len(scenes)} with {display_name}...",
            },
        })

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

    # Review loop with regeneration
    while True:
        response = interrupt({
            "stage": "videos_review",
            "actions": ["approve", "modify", "regenerate"],
        })

        if response.get("action") == "approve":
            break

        indices = response.get("indices", [])
        if response.get("action") == "modify" and not indices:
            user_msg = response.get("message", "")
            indices = interpret_regeneration_request(user_msg, scenes)

        if not indices:
            writer({
                "event": "message",
                "data": {
                    "role": "assistant",
                    "content": (
                        "I couldn't determine which videos to change. "
                        "Try 'regenerate scene 2' or 'redo the last video'."
                    ),
                },
            })
            continue

        for i in indices:
            if i < 0 or i >= len(scenes):
                continue

            # Regenerate image first, then video
            writer({
                "event": "progress",
                "data": {
                    "stage": "videos",
                    "message": f"Regenerating image + video for scene {i + 1}...",
                },
            })

            img_result = generate_image(scenes[i]["image_prompt"])
            scenes[i]["image_url"] = img_result["images"][0]["url"]
            scenes[i]["image_local_path"] = download_file(
                scenes[i]["image_url"], job_id, f"scene_{i + 1}.png"
            )

            vid_result = generate_video(
                model=model,
                image_url=scenes[i]["image_url"],
                prompt=f"Cinematic motion, {scenes[i]['visual_description']}",
                duration=scenes[i]["duration"],
            )
            video_url = vid_result["video"]["url"]
            scenes[i]["video_local_path"] = download_file(
                video_url, job_id, f"scene_{i + 1}.mp4"
            )

            writer({
                "event": "artifact",
                "data": {
                    "type": "video",
                    "scene_index": i,
                    "url": f"/api/media/{job_id}/scene_{i + 1}.mp4?t={int(time.time())}",
                    "regenerated": True,
                },
            })

        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": (
                    f"Regenerated {len(indices)} video(s). "
                    "Review and approve when ready."
                ),
            },
        })

    return {
        "scenes": scenes,
        "status": "videos_approved",
        "progress_messages": [f"Videos approved ({len(scenes)} videos)"],
    }
