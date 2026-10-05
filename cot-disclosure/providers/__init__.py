"""One interface over every model provider used in the project.

    from providers import generate
    reply = generate("voyager", "olmo3-7b-think", messages, max_tokens=16000, temperature=0.6, seed=0)

generate(provider, model, messages, *, tools=None, thinking=None, max_tokens, temperature,
seed, **provider_options) -> Reply. Paid providers (openai, anthropic, xai) pass through the
budget guard first and have their spend recorded after (providers/budget.py).
"""
from importlib import import_module

from . import budget
from .base import Reply  # noqa: F401

ADAPTERS = ("voyager", "ollama", "openai", "anthropic", "xai")


def adapter(provider):
    if provider not in ADAPTERS:
        raise ValueError(f"unknown provider {provider!r}; one of {ADAPTERS}")
    return import_module(f"providers.{provider}")


def generate(provider, model, messages, *, tools=None, thinking=None, max_tokens=4000, temperature=None, seed=None,
             label="", **kw):
    if provider in budget.PAID:
        budget.guard(provider, model, messages, max_tokens)
    reply = adapter(provider).generate(model, messages, tools=tools, thinking=thinking, max_tokens=max_tokens,
                                       temperature=temperature, seed=seed, **kw)
    if provider in budget.PAID and reply.usage:
        reply.cost_usd = budget.record(provider, model, reply.usage, label=label)
    return reply
