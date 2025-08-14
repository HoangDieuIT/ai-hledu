
from app.service.writing import assess_writing
from app.api.view.requests import WritingAssessmentRequest
from app.api.commons import (
    APIRouter,
    Depends,
    vr,
    with_otp,
    OTPAuthorized,
)

router = APIRouter()

@router.post(
    "/assessment", 
    response_model=vr.WritingAssessmentResponse
)
async def assess_writing_endpoint(
    request: WritingAssessmentRequest, 
    auth: OTPAuthorized = Depends(with_otp)
) -> vr.WritingAssessmentResponse:
    """
    Assess writing using AI provider
    
    Args:
        request: Writing assessment request with text and parameters
        auth: OTP authorization
    
    Returns:
        WritingAssessmentResponse: Complete assessment results
    """
    result = await assess_writing(request)
    return result.get()