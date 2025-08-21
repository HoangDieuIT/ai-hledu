from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional, Any, Dict


class ProviderConfig(BaseModel):
    provider_name: str
    api_key: str
    model: Optional[str] = None
    api_secret: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: int = 2048
    timeout_seconds: int = 300


class LLmResponse(BaseModel):
    content: Any
    provider_name: str
    model: str


class BaseProvider(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    async def generate_response(self, prompt: str) -> LLmResponse:
        pass
    
    @abstractmethod
    def parse_writing_response(self, raw_content: str) -> Dict[str, Any]:
        """
        Parse raw response content for writing assessment into structured data.
        Each provider must implement this method for custom parsing logic.
        
        Args:
            raw_content: Raw response content from the provider
            
        Returns:
            Dict containing parsed data that maps to WritingAssessmentResponse model
        """
        pass

    def _get_optional_field(self, data: Dict[str, Any], field_name: str) -> Any:
        """
        Get optional field, respecting AI's decision to include or exclude.
        Common logic for all providers.
        """
        field_data = data.get(field_name)
        
        if field_data is None:
            return None
            
        if (isinstance(field_data, list) and not field_data) or field_data == "":
            return None
            
        return field_data
