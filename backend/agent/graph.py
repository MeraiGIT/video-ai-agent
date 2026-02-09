"""
LangGraph StateGraph for the AI Production Studio.

8-phase universal pipeline with 16 nodes:
  INTAKE → RESEARCH → CREATIVE DIRECTION → BLUEPRINT → PRODUCE → ASSEMBLE → POLISH → DELIVER

Each phase has generate + review (interrupt) node pairs.
The produce phase has a quality gate supervisor loop.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import ProductionState
from agent.nodes import (
    intake,
    interview,
    research,
    creative_direction,
    review_direction,
    blueprint,
    review_blueprint,
    produce,
    quality_gate,
    review_stage,
    assemble,
    review_assembly,
    polish,
    review_polish,
    deliver,
    review_final,
)


# === Conditional Routing Functions ===


def route_after_interview(state: ProductionState) -> str:
    """After interview: go to research if needed, otherwise creative_direction."""
    if state.get("research_needed"):
        return "research"
    return "creative_direction"


def route_after_direction_review(state: ProductionState) -> str:
    """After user reviews creative direction: approve → blueprint, modify → back."""
    if state.get("status") == "direction_approved":
        return "blueprint"
    return "creative_direction"


def route_after_blueprint_review(state: ProductionState) -> str:
    """After user reviews blueprint: approve → produce, modify → back."""
    if state.get("status") == "blueprint_approved":
        return "produce"
    return "blueprint"


def route_after_produce(state: ProductionState) -> str:
    """After producing an asset: evaluate quality or go to stage review."""
    plan = state.get("production_plan", [])
    stage_idx = state.get("current_stage_index", 0)
    if stage_idx >= len(plan):
        return "review_stage"
    return "quality_gate"


def route_after_quality_gate(state: ProductionState) -> str:
    """After quality evaluation: pass → produce next, fail → retry or escalate."""
    results = state.get("quality_results", [])
    last_result = results[-1] if results else {}

    if last_result.get("passed", True):
        return "produce"

    retry_count = state.get("retry_count", 0)
    if retry_count >= 3:
        return "review_stage"

    return "produce"


def route_after_stage_review(state: ProductionState) -> str:
    """After user reviews a production stage: next stage, redo, or assemble."""
    if state.get("status") == "all_stages_complete":
        return "assemble"
    if state.get("status") == "stage_approved":
        return "produce"
    return "produce"


def route_after_assembly_review(state: ProductionState) -> str:
    """After user reviews assembly: approve → polish, modify → redo."""
    if state.get("status") == "assembly_approved":
        return "polish"
    return "assemble"


def route_after_polish_review(state: ProductionState) -> str:
    """After user reviews polish: approve → deliver, modify → redo."""
    if state.get("status") == "polish_approved":
        return "deliver"
    return "polish"


# === Graph Builder ===


def build_graph():
    """Build the 16-node production pipeline graph."""
    builder = StateGraph(ProductionState)

    # Phase 1: Intake
    builder.add_node("intake", intake.run)
    builder.add_node("interview", interview.run)

    # Phase 2: Research
    builder.add_node("research", research.run)

    # Phase 3: Creative Direction
    builder.add_node("creative_direction", creative_direction.run)
    builder.add_node("review_direction", review_direction.run)

    # Phase 4: Blueprint
    builder.add_node("blueprint", blueprint.run)
    builder.add_node("review_blueprint", review_blueprint.run)

    # Phase 5: Produce (dynamic capability executor + quality gate)
    builder.add_node("produce", produce.run)
    builder.add_node("quality_gate", quality_gate.run)
    builder.add_node("review_stage", review_stage.run)

    # Phase 6: Assemble
    builder.add_node("assemble", assemble.run)
    builder.add_node("review_assembly", review_assembly.run)

    # Phase 7: Polish
    builder.add_node("polish", polish.run)
    builder.add_node("review_polish", review_polish.run)

    # Phase 8: Deliver
    builder.add_node("deliver", deliver.run)
    builder.add_node("review_final", review_final.run)

    # === Edges ===

    # Phase 1: Intake → Interview → (research or creative_direction)
    builder.add_edge(START, "intake")
    builder.add_edge("intake", "interview")
    builder.add_conditional_edges("interview", route_after_interview)

    # Phase 2: Research → Creative Direction
    builder.add_edge("research", "creative_direction")

    # Phase 3: Creative Direction → Review → (back or blueprint)
    builder.add_edge("creative_direction", "review_direction")
    builder.add_conditional_edges("review_direction", route_after_direction_review)

    # Phase 4: Blueprint → Review → (back or produce)
    builder.add_edge("blueprint", "review_blueprint")
    builder.add_conditional_edges("review_blueprint", route_after_blueprint_review)

    # Phase 5: Produce → Quality Gate → (produce or review_stage)
    builder.add_conditional_edges("produce", route_after_produce)
    builder.add_conditional_edges("quality_gate", route_after_quality_gate)
    builder.add_conditional_edges("review_stage", route_after_stage_review)

    # Phase 6: Assemble → Review → (back or polish)
    builder.add_edge("assemble", "review_assembly")
    builder.add_conditional_edges("review_assembly", route_after_assembly_review)

    # Phase 7: Polish → Review → (back or deliver)
    builder.add_edge("polish", "review_polish")
    builder.add_conditional_edges("review_polish", route_after_polish_review)

    # Phase 8: Deliver → Final Review → END
    builder.add_edge("deliver", "review_final")
    builder.add_edge("review_final", END)

    # Compile with checkpointer for interrupt support
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


# Module-level singleton — compiled once, reused for every request
graph = build_graph()
