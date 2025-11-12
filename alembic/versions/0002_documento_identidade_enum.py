"""Add DOCUMENTO_IDENTIDADE classification value.

Revision ID: 0002_documento_identidade_enum
Revises: 0001_initial_schema
Create Date: 2025-01-28 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0002_documento_identidade_enum"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_CLASSIFICATION = "DOCUMENTO_IDENTIDADE"

# Values present before introducing DOCUMENTO_IDENTIDADE.
PREVIOUS_CLASSIFICATIONS = (
    "CERTIFICADO_DE_REGULARIDADE",
    "CAEPF",
    "DECLARACAO_DE_RESIDENCIA",
    "CNIS",
    "TERMO_DE_REPRESENTACAO",
    "PROCURACAO",
    "GPS_E_COMPROVANTE",
    "BIOMETRIA",
    "COMPROVANTE_RESIDENCIA",
    "REAP",
    "OUTRO",
)


def upgrade() -> None:
    op.execute(
        f"ALTER TYPE document_classification "
        f"ADD VALUE IF NOT EXISTS '{NEW_CLASSIFICATION}';"
    )


def downgrade() -> None:
    # Ensure no rows keep the value we are about to remove.
    op.execute(
        f"UPDATE documentos "
        f"SET classificacao = 'OUTRO' "
        f"WHERE classificacao = '{NEW_CLASSIFICATION}';"
    )

    previous_values_sql = ", ".join(f"'{value}'" for value in PREVIOUS_CLASSIFICATIONS)

    op.execute(
        "ALTER TYPE document_classification RENAME TO document_classification_old;"
    )
    op.execute(f"CREATE TYPE document_classification AS ENUM ({previous_values_sql});")
    op.execute(
        "ALTER TABLE documentos "
        "ALTER COLUMN classificacao "
        "TYPE document_classification "
        "USING classificacao::text::document_classification;"
    )
    op.execute("DROP TYPE document_classification_old;")
