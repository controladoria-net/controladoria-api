"""Ensure document_classification enum includes every known value.

Revision ID: 0003_sync_doc_class_enum
Revises: 0002_documento_identidade_enum
Create Date: 2025-11-10 22:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

from src.domain.entities.document import DocumentClassification


revision: str = "0003_sync_doc_class_enum"
down_revision: Union[str, None] = "0002_documento_identidade_enum"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for classification in DocumentClassification:
        op.execute(
            "ALTER TYPE document_classification "
            f"ADD VALUE IF NOT EXISTS '{classification.value}';"
        )


def downgrade() -> None:
    # Removing enum values safely would require rewriting the type; skip for now.
    pass
