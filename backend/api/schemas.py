from typing import Literal, Optional
from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    topic: str
    video_model: Literal["seedance", "veo", "kling", "kling_ref"] = "seedance"
    concat_enabled: bool = True
    uploaded_file_urls: Optional[list[str]] = None


class CreateSessionResponse(BaseModel):
    session_id: str


class ResumeRequest(BaseModel):
    action: Literal["approve", "modify", "regenerate"]
    payload: Optional[dict] = None
    # For modify: {"message": "make it more funny"}
    # For regenerate: {"indices": [0, 2]}


class UploadResponse(BaseModel):
    file_url: str
    file_type: str
    filename: str


class ErrorResponse(BaseModel):
    detail: str
