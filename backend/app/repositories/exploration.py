from app.schemas.exploration import Site


class ExplorationRepository:
    def get_sites(self) -> list[Site]:
        return [
            Site(id="zone_a", name="Demo Zone A", latitude=21.123,
                 longitude=79.123, status="ACTIVE"),
            Site(id="zone_b", name="Demo Zone B", latitude=21.456,
                 longitude=79.456, status="INACTIVE"),
            Site(id="zone_c", name="Demo Zone C", latitude=21.3,
                 longitude=79.3, status="ACTIVE"),
        ]

    def get(self, site_id: str) -> Site | None:
        return next((site for site in self.get_sites() if site.id == site_id), None)
