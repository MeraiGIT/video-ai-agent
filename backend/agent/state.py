import operator
from typing import Annotated, NotRequired
from typing_extensions import TypedDict


class Scene(TypedDict):
    scene_number: int
    narration: str
    visual_description: str
    image_prompt: str
    duration: float
    image_url: NotRequired[str]  # public fal.ai CDN URL (for video gen)
    image_local_path: NotRequired[str]  # downloaded file
    video_local_path: NotRequired[str]  # downloaded video file


class VideoState(TypedDict):
    # Input
    job_id: str
    input_topic: str
    video_model: str  # "seedance" | "veo" | "kling"
    concat_enabled: bool  # whether to assemble into single video

    # Generated content
    script: NotRequired[str]
    scenes: NotRequired[list[Scene]]
    voiceover_path: NotRequired[str]
    assembled_video_path: NotRequired[str]
    final_video_path: NotRequired[str]

    # Tracking
    status: NotRequired[str]
    error: NotRequired[str]
    progress_messages: Annotated[list[str], operator.add]
