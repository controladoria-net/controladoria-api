from __future__ import annotations
import functools
import json
import os
from typing import Callable, List, TypeVar
from functools import lru_cache

import google.genai as genai
from google.api_core import exceptions as google_exceptions
from google.genai.types import Part, GenerateContentConfig, ThinkingConfig
import requests
from pydantic import ValidationError
from dotenv import load_dotenv
import yaml
from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

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
from src.domain.core import metrics
from src.domain.core.concurrency import configure_ia_semaphore, ia_slot
from src.infra.external.prompts.prompt import Prompt
from src.infra.config.settings import (
    get_concurrency_settings,
    get_retry_settings,
)


T = TypeVar("T")


class GeminiIAGateway(IAGateway):
    def __init__(self):
        self._model_name: str = "gemini-2.0-flash"
        self._logger = get_logger(__name__)
        self._client = get_gemini_client()
        self._prompts = load_prompts_from_yaml()
        self._concurrency_settings = get_concurrency_settings()
        self._retry_settings = get_retry_settings()
        configure_ia_semaphore(self._concurrency_settings.ia_max_in_flight)
        self._retryable_exceptions = (
            TimeoutError,
            ConnectionError,
            requests.RequestException,
            google_exceptions.GoogleAPIError,
            google_exceptions.RetryError,
        )

    def classify(self, document: ClassificationDocument) -> DocumentClassification:
        try:
            descriptor = self._prompts.get("DOCUMENT_CLASSIFIER")

            def _call_model():
                content = [
                    {
                        "role": "user",
                        "parts": [
                            {"text": descriptor.prompt},
                            Part.from_bytes(
                                data=document.data, mime_type=document.mimetype
                            ),
                        ],
                    }
                ]
                with ia_slot():
                    return self._client.models.generate_content(
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

            result = self._run_with_retry("retries_classify", _call_model)
            classification = result.parsed.classification

            return classification
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
            # TODO: ajustar para quando recebe "Outro"
            document_classification = DocumentClassification[
                document.classification or "OUTRO"
            ]
            descriptor = self._prompts.get(document_classification.name)

            def _call_model():
                content = [
                    {
                        "role": "user",
                        "parts": [
                            {"text": descriptor.prompt},
                            Part.from_bytes(
                                data=file_bytes, mime_type=document.mimetype
                            ),
                        ],
                    }
                ]
                with ia_slot():
                    return self._client.models.generate_content(
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

            result = self._run_with_retry("retries_extract", _call_model)

            return result.parsed
        except Exception as exc:
            # TODO: remover raise e retornar um Left do either
            raise RuntimeError(
                f"Falha ao extrair dados com o modelo Gemini para o documento {document.classification}: {exc}"
            ) from exc

    def _run_with_retry(self, metric_name: str, func: Callable[[], T]) -> T:
        retry = Retrying(
            reraise=True,
            stop=stop_after_attempt(self._retry_settings.max_attempts),
            wait=wait_random_exponential(
                multiplier=max(self._retry_settings.wait_initial, 0.1),
                max=self._retry_settings.wait_max,
            ),
            retry=retry_if_exception_type(self._retryable_exceptions),
            before_sleep=self._before_sleep(metric_name),
        )
        for attempt in retry:
            with attempt:
                return func()
        raise RuntimeError("Retry loop exited unexpectedly.")

    def _before_sleep(self, metric_name: str) -> Callable[[RetryCallState], None]:
        def _handler(retry_state: RetryCallState) -> None:
            metrics.increment(metric_name)
            exc = retry_state.outcome.exception() if retry_state.outcome else None
            self._logger.warning(
                "IA call retry (%s) attempt %s/%s due to %s",
                metric_name,
                retry_state.attempt_number,
                self._retry_settings.max_attempts,
                exc,
            )

        return _handler

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
