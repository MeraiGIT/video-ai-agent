from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agent.state import VideoState
from agent.nodes import (
    analyze_input,
    write_script,
    plan_scenes,
    generate_images,
    generate_videos,
    generate_voiceover,
    assemble_video,
    add_captions,
)
from agent.nodes import finish_individual


def _should_assemble(state: VideoState) -> str:
    """Conditional edge: assemble into single video or finish with individual clips."""
    if state.get("concat_enabled", True):
        return "assemble_video"
    return "finish_individual"


def build_graph():
    """Build the content creation pipeline with interrupt()-based human-in-the-loop."""
    builder = StateGraph(VideoState)

    # Add all nodes
    builder.add_node("analyze_input", analyze_input.run)
    builder.add_node("write_script", write_script.run)
    builder.add_node("plan_scenes", plan_scenes.run)
    builder.add_node("generate_images", generate_images.run)
    builder.add_node("generate_videos", generate_videos.run)
    builder.add_node("generate_voiceover", generate_voiceover.run)
    builder.add_node("assemble_video", assemble_video.run)
    builder.add_node("add_captions", add_captions.run)
    builder.add_node("finish_individual", finish_individual.run)

    # Sequential pipeline with conditional assembly
    builder.add_edge(START, "analyze_input")
    builder.add_edge("analyze_input", "write_script")
    builder.add_edge("write_script", "plan_scenes")
    builder.add_edge("plan_scenes", "generate_images")
    builder.add_edge("generate_images", "generate_videos")
    builder.add_edge("generate_videos", "generate_voiceover")

    # Conditional: assemble or finish with individual clips
    builder.add_conditional_edges("generate_voiceover", _should_assemble)

    builder.add_edge("assemble_video", "add_captions")
    builder.add_edge("add_captions", END)
    builder.add_edge("finish_individual", END)

    # Compile with checkpointer for interrupt/resume support
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


# Module-level singleton - compiled once, reused for every request
graph = build_graph()
