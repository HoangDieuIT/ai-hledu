import logging
import json
import re
from typing import Optional, Dict, Any
from .base import service, Maybe
from .commons import r, Errors
from app.ext.templates.template import PromptTemplate
from app.service.types import TypeRequest, ModeRequest
from app.ext.providers import LLMManager
from app.api.view.requests import WritingAssessmentRequest
from app.api.view.responses import WritingAssessmentResponse, GrammarError, VocabularySuggestion


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

@service
async def assess_writing(request: WritingAssessmentRequest) -> WritingAssessmentResponse:
    """
    Assess writing using AI provider
    
    Args:
        request: Writing assessment request
        
    Returns:
        WritingAssessmentResponse: Assessment results
    """
    try:
        # Build prompt
        r.logger.info(f"Building prompt for {request.type} assessment")
        template = PromptTemplate(
            student_level=request.student_level,
            topic=request.topic,
            text=request.text,
            type=request.type,
            mode=request.mode
        )
        prompt = template.build()
        
        # Step 2: Generate AI response
        r.logger.info("Generating AI response")
        llm_response = await LLMManager().generate(prompt)

        # Step 3: Parse and validate response
        r.logger.info("Parsing AI response")
        assessment_data = _parse_ai_response(llm_response.content)
        
        # Step 4: Build response object
        response = WritingAssessmentResponse(
            **assessment_data,
            provider_used=llm_response.provider_name,
            model_used=llm_response.model_name
        )
        return response
        
    except Exception as e:
        r.logger.error(f"Assessment failed: {str(e)}")
        # Return fallback response
        Errors.IO_ERROR.on(message="Failed to reponse writing")


def _parse_ai_response(response: str) -> Dict[str, Any]:
    try:
        # Nếu response là list/dict thì chuyển sang string trước
        if isinstance(response, (list, dict)):
            response = json.dumps(response)

        # Nếu response là string nhưng có markdown code block thì cắt ra
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            json_str = match.group(0)
        else:
            json_str = response

        data = json.loads(json_str)

        # Map field bắt buộc
        required_fields = [
            'overall_score', 'grammar_score', 'vocabulary_score',
            'coherence_score', 'content_score', 'general_feedback'
        ]
        for field in required_fields:
            if field not in data:
                r.logger.warning(f"Missing required field: {field}")
                data[field] = _extract_from_text(json_str)

        # Chuẩn hóa giá trị score
        score_fields = ['overall_score', 'grammar_score', 'vocabulary_score', 
                        'coherence_score', 'content_score']
        for field in score_fields:
            if field in data:
                try:
                    data[field] = max(0.0, min(10.0, float(data[field])))
                except ValueError:
                    data[field] = 0.0

        return data

    except json.JSONDecodeError as e:
        r.logger.error(f"Failed to parse JSON response: {e}")
        r.logger.info(response)
        from app.model.errors import Errors
        return Errors.IO_ERROR.on(message="Failed to parse response")

def _extract_from_text(content: str) -> Dict[str, Any]:
    """
    Extract assessment data from text response when JSON parsing fails
    
    Args:
        content: Text response from AI
        
    Returns:
        Dict with extracted data
    """
    # Try to extract any useful information from AI content
    extracted_info = _extract_useful_info_from_text(content)
    
    return {
        'overall_score': extracted_info.get('overall_score', 5.0),
        'grammar_score': extracted_info.get('grammar_score', 5.0),
        'vocabulary_score': extracted_info.get('vocabulary_score', 5.0),
        'coherence_score': extracted_info.get('coherence_score', 5.0),
        'content_score': extracted_info.get('content_score', 5.0),
        'general_feedback': extracted_info.get('general_feedback', 'AI response parsing completed'),
        'detailed_feedback': content,
        'grammar_errors': extracted_info.get('grammar_errors', []),
        'grammar_improvements': extracted_info.get('grammar_improvements', []),
        'vocabulary_suggestions': extracted_info.get('vocabulary_suggestions', []),
        'vocabulary_improvements': extracted_info.get('vocabulary_improvements', []),
        'improvement_suggestions': extracted_info.get('improvement_suggestions', []),
        'suggested_writing': content
    }

def _extract_useful_info_from_text(text: str) -> Dict[str, Any]:
    """Extract any useful information from AI text response"""
    info = {}
    
    # Try to find scores in text using regex patterns
    score_patterns = [
        r'grammar.*?(\d+\.?\d*)',
        r'vocabulary.*?(\d+\.?\d*)',
        r'structure.*?(\d+\.?\d*)',
        r'content.*?(\d+\.?\d*)',
        r'overall.*?(\d+\.?\d*)',
        r'coherence.*?(\d+\.?\d*)'
    ]
    
    for pattern in score_patterns:
        match = re.search(pattern, text.lower())
        if match:
            score = float(match.group(1))
            if 'grammar' in pattern:
                info['grammar_score'] = score
            elif 'vocabulary' in pattern:
                info['vocabulary_score'] = score
            elif 'structure' in pattern:
                info['structure_score'] = score
            elif 'content' in pattern:
                info['content_score'] = score
            elif 'overall' in pattern:
                info['overall_score'] = score
            elif 'coherence' in pattern:
                info['coherence_score'] = score
    
    # Calculate overall score if individual scores found
    scores = [info.get(f'{cat}_score', 5.0) for cat in ['grammar_score', 'vocabulary_score', 'coherence_score', 'content_score']]
    if scores:
        info['overall_score'] = round(sum(scores) / len(scores), 1)
    
    # Try to extract feedback and suggestions
    feedback_patterns = [
        r'grammar.*?(?:feedback|comment|note):\s*([^.]+)',
        r'vocabulary.*?(?:feedback|comment|note):\s*([^.]+)',
        r'structure.*?(?:feedback|comment|note):\s*([^.]+)',
        r'content.*?(?:feedback|comment|note):\s*([^.]+)'
    ]
    
    for pattern in feedback_patterns:
        match = re.search(pattern, text.lower())
        if match:
            feedback = match.group(1).strip()
            if 'grammar' in pattern:
                info['grammar_feedback'] = feedback
            elif 'vocabulary' in pattern:
                info['vocabulary_feedback'] = feedback
            elif 'structure' in pattern:
                info['structure_feedback'] = feedback
            elif 'content' in pattern:
                info['content_feedback'] = feedback
    
    # Extract general feedback
    general_feedback_match = re.search(r'(?:overall|general).*?(?:feedback|assessment|comment):\s*([^.]+)', text.lower())
    if general_feedback_match:
        info['general_feedback'] = general_feedback_match.group(1).strip()
    
    return info

