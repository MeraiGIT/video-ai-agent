"""Interview node — asks smart follow-up questions via interrupt.

CRITICAL: This node uses interrupt(). It will re-execute from the beginning
on resume. The Claude call happens BEFORE the interrupt, and since the
questions are deterministic for a given state, the re-execution is safe.
"""

import logging

from langgraph.config import get_stream_writer
from langgraph.types import interrupt

from agent.state import ProductionState
from agent.prompts.interview import INTERVIEW_SYSTEM, build_interview_prompt
from services.claude_service import client, MODEL

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Generate follow-up questions and wait for user response."""
    writer = get_stream_writer()

    # If interview was already completed during intake (clear request), skip
    if state.get("interview_complete"):
        logger.info("Interview: skipping — request was clear enough")
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": "Your request is clear enough to proceed. Let me start working on it!",
            },
        })
        return {
            "status": "interview_complete",
            "progress_messages": ["Interview: skipped (clear request)"],
        }

    # Generate follow-up questions with Claude
    prompt = build_interview_prompt(
        user_request=state.get("user_request", ""),
        content_type=state.get("content_type", "short_video"),
        target_platform=state.get("target_platform", "unspecified"),
        target_audience=state.get("target_audience", "general"),
        constraints=state.get("constraints"),
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=INTERVIEW_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        questions_text = response.content[0].text.strip()
    except Exception as e:
        logger.warning("Interview question generation failed: %s", e)
        questions_text = (
            "I have a few quick questions to make sure we get this right:\n\n"
            "1. **What mood/tone are you going for?** (e.g., professional, playful, dramatic)\n"
            "2. **Any specific references or examples you love?** (links, brands, or styles)\n\n"
            "Or just say 'go ahead' and I'll use my best judgment!"
        )

    # Show questions to user
    writer({
        "event": "message",
        "data": {"role": "assistant", "content": questions_text},
    })

    # Wait for user response
    response = interrupt({
        "stage": "interview",
        "actions": ["approve", "modify"],
    })

    action = response.get("action", "approve")
    user_message = response.get("message", "")

    if action == "approve" or user_message.lower() in ("go ahead", "just do it", "proceed"):
        # User approves / skip — proceed with current info
        logger.info("Interview: user approved, proceeding")
        return {
            "interview_complete": True,
            "status": "interview_complete",
            "progress_messages": ["Interview: user approved"],
        }

    # User provided additional context
    logger.info("Interview: user provided context: %s", user_message[:80])

    # Use Claude to decide if research is needed based on the full context
    research_decision = _decide_research_needed(state, user_message)

    return {
        "interview_complete": True,
        "interview_answers": user_message,
        "research_needed": research_decision,
        "status": "interview_complete",
        "progress_messages": [f"Interview: user provided context ({len(user_message)} chars)"],
    }


def _decide_research_needed(state: ProductionState, user_answers: str) -> bool:
    """Quick Claude call to decide if web research would benefit this project."""
    content_type = state.get("content_type", "short_video")
    user_request = state.get("user_request", "")

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=100,
            system="Answer with ONLY 'yes' or 'no'.",
            messages=[{
                "role": "user",
                "content": (
                    f"Would web research (trending topics, platform best practices, "
                    f"reference gathering) significantly improve this {content_type} project?\n\n"
                    f"Request: {user_request[:200]}\n"
                    f"Additional context: {user_answers[:200]}\n\n"
                    f"Answer 'yes' only if current trends, specific data, or references "
                    f"from the web would meaningfully improve the output."
                ),
            }],
        )
        answer = response.content[0].text.strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False
