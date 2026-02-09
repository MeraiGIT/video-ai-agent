"""Deliver node — prepares the final output for delivery.

Handles:
1. Platform-specific export validation
2. Metadata generation via Claude (title, description, hashtags)
3. Final output path assignment
4. Emits download link artifact
"""

import json
import logging

import anthropic
from langgraph.config import get_stream_writer

from agent.state import ProductionState
from config import settings

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Prepare final output for delivery."""
    writer = get_stream_writer()
    job_id = state.get("job_id", "unknown")
    content_type = state.get("content_type", "short_video")
    polished_path = state.get("polished_path", state.get("assembled_path", ""))
    creative_brief = state.get("creative_brief", {})
    user_request = state.get("user_request", "")
    platform = state.get("target_platform", "youtube")

    writer({
        "event": "progress",
        "data": {"stage": "deliver", "message": "Preparing final delivery..."},
    })

    # Use polished or assembled or any available path
    final_path = polished_path
    if not final_path:
        final_path = _find_best_output(state)

    if not final_path:
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": "No output file available for delivery.",
            },
        })
        return {
            "final_output_path": "",
            "status": "delivery_complete",
            "progress_messages": ["Delivery complete — no output file"],
        }

    # Generate metadata (title, description, hashtags)
    metadata = _generate_metadata(
        user_request=user_request,
        creative_brief=creative_brief,
        content_type=content_type,
        platform=platform,
    )

    # Build cost summary
    total_cost = state.get("total_cost", 0.0)
    cost_breakdown = state.get("cost_breakdown", [])

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": _format_delivery_message(metadata, total_cost, platform),
        },
    })

    # Emit the final downloadable artifact
    writer({
        "event": "artifact",
        "data": {
            "type": "final_video",
            "url": final_path,
        },
    })

    # Emit cost summary
    if total_cost > 0:
        writer({
            "event": "cost_update",
            "data": {
                "total_cost": total_cost,
                "breakdown": cost_breakdown,
            },
        })

    # Emit metadata for the frontend
    writer({
        "event": "artifact",
        "data": {
            "type": "metadata",
            "metadata": metadata,
        },
    })

    return {
        "final_output_path": final_path,
        "status": "delivery_complete",
        "progress_messages": [f"Delivery ready: {final_path}"],
    }


def _generate_metadata(
    user_request: str,
    creative_brief: dict,
    content_type: str,
    platform: str,
) -> dict:
    """Generate metadata (title, description, hashtags) via Claude."""
    brief_summary = ""
    if isinstance(creative_brief, dict):
        brief_summary = json.dumps({
            k: v for k, v in creative_brief.items()
            if k in ("concept", "visual_style", "tone", "key_messages", "target_audience")
        }, indent=2)

    prompt = f"""Generate platform-optimized metadata for this {content_type} project.

User request: {user_request}

Creative brief:
{brief_summary}

Target platform: {platform}

Generate:
1. title: Catchy, platform-appropriate title (max 100 chars)
2. description: Engaging description optimized for {platform} (max 500 chars)
3. hashtags: 5-10 relevant hashtags (without # prefix)
4. seo_tags: 5-8 SEO keywords

Return ONLY valid JSON:
{{
  "title": "...",
  "description": "...",
  "hashtags": ["tag1", "tag2", ...],
  "seo_tags": ["keyword1", "keyword2", ...]
}}"""

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as e:
        logger.warning("Metadata generation failed: %s", e)
        # Fallback metadata
        return {
            "title": user_request[:100] if user_request else "AI Production Studio Output",
            "description": f"Created with AI Production Studio — {content_type}",
            "hashtags": ["AIcreated", "contentcreation", platform],
            "seo_tags": [content_type, "ai", "creative"],
        }


def _find_best_output(state: dict) -> str:
    """Find the best available output path from state."""
    for key in ("polished_path", "assembled_path", "mixed_audio_path", "voiceover_path"):
        path = state.get(key, "")
        if path:
            return path

    videos = state.get("videos", [])
    if videos:
        return videos[-1].get("local_path", videos[-1].get("url", ""))

    images = state.get("images", [])
    if images:
        return images[-1].get("url", images[-1].get("local_path", ""))

    return ""


def _format_delivery_message(metadata: dict, total_cost: float, platform: str) -> str:
    """Format a delivery summary message."""
    title = metadata.get("title", "Untitled")
    description = metadata.get("description", "")
    hashtags = metadata.get("hashtags", [])

    parts = [
        f"**Your project is ready!**\n",
        f"**Title**: {title}\n",
    ]

    if description:
        parts.append(f"**Description**: {description}\n")

    if hashtags:
        tags_str = " ".join(f"#{tag}" for tag in hashtags[:8])
        parts.append(f"**Hashtags**: {tags_str}\n")

    if total_cost > 0:
        parts.append(f"**Total cost**: ${total_cost:.2f}\n")

    parts.append(f"**Optimized for**: {platform}")

    return "\n".join(parts)
