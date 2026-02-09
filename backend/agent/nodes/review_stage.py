"""Review Stage node: user reviews produced assets for the current stage."""

import logging

from langgraph.types import interrupt

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Review Stage: awaiting user approval")
    response = interrupt({"stage": "stage_review", "actions": ["approve", "modify"]})
    if response["action"] == "approve":
        return {
            "status": "all_stages_complete",
            "progress_messages": ["All production stages approved"],
        }
    return {
        "progress_messages": ["Stage modification requested"],
    }
