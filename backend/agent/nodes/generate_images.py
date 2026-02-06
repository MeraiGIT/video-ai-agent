import time
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from services.fal_service import generate_image
from utils.file_manager import download_file
from agent.modification import interpret_regeneration_request
from agent.state import VideoState


def run(state: VideoState) -> dict:
    """Generate images for each scene, then pause for user review."""
    writer = get_stream_writer()
    scenes = list(state["scenes"])  # copy to avoid mutation issues
    job_id = state["job_id"]

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": f"Generating {len(scenes)} images with Seedream 4.5...",
        },
    })

    # Generate all images
    for i, scene in enumerate(scenes):
        writer({
            "event": "progress",
            "data": {
                "stage": "images",
                "current": i + 1,
                "total": len(scenes),
                "message": f"Generating image {i + 1} of {len(scenes)}...",
            },
        })

        result = generate_image(scene["image_prompt"])
        image_url = result["images"][0]["url"]
        scene["image_url"] = image_url
        scene["image_local_path"] = download_file(
            image_url, job_id, f"scene_{i + 1}.png"
        )

        # Emit each image as it completes
        writer({
            "event": "artifact",
            "data": {
                "type": "image",
                "scene_index": i,
                "url": f"/api/media/{job_id}/scene_{i + 1}.png",
                "prompt": scene["image_prompt"][:100],
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

    # Review loop with regeneration support
    while True:
        response = interrupt({
            "stage": "images_review",
            "actions": ["approve", "modify", "regenerate"],
        })

        if response.get("action") == "approve":
            break

        # Determine which scenes to regenerate
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
                        "I couldn't determine which images to change. "
                        "Try 'regenerate scene 2' or 'redo the first and third images'."
                    ),
                },
            })
            continue

        # Regenerate specified images
        for i in indices:
            if i < 0 or i >= len(scenes):
                continue
            writer({
                "event": "progress",
                "data": {
                    "stage": "images",
                    "message": f"Regenerating image for scene {i + 1}...",
                },
            })

            result = generate_image(scenes[i]["image_prompt"])
            image_url = result["images"][0]["url"]
            scenes[i]["image_url"] = image_url
            scenes[i]["image_local_path"] = download_file(
                image_url, job_id, f"scene_{i + 1}.png"
            )

            writer({
                "event": "artifact",
                "data": {
                    "type": "image",
                    "scene_index": i,
                    "url": f"/api/media/{job_id}/scene_{i + 1}.png?t={int(time.time())}",
                    "regenerated": True,
                },
            })

        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": (
                    f"Regenerated {len(indices)} image(s). "
                    "How do they look? Approve or regenerate more."
                ),
            },
        })

    return {
        "scenes": scenes,
        "status": "images_approved",
        "progress_messages": [f"Images approved ({len(scenes)} images)"],
    }
