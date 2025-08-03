import app.service.provider as provider_service
from typing import Optional
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


@router.get(
    "/current",
    response_model=Optional[vr.ProviderResponse],
    summary="Get current active provider",
    description="Get current active provider with active models only."
)
async def get_current_provider(
    auth: OTPAuthorized = Depends(maybe_otp)
):
    """
    Get current active provider with active models.
    Returns None if no provider is active.
    """
    with ServiceContext() as ctx:
        provider = ctx <= await provider_service.load_and_get_provider()
        
        if not provider:
            return None
            
        ai_models = []
        if provider.ai_models:
            ai_models = [
                vr.AIModelResponse(
                    id=model.id,
                    name=model.name,
                    provider_id=model.provider_id,
                    is_active=model.is_active
                )
                for model in provider.ai_models
            ]
        
        return vr.ProviderResponse(
            id=provider.id,
            name=provider.name,
            is_active=provider.is_active,
            ai_models=ai_models
        )


@router.put(
    "/update",
    response_model=vr.ProviderResponse,
    summary="Update active provider",
    description="Update active provider and return current provider with active models."
)
async def update_provider(
    request: vq.UpdateProviderRequest = Body(...),
    auth: OTPAuthorized = Depends(with_otp)
):
    """
    Update active provider.
    Returns updated provider with active models only.
    Requires valid OTP authentication.
    """
    with ServiceContext() as ctx:
        updated_provider = ctx <= await provider_service.update_provider(request.provider_id)
        
        ai_models = []
        if updated_provider.ai_models:
            ai_models = [
                vr.AIModelResponse(
                    id=model.id,
                    name=model.name,
                    provider_id=model.provider_id,
                    is_active=model.is_active
                )
                for model in updated_provider.ai_models
            ]
        
        return vr.ProviderResponse(
            id=updated_provider.id,
            name=updated_provider.name,
            is_active=updated_provider.is_active,
            ai_models=ai_models
        )