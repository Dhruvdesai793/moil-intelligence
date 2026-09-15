"""Separate user exploration locations from demo fixtures."""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "exploration_sites",
        sa.Column(
            "origin", sa.String(32), nullable=False, server_default="demo_fixture"
        ),
    )
    op.add_column("exploration_sites", sa.Column("notes", sa.String(2000)))


def downgrade():
    op.drop_column("exploration_sites", "notes")
    op.drop_column("exploration_sites", "origin")
