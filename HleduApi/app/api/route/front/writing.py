# app/api/route/front/writing.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.service.writing import WritingAssessmentService
from app.api.view.requests import WritingAssessmentRequest
from .commons import r
import json
import asyncio

router = APIRouter()

@router.post("/assess")
async def assess_writing_stream(
    request: WritingAssessmentRequest,
    service: WritingAssessmentService = Depends()
):
    """
    Assess writing using AI provider with SSE streaming
    
    Args:
        request: Writing assessment request with text and parameters
        service: Writing assessment service (auto-injected)
    
    Returns:
        StreamingResponse: SSE stream with real-time assessment results
    """
    
    async def generate_sse():
        try:
            r.logger.info(f"Starting writing assessment for topic: {request.topic}")
            
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting writing assessment...', 'timestamp': asyncio.get_event_loop().time()})}\n\n"
            
            # Send processing event
            yield f"data: {json.dumps({'type': 'processing', 'message': 'Sending text to AI for assessment...', 'progress': 10})}\n\n"
            
            # Send analyzing event
            yield f"data: {json.dumps({'type': 'analyzing', 'message': 'AI is analyzing the text...', 'progress': 30})}\n\n"
            
            try:
                # Send AI processing event
                yield f"data: {json.dumps({'type': 'ai_processing', 'message': 'Processing with AI...', 'progress': 50})}\n\n"
                
                # Use service to assess writing
                r.logger.info("Calling writing assessment service")
                assessment_response = await service.assess_writing(request)
                
                r.logger.info("Writing assessment service completed successfully")
                
                # Send AI complete event
                yield f"data: {json.dumps({'type': 'ai_complete', 'message': 'AI has completed analysis', 'progress': 80})}\n\n"
                
                # Convert service response to SSE format
                assessment_result = _convert_service_response_to_sse(assessment_response)
                
                # Send detailed results for each category
                categories = [
                    ('grammar', assessment_response.grammar_score),
                    ('vocabulary', assessment_response.vocabulary_score),
                    ('structure', assessment_response.coherence_score),  # coherence maps to structure
                    ('content', assessment_response.content_score)
                ]
                
                for category, score in categories:
                    result = {
                        'type': 'result',
                        'category': category,
                        'score': score,
                        'feedback': f"{category.capitalize()} assessment completed",
                        'suggestions': _get_suggestions_for_category(category, score)
                    }
                    r.logger.debug(f"Sending {category} result: score {score}")
                    yield f"data: {json.dumps(result)}\n\n"
                    await asyncio.sleep(0.5)
                
                # Send final summary result
                overall_score = assessment_response.overall_score
                level = _get_level_from_score(overall_score)
                r.logger.info(f"Assessment completed - Overall score: {overall_score}, Level: {level}")
                
                final_result = {
                    'type': 'final',
                    'overall_score': overall_score,
                    'level': level,
                    'summary': assessment_response.general_feedback,
                    'recommendations': _get_recommendations_from_score(overall_score),
                    'next_steps': _get_next_steps_from_score(overall_score)
                }
                
                yield f"data: {json.dumps(final_result)}\n\n"
                
            except Exception as ai_error:
                # If error occurs when calling service
                r.logger.error(f"Error calling writing assessment service: {str(ai_error)}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': f'Error calling service: {str(ai_error)}'})}\n\n"
            
            # Send completion event
            r.logger.info("Writing assessment stream completed successfully")
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Writing assessment completed!', 'timestamp': asyncio.get_event_loop().time()})}\n\n"
            
        except Exception as e:
            # Send error event
            r.logger.error(f"Unexpected error during assessment: {str(e)}", exc_info=True)
            error_data = {
                'type': 'error',
                'message': f'Error during assessment: {str(e)}',
                'timestamp': asyncio.get_event_loop().time()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no"  # Disable buffering for nginx
        }
    )

def _convert_service_response_to_sse(response) -> Dict[str, Any]:
    """Convert service response to SSE format"""
    return {
        'grammar': {
            'score': response.grammar_score,
            'feedback': 'Grammar assessment completed',
            'suggestions': _get_suggestions_for_category('grammar', response.grammar_score)
        },
        'vocabulary': {
            'score': response.vocabulary_score,
            'feedback': 'Vocabulary assessment completed',
            'suggestions': _get_suggestions_for_category('vocabulary', response.vocabulary_score)
        },
        'structure': {
            'score': response.coherence_score,
            'feedback': 'Structure assessment completed',
            'suggestions': _get_suggestions_for_category('structure', response.coherence_score)
        },
        'content': {
            'score': response.content_score,
            'feedback': 'Content assessment completed',
            'suggestions': _get_suggestions_for_category('content', response.content_score)
        },
        'overall_score': response.overall_score,
        'level': _get_level_from_score(response.overall_score),
        'summary': response.general_feedback,
        'recommendations': _get_recommendations_from_score(response.overall_score),
        'next_steps': _get_next_steps_from_score(response.overall_score)
    }

def _get_level_from_score(score: float) -> str:
    """Convert score to level description"""
    if score >= 9.0:
        return "Excellent"
    elif score >= 8.0:
        return "Very Good"
    elif score >= 7.0:
        return "Good"
    elif score >= 6.0:
        return "Fair"
    else:
        return "Needs Improvement"

def _get_suggestions_for_category(category: str, score: float) -> list:
    """Get suggestions based on category and score"""
    if score >= 8.0:
        return [f"Excellent {category} usage", "Continue current practice"]
    elif score >= 6.0:
        return [f"Good {category} usage", f"Focus on improving {category}"]
    else:
        return [f"Needs improvement in {category}", f"Practice {category} fundamentals"]

def _get_recommendations_from_score(score: float) -> list:
    """Get general recommendations based on overall score"""
    if score >= 8.0:
        return ["Continue excellent work", "Maintain current level", "Challenge yourself with advanced topics"]
    elif score >= 6.0:
        return ["Focus on weak areas", "Practice regularly", "Read more English materials"]
    else:
        return ["Need fundamental review", "Daily practice required", "Consider additional support"]

def _get_next_steps_from_score(score: float) -> list:
    """Get next steps based on overall score"""
    if score >= 8.0:
        return ["Advanced writing exercises", "Complex topic practice", "Peer review participation"]
    elif score >= 6.0:
        return ["Targeted practice", "Grammar review", "Vocabulary expansion"]
    else:
        return ["Basic writing exercises", "Grammar fundamentals", "Simple sentence practice"]


