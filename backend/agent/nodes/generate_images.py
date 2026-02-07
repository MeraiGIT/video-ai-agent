from langgraph.config import get_stream_writer
from services.video_router import generate_image_for_scene
from services import supabase_service
from agent.state import VideoState


def generate(state: VideoState) -> dict:
    """Generate images for each scene. Skips scenes that already have images.

    Supports reference images: if the user uploaded photos, uses FLUX dev
    image-to-image to preserve the subject while adapting to each scene.
    """
    writer = get_stream_writer()
    scenes = [dict(s) for s in state["scenes"]]  # deep copy to avoid mutation
    job_id = state["job_id"]

    # Reference image for character consistency (first uploaded image)
    reference_images = state.get("reference_images", [])
    ref_url = reference_images[0] if reference_images else None

    # Determine which scenes need images
    to_generate = [i for i, s in enumerate(scenes) if not s.get("image_url")]

    gen_method = "FLUX Dev (reference)" if ref_url else "Seedream 4.5"

    if len(to_generate) == len(scenes):
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Generating {len(scenes)} images with {gen_method}...",
            },
        })
    elif to_generate:
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Regenerating {len(to_generate)} image(s)...",
            },
        })

    for idx, i in enumerate(to_generate):
        scene = scenes[i]
        writer({
            "event": "progress",
            "data": {
                "stage": "images",
                "current": idx + 1,
                "total": len(to_generate),
                "message": f"Generating image {idx + 1} of {len(to_generate)}...",
            },
        })

        image_url, local_path = generate_image_for_scene(
            prompt=scene["image_prompt"],
            job_id=job_id,
            filename=f"scene_{i + 1}.png",
            reference_image_url=ref_url,
        )
        scene["image_url"] = image_url
        scene["image_local_path"] = local_path

        # Save image to Supabase (fal.ai CDN URLs are permanent, no upload needed)
        project_id = state.get("project_id")
        if project_id:
            supabase_service.create_media_record(
                project_id=project_id,
                media_type="image",
                public_url=image_url,
                filename=f"scene_{i + 1}.png",
                scene_number=i + 1,
            )
            # First image becomes the project thumbnail
            if idx == 0:
                supabase_service.update_project(project_id, {"thumbnail_url": image_url})

        writer({
            "event": "artifact",
            "data": {
                "type": "image",
                "scene_index": i,
                "url": f"/api/media/{job_id}/scene_{i + 1}.png",
                "prompt": scene["image_prompt"][:100],
            },
        })

    # Emit artifacts for already-existing images (so frontend has full set)
    for i, scene in enumerate(scenes):
        if i not in to_generate and scene.get("image_url"):
            writer({
                "event": "artifact",
                "data": {
                    "type": "image",
                    "scene_index": i,
                    "url": f"/api/media/{job_id}/scene_{i + 1}.png",
                },
            })

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                f"All {len(scenes)} images are ready! "
                "Review them and approve, or ask me to regenerate specific ones."
            ),
        },
    })

    return {
        "scenes": scenes,
        "status": "images_generated",
        "progress_messages": [f"Images generated ({len(scenes)} images)"],
    }
