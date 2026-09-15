import importlib
import logging
from threading import Lock
from time import monotonic
import httplib2
from app.core.config import Settings
from app.schemas.common import Metadata, ProviderAvailability, Readiness, utc_now
from app.schemas.features import FeatureBundle, ProductQuality, SpectralBand

logger = logging.getLogger("moil.gee")
BANDS = {
    "B2": (496.6, 10),
    "B3": (560, 10),
    "B4": (664.5, 10),
    "B5": (703.9, 20),
    "B6": (740.2, 20),
    "B7": (782.5, 20),
    "B8": (835.1, 10),
    "B8A": (864.8, 20),
    "B11": (1613.7, 20),
    "B12": (2202.4, 20),
}


class GEEProvider:
    def __init__(
        self, settings: Settings, *, request_timeout_seconds: int | None = None
    ):
        self.settings = settings
        self.request_timeout_seconds = (
            request_timeout_seconds or settings.gee_timeout_seconds
        )
        self._ee = None
        self._lock = Lock()
        self._checked_at = 0.0
        self._availability = None

    def availability(self) -> ProviderAvailability:
        if not self.settings.gee_enabled:
            return self._status(
                Readiness.NOT_CONFIGURED,
                "GEE_ENABLED=false; no Earth Engine calls made.",
            )
        with self._lock:
            if self._availability is not None and monotonic() - self._checked_at < 30:
                return self._availability.model_copy(deep=True)
            try:
                ee = importlib.import_module("ee")
                if self.settings.gee_auth_method != "oauth":
                    return self._status(
                        Readiness.NOT_CONFIGURED, "Only development OAuth is supported."
                    )
                ee.Initialize(
                    project=self.settings.gee_project_id,
                    http_transport=httplib2.Http(timeout=self.request_timeout_seconds),
                )
                ee.data.setDeadline(self.request_timeout_seconds * 1000)
                ee.data.getAlgorithms()
                self._ee = ee
                result = self._status(
                    Readiness.OK,
                    "Earth Engine initialized; algorithm smoke check passed.",
                )
            except ImportError:
                result = self._status(Readiness.UNAVAILABLE, "Install earthengine-api.")
            except Exception as exc:
                auth = any(
                    w in str(exc).lower()
                    for w in (
                        "authenticate",
                        "credential",
                        "invalid_grant",
                        "refresherror",
                    )
                )
                result = self._status(
                    Readiness.AUTH_REQUIRED if auth else Readiness.UNAVAILABLE,
                    "Run earthengine authenticate and accept browser OAuth."
                    if auth
                    else "Earth Engine initialization failed. Check project access and network.",
                )
                logger.warning(
                    "Earth Engine initialization failed (%s)", type(exc).__name__
                )
            self._availability = result
            self._checked_at = monotonic()
            return result.model_copy(deep=True)

    def cached_availability(self) -> ProviderAvailability:
        if not self.settings.gee_enabled:
            return self._status(Readiness.NOT_CONFIGURED, "GEE_ENABLED=false.")
        # Never wait on the initialization lock or remote network in ordinary reads.
        if self._availability is None or monotonic() - self._checked_at > 300:
            return self._status(
                Readiness.NOT_CHECKED,
                "Provider readiness has not been checked recently. Use Check GEE; stored features remain available.",
            )
        return self._availability.model_copy(deep=True)

    def _status(self, readiness, warning):
        return ProviderAvailability(
            provider="gee",
            readiness=readiness,
            features=[
                "ndvi",
                "ndmi",
                "sentinel2_reflectance",
                "land_surface_temperature",
                "soil_moisture",
                "rainfall_history",
                "terrain",
            ],
            metadata=Metadata(
                source="earth_engine",
                is_stub=False,
                message=warning,
                warning=None if readiness == Readiness.OK else warning,
            ),
        )

    def extract_features_for_point(self, latitude, longitude, start_date, end_date):
        return self._extract([longitude, latitude], None, start_date, end_date)

    def extract_features_for_aoi(self, geojson, start_date, end_date):
        return self._extract(None, geojson, start_date, end_date)

    def _extract(self, point, aoi, start_date, end_date):
        status = self.availability()
        if status.readiness != Readiness.OK:
            return FeatureBundle(
                readiness=status.readiness, warning=status.metadata.warning
            )
        ee = self._ee
        location = ee.Geometry.Point(point) if point else ee.Geometry(aoi)

        # Metric sampling support; never buffer longitude/latitude in degrees.
        def region(scale):
            return location.buffer(scale * 1.5).bounds() if point else location

        payload, quality, spectra = {}, {}, []
        start, end = str(start_date), str(end_date)

        def collection(name):
            return (
                ee.ImageCollection(name).filterBounds(location).filterDate(start, end)
            )

        def reduce(image, scale, projection=None):
            return image.reduceRegion(
                reducer=ee.Reducer.median(),
                geometry=region(scale),
                scale=scale,
                crs=projection,
                maxPixels=2000000,
                tileScale=2,
            ).getInfo()

        def info(col):
            count = int(col.size().getInfo())
            latest = (
                ee.Date(col.aggregate_max("system:time_start"))
                .format("YYYY-MM-dd")
                .getInfo()
                if count
                else None
            )
            return count, latest

        def product(key, name, scale, units, operation):
            try:
                operation()
            except Exception as exc:
                logger.warning("GEE product %s failed (%s)", key, type(exc).__name__)
                quality[key] = ProductQuality(
                    collection=name,
                    status="unavailable",
                    native_resolution_m=scale,
                    units=units,
                    warning="Product extraction failed; no replacement values.",
                )

        def sentinel():
            name = "COPERNICUS/S2_SR_HARMONIZED"
            col = collection(name)
            count, latest = info(col)
            if not count:
                quality["sentinel2"] = ProductQuality(
                    collection=name,
                    status="no_observations",
                    native_resolution_m=10,
                    units="reflectance",
                )
                return

            def mask(image):
                scl = image.select("SCL")
                valid = (
                    scl.neq(0)
                    .And(scl.neq(1))
                    .And(scl.neq(3))
                    .And(scl.neq(8))
                    .And(scl.neq(9))
                    .And(scl.neq(10))
                    .And(scl.neq(11))
                )
                return (
                    image.select(list(BANDS))
                    .multiply(0.0001)
                    .updateMask(valid)
                    .copyProperties(image, ["system:time_start"])
                )

            composite = col.map(mask).median()
            fractions = []
            for scale in (10, 20):
                names = [b for b, (_, s) in BANDS.items() if s == scale]
                image = composite.select(names)
                projection = ee.Image(col.first()).select(names[0]).projection()
                coverage = (
                    image.mask()
                    .reduce(ee.Reducer.min())
                    .unmask(0)
                    .reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=region(scale),
                        scale=scale,
                        crs=projection,
                        maxPixels=2000000,
                    )
                    .getInfo()
                )
                fraction = float(next(iter(coverage.values())) or 0)
                fractions.append(fraction)
                values = (
                    reduce(image, scale, projection)
                    if fraction >= self.settings.gee_min_valid_fraction
                    else {}
                )
                for band in names:
                    value = values.get(band)
                    payload["s2_" + band] = value
                    spectra.append(
                        SpectralBand(
                            band=band,
                            wavelength_nm=BANDS[band][0],
                            native_resolution_m=scale,
                            reflectance=value,
                        )
                    )

            def ratio(a, b, key):
                image = composite.expression(
                    "(a-b)/(a+b)", {"a": composite.select(a), "b": composite.select(b)}
                )
                projection = ee.Image(col.first()).select("B8A").projection()
                payload[key] = (
                    next(iter(reduce(image, 20, projection).values()), None)
                    if min(fractions) >= self.settings.gee_min_valid_fraction
                    else None
                )

            ratio("B8", "B4", "ndvi")
            ratio("B8A", "B11", "ndmi")
            quality["sentinel2"] = ProductQuality(
                collection=name,
                status="ok"
                if min(fractions) >= self.settings.gee_min_valid_fraction
                else "insufficient_coverage",
                scene_count=count,
                native_resolution_m=10,
                units="reflectance (unitless)",
                valid_fraction=min(fractions),
                latest_observation=latest,
                warning="10 m and 20 m bands have different sampling supports. Vegetation/soil mixtures are not mineral identification.",
            )

        product("sentinel2", "COPERNICUS/S2_SR_HARMONIZED", 10, "reflectance", sentinel)

        def landsat():
            name = "LANDSAT/LC08/C02/T1_L2"
            col = collection(name).filter(ee.Filter.eq("PROCESSING_LEVEL", "L2SP"))
            count, latest = info(col)
            if not count:
                quality["landsat"] = ProductQuality(
                    collection=name,
                    status="no_observations",
                    native_resolution_m=100,
                    units="Celsius",
                )
                return

            def temperature(image):
                qa = image.select("QA_PIXEL")
                valid = qa.bitwiseAnd(63).eq(0).And(image.select("QA_RADSAT").eq(0))
                return (
                    image.select("ST_B10")
                    .multiply(0.00341802)
                    .add(149)
                    .subtract(273.15)
                    .updateMask(valid)
                )

            payload["land_surface_temperature_c"] = reduce(
                col.map(temperature).median(),
                30,
                ee.Image(col.first()).select("ST_B10").projection(),
            ).get("ST_B10")
            quality["landsat"] = ProductQuality(
                collection=name,
                status="ok"
                if payload["land_surface_temperature_c"] is not None
                else "no_valid_pixels",
                scene_count=count,
                native_resolution_m=100,
                units="Celsius",
                latest_observation=latest,
                warning="Thermal native support ~100 m; delivered product grid 30 m. Surface temperature, not air temperature.",
            )

        product("landsat", "LANDSAT/LC08/C02/T1_L2", 100, "Celsius", landsat)

        def coarse(key, name, scale, bands, units, sum_time=False):
            col = collection(name)
            count, latest = info(col)
            if count:
                image = col.select(list(bands))
                values = reduce(
                    image.sum() if sum_time else image.median(),
                    scale,
                    ee.Image(col.first()).select(next(iter(bands))).projection(),
                )
                for band, label in bands.items():
                    payload[label] = values.get(band)
            quality[key] = ProductQuality(
                collection=name,
                status="ok" if count else "no_observations",
                scene_count=count,
                native_resolution_m=scale,
                units=units,
                latest_observation=latest,
                warning=(
                    "Historical observed sum; not a forecast. Missing days can make totals incomplete."
                    if sum_time
                    else "Coarse environmental context; not a site-scale manganese measurement."
                ),
            )
            if sum_time and count != (end_date - start_date).days:
                quality[key].status = "partial_coverage"
            if count and not any(
                payload.get(label) is not None for label in bands.values()
            ):
                quality[key].status = "no_valid_pixels"

        product(
            "rainfall",
            "UCSB-CHG/CHIRPS/DAILY",
            5566,
            "mm",
            lambda: coarse(
                "rainfall",
                "UCSB-CHG/CHIRPS/DAILY",
                5566,
                {"precipitation": "rainfall_total_mm"},
                "mm",
                True,
            ),
        )
        product(
            "soil_moisture",
            "NASA/SMAP/SPL4SMGP/008",
            9000,
            "m3/m3",
            lambda: coarse(
                "soil_moisture",
                "NASA/SMAP/SPL4SMGP/008",
                9000,
                {
                    "sm_surface": "soil_moisture_surface",
                    "sm_rootzone": "soil_moisture_rootzone",
                },
                "m3/m3",
            ),
        )

        def terrain():
            image = ee.Image("USGS/SRTMGL1_003")
            payload["elevation_m"] = reduce(image, 30).get("elevation")
            payload["slope_degrees"] = reduce(ee.Terrain.slope(image), 30).get("slope")
            quality["terrain"] = ProductQuality(
                collection="USGS/SRTMGL1_003",
                status="ok",
                native_resolution_m=30,
                units="metres / degrees",
                warning="Static SRTM terrain; not current mine geometry.",
            )

        product("terrain", "USGS/SRTMGL1_003", 30, "metres/degrees", terrain)
        usable = any(isinstance(v, (float, int)) for v in payload.values())
        return FeatureBundle(
            source="earth_engine",
            is_stub=False,
            feature_version="gee-environment-v1",
            feature_payload=payload,
            quality=quality,
            spectral_bands=sorted(spectra, key=lambda b: b.wavelength_nm),
            extraction_method="Cloud-masked temporal median; point metric square 3x native pixel width; AOI median; coarse products retain native support.",
            readiness=Readiness.OK if usable else Readiness.UNAVAILABLE,
            extracted_at=utc_now(),
            message="Measured environmental features; not validated manganese model inputs.",
            warning="Partial products may be missing. No zero filling. Surface spectra cannot confirm subsurface manganese or reserves.",
        )
