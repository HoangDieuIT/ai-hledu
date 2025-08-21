from typing import Optional, List

from .base import service
from .commons import r
from app.ext.templates.template import PromptTemplate
from app.ext.providers import LLMManager
from app.api.view.requests import WritingAssessmentRequest
from app.api.view.responses import WritingAssessmentResponse
from app.ext.custom_datetime.time_handler import CustomDateTime
from app.service.types import ModeRequest


@service
async def assess_writing(request: WritingAssessmentRequest) -> WritingAssessmentResponse:
    try:
        r.logger.info(f"Starting {request.type} assessment")
        
        template = PromptTemplate(
            student_level=request.student_level,
            topic=request.topic,
            text=request.text,
            type=request.type,
            mode=ModeRequest.WRITING
        )
        prompt = template.build()

        llm_manager = LLMManager()
        llm_response = await llm_manager.generate(prompt)
        provider_instance = await llm_manager._ensure_provider()

        assessment_data = provider_instance.parse_writing_response(llm_response.content)
        return WritingAssessmentResponse.of(
            assessment_data,
            provider=llm_response.provider_name,
            model=llm_response.model,
            assessment_timestamp=CustomDateTime.now()
        )
    except Exception as e:
        r.logger.error(f"Assessment failed: {str(e)}")
        return WritingAssessmentResponse.of(
            {
                "overall_score": 0.0,
                "grammar_score": 0.0,
                "vocabulary_score": 0.0,
                "coherence_score": 0.0,
                "content_score": 0.0,
                "general_feedback": "Assessment failed due to technical error.",
                "detailed_feedback": str(e),
                "grammar_errors": None,
                "grammar_improvements": None,
                "vocabulary_suggestions": None,
                "vocabulary_improvements": None,
                "improvement_suggestions": None,
                "suggested": None,
            },
            provider="unknown",
            model="unknown",
            assessment_timestamp=CustomDateTime.now()
        )