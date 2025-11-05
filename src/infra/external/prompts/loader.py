from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict


EXTRACTOR_FILE = Path("ia/extrator.txt")
VALIDATOR_FILE = Path("ia/validador.txt")


@lru_cache(maxsize=1)
def load_extraction_descriptors() -> Dict[str, str]:
    namespace: Dict[str, object] = {}
    exec(EXTRACTOR_FILE.read_text(), namespace)  # pylint: disable=exec-used
    descriptor_class = namespace.get("Descriptor")
    if descriptor_class is None:
        raise RuntimeError("Arquivo de descritores não define a classe 'Descriptor'.")

    descriptors: Dict[str, str] = {}
    # 1) Coleta pelos nomes de variáveis e siglas
    for key, value in namespace.items():
        if isinstance(value, descriptor_class):  # type: ignore[arg-type]
            instruction = getattr(value, "system_instruction", None) or getattr(
                value, "instruction", ""
            )
            descriptors[key.upper()] = instruction
            sigla = getattr(value, "sigla", None)
            if sigla:
                descriptors[str(sigla).upper()] = instruction

    # 2) Coleta aliases declarados como dicionários no arquivo (ex.: "CADASTRO_NACIONAL_...": CNIS)
    for _, obj in namespace.items():
        if isinstance(obj, dict):
            for alias_key, alias_value in obj.items():
                if isinstance(alias_value, descriptor_class):  # type: ignore[arg-type]
                    instruction = getattr(
                        alias_value, "system_instruction", None
                    ) or getattr(alias_value, "instruction", "")
                    descriptors[str(alias_key).upper()] = instruction

    return descriptors


@lru_cache(maxsize=1)
def load_validator_rules() -> str:
    return VALIDATOR_FILE.read_text()
