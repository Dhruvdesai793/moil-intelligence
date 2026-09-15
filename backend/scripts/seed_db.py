"""Idempotent software fixtures. No validated geological or MOIL data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geoalchemy2.elements import WKTElement
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.models.exploration import ExplorationSite

SITES = [
    ("exp_001", "Nagpur North Demo", "Maharashtra", "ACTIVE", 21.1458, 79.0882),
    ("exp_002", "Bhandara East Demo", "Maharashtra", "ACTIVE", 21.1680, 79.6500),
    ("exp_003", "Balaghat Belt Demo", "Madhya Pradesh", "UNDER_REVIEW", 21.8129, 80.1838),
    ("exp_004", "Dongri Buzurg Demo", "Maharashtra", "INACTIVE", 21.4000, 79.7000),
]


def seed():
    with Session(get_engine()) as session, session.begin():
        for site_id, name, region, status, latitude, longitude in SITES:
            statement = insert(ExplorationSite).values(
                id=site_id, name=name, region=region, status=status, latitude=latitude,
                longitude=longitude, geometry=WKTElement(f"POINT({longitude} {latitude})", srid=4326))
            # Preserve locally edited fixtures on rerun.
            session.execute(statement.on_conflict_do_nothing(index_elements=["id"]))
    print("Demo fixtures seeded (existing IDs preserved).")


if __name__ == "__main__":
    seed()
