from datetime import datetime, timezone
from uuid import UUID as UUIDType, uuid4
from typing import List, Optional
import random

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.categorias import CategoriaDocumento
from src.infra.database.base import Base


def generate_uuid7() -> UUIDType:
    """Generate a UUID version 7 compatible value for databases lacking native support."""
    # milliseconds since epoch fits in 48 bits
    unix_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    rand_a = random.getrandbits(12)  # 12-bit random
    rand_b = random.getrandbits(62)  # 62-bit random

    value = unix_ms << 80
    value |= 0x7 << 76  # version 7 in bits 48..51
    value |= rand_a << 64
    value |= 0b10 << 62  # RFC 4122 variant
    value |= rand_b
    return UUIDType(int=value)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class LegalCaseModel(Base, TimestampMixin):
    __tablename__ = "legal_cases"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    numero_processo: Mapped[str] = mapped_column(
        String(25), unique=True, nullable=False, index=True
    )
    tribunal: Mapped[Optional[str]] = mapped_column(String(100))
    orgao_julgador: Mapped[Optional[str]] = mapped_column(String(150))
    classe_processual: Mapped[Optional[str]] = mapped_column(String(150))
    assunto: Mapped[Optional[str]] = mapped_column(String(200))
    situacao: Mapped[Optional[str]] = mapped_column(String(100))
    data_ajuizamento: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    movimentacoes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ultima_movimentacao: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    ultima_movimentacao_descricao: Mapped[Optional[str]] = mapped_column(String(255))
    prioridade: Mapped[str] = mapped_column(
        Enum("baixa", "media", "alta", name="process_priority"),
        default="baixa",
        nullable=False,
    )
    status: Mapped[Optional[str]] = mapped_column(String(50))
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )

    movements: Mapped[List["LegalCaseMovementModel"]] = relationship(
        back_populates="legal_case",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LegalCaseMovementModel(Base):
    __tablename__ = "legal_case_movements"
    __table_args__ = (
        UniqueConstraint(
            "legal_case_id",
            "movement_date",
            "description",
            name="uq_legal_case_movement",
        ),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    legal_case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    movement_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    legal_case: Mapped[LegalCaseModel] = relationship(back_populates="movements")


class SolicitationModel(Base, TimestampMixin):
    __tablename__ = "solicitacoes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(
        Enum(
            "pendente",
            "em_analise",
            "aprovada",
            "reprovada",
            "documentacao_incompleta",
            name="solicitacao_status",
        ),
        default="pendente",
        nullable=False,
    )
    prioridade: Mapped[str] = mapped_column(
        Enum("baixa", "media", "alta", name="solicitacao_priority"),
        default="baixa",
        nullable=False,
    )
    pescador: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    municipio: Mapped[Optional[str]] = mapped_column(String(120))
    estado: Mapped[Optional[str]] = mapped_column(String(2))
    analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    documentos: Mapped[List["DocumentModel"]] = relationship(
        back_populates="solicitacao",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    eligibility_result: Mapped[Optional["EligibilityResultModel"]] = relationship(
        back_populates="solicitacao",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DocumentModel(Base, TimestampMixin):
    __tablename__ = "documentos"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid7,
    )
    solicitacao_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    mimetype: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    uploaded_by: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    classificacao: Mapped[Optional[str]] = mapped_column(
        Enum(
            *[member.value for member in CategoriaDocumento],
            name="document_classification",
        ),
        nullable=True,
    )
    confianca: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50))

    solicitacao: Mapped[SolicitationModel] = relationship(back_populates="documentos")
    extracao: Mapped[Optional["DocumentExtractionModel"]] = relationship(
        back_populates="documento",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DocumentExtractionModel(Base):
    __tablename__ = "document_extractions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    documento_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documentos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    documento: Mapped[DocumentModel] = relationship(back_populates="extracao")


class EligibilityResultModel(Base):
    __tablename__ = "eligibility_results"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    solicitacao_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("solicitacoes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        Enum("apto", "nao_apto", name="eligibility_status"),
        nullable=False,
    )
    score_texto: Mapped[str] = mapped_column(String(20), nullable=False)
    pendencias: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    solicitacao: Mapped[SolicitationModel] = relationship(
        back_populates="eligibility_result"
    )


class SchedulerLockModel(Base):
    __tablename__ = "scheduler_locks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lock_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
