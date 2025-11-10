from __future__ import annotations
import functools
import json
import os
from typing import List
from functools import lru_cache

import google.genai as genai
from google.genai.types import Part, GenerateContentConfig, ThinkingConfig
from pydantic import ValidationError
from dotenv import load_dotenv
import yaml

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
from src.infra.external.prompts.prompt import Prompt
from src.infra.external.prompts.prompt_classificador import PROMPT_MESTRE


class GeminiIAGateway(IAGateway):
    def __init__(self):
        self.model_name: str = "gemini-2.0-flash"
        self.generation_config: dict | None = {"response_mime_type": "application/json"}
        self._logger = get_logger(__name__)
        self.client = get_gemini_client()
        self._prompts = load_prompts_from_yaml()

    def classify(self, document: ClassificationDocument) -> DocumentClassification:
        try:
            # if document.mimetype == "application/pdf":
            #     reader = PdfReader(BytesIO(document.data))
            #     text = " ".join(page.extract_text() or "" for page in reader.pages)
            #     file_part = Part.from_text(text=text)
            # else:
            #     file_part = Part.from_bytes(
            #         data=document.data, mime_type=document.mimetype
            #     )

            file_part = Part.from_bytes(data=document.data, mime_type=document.mimetype)

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
        document: DocumentMetadata,
        file_bytes: bytes,
    ) -> dict:
        try:
            documentClassification = DocumentClassification[
                document.classification or "OUTRO"
            ]
            descriptor = self._prompts.get(documentClassification.name)
            content = [
                {
                    "role": "user",
                    "parts": [
                        {"text": descriptor.prompt},
                        Part.from_bytes(data=file_bytes, mime_type=document.mimetype),
                    ],
                }
            ]

            result = self._client.models.generate_content(
                model=self._model_name,
                contents=content,
                config=GenerateContentConfig(
                    response_mime_type=descriptor.response_mime_type,
                    response_schema=descriptor.response_schema,
                    system_instruction=descriptor.system_prompt,
                    temperature=0.2,
                    thinking_config=ThinkingConfig(thinking_budget=0),
                ),
            )

            return result.parsed

            # part = (
            #     Part.from_uri(file_uri=file_uri, mime_type=mimetype)
            #     if file_uri
            #     else upload
            # )

            # response = self._client.models.generate_content(
            #     model=self._model_name,
            #     contents=[
            #         {
            #             "role": "user",
            #             "parts": [
            #                 {"text": descriptor_text},
            #                 part,
            #             ],
            #         }
            #     ],
            #     config={"response_mime_type": "application/json"},
            # )

            # json_payload = self._extract_json(response)
            # if not isinstance(json_payload, dict):
            #     raise ValueError(
            #         "Resposta do modelo não está em formato JSON de objeto."
            #     )
            # return json_payload
        except Exception as exc:
            # TODO: remover raise e retornar um Left do either
            raise RuntimeError(
                f"Falha ao extrair dados com o modelo Gemini: {exc}"
            ) from exc

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


@functools.cache
def load_prompts_from_yaml(file_path: str = None) -> dict[str, Prompt]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(base_dir, "..", "..", "..", "..", "ia", "prompts.yml")

    file_path = file_path or default_path

    with open(file_path, "r", encoding="utf-8") as file:
        data: dict = yaml.safe_load(file)

    if not isinstance(data, dict) or "prompts" not in data:
        raise ValueError("Invalid prompt YAML structure.")

    prompts = map(Prompt.from_dict, data.get("prompts", []))
    return {prompt.key: prompt for prompt in prompts}
