from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExplorationSite(Base):
    __tablename__ = "exploration_sites"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90"),
        CheckConstraint("longitude BETWEEN -180 AND 180"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'UNDER_REVIEW')"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), index=True)
    region: Mapped[str | None] = mapped_column(String(100))
    origin: Mapped[str] = mapped_column(
        String(32), default="user_location", server_default="demo_fixture"
    )
    notes: Mapped[str | None] = mapped_column(String(2000))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    geometry = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    boundary = mapped_column(Geometry("POLYGON", srid=4326), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
