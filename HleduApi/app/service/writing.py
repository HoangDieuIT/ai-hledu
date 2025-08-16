from typing import Optional, List

from .base import service
from .commons import r
from app.ext.templates.template import PromptTemplate
from app.ext.providers import LLMManager
from app.api.view.requests import WritingAssessmentRequest
from app.api.view.responses import WritingAssessmentResponse, GrammarError, VocabularySuggestion
from app.ext.custom_datetime.time_handler import CustomDateTime
from app.service.types import ModeRequest


def _parse_optional_objects(data_list, object_class) -> Optional[List]:
    """Parse optional list of objects from raw data"""
    if not data_list or not isinstance(data_list, list):
        return None
        
    parsed_objects = []
    for item in data_list:
        if isinstance(item, dict):
            try:
                parsed_objects.append(object_class(**item))
            except Exception as e:
                r.logger.warning(f"Failed to create {object_class.__name__}: {e}")
    
    return parsed_objects if parsed_objects else None


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
        grammar_errors = (
            assessment_data.get("grammar_errors"), GrammarError
        )
        vocabulary_suggestions = _parse_optional_objects(
            assessment_data.get("vocabulary_suggestions"), VocabularySuggestion
        )


        response = WritingAssessmentResponse.of(
            {
                **assessment_data,
                "grammar_errors": grammar_errors,
                "vocabulary_suggestions": vocabulary_suggestions,
            },
            provider=llm_response.provider_name,
            model=llm_response.model,
            assessment_timestamp=CustomDateTime.now()
        )
        return response
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