"""Model facts from configs/models.yaml (read 2026-10-04 from the providers' docs)."""
from functools import lru_cache

import yaml

from .base import CODE

MODELS = CODE / "configs" / "models.yaml"


@lru_cache(maxsize=1)
def _load():
    return yaml.safe_load(open(MODELS))


def model_info(model):
    info = _load()["models"].get(model)
    if info is None:
        raise KeyError(f"{model} is not in configs/models.yaml; check the provider's docs and add it there first")
    return info


def resolve_effort(model, thinking, effort=None, default="medium"):
    """Reasoning effort for OpenAI/xAI-style models. thinking=False uses the model's
    documented off value; models that cannot turn reasoning off raise."""
    info = model_info(model)
    if thinking is False:
        if info.get("thinking") != "toggle":
            raise ValueError(f"{model}: reasoning cannot be turned off ({info.get('note', 'see models.yaml')})")
        return info["off_effort"]
    eff = effort or default
    if info.get("efforts") and eff not in info["efforts"]:
        raise ValueError(f"{model}: effort {eff!r} not in {info['efforts']}")
    return eff
