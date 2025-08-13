# app/api/route/front/writing.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.service.writing import assess_writing
from app.api.view.requests import WritingAssessmentRequest
from typing import Dict, Any
import json
import asyncio
from app.api.commons import (
    APIRouter,
    Depends,
    Body,
    vr,
    vq,
    with_otp,
    maybe_otp,
    OTPAuthorized,
    ServiceContext,
)

router = APIRouter()

@router.post(
    "/assess", 
    response_model=vr.WritingAssessmentResponse
)
async def assess_writing_stream(
    request: WritingAssessmentRequest, 
    auth: OTPAuthorized = Depends(with_otp)
):
    """
    Assess writing using AI provider with SSE streaming
    
    Args:
        request: Writing assessment request with text and parameters
        service: Writing assessment service (auto-injected)
    
    Returns:
        StreamingResponse: SSE stream with real-time assessment results
    """
    
    # async def generate_sse():
    #     try:
    #         # Send start event
    #         yield f"data: {json.dumps({'type': 'start', 'message': 'Starting writing assessment...', 'timestamp': asyncio.get_event_loop().time()})}\n\n"
            
    #         # Send processing event
    #         yield f"data: {json.dumps({'type': 'processing', 'message': 'Sending text to AI for assessment...', 'progress': 10})}\n\n"
            
    #         # Send analyzing event
    #         yield f"data: {json.dumps({'type': 'analyzing', 'message': 'AI is analyzing the text...', 'progress': 30})}\n\n"
            
    #         try:
    #             # Send AI processing event
    #             yield f"data: {json.dumps({'type': 'ai_processing', 'message': 'Processing with AI...', 'progress': 50})}\n\n"
                
    #             # Use service to assess writing
    #             assessment_response = await response_model.assess_writing(request)
                            
    #             # Send AI complete event
    #             yield f"data: {json.dumps({'type': 'ai_complete', 'message': 'AI has completed analysis', 'progress': 80})}\n\n"
                
    #             # Send detailed results for each category
    #             categories = [
    #                 ('grammar', assessment_response.grammar_score),
    #                 ('vocabulary', assessment_response.vocabulary_score),
    #                 ('structure', assessment_response.coherence_score),  # coherence maps to structure
    #                 ('content', assessment_response.content_score)
    #             ]
                
    #             for category, score in categories:
    #                 result = {
    #                     'type': 'result',
    #                     'category': category,
    #                     'score': score,
    #                     'feedback': f"{category.capitalize()} assessment completed",
    #                 }
    #                 yield f"data: {json.dumps(result)}\n\n"
    #                 await asyncio.sleep(0.5)
                
    #             # Send final summary result
    #             overall_score = assessment_response.overall_score
                
    #             final_result = {
    #                 'type': 'final',
    #                 'overall_score': overall_score,
    #                 'summary': assessment_response.general_feedback,
    #             }
                
    #             yield f"data: {json.dumps(final_result)}\n\n"
                
    #         except Exception as ai_error:
    #             # If error occurs when calling service
    #             yield f"data: {json.dumps({'type': 'error', 'message': f'Error calling service: {str(ai_error)}'})}\n\n"
            
    #         # Send completion event
    #         yield f"data: {json.dumps({'type': 'complete', 'message': 'Writing assessment completed!', 'timestamp': asyncio.get_event_loop().time()})}\n\n"
            
    #     except Exception as e:
    #         # Send error event
    #         error_data = {
    #             'type': 'error',
    #             'message': f'Error during assessment: {str(e)}',
    #             'timestamp': asyncio.get_event_loop().time()
    #         }
    #         yield f"data: {json.dumps(error_data)}\n\n"
    
    # return StreamingResponse(
    #     generate_sse(),
    #     media_type="text/event-stream",
    #     headers={
    #         "Cache-Control": "no-cache",
    #         "Connection": "keep-alive",
    #         "Access-Control-Allow-Origin": "*",
    #         "Access-Control-Allow-Headers": "Cache-Control",
    #         "X-Accel-Buffering": "no"  # Disable buffering for nginx
    #     }
    # )
    result = await assess_writing(request)
    return result



