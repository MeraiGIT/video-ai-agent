from langgraph.config import get_stream_writer
from services.video_router import generate_video, generate_image_for_scene
from services.model_registry import get_video_model
from agent.state import VideoState


def generate(state: VideoState) -> dict:
    """Generate videos for each scene. Skips scenes that already have videos.

    Routes through video_router which picks the correct provider (fal.ai or Kie AI).
    For kling_ref model, passes reference images for character consistency.
    """
    writer = get_stream_writer()
    scenes = [dict(s) for s in state["scenes"]]
    model_id = state["video_model"]
    job_id = state["job_id"]

    model_info = get_video_model(model_id)
    display_name = model_info["name"]

    reference_images = state.get("reference_images", [])

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
            ref_url = reference_images[0] if reference_images else None
            image_url, local_path = generate_image_for_scene(
                prompt=scene["image_prompt"],
                job_id=job_id,
                filename=f"scene_{i + 1}.png",
                reference_image_url=ref_url,
            )
            scene["image_url"] = image_url
            scene["image_local_path"] = local_path

        local_path = generate_video(
            model_id=model_id,
            image_url=scene["image_url"],
            prompt=f"Cinematic motion, {scene['visual_description']}",
            duration=scene["duration"],
            job_id=job_id,
            filename=f"scene_{i + 1}.mp4",
            reference_images=reference_images if reference_images else None,
        )
        scene["video_local_path"] = local_path

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
