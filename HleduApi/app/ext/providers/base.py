from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional, Any, Dict

class ProviderConfig(BaseModel):
    provider_name: str
    api_key: str
    model: Optional[str] = None
    api_secret: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: int = 8192
    timeout_seconds: int = 300

class LLmResponse(BaseModel):
    content: Any
    provider_name: str
    model: str

class BaseProvider(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    async def generate_response(self, prompt_or_payload) -> LLmResponse:
        """
        Generate response from LLM provider.
        
        Args:
            prompt_or_payload: Either a string prompt or dict with messages structure
            
        Returns:
            LLmResponse containing the generated content
        """
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