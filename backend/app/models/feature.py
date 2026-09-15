from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SiteFeature(Base):
    __tablename__ = "site_features"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    site_id: Mapped[str | None] = mapped_column(ForeignKey("exploration_sites.id"), index=True)
    source: Mapped[str] = mapped_column(String(64))
    feature_version: Mapped[str] = mapped_column(String(64))
    feature_payload: Mapped[dict] = mapped_column(JSONB)
    geometry = mapped_column(Geometry("GEOMETRY", srid=4326), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_stub: Mapped[bool] = mapped_column(Boolean)
    readiness: Mapped[str] = mapped_column(String(32))
    warning: Mapped[str | None] = mapped_column(String)
