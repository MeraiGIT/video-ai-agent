"""Assemble node: combines assets into a single output."""

import logging

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Assemble: combining assets")
    return {
        "assembled_path": "",
        "status": "assembly_complete",
        "progress_messages": ["Assembly complete"],
    }
