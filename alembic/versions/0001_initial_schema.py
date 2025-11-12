"""Initial schema for legal cases and solicitation workflows

Revision ID: 0001_initial_schema
Revises:
Create Date: 2024-11-05 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


process_priority_enum = postgresql.ENUM(
    "baixa",
    "media",
    "alta",
    name="process_priority",
)

solicitacao_status_enum = postgresql.ENUM(
    "pendente",
    "em_analise",
    "aprovada",
    "reprovada",
    "documentacao_incompleta",
    name="solicitacao_status",
)

solicitacao_priority_enum = postgresql.ENUM(
    "baixa",
    "media",
    "alta",
    name="solicitacao_priority",
)

document_classification_enum = postgresql.ENUM(
    "CERTIFICADO_DE_REGULARIDADE",
    "CAEPF",
    "DECLARACAO_DE_RESIDENCIA",
    "CNIS",
    "TERMO_DE_REPRESENTACAO",
    "PROCURACAO",
    "GPS_E_COMPROVANTE",
    "BIOMETRIA",
    "COMPROVANTE_RESIDENCIA",
    "DOCUMENTO_IDENTIDADE",
    "REAP",
    "OUTRO",
    name="document_classification",
)

eligibility_status_enum = postgresql.ENUM(
    "apto",
    "nao_apto",
    name="eligibility_status",
)


def upgrade() -> None:
    process_priority_enum.create(op.get_bind(), checkfirst=True)
    solicitacao_status_enum.create(op.get_bind(), checkfirst=True)
    solicitacao_priority_enum.create(op.get_bind(), checkfirst=True)
    document_classification_enum.create(op.get_bind(), checkfirst=True)
    eligibility_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "legal_cases",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("numero_processo", sa.String(length=25), nullable=False),
        sa.Column("tribunal", sa.String(length=100), nullable=True),
        sa.Column("orgao_julgador", sa.String(length=150), nullable=True),
        sa.Column("classe_processual", sa.String(length=150), nullable=True),
        sa.Column("assunto", sa.String(length=200), nullable=True),
        sa.Column("situacao", sa.String(length=100), nullable=True),
        sa.Column("data_ajuizamento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("movimentacoes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ultima_movimentacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ultima_movimentacao_descricao", sa.String(length=255), nullable=True
        ),
        sa.Column(
            "prioridade",
            postgresql.ENUM(
                "baixa",
                "media",
                "alta",
                name="process_priority",
                create_type=False,
            ),
            nullable=False,
            server_default="baixa",
        ),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_legal_cases_numero_processo",
        "legal_cases",
        ["numero_processo"],
        unique=True,
    )
    op.create_index(
        "ix_legal_cases_last_synced_at",
        "legal_cases",
        ["last_synced_at"],
        unique=False,
    )

    op.create_table(
        "solicitacoes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pendente",
                "em_analise",
                "aprovada",
                "reprovada",
                "documentacao_incompleta",
                name="solicitacao_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pendente",
        ),
        sa.Column(
            "prioridade",
            postgresql.ENUM(
                "baixa",
                "media",
                "alta",
                name="solicitacao_priority",
                create_type=False,
            ),
            nullable=False,
            server_default="baixa",
        ),
        sa.Column("pescador", sa.JSON(), nullable=True),
        sa.Column("municipio", sa.String(length=120), nullable=True),
        sa.Column("estado", sa.String(length=2), nullable=True),
        sa.Column("analysis", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "legal_case_movements",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "legal_case_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("legal_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("movement_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_legal_case_movements_movement_date",
        "legal_case_movements",
        ["movement_date"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_legal_case_movement",
        "legal_case_movements",
        ["legal_case_id", "movement_date", "description"],
    )

    op.create_table(
        "documentos",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "solicitacao_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("solicitacoes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome_arquivo", sa.String(length=255), nullable=False),
        sa.Column("mimetype", sa.String(length=100), nullable=False),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("uploaded_by", sa.String(length=100), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "classificacao",
            postgresql.ENUM(
                "CERTIFICADO_DE_REGULARIDADE",
                "CAEPF",
                "DECLARACAO_DE_RESIDENCIA",
                "CNIS",
                "TERMO_DE_REPRESENTACAO",
                "PROCURACAO",
                "GPS_E_COMPROVANTE",
                "BIOMETRIA",
                "CIN",
                "CPF",
                "REAP",
                "OUTRO",
                name="document_classification",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_documentos_solicitacao_id",
        "documentos",
        ["solicitacao_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_documentos_s3_key",
        "documentos",
        ["s3_key"],
    )

    op.create_table(
        "document_extractions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "documento_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documentos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("extracted_payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_document_extractions_documento_id",
        "document_extractions",
        ["documento_id"],
    )

    op.create_table(
        "eligibility_results",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "solicitacao_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("solicitacoes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "apto",
                "nao_apto",
                name="eligibility_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("score_texto", sa.String(length=20), nullable=False),
        sa.Column("pendencias", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_eligibility_results_solicitacao_id",
        "eligibility_results",
        ["solicitacao_id"],
    )

    op.create_table(
        "scheduler_locks",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lock_name", sa.String(length=128), nullable=False, unique=True),
        sa.Column(
            "acquired_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("scheduler_locks")

    op.drop_constraint(
        "uq_eligibility_results_solicitacao_id", "eligibility_results", type_="unique"
    )
    op.drop_table("eligibility_results")

    op.drop_constraint(
        "uq_document_extractions_documento_id", "document_extractions", type_="unique"
    )
    op.drop_table("document_extractions")

    op.drop_constraint("uq_documentos_s3_key", "documentos", type_="unique")
    op.drop_index("ix_documentos_solicitacao_id", table_name="documentos")
    op.drop_table("documentos")

    op.drop_constraint("uq_legal_case_movement", "legal_case_movements", type_="unique")
    op.drop_index(
        "ix_legal_case_movements_movement_date", table_name="legal_case_movements"
    )
    op.drop_table("legal_case_movements")

    op.drop_table("solicitacoes")

    op.drop_index("ix_legal_cases_last_synced_at", table_name="legal_cases")
    op.drop_index("ix_legal_cases_numero_processo", table_name="legal_cases")
    op.drop_table("legal_cases")

    eligibility_status_enum.drop(op.get_bind(), checkfirst=True)
    document_classification_enum.drop(op.get_bind(), checkfirst=True)
    solicitacao_priority_enum.drop(op.get_bind(), checkfirst=True)
    solicitacao_status_enum.drop(op.get_bind(), checkfirst=True)
    process_priority_enum.drop(op.get_bind(), checkfirst=True)
