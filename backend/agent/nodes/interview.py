"""Interview review node: gathers user input via interrupt."""

import logging

from langgraph.types import interrupt

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Interview: awaiting user input")
    response = interrupt({"stage": "interview", "actions": ["approve", "modify"]})
    if response["action"] == "approve":
        return {
            "interview_complete": True,
            "research_needed": False,
            "status": "interview_complete",
            "progress_messages": ["Interview complete"],
        }
    return {
        "interview_answers": response.get("message", ""),
        "progress_messages": ["Interview updated"],
    }
