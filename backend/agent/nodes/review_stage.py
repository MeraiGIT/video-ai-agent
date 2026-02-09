"""Review Stage node — user reviews produced assets at stage boundaries.

Called when the quality gate determines all production steps are complete
or at natural stage boundaries. Presents all assets to the user for approval.
"""

import logging

from langgraph.config import get_stream_writer
from langgraph.types import interrupt

from agent.state import ProductionState
from services.supabase_service import save_project_state

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Present production results to user for stage-level approval."""
    writer = get_stream_writer()
    plan = state.get("production_plan", [])
    stage_idx = state.get("current_stage_index", 0)
    total_cost = state.get("total_cost", 0.0)

    # Summarize what was produced
    images = state.get("images", [])
    videos = state.get("videos", [])
    voiceover = state.get("voiceover_path", "")
    quality_results = state.get("quality_results", [])

    summary_parts = []
    if images:
        summary_parts.append(f"{len(images)} images")
    if videos:
        summary_parts.append(f"{len(videos)} videos")
    if voiceover:
        summary_parts.append("voiceover")
    summary = ", ".join(summary_parts) if summary_parts else "production assets"

    # Quality summary
    if quality_results:
        scores = [r.get("score", 0) for r in quality_results if r.get("score")]
        avg_score = sum(scores) / len(scores) if scores else 0
        passed = sum(1 for r in quality_results if r.get("passed"))
        quality_msg = f"Quality: {passed}/{len(quality_results)} passed (avg {avg_score:.1f}/10)"
    else:
        quality_msg = ""

    # Chunk progress info
    total_chunks = state.get("total_chunks", 1)
    current_chunk = state.get("current_chunk", 0)
    chunk_msg = ""
    if total_chunks > 1:
        chunk_msg = f"\n**Chapter {current_chunk + 1} of {total_chunks}**"

    content = f"**Production complete!** Generated {summary}.{chunk_msg}"
    if quality_msg:
        content += f"\n{quality_msg}"
    content += f"\nTotal cost so far: ${total_cost:.2f}"

    if stage_idx < len(plan):
        remaining = len(plan) - stage_idx
        content += f"\n\n{remaining} more steps remaining."
    elif total_chunks > 1 and current_chunk < total_chunks - 1:
        content += f"\n\n{total_chunks - current_chunk - 1} chapters remaining."
    else:
        content += "\n\nAll production steps are complete."

    content += "\n\nApprove to continue, or ask me to regenerate specific items."

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": content},
    })

    # Interrupt for user approval
    response = interrupt({
        "stage": "stage_review",
        "actions": ["approve", "modify", "regenerate"],
        "assets": {
            "images": len(images),
            "videos": len(videos),
            "voiceover": bool(voiceover),
        },
    })

    action = response.get("action", "approve")

    if action == "approve":
        # Check if all stages complete
        if stage_idx >= len(plan):
            logger.info("All production stages approved")
            writer({
                "event": "message",
                "data": {
                    "role": "assistant",
                    "content": "All production approved! Moving to assembly...",
                },
            })
            result = {
                "status": "all_stages_complete",
                "progress_messages": ["All production stages approved — moving to assembly"],
            }
            project_id = state.get("project_id")
            if project_id:
                save_project_state(project_id, {**dict(state), **result})
            return result

        logger.info("Stage approved, continuing production")
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": "Approved! Continuing production...",
            },
        })
        result = {
            "status": "stage_approved",
            "progress_messages": [f"Stage approved — continuing ({stage_idx}/{len(plan)} done)"],
        }
        project_id = state.get("project_id")
        if project_id:
            save_project_state(project_id, {**dict(state), **result})
        return result

    if action == "regenerate":
        # User wants to regenerate specific items
        indices = response.get("indices", [])
        feedback = response.get("message", "")
        logger.info("Regeneration requested for indices: %s", indices)

        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Regenerating {len(indices)} items...",
            },
        })

        # For now, restart from the beginning of the batch
        # A more sophisticated approach would target specific items
        return {
            "current_stage_index": max(0, stage_idx - 1),
            "retry_count": 0,
            "status": "stage_regenerating",
            "progress_messages": [f"Regenerating {len(indices)} items"],
        }

    # User wants modifications
    feedback = response.get("message", "")
    logger.info("Stage modification requested: %s", feedback[:80])

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Got it, revising the production...",
        },
    })

    return {
        "status": "stage_needs_revision",
        "progress_messages": [f"Stage revision requested: {feedback[:50]}"],
    }
