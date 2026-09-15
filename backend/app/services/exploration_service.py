from app.core.exceptions import NotFoundError
from app.ml.registry import ModelRegistry
from app.providers.gee import GEEProvider
from app.providers.weather import WeatherProvider
from app.repositories.exploration import ExplorationRepository
from app.schemas.exploration import Site, SiteStatus, SiteSummary


class ExplorationService:
    def __init__(self, repository: ExplorationRepository, registry: ModelRegistry,
                 gee_provider: GEEProvider, weather_provider: WeatherProvider):
        self.repository = repository
        self.registry = registry
        self.gee_provider = gee_provider
        self.weather_provider = weather_provider

    def get_sites(self) -> list[Site]:
        return [site for site in self.repository.list_sites() if site.status == SiteStatus.ACTIVE]

    def get_site(self, site_id: str) -> Site:
        site = self.repository.get(site_id)
        if site is None:
            raise NotFoundError(f"Exploration site '{site_id}' was not found.")
        return site

    def summary(self, site_id: str) -> SiteSummary:
        return SiteSummary(
            site=self.get_site(site_id),
            feature_availability=[self.gee_provider.availability(), self.weather_provider.availability()],
            model_readiness={name: ("not_configured" if name == "grade" else "stub")
                             if name in self.registry.adapters else "unavailable"
                             for name in ("prospectivity", "grade", "production")},
        )
