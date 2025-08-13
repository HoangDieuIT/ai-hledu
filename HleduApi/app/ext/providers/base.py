from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional, Any


class ProviderConfig(BaseModel):
    provider_name: str
    api_key: str
    model_name: Optional[str] = None
    api_secret: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: int = 2048
    timeout_seconds: int = 300


class LLmResponse(BaseModel):
    content: Any
    provider_name: str
    model_name: str


class BaseProvider(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    async def generate_response(self, prompt: str) -> LLmResponse:
        pass
    