from typing import Protocol

from app.schemas.common import ProviderAvailability


class FeatureProvider(Protocol):
    def availability(self) -> ProviderAvailability: ...


class GEEProvider:
    def availability(self) -> ProviderAvailability:
        return ProviderAvailability(provider="gee", features=[
            "rainfall_history", "soil_moisture", "ndvi", "land_surface_temperature",
            "geology", "terrain",
        ])
