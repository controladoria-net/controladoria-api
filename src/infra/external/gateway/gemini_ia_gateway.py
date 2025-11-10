from __future__ import annotations
from io import BytesIO
import json
import os
import tempfile
from typing import List
from functools import lru_cache

import google.genai as genai
from google.genai.types import Part
from pydantic import ValidationError
from dotenv import load_dotenv
from PyPDF2 import PdfReader

from src.domain.core.logger import get_logger
from src.domain.gateway.ia_gateway import IAGateway
from src.domain.entities.document import (
    ClassificationDocument,
    DocumentClassification,
    DocumentMetadata,
)
from src.domain.repositories.document_extraction_repository import (
    DocumentExtractionRecord,
)
from src.domain.repositories.solicitation_repository import SolicitationRecord
from src.infra.external.prompts.prompt_classificador import PROMPT_MESTRE


class GeminiIAGateway(IAGateway):

    def __init__(self):
        self.model_name: str = "gemini-2.0-flash"
        self.generation_config: dict | None = {"response_mime_type": "application/json"}
        self._logger = get_logger(__name__)
        self.client = get_gemini_client()

    def classificar(self, document: ClassificationDocument) -> DocumentClassification:
        try:
            if document.mimetype == "application/pdf":
                reader = PdfReader(BytesIO(document.data))
                text = " ".join(page.extract_text() or "" for page in reader.pages)
                file_part = Part.from_text(text=text)
            else:
                file_part = Part.from_bytes(
                    data=document.data, mime_type=document.mimetype
                )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[PROMPT_MESTRE, file_part],
                config=self.generation_config,
            )

            text = getattr(response, "text", None)

            try:
                response_json = json.loads(text)
            except json.JSONDecodeError:
                s, e = text.find("{"), text.rfind("}")
                if s != -1 and e != -1 and e > s:
                    response_json = json.loads(text[s : e + 1])
                else:
                    raise

            result = DocumentClassification[response_json["classification"]]
            return result

        except (json.JSONDecodeError, ValidationError) as e:
            self._logger.warning(
                "Resposta inválida do modelo (JSON/Schema): %s", e, exc_info=True
            )
            return DocumentClassification.OUTRO

    # Extract
    def extract(
        self,
        *,
        document_type: str,
        document_name: str,
        mimetype: str,
        file_bytes: bytes,
        descriptor: str,
    ) -> dict:
        descriptor_text = self._compose_prompt(document_type, descriptor)
        temp_file_path = self._write_temp_file(document_name, file_bytes)
        try:
            upload = self._client.files.upload(
                file=temp_file_path,
                config={
                    "mime_type": mimetype or "application/octet-stream",
                    "display_name": document_name,
                },
            )

            file_uri = getattr(upload, "uri", None) or getattr(upload, "name", None)
            part = (
                Part.from_uri(file_uri=file_uri, mime_type=mimetype)
                if file_uri
                else upload
            )

            response = self._client.models.generate_content(
                model=self._model_name,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": descriptor_text},
                            part,
                        ],
                    }
                ],
                config={"response_mime_type": "application/json"},
            )

            json_payload = self._extract_json(response)
            if not isinstance(json_payload, dict):
                raise ValueError(
                    "Resposta do modelo não está em formato JSON de objeto."
                )
            return json_payload
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @staticmethod
    def _compose_prompt(document_type: str, descriptor: str) -> str:
        header = (
            "Você é uma IA especializada em extração de dados para análise jurídica. "
            "Retorne SEMPRE um JSON válido. Documento classificado como: "
        )
        return f"{header}{document_type}.\n\n{descriptor}"

    @staticmethod
    def _write_temp_file(document_name: str, file_bytes: bytes) -> str:
        suffix = os.path.splitext(document_name)[1] if "." in document_name else ""
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            temp.write(file_bytes)
            temp.flush()
        finally:
            temp.close()
        return temp.name

    @staticmethod
    def _extract_json(response) -> dict:
        text = getattr(response, "text", None)
        if not text and getattr(response, "candidates", None):
            candidate = response.candidates[0]
            content = getattr(candidate, "content", None)
            if content and getattr(content, "parts", None):
                text = content.parts[0].text
        if not text:
            raise ValueError("Resposta vazia do modelo Gemini.")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Falha ao interpretar JSON retornado pelo modelo."
            ) from exc

    # End Extract

    # Evaluate
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

    # End Evaluate


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not defined.")
    return genai.Client(api_key=api_key)
