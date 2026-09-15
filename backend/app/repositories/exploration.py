from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exploration import ExplorationSite
from app.schemas.common import Metadata
from app.schemas.exploration import Site
from geoalchemy2.elements import WKTElement


class ExplorationRepository:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _schema(row: ExplorationSite) -> Site:
        return Site(
            id=row.id,
            name=row.name,
            region=row.region,
            status=row.status,
            latitude=row.latitude,
            longitude=row.longitude,
            origin=row.origin,
            notes=row.notes,
            metadata=Metadata(
                source=row.origin,
                is_stub=row.origin == "demo_fixture",
                message="Saved exploration location; mineral occurrence is unverified.",
                warning="Not a confirmed deposit or reserve.",
            ),
        )

    def list_sites(self) -> list[Site]:
        return [
            self._schema(row)
            for row in self.session.scalars(
                select(ExplorationSite).order_by(ExplorationSite.id)
            )
        ]

    def get(self, site_id: str) -> Site | None:
        row = self.session.get(ExplorationSite, site_id)
        return self._schema(row) if row else None

    def create(self, site_id, request) -> Site:
        row = ExplorationSite(
            id=site_id,
            name=request.name,
            latitude=request.latitude,
            longitude=request.longitude,
            region=request.region,
            notes=request.notes,
            origin="user_location",
            status="ACTIVE",
            geometry=WKTElement(
                f"POINT({request.longitude} {request.latitude})", srid=4326
            ),
        )
        self.session.add(row)
        self.session.flush()
        return self._schema(row)
