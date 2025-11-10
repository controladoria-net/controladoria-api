from dataclasses import dataclass
from textwrap import dedent
from string import Template
from google.genai.types import Schema

from src.infra.external.prompts.constants import (
    DOCUMENT_METADATA_SCHEMA_REGISTRY,
    PROMPT_COMMON_ENV_VARS,
)


@dataclass
class Prompt:
    key: str
    description: str | None
    system_prompt: str | None
    prompt: str
    response_schema: Schema
    response_mime_type: str = "application/json"

    @classmethod
    def from_dict(cls, data: dict) -> "Prompt":
        schema = DOCUMENT_METADATA_SCHEMA_REGISTRY.get(data["response_schema"])  # type: ignore[index]
        if not schema:
            raise ValueError(
                f"Schema não encontrado para a chave: {data.get('response_schema')}"
            )
        return cls(
            key=data["key"],
            description=data.get("description"),
            system_prompt=data.get("system_prompt"),
            prompt=data["prompt"],
            response_schema=schema,
            response_mime_type=data.get("response_mime_type", "application/json"),
        )

    def __post_init__(self):
        if not self.prompt:
            raise ValueError("Prompt text cannot be empty.")
        if not self.response_schema:
            raise ValueError("Response schema cannot be empty.")
        if not self.key:
            raise ValueError("Prompt key cannot be empty.")
        self.prompt = self._substitute_template_vars(self.prompt)
        self.system_prompt = self._substitute_template_vars(self.system_prompt)

    def _substitute_template_vars(self, text: str) -> str:
        if isinstance(text, str):
            return Template(text).safe_substitute(PROMPT_COMMON_ENV_VARS)
        return text

    def build_full_prompt(self) -> str:
        if self.system_prompt:
            return dedent(f"{self.system_prompt}\n\n{self.prompt}")
        return dedent(self.prompt)
