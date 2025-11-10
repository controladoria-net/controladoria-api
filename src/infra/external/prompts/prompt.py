from dataclasses import dataclass
from textwrap import dedent
from string import Template

from src.infra.external.prompts.constants import PROMPT_COMMON_ENV_VARS


@dataclass
class Prompt:
    key: str
    description: str | None
    system_prompt: str | None
    prompt: str
    response_schema: str
    response_mime_type: str = "application/json"

    @classmethod
    def from_dict(cls, data: dict) -> "Prompt":
        return cls(
            key=data["key"],
            description=data.get("description"),
            system_prompt=data.get("system_prompt"),
            prompt=data["prompt"],
            response_schema=data["response_schema"],
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
