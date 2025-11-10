from datetime import datetime, timezone
from typing import Dict, List

from src.domain.entities.document import DocumentClassification
from src.domain.entities.solicitation import SolicitationDetails, SolicitationDocument
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
    DocumentDTO,
    ClassificationResponseDTO,
    ClassificationResultDTO,
    EligibilityResponseDTO,
    ExtractionItemDTO,
    ExtractionResponseDTO,
    SolicitationDashboardDTO,
    SolicitacaoDTO,
)


class SolicitacaoMapper:
    """Mappings for solicitation-related flows."""

    @staticmethod
    def classification_response(
        solicitation_id: str,
        grouped: Dict[str, List[DocumentClassification]],
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

    @staticmethod
    def solicitation_to_dto(details: SolicitationDetails) -> SolicitacaoDTO:
        documents = [
            SolicitacaoMapper._document_to_dto(doc) for doc in details.documents
        ]
        return SolicitacaoDTO(
            id=details.id,
            pescador=details.pescador,
            status=details.status,
            documents=documents,
            analysis=details.analysis,
            createdAt=details.created_at,
            updatedAt=details.updated_at,
            lawyerNotes=details.lawyer_notes,
            priority=details.priority,
        )

    @staticmethod
    def _document_to_dto(document: SolicitationDocument) -> DocumentDTO:
        return DocumentDTO(
            id=document.id,
            fileName=document.file_name,
            mimetype=document.mimetype,
            classification=document.classification,
            confidence=document.confidence,
            uploadedAt=document.uploaded_at,
        )
