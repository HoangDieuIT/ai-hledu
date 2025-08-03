from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid


class Base(DeclarativeBase):
    pass


class Provider(Base):
    """
    AI service provider model.
    """
    __tablename__ = "provider"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(150), unique=True)
    api_key: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationship
    ai_models: Mapped[list["AIModels"]] = relationship(back_populates="provider")


class AIModels(Base):
    """
    AI model configuration.
    """
    __tablename__ = "ai_models"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(150), unique=True)
    provider_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("provider.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationship
    provider: Mapped["Provider"] = relationship(back_populates="ai_models")