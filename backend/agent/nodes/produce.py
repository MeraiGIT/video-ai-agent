"""Produce node — the core production executor.

Walks the production plan step by step, calling capability functions
from the registry. Handles batch operations (e.g., generate 5 images),
stores results in state, tracks costs, and routes to quality_gate.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

from langgraph.config import get_stream_writer

from agent.state import ProductionState
from agent.capabilities.registry import get_capability_function, get_capability

logger = logging.getLogger(__name__)

# Max parallel generation within a batch
MAX_PARALLEL = 4
# Budget safety multiplier — halt production if cost exceeds this factor of budget
BUDGET_SAFETY_FACTOR = 1.5
# Timeout per capability execution (seconds) — video gen can be slow
CAPABILITY_TIMEOUT = 300  # 5 minutes


def run(state: ProductionState) -> dict:
    """Execute the current production plan step."""
    writer = get_stream_writer()
    plan = state.get("production_plan", [])
    stage_idx = state.get("current_stage_index", 0)
    total_chunks = state.get("total_chunks", 1)
    current_chunk = state.get("current_chunk", 0)

    # Budget enforcement — halt if cost exceeds safety limit
    budget_limit = state.get("budget_limit", 0)
    total_cost_so_far = state.get("total_cost", 0.0)
    if budget_limit > 0 and total_cost_so_far >= budget_limit * BUDGET_SAFETY_FACTOR:
        logger.warning(
            "Budget exceeded: $%.2f / $%.2f (%.1fx limit)",
            total_cost_so_far, budget_limit, BUDGET_SAFETY_FACTOR,
        )
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": (
                    f"Production paused — budget limit reached "
                    f"(${total_cost_so_far:.2f} / ${budget_limit:.2f}). "
                    f"Proceeding to assembly with what we have."
                ),
            },
        })
        return {
            "status": "all_stages_complete",
            "progress_messages": [f"Budget limit reached: ${total_cost_so_far:.2f}"],
        }

    if stage_idx >= len(plan):
        # Check if there are more chunks to process
        if total_chunks > 1 and current_chunk < total_chunks - 1:
            next_chunk = current_chunk + 1
            logger.info("Chunk %d/%d complete, moving to chunk %d", current_chunk + 1, total_chunks, next_chunk + 1)
            writer({
                "event": "progress",
                "data": {
                    "stage": "producing",
                    "message": f"Chapter {current_chunk + 1} complete! Moving to chapter {next_chunk + 1} of {total_chunks}...",
                },
            })
            # Reset stage index for next chunk, advance chunk counter
            return {
                "current_chunk": next_chunk,
                "current_stage_index": 0,
                "status": "chunk_complete",
                "progress_messages": [f"Chapter {current_chunk + 1}/{total_chunks} complete"],
            }

        logger.info("All production steps complete")
        return {
            "status": "all_stages_complete",
            "progress_messages": ["All production steps complete"],
        }

    step = plan[stage_idx]
    capability_id = step.get("capability", "")
    model = step.get("model", "")
    params = step.get("params", {})
    count = step.get("count", 1)
    description = step.get("description", f"Step {stage_idx + 1}")

    logger.info(
        "Produce step %d/%d: %s (model=%s, count=%d)",
        stage_idx + 1, len(plan), capability_id, model, count,
    )

    writer({
        "event": "progress",
        "data": {
            "stage": "producing",
            "message": f"Step {stage_idx + 1}/{len(plan)}: {description}",
            "step": stage_idx + 1,
            "total_steps": len(plan),
        },
    })

    # Merge model into params
    if model:
        params["model"] = model
    params["step"] = stage_idx

    # Get the capability function
    try:
        cap_meta = get_capability(capability_id)
        execute_fn = get_capability_function(capability_id)
    except KeyError:
        logger.error("Unknown capability: %s", capability_id)
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Skipping unknown capability: {capability_id}",
            },
        })
        return {
            "current_stage_index": stage_idx + 1,
            "progress_messages": [f"Skipped unknown capability: {capability_id}"],
        }

    # Build execution context — chunk-aware blueprint
    blueprint = state.get("blueprint", {})
    chunk_blueprint = _get_chunk_blueprint(blueprint, current_chunk, total_chunks)
    ctx = {
        "blueprint": chunk_blueprint,
        "creative_brief": state.get("creative_brief", {}),
        "stage_index": stage_idx,
        "current_chunk": current_chunk,
        "total_chunks": total_chunks,
    }

    # Enrich params from blueprint (e.g., scene prompts) — uses chunk-aware blueprint
    params = _enrich_params_from_blueprint(params, chunk_blueprint, stage_idx, capability_id)

    # Execute — batch or single
    results = []
    step_cost = 0.0
    output_type = cap_meta.get("output_type", "")

    try:
        if count > 1:
            results, step_cost = _execute_batch(
                execute_fn, params, state, ctx, count, capability_id, writer,
            )
        else:
            # Single execution with timeout protection
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(execute_fn, params, dict(state), ctx)
                try:
                    result = future.result(timeout=CAPABILITY_TIMEOUT)
                except TimeoutError:
                    raise TimeoutError(
                        f"{capability_id} timed out after {CAPABILITY_TIMEOUT}s"
                    )
            results = [result]
            step_cost = result.get("cost", 0.0)
    except Exception as e:
        logger.error("Capability %s failed: %s", capability_id, e)
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Production step failed: {description} — {str(e)[:100]}",
            },
        })
        # Move to next step instead of crashing
        return {
            "current_stage_index": stage_idx + 1,
            "retry_count": 0,
            "progress_messages": [f"Step {stage_idx + 1} failed: {str(e)[:80]}"],
        }

    # Store results in appropriate state fields
    state_updates = _store_results(
        results, output_type, capability_id, state, stage_idx, writer,
    )

    # Track costs
    total_cost = state.get("total_cost", 0.0) + step_cost
    cost_breakdown = list(state.get("cost_breakdown", []))
    cost_breakdown.append({
        "step": description,
        "model": model,
        "count": count,
        "unit_cost": step_cost / max(count, 1),
        "total": step_cost,
    })

    state_updates.update({
        "current_stage_index": stage_idx + 1,
        "total_cost": total_cost,
        "cost_breakdown": cost_breakdown,
        "retry_count": 0,
        "status": "stage_produced",
        "progress_messages": [
            f"Completed: {description} (${step_cost:.2f})"
        ],
    })

    # Emit cost update
    budget_limit = state.get("budget_limit", 0)
    writer({
        "event": "cost_update",
        "data": {
            "step_cost": step_cost,
            "total_cost": total_cost,
            "budget_limit": budget_limit,
        },
    })

    # Warn if approaching budget limit
    if budget_limit > 0 and total_cost >= budget_limit * 0.8:
        pct = (total_cost / budget_limit) * 100
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Budget alert: ${total_cost:.2f} / ${budget_limit:.2f} ({pct:.0f}% used)",
            },
        })

    return state_updates


def _execute_batch(
    execute_fn, params, state, ctx, count, capability_id, writer,
):
    """Execute a capability multiple times in parallel for batch operations."""
    results = []
    total_cost = 0.0
    state_dict = dict(state)

    # Build per-item params (e.g., different prompts per scene)
    item_params_list = []
    blueprint = state.get("blueprint", {})
    scenes = blueprint.get("scenes", [])

    for i in range(count):
        item_params = dict(params)
        item_params["batch_index"] = i
        item_params["filename"] = f"{capability_id}_{i}.{'mp4' if 'video' in capability_id else 'png'}"

        # Pull scene-specific prompts if available
        if i < len(scenes):
            scene = scenes[i]
            if capability_id == "image_gen" and scene.get("image_prompt"):
                item_params["prompt"] = scene["image_prompt"]
            elif capability_id == "video_gen" and scene.get("video_prompt"):
                item_params["prompt"] = scene["video_prompt"]
                item_params["camera"] = scene.get("camera", {})
                if not item_params.get("image_url"):
                    # Try to use the generated image for this scene
                    images = state.get("images", [])
                    matching = [img for img in images if img.get("scene_index") == i]
                    if matching:
                        item_params["image_url"] = matching[0].get("url", "")

        item_params_list.append(item_params)

    # Execute in parallel with thread pool
    with ThreadPoolExecutor(max_workers=min(count, MAX_PARALLEL)) as pool:
        futures = {
            pool.submit(execute_fn, p, state_dict, ctx): idx
            for idx, p in enumerate(item_params_list)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                result = future.result(timeout=CAPABILITY_TIMEOUT)
                result["batch_index"] = idx
                results.append(result)
                total_cost += result.get("cost", 0.0)
                writer({
                    "event": "progress",
                    "data": {
                        "stage": "producing",
                        "message": f"Generated {len(results)}/{count}",
                    },
                })
            except TimeoutError:
                logger.error("Batch item %d timed out after %ds", idx, CAPABILITY_TIMEOUT)
                results.append({"error": f"Timed out after {CAPABILITY_TIMEOUT}s", "batch_index": idx})
            except Exception as e:
                logger.error("Batch item %d failed: %s", idx, e)
                results.append({"error": str(e), "batch_index": idx})

    # Sort by batch_index to maintain order
    results.sort(key=lambda r: r.get("batch_index", 0))
    return results, total_cost


def _enrich_params_from_blueprint(params, blueprint, stage_idx, capability_id):
    """Pull additional params from the blueprint based on capability type."""
    params = dict(params)

    # For voiceover, pull script from blueprint
    if capability_id == "voiceover" and not params.get("text"):
        audio_map = blueprint.get("audio_map", {})
        vo = audio_map.get("voiceover", {})
        if vo.get("full_script"):
            params["text"] = vo["full_script"]

    return params


def _get_chunk_blueprint(blueprint: dict, current_chunk: int, total_chunks: int) -> dict:
    """Get the blueprint for the current chunk (chapter).

    For single-chunk projects, returns the full blueprint unchanged.
    For multi-chunk, returns a modified blueprint with only the current chapter's
    scenes and audio_map, plus continuity notes from previous chapters.
    """
    if total_chunks <= 1:
        return blueprint

    chapters = blueprint.get("chapters", [])
    if current_chunk >= len(chapters):
        return blueprint

    chapter = chapters[current_chunk]
    # Build a chunk-specific blueprint by merging chapter data with top-level style
    chunk_bp = dict(blueprint)
    chunk_bp["scenes"] = chapter.get("scenes", [])
    chunk_bp["audio_map"] = chapter.get("audio_map", blueprint.get("audio_map", {}))
    chunk_bp["_chapter_title"] = chapter.get("title", f"Chapter {current_chunk + 1}")
    chunk_bp["_continuity_notes"] = chapter.get("continuity_notes", "")
    chunk_bp["_chapter_number"] = current_chunk + 1
    chunk_bp["_total_chapters"] = total_chunks
    return chunk_bp


def _store_results(results, output_type, capability_id, state, stage_idx, writer):
    """Map capability results to the appropriate state fields."""
    updates: dict = {}

    if output_type == "ImageAsset":
        images = list(state.get("images", []))
        for i, r in enumerate(results):
            if r.get("error"):
                continue
            images.append({
                "scene_index": r.get("batch_index", i),
                "url": r.get("url", ""),
                "local_path": r.get("local_path", ""),
                "model": r.get("model", ""),
                "cost": r.get("cost", 0.0),
                "prompt": r.get("prompt", ""),
            })
            # Emit image artifact
            writer({
                "event": "artifact",
                "data": {
                    "type": "image",
                    "scene_index": r.get("batch_index", i),
                    "url": r.get("url", ""),
                    "total_scenes": len(results),
                },
            })
        updates["images"] = images

    elif output_type == "VideoAsset":
        videos = list(state.get("videos", []))
        for i, r in enumerate(results):
            if r.get("error"):
                continue
            videos.append({
                "scene_index": r.get("batch_index", i),
                "url": r.get("url", ""),
                "local_path": r.get("local_path", ""),
                "model": r.get("model", ""),
                "cost": r.get("cost", 0.0),
                "duration": r.get("duration", 0),
                "prompt": r.get("prompt", ""),
            })
            writer({
                "event": "artifact",
                "data": {
                    "type": "video",
                    "scene_index": r.get("batch_index", i),
                    "url": r.get("url", r.get("local_path", "")),
                    "total_scenes": len(results),
                },
            })
        updates["videos"] = videos

    elif output_type == "audio_path":
        r = results[0] if results else {}
        path = r.get("path", "")
        if capability_id == "voiceover":
            updates["voiceover_path"] = path
            if path:
                writer({
                    "event": "artifact",
                    "data": {"type": "voiceover", "url": path},
                })
        elif capability_id == "music_gen":
            updates["music_path"] = path
        elif capability_id == "sfx_gen":
            sfx_paths = list(state.get("sfx_paths", []))
            if path:
                sfx_paths.append(path)
            updates["sfx_paths"] = sfx_paths
        elif capability_id == "audio_mix":
            updates["mixed_audio_path"] = path

    elif output_type == "character_sheet":
        r = results[0] if results else {}
        sheets = list(state.get("character_sheets", []))
        sheets.append(r.get("character_sheet", {}))
        updates["character_sheets"] = sheets

    elif output_type == "frame_pair":
        # Store for use by subsequent video_gen step
        r = results[0] if results else {}
        updates["_first_frame_url"] = r.get("first_frame_url", "")
        updates["_last_frame_url"] = r.get("last_frame_url", "")

    elif output_type in ("video_path", "image_path", "srt_path"):
        # Processing capabilities store their path
        r = results[0] if results else {}
        path = r.get("path", "")
        if capability_id == "video_concat":
            updates["assembled_path"] = path
        elif capability_id == "audio_overlay":
            updates["assembled_path"] = path
        elif capability_id == "caption_burn":
            updates["polished_path"] = path
        elif capability_id == "text_overlay":
            updates["polished_path"] = path

    elif output_type == "voice_id":
        r = results[0] if results else {}
        # Store voice_id so voiceover capability can use it
        updates["_selected_voice_id"] = r.get("voice_id", "")

    return updates
