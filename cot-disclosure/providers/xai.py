"""xAI Responses API adapter: same request/response shapes as OpenAI's Responses API
(docs.x.ai, read 2026-10-04); grok-4.7 cannot turn reasoning off, grok-4.3 lists `none`."""
from . import openai as _openai

NAME = "xai"
URL = "https://api.x.ai/v1/responses"
KEY_ENV = "XAI_API_KEY"


def generate(model, messages, **kw):
    return _openai.generate(model, messages, url=URL, provider=NAME, key_env=KEY_ENV, label="xAI", **kw)
