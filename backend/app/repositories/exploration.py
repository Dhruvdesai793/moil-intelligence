from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exploration import ExplorationSite
from app.schemas.common import Metadata
from app.schemas.exploration import Site


class ExplorationRepository:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _schema(row: ExplorationSite) -> Site:
        return Site(id=row.id, name=row.name, region=row.region, status=row.status,
                    latitude=row.latitude, longitude=row.longitude,
                    metadata=Metadata(source="postgresql_demo_fixture",
                                      warning="Seeded software fixtures, not validated MOIL/geological sites."))

    def list_sites(self) -> list[Site]:
        return [self._schema(row) for row in self.session.scalars(
            select(ExplorationSite).order_by(ExplorationSite.id))]

    def get(self, site_id: str) -> Site | None:
        row = self.session.get(ExplorationSite, site_id)
        return self._schema(row) if row else None
