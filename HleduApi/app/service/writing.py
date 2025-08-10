import logging
import json
from typing import Optional, Dict, Any
from .base import service, Maybe
from app.ext.templates.template import PromptTemplate
from app.service.types import TypeRequest, ModeRequest
from app.ext.providers import LLMManager
from app.api.view.requests import WritingAssessmentRequest
from app.api.view.responses import WritingAssessmentResponse, GrammarError, VocabularySuggestion

logger = logging.getLogger(__name__)

# example use 
# pt = PromptTemplate(
#     student_level="3.5", ## or 3.5-4.5, 4.0, 4.5-5.5 etc.
#     topic="Travel",
#     text="I like to travel by train...",
#     type=TypeRequest.PARAGRAPH,
#     mode=ModeRequest.WRITING,
# )
# prompt = pt.build()

# resp = await LLMManager().generate(prompt)

#@service
class WritingAssessmentService:
    """
    Service for assessing writing using AI providers
    """
    
    def __init__(self):
        self.llm_manager = LLMManager()

    async def assess_writing(self, request: WritingAssessmentRequest) -> WritingAssessmentResponse:
        """
        Assess writing using AI provider
        
        Args:
            request: Writing assessment request
            
        Returns:
            WritingAssessmentResponse: Assessment results
        """
        try:
            # Build prompt
            logger.info(f"Building prompt for {request.type} assessment")
            template = PromptTemplate(
                student_level=request.student_level,
                topic=request.topic,
                text=request.text,
                type=request.type,
                mode=request.mode
            )
            prompt = template.build()
            
            # Step 2: Generate AI response
            logger.info("Generating AI response")
            llm_response = await self.llm_manager.generate(prompt)

            # Step 3: Parse and validate response
            logger.info("Parsing AI response")
            assessment_data = self._parse_ai_response(llm_response.content)
            
            # Step 4: Build response object
            response = WritingAssessmentResponse(
                **assessment_data,
                provider_used=llm_response.provider_name,
                model_used=llm_response.model_name
            )
            return response
            
        except Exception as e:
            logger.error(f"Assessment failed: {str(e)}")
            # Return fallback response
            return self._create_fallback_response(request, llm_response, str(e))

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Parse AI response and extract assessment data
        
        Args:
            response: Raw AI response content
            
        Returns:
            Dict[str, Any]: Parsed assessment data

        """
        try:
            # Try to parse JSON response
            data = json.loads(content)
            
            # Validate required fields
            required_fields = ['overall_score', 'grammar_score', 'vocabulary_score', 
                             'coherence_score', 'content_score', 'general_feedback']
            
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    data[field] = self._get_default_value(field)
            
            # Ensure scores are within valid range
            score_fields = ['overall_score', 'grammar_score', 'vocabulary_score', 
                          'coherence_score', 'content_score']
            
            for field in score_fields:
                if field in data:
                    data[field] = max(0.0, min(10.0, float(data[field])))
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Try to extract information from text response
            return self._extract_from_text(content)

    def _extract_from_text(self, content: str) -> Dict[str, Any]:
        """
        Extract assessment data from text response when JSON parsing fails
        
        Args:
            content: Text response from AI
            
        Returns:
            Dict with extracted data
        """
        # Simple text parsing as fallback
        return {
            'overall_score': 5.0,
            'grammar_score': 5.0,
            'vocabulary_score': 5.0,
            'coherence_score': 5.0,
            'content_score': 5.0,
            'general_feedback': 'AI response parsing failed',
            'detailed_feedback': content,
            'grammar_errors': [],
            'grammar_improvements': [],
            'vocabulary_suggestions': [],
            'vocabulary_improvements': [],
            'improvement_suggestions': [],
            'suggested_writing': content
        }
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            'overall_score': 5.0,
            'grammar_score': 5.0,
            'vocabulary_score': 5.0,
            'coherence_score': 5.0,
            'content_score': 5.0,
            'general_feedback': 'Assessment incomplete',
            'detailed_feedback': 'Some assessment data is missing',
            'grammar_errors': [],
            'grammar_improvements': [],
            'vocabulary_suggestions': [],
            'vocabulary_improvements': [],
            'improvement_suggestions': [],
            'suggested_writing': ''
        }
        return defaults.get(field, '')
    
    def _create_fallback_response(self, request: WritingAssessmentRequest, 
                                llm_response, error_msg: str) -> WritingAssessmentResponse:
        """Create fallback response when assessment fails"""
        return WritingAssessmentResponse(
            overall_score=0.0,
            grammar_score=0.0,
            vocabulary_score=0.0,
            coherence_score=0.0,
            content_score=0.0,
            general_feedback=f"Assessment failed: {error_msg}",
            detailed_feedback="Unable to complete assessment due to technical issues",
            grammar_errors=[],
            grammar_improvements=[],
            vocabulary_suggestions=[],
            vocabulary_improvements=[],
            improvement_suggestions=[],
            suggested_writing=request.text,
            provider_used=getattr(llm_response, 'provider_name', 'unknown'),
            model_used=getattr(llm_response, 'model_name', 'unknown')
        )