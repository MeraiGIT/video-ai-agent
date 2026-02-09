from typing import Literal, Optional
from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    topic: str  # user's creative request (universal)
    video_model: Optional[str] = None  # legacy — ignored in v3
    concat_enabled: Optional[bool] = None  # legacy — ignored in v3
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
