from . import db
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Provider:
    """
    Provider composite model.
    """
    id: str
    name: str
    api_key: str
    is_active: bool
    ai_models: Optional[List['AIModel']] = None

    @classmethod
    def from_db(cls, provider: db.Provider) -> 'Provider':
        """
        Create composite from database model.
        """
        return cls(
            id=provider.id,
            name=provider.name,
            api_key=provider.api_key,
            is_active=provider.is_active,
            ai_models=[AIModel.from_db(model) for model in provider.ai_models] if provider.ai_models else None
        )


@dataclass
class AIModel:
    """
    AI Model composite model.
    """
    id: str
    name: str
    provider_id: str
    is_active: bool
    provider: Optional[Provider] = None

    @classmethod
    def from_db(cls, ai_model: db.AIModels) -> 'AIModel':
        """
        Create composite from database model.
        """
        provider = None
        if hasattr(ai_model, 'provider') and ai_model.provider:
            provider = Provider(
                id=ai_model.provider.id,
                name=ai_model.provider.name,
                api_key=ai_model.provider.api_key,
                is_active=ai_model.provider.is_active
            )
        
        return cls(
            id=ai_model.id,
            name=ai_model.name,
            provider_id=ai_model.provider_id,
            is_active=ai_model.is_active,
            provider=provider
        )