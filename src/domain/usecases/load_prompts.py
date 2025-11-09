from domain.entities.prompt import Prompt
import functools
import yaml

@functools.cache
def load_prompts_from_yaml(file_path: str) -> dict[str, Prompt]:
    with open(file_path, "r", encoding="utf-8") as file:
        data: dict = yaml.safe_load(file)

    if not isinstance(data, dict) or "prompts" not in data:
        raise ValueError("Invalid prompt YAML structure.")

    prompts = map(Prompt.from_dict, data.get("prompts", []))
    return {prompt.key: prompt for prompt in prompts}