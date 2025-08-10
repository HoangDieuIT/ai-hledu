# app/api/route/front/writing.py
from fastapi import APIRouter, Depends, HTTPException
from app.service.writing import WritingAssessmentService
from app.api.view.requests import WritingAssessmentRequest
from app.api.view.responses import WritingAssessmentResponse
from app.api.shared.dependencies import get_current_user 

router = APIRouter()

@router.post("/assess", response_model=WritingAssessmentResponse)
async def assess_writing(
    request: WritingAssessmentRequest,
    service: WritingAssessmentService = Depends()
):
    """
    Assess writing using AI provider
    
    Args:
        request: Writing assessment request with text and parameters
        service: Writing assessment service (auto-injected)
    
    Returns:
        WritingAssessmentResponse: Detailed assessment results
    """
    try:
        result = await service.assess_writing(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint for writing service"""
    return {"status": "healthy", "service": "writing-assessment"}