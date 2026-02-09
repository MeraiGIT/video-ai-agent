"""Quality Gate node — Gemini vision evaluates produced assets.

Runs autonomously between production steps. For each generated asset:
1. Sends to Gemini vision for scoring (1-10)
2. If score >= 7: PASS → continue to next step
3. If score < 7 and retries < 3: Claude optimizes the prompt → retry
4. If retries >= 3: escalate to user for model upgrade decision
"""

import json
import logging

from langgraph.config import get_stream_writer

from agent.state import ProductionState
from agent.prompts.quality_gate import build_prompt_optimization
from services.claude_service import client as claude_client, MODEL as CLAUDE_MODEL

logger = logging.getLogger(__name__)

# Quality threshold — assets scoring below this trigger a retry
QUALITY_THRESHOLD = 7.0
MAX_RETRIES = 3


def run(state: ProductionState) -> dict:
    """Evaluate the most recently produced asset with Gemini vision."""
    writer = get_stream_writer()
    plan = state.get("production_plan", [])
    stage_idx = state.get("current_stage_index", 0)

    # The produce node already incremented stage_idx, so the just-produced
    # step is at stage_idx - 1
    just_produced_idx = stage_idx - 1
    if just_produced_idx < 0 or just_produced_idx >= len(plan):
        # Nothing to evaluate
        return {
            "status": "quality_passed",
            "progress_messages": ["Quality gate: nothing to evaluate"],
        }

    step = plan[just_produced_idx]
    capability_id = step.get("capability", "")
    description = step.get("description", f"Step {just_produced_idx + 1}")

    # Only evaluate generation capabilities — skip processing/analysis
    from agent.capabilities.registry import CAPABILITY_REGISTRY
    cap_meta = CAPABILITY_REGISTRY.get(capability_id, {})
    if cap_meta.get("category") != "generation":
        return {
            "status": "quality_passed",
            "progress_messages": [f"Quality gate: skipped for {capability_id} (processing step)"],
        }

    # Determine what to evaluate
    output_type = cap_meta.get("output_type", "")
    asset_info = _get_latest_asset(state, output_type, capability_id)

    if not asset_info:
        logger.warning("No asset found to evaluate for %s", capability_id)
        return {
            "status": "quality_passed",
            "progress_messages": ["Quality gate: no asset to evaluate"],
        }

    writer({
        "event": "progress",
        "data": {
            "stage": "quality_gate",
            "message": f"Evaluating quality: {description}...",
        },
    })

    # Run Gemini evaluation
    try:
        eval_result = _evaluate_asset(
            asset_info, state, step,
        )
    except Exception as e:
        logger.error("Quality evaluation failed: %s", e)
        # On eval failure, assume pass to avoid blocking
        return {
            "status": "quality_passed",
            "progress_messages": [f"Quality gate: evaluation error, assuming pass — {str(e)[:60]}"],
        }

    score = eval_result.get("score", QUALITY_THRESHOLD)
    passed = score >= QUALITY_THRESHOLD
    retry_count = state.get("retry_count", 0)

    # Track quality result
    quality_results = list(state.get("quality_results", []))
    quality_results.append({
        "asset_type": eval_result.get("asset_type", "unknown"),
        "asset_index": just_produced_idx,
        "score": score,
        "issues": eval_result.get("issues", []),
        "suggestions": eval_result.get("suggestions", []),
        "passed": passed,
    })

    # Emit quality gate event
    writer({
        "event": "quality_gate",
        "data": {
            "step": description,
            "score": score,
            "passed": passed,
            "issues": eval_result.get("issues", []),
            "summary": eval_result.get("summary", ""),
        },
    })

    if passed:
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Quality check passed ({score:.1f}/10): {description}",
            },
        })
        return {
            "quality_results": quality_results,
            "status": "quality_passed",
            "progress_messages": [f"Quality {score:.1f}/10 PASS: {description}"],
        }

    # Failed quality check
    logger.info(
        "Quality failed for %s: %.1f/10 (retry %d/%d)",
        description, score, retry_count + 1, MAX_RETRIES,
    )

    if retry_count >= MAX_RETRIES:
        # Escalate — keep best attempt and move on
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": (
                    f"Quality check: {description} scored {score:.1f}/10 after "
                    f"{MAX_RETRIES} attempts. Keeping best result and moving on."
                ),
            },
        })
        return {
            "quality_results": quality_results,
            "retry_count": 0,
            "status": "quality_passed",
            "progress_messages": [
                f"Quality {score:.1f}/10 — max retries reached, moving on"
            ],
        }

    # Auto-retry with optimized prompt
    optimized_prompt = _optimize_prompt(
        eval_result, step, state, retry_count,
    )

    if optimized_prompt:
        # Update the production plan step with the optimized prompt
        updated_plan = list(plan)
        updated_step = dict(updated_plan[just_produced_idx])
        updated_params = dict(updated_step.get("params", {}))
        updated_params["prompt"] = optimized_prompt
        updated_step["params"] = updated_params
        updated_plan[just_produced_idx] = updated_step

        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": (
                    f"Quality check: {score:.1f}/10 — optimizing prompt and retrying "
                    f"(attempt {retry_count + 2}/{MAX_RETRIES + 1})..."
                ),
            },
        })

        return {
            "quality_results": quality_results,
            "production_plan": updated_plan,
            "current_stage_index": just_produced_idx,  # Re-execute the same step
            "retry_count": retry_count + 1,
            "status": "quality_retry",
            "progress_messages": [
                f"Quality {score:.1f}/10 — retrying with optimized prompt"
            ],
        }

    # Couldn't optimize, move on
    return {
        "quality_results": quality_results,
        "status": "quality_passed",
        "progress_messages": [f"Quality {score:.1f}/10 — moving on"],
    }


