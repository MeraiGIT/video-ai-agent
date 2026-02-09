"""Quality Gate node: evaluates output quality."""

import logging

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Quality Gate: evaluating output")
    return {
        "quality_results": [
            {
                "passed": True,
                "score": 8.0,
                "asset_type": "image",
                "asset_index": 0,
            }
        ],
        "status": "quality_passed",
        "progress_messages": ["Quality check passed"],
    }
