"""Intake node: classifies the incoming request."""

import logging

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Intake: classifying request")
    return {
        "status": "intake_complete",
        "interview_complete": False,
        "progress_messages": ["Intake complete"],
    }
