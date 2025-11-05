from __future__ import annotations

import json
import os
import tempfile
from typing import Optional

from google.genai import types

from src.domain.gateway.document_extraction_gateway import IDocumentExtractionGateway
from src.infra.external.gateway.gemini_client import get_gemini_client


class GeminiExtractionGateway(IDocumentExtractionGateway):
    """Gemini-based implementation for document data extraction."""

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        self._client = get_gemini_client()
        self._model_name = model_name

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
                types.Part.from_uri(file_uri=file_uri, mime_type=mimetype)
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
