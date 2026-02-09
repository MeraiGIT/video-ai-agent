"""Review Final node — user gives final approval for delivery.

Uses interrupt() for the final user approval before the pipeline ends.
"""

import logging

from langgraph.config import get_stream_writer
from langgraph.types import interrupt

from agent.state import ProductionState
from services.supabase_service import save_project_state

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Present final output to user for approval."""
    writer = get_stream_writer()
    final_path = state.get("final_output_path", "")

    content = "**Your project is ready for delivery!** Review the output and metadata above, then approve to finalize."
    if not final_path:
        content = "The project is complete. Approve to finalize."

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": content},
    })

    response = interrupt({
        "stage": "final_review",
        "actions": ["approve"],
    })

    logger.info("Final approval received")
    writer({
        "event": "complete",
        "data": {
            "message": "Project delivered successfully!",
            "final_output": final_path,
        },
    })
    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Project delivered! Thanks for using AI Production Studio.",
        },
    })

    result = {
        "status": "complete",
        "progress_messages": ["Project delivered!"],
    }

    # Final auto-save — mark project as completed
    project_id = state.get("project_id")
    if project_id:
        save_project_state(project_id, {
            **dict(state),
            **result,
            "status": "completed",
        })

    return result
