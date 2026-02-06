from langgraph.config import get_stream_writer
from services.fal_service import generate_image
from utils.file_manager import download_file
from agent.state import VideoState


def generate(state: VideoState) -> dict:
    """Generate images for each scene. Skips scenes that already have images."""
    writer = get_stream_writer()
    scenes = [dict(s) for s in state["scenes"]]  # deep copy to avoid mutation
    job_id = state["job_id"]

    # Determine which scenes need images
    to_generate = [i for i, s in enumerate(scenes) if not s.get("image_url")]

    if len(to_generate) == len(scenes):
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Generating {len(scenes)} images with Seedream 4.5...",
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

        result = generate_image(scene["image_prompt"])
        image_url = result["images"][0]["url"]
        scene["image_url"] = image_url
        scene["image_local_path"] = download_file(
            image_url, job_id, f"scene_{i + 1}.png"
        )

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
