from sqlalchemy import text

from app.schemas.common import HealthResponse


class HealthService:
    def __init__(self, engine_provider, gee, registry, settings):
        self.engine_provider = engine_provider
        self.gee = gee
        self.registry = registry
        self.settings = settings

    def check(self) -> HealthResponse:
        database = postgis = "unavailable"
        try:
            with self.engine_provider().connect() as connection:
                connection.execute(text("SELECT 1"))
                database = "ok"
                connection.execute(text("SELECT PostGIS_Version()"))
                postgis = "ok"
        except Exception:
            pass
        gee = self.gee.availability().readiness.value
        models = "stub" if self.registry.adapters else "unavailable"
        status = "ok" if database == postgis == "ok" and gee in ("ok", "not_configured") else "degraded"
        return HealthResponse(status=status, service=self.settings.app_name,
                              version=self.settings.app_version, environment=self.settings.environment,
                              database=database, postgis=postgis, gee=gee, model_registry=models)
