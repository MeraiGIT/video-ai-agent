"""Image compositing capability — layer composition for graphic design."""

import logging
import os

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Composite multiple image layers into one image.

    params:
        layers: list[dict] — [{url, x, y, width, height, opacity}]
        canvas_width: int — output width
        canvas_height: int — output height
        background_color: str — hex color or "transparent"
    """
    layers = params.get("layers", [])
    canvas_width = params.get("canvas_width", 1920)
    canvas_height = params.get("canvas_height", 1080)
    bg_color = params.get("background_color", "#000000")
    job_id = state.get("job_id", "unknown")

    if not layers:
        raise ValueError("No layers for image compositing")

    try:
        from PIL import Image
        import httpx
    except ImportError:
        raise ImportError("Pillow and httpx required for image compositing")

    # Create canvas
    if bg_color == "transparent":
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    else:
        r = int(bg_color[1:3], 16)
        g = int(bg_color[3:5], 16)
        b = int(bg_color[5:7], 16)
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (r, g, b, 255))

    with httpx.Client() as client:
        for layer in layers:
            url = layer.get("url", "")
            if not url:
                continue

            resp = client.get(url)
            resp.raise_for_status()

            from io import BytesIO
            img = Image.open(BytesIO(resp.content)).convert("RGBA")

            # Resize if specified
            w = layer.get("width", img.width)
            h = layer.get("height", img.height)
            if (w, h) != (img.width, img.height):
                img = img.resize((w, h), Image.LANCZOS)

            # Apply opacity
            opacity = layer.get("opacity", 1.0)
            if opacity < 1.0:
                alpha = img.split()[3]
                alpha = alpha.point(lambda p: int(p * opacity))
                img.putalpha(alpha)

            x = layer.get("x", 0)
            y = layer.get("y", 0)
            canvas.paste(img, (x, y), img)

    # Save
    workspace = f"backend/workspace/{job_id}"
    os.makedirs(workspace, exist_ok=True)
    output_path = os.path.join(workspace, "composite.png")
    canvas.save(output_path)

    return {
        "path": output_path,
        "model": "pillow",
        "cost": 0.0,
    }
