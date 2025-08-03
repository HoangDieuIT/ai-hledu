from pydantic import BaseModel, Field


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