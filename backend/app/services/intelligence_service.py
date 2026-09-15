import csv
import io
import json
from pathlib import Path
from app.schemas.intelligence import (
    StudyArea,
    ReferenceMine,
    SpectralReference,
)


class IntelligenceService:
    def __init__(self, exploration, features, orchestrator):
        self.exploration = exploration
        self.features = features
        self.orchestrator = orchestrator

    def model_input(self, site_id):
        return self.orchestrator.model_input_for_site(site_id)

    def rankings(self):
        return self.orchestrator.rankings()

    def export(self, site_id, format):
        site = self.exploration.get_site(site_id)
        model_input = self.model_input(site_id)
        document = {
            "site": site.model_dump(mode="json"),
            "model_input": model_input.model_dump(mode="json"),
            "warning": "Exploration candidate only; stub models, no validated manganese conclusions.",
        }
        ranking = next(
            (r for r in self.rankings().locations if r.site_id == site_id), None
        )
        document["ranking"] = ranking.model_dump(mode="json") if ranking else None
        if format == "text":
            return json.dumps(document, indent=2)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["section", "field", "value"])
        for section, fields in document.items():
            if isinstance(fields, dict):
                for key, value in fields.items():
                    cell = (
                        json.dumps(value) if isinstance(value, (dict, list)) else value
                    )
                    if isinstance(cell, str) and cell.lstrip().startswith(
                        ("=", "+", "-", "@")
                    ):
                        cell = "'" + cell
                    writer.writerow([section, key, cell])
            else:
                writer.writerow(["metadata", section, fields])
        return buffer.getvalue()

    @staticmethod
    def study_area():
        return StudyArea(
            mines=[
                ReferenceMine(
                    name="Munsar",
                    latitude=21 + 23 / 60 + 59 / 3600,
                    longitude=79 + 16 / 60 + 51 / 3600,
                    coordinate_method="Published mining-scheme reference point",
                    source_url="https://environmentclearance.nic.in/writereaddata/online/EC/140620161J0QBZKYSchemeofMiningMunsar.pdf",
                ),
                ReferenceMine(
                    name="Kandri",
                    latitude=21 + 24 / 60 + 45 / 3600,
                    longitude=79 + 16 / 60,
                    coordinate_method="Published environmental-clearance reference point",
                    source_url="https://environmentclearance.nic.in/viewminutes.aspx?code=MIN&date1=05%2F15%2F2015",
                ),
                ReferenceMine(
                    name="Chikla",
                    latitude=21 + (31 + 56.45 / 60 + 33 + 3.72 / 60) / 120,
                    longitude=79 + (44 + 30.11 / 60 + 46 + 9.13 / 60) / 120,
                    coordinate_method="Midpoint of published coordinate extent, not lease centroid",
                    source_url="https://environmentclearance.nic.in/writereaddata/Online/TOR/30_Nov_2021_16285060029299741PFRChikla.pdf",
                ),
                ReferenceMine(
                    name="Balaghat / Bharweli",
                    latitude=21 + 50 / 60 + 49.40 / 3600,
                    longitude=80 + 13 / 60 + 40.50 / 3600,
                    coordinate_method="Published boundary reference point, not lease centroid",
                    source_url="https://environmentclearance.nic.in/writereaddata/Form-1A/Minutes/09062017IQEQ38Q4MinutesMergedMayMeeting.pdf",
                ),
            ]
        )

    @staticmethod
    def spectral_reference():
        path = (
            Path(__file__).resolve().parents[1] / "resources" / "pyrolusite_hs138.json"
        )
        if path.exists():
            return SpectralReference(**json.loads(path.read_text()))
        return SpectralReference(
            message="Measured laboratory reference not loaded. No synthetic curve is substituted."
        )
