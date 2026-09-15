import json
from datetime import datetime

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.feature import SiteFeature
from app.schemas.features import FeatureBundle


class FeatureRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_feature_bundle(self, bundle: FeatureBundle) -> FeatureBundle:
        geometry = None
        if bundle.coordinates:
            geometry = WKTElement(f"POINT({bundle.coordinates.longitude} {bundle.coordinates.latitude})", srid=4326)
        elif bundle.aoi:
            geometry = func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(bundle.aoi.model_dump())), 4326)
        self.session.add(SiteFeature(
            id=bundle.feature_id, site_id=bundle.site_id, source=bundle.source,
            feature_version=bundle.feature_version, feature_payload=bundle.model_dump(mode="json"),
            geometry=geometry, extracted_at=bundle.extracted_at, is_stub=bundle.is_stub,
            readiness=bundle.readiness.value, warning=bundle.warning))
        self.session.flush()
        return bundle

    def get_latest_for_site(self, site_id: str, as_of: datetime | None = None) -> FeatureBundle | None:
        query = select(SiteFeature).where(SiteFeature.site_id == site_id)
        if as_of:
            # Never serve features materialized after a historical prediction origin.
            query = query.where(SiteFeature.extracted_at <= as_of)
        row = self.session.scalars(query.order_by(SiteFeature.extracted_at.desc()).limit(1)).first()
        return FeatureBundle.model_validate(row.feature_payload) if row else None

    def list_for_site(self, site_id: str) -> list[FeatureBundle]:
        return [FeatureBundle.model_validate(row.feature_payload) for row in self.session.scalars(
            select(SiteFeature).where(SiteFeature.site_id == site_id).order_by(SiteFeature.extracted_at.desc()))]
