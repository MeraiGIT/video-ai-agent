from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agent.state import VideoState
from agent.nodes import (
    analyze_input,
    write_script,
    review_script,
    plan_scenes,
    review_scenes,
    generate_images,
    review_images,
    generate_videos,
    review_videos,
    generate_voiceover,
    review_voiceover,
    assemble_video,
    add_captions,
    finish_individual,
)


# --- Conditional edge functions ---

def _after_review_script(state: VideoState) -> str:
    if state.get("status") == "script_approved":
        return "generate_scenes"
    return "review_script"


def _after_review_scenes(state: VideoState) -> str:
    if state.get("status") == "scenes_approved":
        return "generate_images"
    return "review_scenes"


def _after_review_images(state: VideoState) -> str:
    if state.get("status") == "images_approved":
        return "generate_videos"
    if state.get("status") == "images_regenerating":
        return "generate_images"
    # Unclear request - loop back to review
    return "review_images"


def _after_review_videos(state: VideoState) -> str:
    if state.get("status") == "videos_approved":
        return "generate_voiceover"
    if state.get("status") == "videos_regenerating":
        return "generate_videos"
    return "review_videos"


def _after_review_voiceover(state: VideoState) -> str:
    if state.get("status") == "voiceover_approved":
        if state.get("concat_enabled", True):
            return "assemble_video"
        return "finish_individual"
    return "review_voiceover"


def build_graph():
    """Build the content creation pipeline with separate generate/review nodes."""
    builder = StateGraph(VideoState)

    # Add all nodes
    builder.add_node("analyze_input", analyze_input.run)
    builder.add_node("generate_script", write_script.generate)
    builder.add_node("review_script", review_script.review)
    builder.add_node("generate_scenes", plan_scenes.generate)
    builder.add_node("review_scenes", review_scenes.review)
    builder.add_node("generate_images", generate_images.generate)
    builder.add_node("review_images", review_images.review)
    builder.add_node("generate_videos", generate_videos.generate)
    builder.add_node("review_videos", review_videos.review)
    builder.add_node("generate_voiceover", generate_voiceover.generate)
    builder.add_node("review_voiceover", review_voiceover.review)
    builder.add_node("assemble_video", assemble_video.run)
    builder.add_node("add_captions", add_captions.run)
    builder.add_node("finish_individual", finish_individual.run)

    # Linear flow: analyze → generate → review (with conditional loops)
    builder.add_edge(START, "analyze_input")
    builder.add_edge("analyze_input", "generate_script")
    builder.add_edge("generate_script", "review_script")
    builder.add_conditional_edges("review_script", _after_review_script)

    builder.add_edge("generate_scenes", "review_scenes")
    builder.add_conditional_edges("review_scenes", _after_review_scenes)

    builder.add_edge("generate_images", "review_images")
    builder.add_conditional_edges("review_images", _after_review_images)

    builder.add_edge("generate_videos", "review_videos")
    builder.add_conditional_edges("review_videos", _after_review_videos)

    builder.add_edge("generate_voiceover", "review_voiceover")
    builder.add_conditional_edges("review_voiceover", _after_review_voiceover)

    builder.add_edge("assemble_video", "add_captions")
    builder.add_edge("add_captions", END)
    builder.add_edge("finish_individual", END)

    # Compile with checkpointer for interrupt/resume support
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


# Module-level singleton - compiled once, reused for every request
graph = build_graph()
