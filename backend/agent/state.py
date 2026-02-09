"""
Universal ProductionState for the AI Production Studio.

All fields are optional (NotRequired) so the state works for ANY content type.
The LLM populates only the fields relevant to the current project.
"""

import operator
from typing import Annotated, NotRequired
from typing_extensions import TypedDict


# === Supporting Types ===


class UploadedFile(TypedDict):
    url: str
    type: str  # "image" | "video" | "audio" | "document"
    filename: str
    analysis: NotRequired[str]  # Gemini analysis of the file


class Scene(TypedDict):
    scene_number: int
    narration: str
    visual_description: str
    image_prompt: str
    video_prompt: NotRequired[str]
    camera: NotRequired[dict]  # {shot_type, movement, angle}
    duration: float
    transition_to_next: NotRequired[str]  # "cut" | "fade" | "dissolve" | etc.
    text_overlay: NotRequired[str]
    sfx_cue: NotRequired[str]
    image_url: NotRequired[str]
    image_local_path: NotRequired[str]
    video_url: NotRequired[str]
    video_local_path: NotRequired[str]


class ImageAsset(TypedDict):
    scene_index: NotRequired[int]
    url: str
    local_path: NotRequired[str]
    model: str
    cost: float
    prompt: NotRequired[str]


class VideoAsset(TypedDict):
    scene_index: NotRequired[int]
    url: NotRequired[str]
    local_path: str
    model: str
    cost: float
    duration: float
    prompt: NotRequired[str]


class QualityResult(TypedDict):
    asset_type: str  # "image" | "video" | "audio"
    asset_index: int
    score: float  # 1-10
    issues: NotRequired[list[str]]
    suggestions: NotRequired[list[str]]
    passed: bool


class BudgetVariant(TypedDict):
    tier: str  # "budget" | "standard" | "premium"
    total_estimate: float
    model_selections: dict  # {capability: model_id}
    cost_breakdown: list[dict]  # [{step, model, count, unit_cost, total}]
    tradeoffs: str


class PipelineStage(TypedDict):
    name: str
    status: str  # "pending" | "active" | "completed" | "failed"
    cost: NotRequired[float]
    assets_count: NotRequired[int]
    substeps: NotRequired[list[dict]]


# === Main State ===


class ProductionState(TypedDict):
    # === Identity ===
    job_id: str
    project_id: NotRequired[str]  # Supabase project ID
    project_name: NotRequired[str]

    # === User Input ===
    user_request: NotRequired[str]
    uploaded_files: NotRequired[list[UploadedFile]]

    # === Phase 1: Intake ===
    content_type: NotRequired[str]  # "short_video" | "long_video" | "graphic" | "audio" | "presentation"
    target_platform: NotRequired[str]  # "tiktok" | "youtube" | "instagram" | "linkedin" | "custom"
    target_audience: NotRequired[str]
    constraints: NotRequired[dict]  # {duration, aspect_ratio, dimensions, style, etc.}
    reference_materials: NotRequired[list[dict]]  # Processed references {type, url, analysis}
    interview_complete: NotRequired[bool]
    interview_answers: NotRequired[str]  # User's answers to follow-up questions

    # === Phase 2: Research ===
    research_needed: NotRequired[bool]
    research_insights: NotRequired[dict]  # {trends, references, specs, recommendations}

    # === Phase 3: Creative Direction ===
    creative_brief: NotRequired[dict]
    production_plan: NotRequired[list[dict]]  # Ordered capability steps
    budget_variants: NotRequired[list[BudgetVariant]]
    selected_variant: NotRequired[str]  # "budget" | "standard" | "premium"

    # === Phase 4: Blueprint ===
    blueprint: NotRequired[dict]  # Freeform, LLM-generated structure

    # === Phase 5: Production ===
    current_stage_index: NotRequired[int]
    current_chunk: NotRequired[int]  # For long-form: which chunk (0-based)
    total_chunks: NotRequired[int]  # For long-form: total chunks

    # Production artifacts
    script: NotRequired[str]
    scenes: NotRequired[list[Scene]]
    character_sheets: NotRequired[list[dict]]  # Face consistency data
    images: NotRequired[list[ImageAsset]]
    videos: NotRequired[list[VideoAsset]]
    voiceover_path: NotRequired[str]
    music_path: NotRequired[str]
    sfx_paths: NotRequired[list[str]]
    mixed_audio_path: NotRequired[str]

    # Quality tracking
    quality_results: NotRequired[list[QualityResult]]
    retry_count: NotRequired[int]

    # === Phase 6-8: Post-production ===
    assembled_path: NotRequired[str]
    polished_path: NotRequired[str]
    final_output_path: NotRequired[str]
    caption_style: NotRequired[str]
    transition_type: NotRequired[str]

    # === Cost Tracking ===
    total_cost: NotRequired[float]
    cost_breakdown: NotRequired[list[dict]]  # [{step, model, count, unit_cost, total}]
    budget_limit: NotRequired[float]

    # === Pipeline Visualization ===
    pipeline_stages: NotRequired[list[PipelineStage]]

    # === Meta ===
    status: NotRequired[str]
    error: NotRequired[str]
    progress_messages: Annotated[list[str], operator.add]
