# providers/

One interface over the places a model can run.

- `base.py`: the interface every provider follows.
- `voyager.py`: ASU Voyager, the hosted API most Track B and Track C runs used.
- `sol_vllm.py`, `sol_hf.py`, `sol_chat.py`: our own models on Sol (vLLM or Hugging Face).
- `ollama.py`, `openai.py`, `anthropic.py`, `xai.py`, `responses_api.py`: other providers. The project made no paid
  calls, so these were not used for results.
- `config.py` reads `../configs/models.yaml`; `budget.py` caps spend.

Open `base.py`, then `voyager.py`. Keys come from your own `.env` ([`../../REPRODUCE.md`](../../REPRODUCE.md)).
