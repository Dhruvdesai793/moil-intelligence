from app.schemas.common import ProviderAvailability


class WeatherProvider:
    def availability(self) -> ProviderAvailability:
        return ProviderAvailability(provider="weather",
                                    features=["observed_rainfall", "forecast_at_origin"])
