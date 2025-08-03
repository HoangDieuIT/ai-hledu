from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal

import app.model.composite as c
from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass
from typing_extensions import Self
from app.resources import context as r

# ================================================================
# Settings
# ================================================================

config = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
)


@dataclass(config=config)
class AIModelResponse:
    """
    AI Model response model.
    """
    id: str = Field(description="AI Model ID")
    name: str = Field(description="AI Model name")
    provider_id: str = Field(description="Provider ID")
    is_active: bool = Field(description="Whether the model is active")


@dataclass(config=config) 
class ProviderResponse:
    """
    Provider response model.
    """
    id: str = Field(description="Provider ID")
    name: str = Field(description="Provider name") 
    is_active: bool = Field(description="Whether the provider is active")
    ai_models: Optional[List[AIModelResponse]] = Field(default=None, description="AI models associated with this provider")