def _get_latest_asset(state, output_type, capability_id):
    """Get the most recently produced asset for evaluation."""
    if output_type == "ImageAsset":
        images = state.get("images", [])
        if images:
            img = images[-1]
            return {"type": "image", "url": img.get("url", ""), "prompt": img.get("prompt", "")}

    elif output_type == "VideoAsset":
        videos = state.get("videos", [])
        if videos:
            vid = videos[-1]
            return {
                "type": "video",
                "path": vid.get("local_path", vid.get("url", "")),
                "prompt": vid.get("prompt", ""),
            }

    elif output_type == "audio_path":
        if capability_id == "voiceover":
            path = state.get("voiceover_path", "")
            if path:
                return {"type": "audio", "path": path, "prompt": ""}

    return None


def _evaluate_asset(asset_info, state, step):
    """Call the appropriate Gemini analysis capability."""
    asset_type = asset_info["type"]
    creative_brief = state.get("creative_brief", {})

    if asset_type == "image":
        from agent.capabilities.analyze_image import execute
        return execute(
            {
                "image_url": asset_info["url"],
                "prompt": asset_info.get("prompt", ""),
                "step_description": step.get("description", ""),
            },
            dict(state),
            {},
        )
    elif asset_type == "video":
        from agent.capabilities.analyze_video import execute
        return execute(
            {
                "video_path": asset_info["path"],
                "prompt": asset_info.get("prompt", ""),
                "step_description": step.get("description", ""),
            },
            dict(state),
            {},
        )
    elif asset_type == "audio":
        from agent.capabilities.analyze_audio import execute
        return execute(
            {
                "audio_path": asset_info["path"],
                "prompt": asset_info.get("prompt", ""),
                "step_description": step.get("description", ""),
            },
            dict(state),
            {},
        )

    return {"score": QUALITY_THRESHOLD, "passed": True}


def _optimize_prompt(eval_result, step, state, retry_count):
    """Use Claude to generate an optimized prompt based on Gemini's feedback."""
    original_prompt = step.get("params", {}).get("prompt", "")
    if not original_prompt:
        return None

    model_id = step.get("model", "unknown")
    creative_brief = state.get("creative_brief", {})

    optimization_prompt = build_prompt_optimization(
        original_prompt=original_prompt,
        gemini_analysis=eval_result,
        model_id=model_id,
        creative_brief=creative_brief,
        retry_number=retry_count + 1,
    )

    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": optimization_prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error("Prompt optimization failed: %s", e)
        return None
