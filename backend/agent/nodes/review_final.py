"""Review Final node: user gives final approval for delivery."""

import logging

from langgraph.types import interrupt

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Review Final: awaiting final approval")
    response = interrupt({"stage": "final_review", "actions": ["approve"]})
    return {
        "status": "complete",
        "progress_messages": ["Project delivered!"],
    }
