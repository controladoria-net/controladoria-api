from __future__ import annotations

from typing import Callable, List
import re
import unicodedata

from src.domain.core.either import Either, Left, Right
from src.domain.core.errors import (
    EligibilityComputationError,
    IncompleteDataError,
    SolicitationNotFoundError,
)
from src.domain.gateway.ia_gateway import IAGateway
from src.domain.repositories.document_extraction_repository import (
    DocumentExtractionRecord,
    IDocumentExtractionRepository,
)
from src.domain.repositories.document_repository import (
    DocumentMetadata,
    IDocumentRepository,
)
from src.domain.repositories.eligibility_repository import (
    EligibilityRecord,
    IEligibilityRepository,
)
from src.domain.repositories.solicitation_repository import ISolicitationRepository
from src.domain.core import metrics


RulesProvider = Callable[[], str]


class EvaluateEligibilityUseCase:
    """Evaluate solicitation eligibility based on extracted document data."""

    def __init__(
        self,
        solicitation_repository: ISolicitationRepository,
        document_repository: IDocumentRepository,
        extraction_repository: IDocumentExtractionRepository,
        eligibility_repository: IEligibilityRepository,
        validator_gateway: IAGateway,
        rules_provider: RulesProvider,
    ) -> None:
        self._solicitation_repository = solicitation_repository
        self._document_repository = document_repository
        self._extraction_repository = extraction_repository
        self._eligibility_repository = eligibility_repository
        self._validator_gateway = validator_gateway
        self._rules_provider = rules_provider

    def execute(self, solicitation_id: str) -> Either[Exception, EligibilityRecord]:
        metrics.increment("eligibility_requests")
        try:
            solicitation = self._solicitation_repository.get_by_id(solicitation_id)
        except SolicitationNotFoundError as exc:
            metrics.increment("eligibility_errors")
            return Left(exc)

        documents = self._document_repository.list_by_solicitation(solicitation_id)
        if not documents:
            metrics.increment("eligibility_errors")
            return Left(
                IncompleteDataError("Nenhum documento encontrado para a solicitação.")
            )

        extractions = self._collect_extractions(documents)
        if not extractions:
            metrics.increment("eligibility_errors")
            return Left(
                IncompleteDataError("Não existem dados extraídos para avaliação.")
            )

        rules_prompt = self._rules_provider()

        try:
            evaluation = self._validator_gateway.evaluate(
                solicitation=solicitation,
                documents=documents,
                extractions=extractions,
                rules_prompt=rules_prompt,
            )
        except Exception as exc:  # pylint: disable=broad-except
            metrics.increment("eligibility_errors")
            return Left(EligibilityComputationError(str(exc)))

        raw_status = evaluation.get("status")
        score_text = evaluation.get("score_texto")
        pendencias = evaluation.get("pendencias", [])

        if raw_status is None or score_text is None:
            metrics.increment("eligibility_errors")
            return Left(
                EligibilityComputationError(
                    "Resposta do avaliador incompleta. 'status' e 'score_texto' são obrigatórios."
                )
            )

        status = self._normalize_status(str(raw_status))
        record = self._eligibility_repository.upsert(
            solicitation_id=solicitation_id,
            status=status,
            score_text=score_text,
            pending_items=pendencias,
        )
        # Map eligibility status (apto/nao_apto) to solicitation workflow statuses
        mapped_status = None
        if status == "apto":
            mapped_status = "aprovada"
        elif status == "nao_apto":
            # If there are pending items, mark as documentation incomplete; else rejected
            mapped_status = "documentacao_incompleta" if pendencias else "reprovada"

        if mapped_status:
            try:
                self._solicitation_repository.update_status(
                    solicitation_id, mapped_status
                )
            except SolicitationNotFoundError:
                # Solicitation must exist because it was previously retrieved; ignore to avoid hiding the main result.
                pass

        metrics.increment("eligibility_processed")
        return Right(record)

    @staticmethod
    def _normalize_status(value: str) -> str:
        """Normalize evaluator output into enum values: 'apto' | 'nao_apto'."""
        nfkd = unicodedata.normalize("NFKD", value)
        ascii_only = nfkd.encode("ASCII", "ignore").decode("ASCII").lower()
        compact = re.sub(r"[^a-z]+", "", ascii_only)
        if compact in {"apto", "eligible", "eligivel"}:
            return "apto"
        if compact in {
            "naoapto",
            "naoelegivel",
            "ineligible",
            "noteligible",
            "reprovado",
        }:
            return "nao_apto"
        if "nao" in compact and "apto" in compact:
            return "nao_apto"
        if "apto" in compact:
            return "apto"
        # default conservative fallback
        return "nao_apto"

    def _collect_extractions(
        self, documents: List[DocumentMetadata]
    ) -> List[DocumentExtractionRecord]:
        records: List[DocumentExtractionRecord] = []
        for metadata in documents:
            record = self._extraction_repository.get_extraction(metadata.document_id)
            if record is None:
                continue
            records.append(record)
        return records
