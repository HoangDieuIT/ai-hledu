# app/api/view/requests.py
from pydantic import BaseModel, Field
from app.service.types import TypeRequest, ModeRequest
from typing import Optional


class UpdateProviderRequest(BaseModel):
    """
    Request model for updating provider status.
    """
    provider_id: str = Field(description="Provider ID to activate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class WritingAssessmentRequest(BaseModel):
    """Request model cho việc chấm bài writing"""
    student_level: str = Field(
        ..., 
        description="Trình độ học sinh (ví dụ: 3.5, 4.0, 4.5-5.0)",
        example="4.0"
    )
    topic: str = Field(
        ..., 
        description="Chủ đề bài viết",
        example="Environmental Protection",
        min_length=1,
        max_length=200
    )
    text: str = Field(
        ..., 
        description="Nội dung bài viết cần chấm",
        example="Climate change is a serious problem that affects everyone on Earth. We need to take action to reduce carbon emissions and protect our environment.",
        min_length=10,
        max_length=5000
    )
    type: TypeRequest = Field(
        default=TypeRequest.PARAGRAPH,
        description="Loại bài viết"
    )
    mode: ModeRequest = Field(
        default=ModeRequest.WRITING,
        description="Chế độ đánh giá"
    )
    preferred_provider: Optional[str] = Field(
        default=None,
        description="AI provider ưu tiên (optional)",
        example="openai"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "student_level": "4.0",
                "topic": "Environmental Protection",
                "text": "Climate change is a serious problem that affects everyone on Earth. We need to take action to reduce carbon emissions and protect our environment.",
                "type": "paragraph",
                "mode": "writing"
            }
        }