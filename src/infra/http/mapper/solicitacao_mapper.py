from datetime import datetime, timezone
from typing import Dict, List

from src.domain.entities.documento import ResultadoClassificacao
from src.domain.repositories.document_repository import DocumentMetadata
from src.domain.repositories.document_extraction_repository import (
    DocumentExtractionRecord,
)
from src.domain.repositories.eligibility_repository import EligibilityRecord
from src.domain.repositories.solicitation_repository import (
    SolicitationDashboardAggregation,
)
from src.infra.http.dto.solicitacao_dto import (
    ClassificationGroupDTO,
    ClassificationResponseDTO,
    ClassificationResultDTO,
    EligibilityResponseDTO,
    ExtractionItemDTO,
    ExtractionResponseDTO,
    SolicitationDashboardDTO,
)


class SolicitacaoMapper:
    """Mappings for solicitation-related flows."""

    @staticmethod
    def classification_response(
        solicitation_id: str,
        grouped: Dict[str, List[ResultadoClassificacao]],
        documents: Dict[str, DocumentMetadata],
    ) -> ClassificationResponseDTO:
        groups: List[ClassificationGroupDTO] = []
        for categoria, results in grouped.items():
            itens = []
            for result in results:
                metadata = documents.get(result.arquivo)
                document_id = metadata.document_id if metadata else ""
                itens.append(
                    ClassificationResultDTO(
                        document_id=document_id,
                        categoria=result.classificacao.value,
                        confianca=result.confianca,
                        arquivo=result.arquivo,
                        mimetype=result.mimetype,
                    )
                )
            groups.append(ClassificationGroupDTO(categoria=categoria, documentos=itens))
        return ClassificationResponseDTO(solicitation_id=solicitation_id, groups=groups)

    @staticmethod
    def extraction_response(
        solicitation_id: str,
        records: List[DocumentExtractionRecord],
    ) -> ExtractionResponseDTO:
        items = [
            ExtractionItemDTO(
                document_id=record.document_id,
                document_type=record.document_type,
                extracted=record.payload,
            )
            for record in records
        ]
        return ExtractionResponseDTO(solicitation_id=solicitation_id, items=items)

    @staticmethod
    def eligibility_response(record: EligibilityRecord) -> EligibilityResponseDTO:
        return EligibilityResponseDTO(
            solicitation_id=record.solicitation_id,
            status=record.status,
            score_texto=record.score_text,
            pendencias=record.pending_items,
            evaluated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def dashboard_to_dto(
        aggregation: SolicitationDashboardAggregation,
    ) -> SolicitationDashboardDTO:
        data = aggregation.data
        return SolicitationDashboardDTO(
            status_count=data.get("status_count", {}),
            by_period=data.get("by_period", []),
            period_granularity=str(data.get("period_granularity", "monthly")),
            avg_processing_time_days=float(data.get("avg_processing_time_days", 0.0)),
            approval_rate=float(data.get("approval_rate", 0.0)),
            most_missing_documents=data.get("most_missing_documents", []),
        )
