"""Intake node — classifies any creative request.

Analyzes the user's request (text + optional files), classifies the content
type, identifies constraints, and decides whether an interview is needed.
"""

import json
import logging

from langgraph.config import get_stream_writer

from agent.state import ProductionState
from agent.prompts.intake import INTAKE_SYSTEM, build_intake_prompt
from services.claude_service import client, MODEL

logger = logging.getLogger(__name__)


def _analyze_uploaded_file(file_info: dict) -> dict:
    """Use Gemini vision to analyze an uploaded file.

    Returns the file_info dict enriched with an 'analysis' field.
    """
    from services.gemini_service import analyze_image, analyze_video, analyze_audio

    file_type = file_info.get("type", "")
    url = file_info.get("url", "")
    result = dict(file_info)

    try:
        if file_type.startswith("image"):
            analysis = analyze_image(
                url,
                "Describe this image in detail: subject(s), style, colors, setting, "
                "composition, mood. If it contains a person or character, describe "
                "their appearance precisely (hair, clothing, features).",
            )
            result["analysis"] = analysis
        elif file_type.startswith("video"):
            analysis = analyze_video(
                url,
                "Analyze this video: describe the content, visual style, pacing, "
                "transitions, camera work, subjects, setting, mood. Break down "
                "the key scenes and their duration.",
            )
            result["analysis"] = analysis
        elif file_type.startswith("audio"):
            analysis = analyze_audio(
                url,
                "Analyze this audio: describe the content, tone, pacing, "
                "speaker characteristics, background music/sounds, overall mood.",
            )
            result["analysis"] = analysis
        else:
            result["analysis"] = "File type not supported for analysis."
    except Exception as e:
        logger.warning("Gemini analysis failed for %s: %s", file_info.get("filename"), e)
        result["analysis"] = f"Analysis unavailable: {e}"

    return result


def run(state: ProductionState) -> dict:
    """Classify the user's creative request and extract structured project details."""
    writer = get_stream_writer()
    user_request = state.get("user_request", "").strip()

    if not user_request:
        raise ValueError("User request cannot be empty")

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": f'Analyzing your request: "{user_request[:100]}{"..." if len(user_request) > 100 else ""}"',
        },
    })

    # Analyze uploaded files with Gemini vision
    uploaded_files = state.get("uploaded_files", [])
    file_analyses = []
    if uploaded_files:
        writer({
            "event": "progress",
            "data": {
                "stage": "intake",
                "message": f"Analyzing {len(uploaded_files)} uploaded file(s) with Gemini vision...",
            },
        })
        for f in uploaded_files:
            analyzed = _analyze_uploaded_file(f)
            file_analyses.append(analyzed)

    # Call Claude for intake classification
    prompt = build_intake_prompt(user_request, file_analyses or None)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=INTAKE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        classification = json.loads(text)
    except Exception as e:
        logger.warning("Intake classification failed, using defaults: %s", e)
        classification = {
            "content_type": "short_video",
            "target_platform": "unspecified",
            "target_audience": "general",
            "constraints": {},
            "reference_materials": [],
            "project_name": user_request[:50],
            "summary": user_request,
            "needs_interview": True,
            "interview_reason": "Classification failed, asking user to clarify.",
            "needs_research": False,
            "research_reason": "",
        }

    # Build summary message for user
    summary = classification.get("summary", user_request[:100])
    content_type = classification.get("content_type", "short_video")
    platform = classification.get("target_platform", "unspecified")

    msg_parts = [f"I understand — you want to create a **{content_type.replace('_', ' ')}**"]
    if platform != "unspecified":
        msg_parts.append(f" for **{platform}**")
    msg_parts.append(f".\n\n*{summary}*")

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": "".join(msg_parts)},
    })

    needs_interview = classification.get("needs_interview", True)

    result: dict = {
        "content_type": content_type,
        "target_platform": platform,
        "target_audience": classification.get("target_audience", "general"),
        "constraints": classification.get("constraints", {}),
        "reference_materials": classification.get("reference_materials", []),
        "project_name": classification.get("project_name", user_request[:50]),
        "interview_complete": not needs_interview,
        "research_needed": classification.get("needs_research", False),
        "status": "intake_complete",
        "progress_messages": [f"Intake: {content_type} for {platform}"],
    }

    # Store enriched file analyses back
    if file_analyses:
        result["uploaded_files"] = file_analyses

    return result
