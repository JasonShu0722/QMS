"""fix allowed_environments column

Revision ID: 6f3b2d4c1a9e
Revises: 0255a0347193
Create Date: 2026-03-30 10:30:00+08:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "6f3b2d4c1a9e"
down_revision = "0255a0347193"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}

    if "allowed_environments" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "allowed_environments",
                sa.String(length=50),
                nullable=False,
                server_default="stable",
                comment="允许访问的环境，逗号分隔",
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}

    if "allowed_environments" in columns:
        op.drop_column("users", "allowed_environments")
