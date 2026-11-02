"""Add sync package status and path columns.

Revision ID: 20260926_pkg_status
Revises:
Create Date: 2026-09-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260926_pkg_status"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pi_sync_packages",
        sa.Column("package_path", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "pi_sync_packages",
        sa.Column(
            "status",
            sa.Enum("pending", "ready", "expired", "failed", name="packagestatus"),
            nullable=False,
            server_default="pending",
        ),
    )
    op.create_index(
        "ix_pi_sync_packages_status", "pi_sync_packages", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_pi_sync_packages_status", table_name="pi_sync_packages")
    op.drop_column("pi_sync_packages", "status")
    op.drop_column("pi_sync_packages", "package_path")
    sa.Enum(name="packagestatus").drop(op.get_bind(), checkfirst=True)
