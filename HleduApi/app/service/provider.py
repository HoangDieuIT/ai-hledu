from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import app.model.db as m
import app.model.composite as c
from app.resources import context as r
from .base import service, Maybe

_current_provider: Optional[c.Provider] = None


@service
async def load_and_get_provider() -> Maybe[Optional[c.Provider]]:
    """
    Load current active provider from database into cache and return it.
    """
    global _current_provider
    
    try:
        stmt = (
            select(m.Provider)
            .options(selectinload(m.Provider.ai_models))
            .where(m.Provider.is_active == True)
        )
        result = await r.db.execute(stmt)
        provider_db = result.scalar_one_or_none()
        
        if provider_db:
            active_models = [model for model in provider_db.ai_models if model.is_active]
            
            _current_provider = c.Provider.from_db(provider_db)
            
            if active_models:
                _current_provider.ai_models = [c.AIModel.from_db(model) for model in active_models]
            else:
                _current_provider.ai_models = []
            
            r.logger.info(f"Loaded active provider: {_current_provider.name} with {len(_current_provider.ai_models or [])} active models")
            return _current_provider
        else:
            _current_provider = None
            r.logger.warning("No active provider found in database")
            return None
            
    except Exception as e:
        _current_provider = None
        r.logger.error(f"Failed to load provider from database: {e}")
        return None


@service
async def update_provider(provider_id: str) -> Maybe[c.Provider]:
    """
    Update provider as active and reload cache.
    Returns updated provider with active models only.
    """
    global _current_provider
    
    try:
        await r.db.execute(
            m.Provider.__table__.update().values(is_active=False)
        )
        
        result = await r.db.execute(
            m.Provider.__table__.update()
            .where(m.Provider.id == provider_id)
            .values(is_active=True)
        )
        
        if result.rowcount == 0:
            from app.model.errors import Errors
            return Errors.DATA_NOT_FOUND.on(message=f"Provider with ID {provider_id} not found")
        
        await r.db.commit()
        
        provider_result = await load_and_get_provider()
        if provider_result and _current_provider:
            r.logger.info(f"Provider updated to: {_current_provider.name}")
            return _current_provider
        else:
            from app.model.errors import Errors
            return Errors.IO_ERROR.on(message="Failed to reload provider after update")
            
    except Exception as e:
        await r.db.rollback()
        r.logger.error(f"Failed to update provider: {e}")
        from app.model.errors import Errors
        return Errors.IO_ERROR.on(message="Failed to update provider")