"""Create MVP persistence and PostGIS. Extension requires privileged migration role."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "exploration_sites",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("region", sa.String(100)),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("geometry", Geometry("POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("boundary", Geometry("POLYGON", srid=4326, spatial_index=False)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180"),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'UNDER_REVIEW')"),
    )
    op.create_index("ix_exploration_sites_status", "exploration_sites", ["status"])
    op.create_index("idx_exploration_sites_geometry", "exploration_sites", ["geometry"], postgresql_using="gist")
    op.create_index("idx_exploration_sites_boundary", "exploration_sites", ["boundary"], postgresql_using="gist")
    op.create_table(
        "site_features",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(64), sa.ForeignKey("exploration_sites.id")),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("feature_version", sa.String(64), nullable=False),
        sa.Column("feature_payload", JSONB, nullable=False),
        sa.Column("geometry", Geometry("GEOMETRY", srid=4326, spatial_index=False)),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_stub", sa.Boolean, nullable=False),
        sa.Column("readiness", sa.String(32), nullable=False),
        sa.Column("warning", sa.String),
    )
    op.create_index("ix_site_features_site_id", "site_features", ["site_id"])
    op.create_index("idx_site_features_geometry", "site_features", ["geometry"], postgresql_using="gist")
    op.create_table(
        "predictions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(64), sa.ForeignKey("exploration_sites.id")),
        sa.Column("coordinates", JSONB, nullable=False),
        sa.Column("prediction_type", sa.String(64), nullable=False),
        sa.Column("result_payload", JSONB, nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("feature_version", sa.String(64), nullable=False),
        sa.Column("is_stub", sa.Boolean, nullable=False),
        sa.Column("warning", sa.String),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_predictions_site_id", "predictions", ["site_id"])
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("result", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])


def downgrade():
    for table in ("jobs", "predictions", "site_features", "exploration_sites"):
        op.drop_table(table)
    # Keep PostGIS: other applications may use the extension.
