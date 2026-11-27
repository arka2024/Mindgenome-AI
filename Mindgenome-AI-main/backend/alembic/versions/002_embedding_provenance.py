"""Add embedding provenance to document chunks.

Revision ID: 002_embedding_provenance
Revises: 001_initial
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_embedding_provenance"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chunks", sa.Column("embedding_model", sa.String(length=255), nullable=True))
    op.add_column("chunks", sa.Column("embedding_version", sa.String(length=100), nullable=True))
    op.add_column("chunks", sa.Column("embedding_dimension", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("chunks", "embedding_dimension")
    op.drop_column("chunks", "embedding_version")
    op.drop_column("chunks", "embedding_model")
