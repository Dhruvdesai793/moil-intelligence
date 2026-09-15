from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    site_id: Mapped[str | None] = mapped_column(ForeignKey("exploration_sites.id"), index=True)
    coordinates: Mapped[dict] = mapped_column(JSONB)
    prediction_type: Mapped[str] = mapped_column(String(64))
    result_payload: Mapped[dict] = mapped_column(JSONB)
    model_version: Mapped[str] = mapped_column(String(64))
    feature_version: Mapped[str] = mapped_column(String(64))
    is_stub: Mapped[bool] = mapped_column(Boolean)
    warning: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
