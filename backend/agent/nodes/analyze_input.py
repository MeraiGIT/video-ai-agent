import logging
from langgraph.config import get_stream_writer
from services.claude_service import analyze_user_request
from services.model_registry import get_video_model, get_model_description_for_llm
from agent.state import VideoState

logger = logging.getLogger(__name__)


def run(state: VideoState) -> dict:
    """Analyze user input with Claude to produce a smart generation plan.

    Determines character consistency needs, optimal model, and whether
    to use reference images from uploads.
    """
    writer = get_stream_writer()
    topic = state["input_topic"].strip()

    if not topic:
        raise ValueError("Input topic cannot be empty")

    uploaded_files = state.get("uploaded_files", [])
    chosen_model = state["video_model"]

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                f"Analyzing your request: "
                f'"{topic[:80]}{"..." if len(topic) > 80 else ""}"...'
            ),
        },
    })

    # Use Claude to analyze the request
    try:
        plan = analyze_user_request(
            topic=topic,
            uploaded_files=uploaded_files or None,
            available_models=get_model_description_for_llm(),
        )
    except Exception as e:
        logger.warning(f"Smart analysis failed, using defaults: {e}")
        plan = {
            "character_description": "",
            "recommended_video_model": chosen_model,
            "use_reference_images": False,
            "reasoning": "Using default settings.",
        }

    character_desc = plan.get("character_description", "")
    recommended_model = plan.get("recommended_video_model", chosen_model)
    use_refs = plan.get("use_reference_images", False)
    reasoning = plan.get("reasoning", "")

    # Extract reference image URLs from uploads
    reference_images = []
    if use_refs and uploaded_files:
        reference_images = [
            f["url"] for f in uploaded_files
            if f.get("type", "").startswith("image/")
        ]

    # Build a message about the plan for the user
    plan_parts = []
    if character_desc:
        plan_parts.append(f"Character: {character_desc}")

    # Check if the recommended model differs from chosen and needs a capability
    # the chosen model lacks
    model_note = ""
    if recommended_model != chosen_model:
        try:
            rec_model = get_video_model(recommended_model)
            chosen_info = get_video_model(chosen_model)
            # Only suggest switching for capability reasons, not preference
            rec_caps = set(rec_model.get("supports", []))
            chosen_caps = set(chosen_info.get("supports", []))
            missing = rec_caps - chosen_caps
            if missing and ("character-consistency" in missing or "reference-to-video" in missing):
                model_note = (
                    f"For character consistency, I'd recommend switching to "
                    f"**{rec_model['name']}** (supports reference-to-video). "
                    f"Your current model ({chosen_info['name']}) doesn't support this. "
                    f"I'll note this recommendation, but using your selected model for now."
                )
        except KeyError:
            pass

    # Build the summary message
    chosen_info = get_video_model(chosen_model)
    summary = f"I'll create a video about \"{topic[:60]}\" using **{chosen_info['name']}**."
    if character_desc:
        summary += f" I've identified a character to maintain consistently: *{character_desc}*."
    if reference_images:
        summary += f" Using {len(reference_images)} uploaded reference image(s)."
    if model_note:
        summary += f"\n\n{model_note}"
    if reasoning:
        summary += f"\n\n*{reasoning}*"

    summary += "\n\nLet me start by writing a script..."

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": summary},
    })

    result = {
        "input_topic": topic,
        "generation_plan": plan,
        "status": "input_analyzed",
        "progress_messages": [f"Topic: {topic[:80]}"],
    }

    if character_desc:
        result["character_description"] = character_desc
    if reference_images:
        result["reference_images"] = reference_images

    return result
