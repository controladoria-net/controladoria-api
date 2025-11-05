from __future__ import annotations

import json
from typing import List

from src.domain.gateway.eligibility_gateway import IEligibilityValidatorGateway
from src.domain.repositories.document_extraction_repository import (
    DocumentExtractionRecord,
)
from src.domain.repositories.document_repository import DocumentMetadata
from src.domain.repositories.solicitation_repository import SolicitationRecord
from src.infra.external.gateway.gemini_client import get_gemini_client


class GeminiEligibilityGateway(IEligibilityValidatorGateway):
    """Runs eligibility validation using Gemini models and custom rules."""

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        self._client = get_gemini_client()
        self._model_name = model_name

    def evaluate(
        self,
        *,
        solicitation: SolicitationRecord,
        documents: List[DocumentMetadata],
        extractions: List[DocumentExtractionRecord],
        rules_prompt: str,
    ) -> dict:
        payload = {
            "solicitation": self._solicitation_to_dict(solicitation),
            "documents": [self._document_to_dict(doc) for doc in documents],
            "extractions": [
                self._extraction_to_dict(extraction) for extraction in extractions
            ],
        }

        prompt = (
            f"{rules_prompt}\n\n"
            "Avalie os dados a seguir e responda apenas com JSON no formato:\n"
            '{"status": "apto|nao_apto", "score_texto": "string", "pendencias": ["..."]}.\n'
            "Dados:\n"
            f"```json\n{json.dumps(payload, ensure_ascii=False)}\n```"
        )

        response = self._client.models.generate_content(
            model=self._model_name,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config={"response_mime_type": "application/json"},
        )

        text = getattr(response, "text", None)
        if not text and getattr(response, "candidates", None):
            candidate = response.candidates[0]
            content = getattr(candidate, "content", None)
            if content and getattr(content, "parts", None):
                text = content.parts[0].text
        if not text:
            raise ValueError("Resposta vazia do modelo de elegibilidade.")
        return json.loads(text)

    @staticmethod
    def _solicitation_to_dict(record: SolicitationRecord) -> dict:
        return {
            "id": record.solicitation_id,
            "status": record.status,
            "priority": record.priority,
            "fisher_data": record.fisher_data,
            "municipality": record.municipality,
            "state": record.state,
            "analysis": record.analysis,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

    @staticmethod
    def _document_to_dict(metadata: DocumentMetadata) -> dict:
        return {
            "document_id": metadata.document_id,
            "classification": metadata.classification,
            "confidence": metadata.confidence,
            "mimetype": metadata.mimetype,
            "file_name": metadata.file_name,
            "uploaded_at": (
                metadata.uploaded_at.isoformat() if metadata.uploaded_at else None
            ),
        }

    @staticmethod
    def _extraction_to_dict(record: DocumentExtractionRecord) -> dict:
        return {
            "document_id": record.document_id,
            "document_type": record.document_type,
            "payload": record.payload,
        }
