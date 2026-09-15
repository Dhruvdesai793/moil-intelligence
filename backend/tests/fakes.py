from app.schemas.exploration import Site


class FakeExplorationRepository:
    def list_sites(self):
        return [
            Site(id="zone_a", name="Demo A", status="ACTIVE", latitude=21.123, longitude=79.123),
            Site(id="zone_b", name="Demo B", status="INACTIVE", latitude=21.456, longitude=79.456),
            Site(id="zone_c", name="Demo C", status="ACTIVE", latitude=21.3, longitude=79.3),
        ]

    def get(self, site_id):
        return next((site for site in self.list_sites() if site.id == site_id), None)


class FakeRecords:
    def __init__(self):
        self.records = {}

    def save(self, record):
        key = getattr(record, "prediction_id", None) or getattr(record, "job_id", None)
        self.records[key] = record.model_copy(deep=True)
        return record

    def get(self, key):
        return self.records.get(key)


class FakeFeatures:
    def __init__(self):
        self.records = []

    def save_feature_bundle(self, bundle):
        self.records.append(bundle)
        return bundle

    def get_latest_for_site(self, site_id, as_of=None):
        records = [r for r in self.records if r.site_id == site_id and
                   (as_of is None or r.extracted_at <= as_of)]
        return records[-1] if records else None

    def list_for_site(self, site_id):
        return [r for r in self.records if r.site_id == site_id]
