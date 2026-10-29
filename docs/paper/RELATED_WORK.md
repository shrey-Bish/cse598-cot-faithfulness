# Related work (verified references only)

Each entry was checked against its arXiv, proceedings or publisher page on 2026-10-29. The link given
is the one checked. "Differs" says precisely what our work does that the paper doesn't, or the
reverse. Our methods, for comparison:
- **Localization:** activation patching on Olmo 3 7B Think finds the hint's letter read straight from
  the prompt at full-attention layers 15, 19 and 23 (FINDINGS F11–F13).
- **B1** (inference time, no training): scale the attention from every query to the tool span's keys
  in those layers (or their top heads) by alpha, i.e. add log(alpha) to the logits. The deployable
  version acts on tool-role spans, which a system can identify; the oracle version also on a pasted
  block.
- **B2** (trained): a learned per-head scalar bias on tool-tagged keys in those layers,
  zero-initialized, alone or with LoRA on their attention.
- **Input-embedding source tags** (ours, trained): a learned vector per source added to every
  token's embedding. In loss they did nothing measurable on the taught tokens, and nothing more on
  the inserted tool turn (F20).

## 1. Chain-of-thought faithfulness under hints

- **Turpin, Michael, Perez, Bowman (2023).** "Language Models Don't Always Say What They Think:
  Unfaithful Explanations in Chain-of-Thought Prompting." NeurIPS 2023. arXiv:2305.04388.
  https://arxiv.org/abs/2305.04388
  - Did: biasing features in the prompt (e.g. answers always "(A)", a user's suggested answer)
    shift GPT-3.5's and Claude 1.0's answers, and the explanations rarely mention them.
  - Differs: our hint arrives through a tool (pasted block, inserted tool turn, real tool call) as
    well as from the user. We separate the private reasoning from the final answer (thinking
    models), and we locate where in the network the hint is read (F11).
- **Lanham et al. (2023).** "Measuring Faithfulness in Chain-of-Thought Reasoning." arXiv:2307.13702.
  https://arxiv.org/abs/2307.13702
  - Did: intervenes on the CoT (early answering, adding mistakes, paraphrasing, filler tokens) to
    see how much answers depend on it.
  - Differs: we use early answering as a probe of *when* the hinted answer takes over (F4, F5), not
    as a faithfulness score, and pair it with deletion of the hint's mentions (F7) and patching.
- **Chen et al. (2025).** "Reasoning Models Don't Always Say What They Think." arXiv:2505.05410.
  https://arxiv.org/abs/2505.05410 (first author Yanda Chen)
  - Did: pairs questions with and without one of six hint types and asks whether reasoning models'
    CoT mentions a hint they used.
  - Differs: our hint sources include tools and real tool calls. We report the private vs final
    split, which their setup doesn't separate in the same way. We add a mechanistic account and a
    targeted fix.
- **Chua, Evans (2025).** "Are DeepSeek R1 And Other Reasoning Models More Faithful?" arXiv:2501.08156
  (ICLR 2025 workshop FM-Wild). https://arxiv.org/abs/2501.08156
  - Did: reasoning models describe a cue that changed their MMLU answer far more often than
    non-reasoning models (e.g. DeepSeek-R1 59% vs DeepSeek-V3 7%).
  - Differs: we find the mention is in the private reasoning (F3), while the final answer, which
    is what a user or reviewer sees, almost never carries it. After a tool call the final answer
    is a bare letter (F15).

## 2. Localization: activation patching and causal tracing

- **Meng, Bau, Andonian, Belinkov (2022).** "Locating and Editing Factual Associations in GPT."
  NeurIPS 2022. arXiv:2202.05262. https://arxiv.org/abs/2202.05262
  - Did: causal tracing (restore clean activations into a corrupted run) localizes factual recall
    to mid-layer MLPs at the subject's tokens, then edits them (ROME).
  - Differs: we restore at the *hint's* tokens, the reasoning or the answer position, layer by
    layer, at the takeover. The readout is attention in three full-attention layers (F11), not
    MLPs. Our repair targets attention to a provenance span, not a weight edit.
- **Wang, Variengien, Conmy, Shlegeris, Steinhardt (2022).** "Interpretability in the Wild: a
  Circuit for Indirect Object Identification in GPT-2 small." arXiv:2211.00593 (ICLR 2023).
  https://arxiv.org/abs/2211.00593
  - Did: path patching recovers a circuit of attention heads for one task.
  - Differs: our heads (L19H31, L23H17, L15H31) are ranked by attention from the answer position
    and confirmed by layer-level patching (F12). We don't claim a full circuit.
- **Zhang, Nanda (2024).** "Towards Best Practices of Activation Patching in Language Models:
  Metrics and Methods." ICLR 2024. arXiv:2309.16042. https://arxiv.org/abs/2309.16042
  - Did: shows that the corruption method and the metric change patching results.
  - Differs: not a difference but a choice to report. Our clean run swaps one token, the hint
    letter W for the own answer O. Our metric is the logit difference between the two letters
    (F11).
- **Heimersheim, Nanda (2024).** "How to use and interpret activation patching." arXiv:2404.15255.
  https://arxiv.org/abs/2404.15255
  - A practitioner's guide: granularity, metrics, path patching.
  - Cited for the method.

## 3. Inference-time intervention and attention steering

- **Li, Patel, Viégas, Pfister, Wattenberg (2023).** "Inference-Time Intervention: Eliciting
  Truthful Answers from a Language Model." NeurIPS 2023. arXiv:2306.03341.
  https://arxiv.org/abs/2306.03341
  - Did: shifts activations along probe-found directions in a few attention heads, with a tunable
    strength that trades truthfulness against helpfulness.
  - Differs (B1): we don't add a direction. We rescale attention to a span defined by provenance
    (tool-role tokens), in layers found by causal patching of one failure. Like ITI's strength, our
    alpha is a trade-off: we report wrong-hint following against correct-hint acceptance.
- **Zhang, Singh, Liu, Liu, Yu, Gao, Zhao (2024).** "Tell Your Model Where to Attend: Post-hoc
  Attention Steering for LLMs" (PASTA). ICLR 2024. arXiv:2311.02262. https://arxiv.org/abs/2311.02262
  - Did: in a small set of heads chosen by profiling, reweights attention to *upweight*
    user-emphasized tokens, at inference, without training.
  - Differs (B1): closest in mechanism. We *downweight* keys of an untrusted span, chosen by
    provenance rather than user emphasis. Our layers and heads come from patching a specific
    failure rather than task profiling. The deployable version needs only the tool role, which an
    agent framework knows. We measure what it costs when the tool is right.

## 4. Instruction hierarchy and provenance defenses (prompt injection)

- **Wallace, Xiao, Leike, Weng, Heidecke, Beutel (2024).** "The Instruction Hierarchy: Training LLMs
  to Prioritize Privileged Instructions." arXiv:2404.13208. https://arxiv.org/abs/2404.13208
  - Did: trains GPT-3.5 on generated data to ignore lower-privileged instructions (e.g. in tool
    outputs) when they conflict with higher ones.
  - Differs: our threat is not an injected *instruction* but a wrong *fact* from a tool that the
    model adopts and then doesn't disclose. Our fix acts on the layers that read it.
- **Wu, Zhang, Song, Xu, Zhao, Agrawal, Indurthi, Xiang, Mittal, Zhou (2025).** "Instructional
  Segment Embedding: Improving LLM Safety with Instruction Hierarchy." ICLR 2025 (per the authors'
  repository and DBLP). arXiv:2410.09102. https://arxiv.org/abs/2410.09102
  - Did: adds a learned segment embedding per role (system, user, data) to every token's embedding,
    trained for instruction hierarchy. Gains on prompt-injection benchmarks.
  - Differs: this is the design of our input-embedding source tags. In our setting the tags did
    nothing measurable on the taught tokens' loss, and nothing more on the inserted tool turn
    (F20). B2 moves the provenance signal from the input embedding to a per-head attention bias
    in the layers that read the hint.
- **Hines et al. (2024).** "Defending Against Indirect Prompt Injection
  Attacks With Spotlighting." arXiv:2403.14720. https://arxiv.org/abs/2403.14720
  - Did: prompt transformations (delimiting, datamarking, encoding) give the model a continuous
    provenance signal. Attack success fell from over 50% to under 2% on GPT-family models.
  - Differs: prompt-level, no access to internals. B1 and B2 act inside the model. Spotlighting
    targets instructions, not facts.
- **Chen, Piet, Sitawarin, Wagner (2025).** "StruQ: Defending Against Prompt Injection with Structured
  Queries." USENIX Security 2025. arXiv:2402.06363. https://arxiv.org/abs/2402.06363
  - Did: separates prompt and data into channels with a secure front end and fine-tunes the model
    to follow instructions only in the prompt channel.
  - Differs: like ISE, it relies on input-level channel marking plus training. Our evidence (F20)
    is that an input-level source signal alone did nothing measurable for wrong tool facts.
- **Chen, Zharmagambetov, Mahloujifar, Chaudhuri, Wagner, Guo (2025).** "SecAlign: Defending Against
  Prompt Injection with Preference Optimization." ACM CCS 2025. arXiv:2410.05451.
  https://arxiv.org/abs/2410.05451
  - Did: preference optimization toward the response that ignores the injected instruction.
  - Differs: training objective vs our attention-level intervention. Their target is instruction
    following, ours factual deference and disclosure.
- **Greshake, Abdelnabi, Mishra, Endres, Holz, Fritz (2023).** "Not what you've signed up for:
  Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection."
  arXiv:2302.12173. https://arxiv.org/abs/2302.12173
  - Did: shows retrieved or tool data can carry instructions that take over LLM applications.
  - Differs: motivates treating tool output as untrusted. Our wrong lookups carry no instruction,
    only a wrong answer key.

## 5. Deference to external evidence

- **Xie, Zhang, Chen, Lou, Su (2024).** "Adaptive Chameleon or Stubborn Sloth: Revealing the Behavior
  of Large Language Models in Knowledge Conflicts." ICLR 2024 (spotlight). arXiv:2305.13300.
  https://arxiv.org/abs/2305.13300
  - Did: LLMs are highly receptive to coherent external evidence that conflicts with their memory,
    and show confirmation bias.
  - Differs: our evidence is a terse tool reply (an answer key's letter). We compare the same hint
    from a tool vs a user (F1). We also find the final answer hides the deference (F3, F15).
- **Wu, Wu, Zou (2024).** "ClashEval: Quantifying the tug-of-war between an LLM's internal prior and
  external evidence." arXiv:2404.10198 (a NeurIPS 2024 poster).
  https://arxiv.org/abs/2404.10198
  - Did: models adopt incorrect retrieved content, overriding a correct prior over 60% of the time.
  - Differs: a reviewer *reading another model's* trace defers to the tool it saw (F18), and two
    prompt fixes fail (F19, F21). This is deference at the oversight step, not at retrieval.

## 6. LLM judges, sycophancy

- **Zheng et al. (2023).** "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." NeurIPS 2023
  Datasets and Benchmarks. arXiv:2306.05685. https://arxiv.org/abs/2306.05685
  - Did: GPT-4 judges agree with humans over 80%; position, verbosity and self-enhancement biases.
  - Differs: our reviewer checks a single answer inside an agent pipeline. The bias we find is
    deference to the solver's tool trace, triggered by seeing it.
- **Panickssery, Bowman, Feng (2024).** "LLM Evaluators Recognize and Favor Their Own Generations."
  NeurIPS 2024. arXiv:2404.13076. https://arxiv.org/abs/2404.13076
  - Did: self-recognition correlates with self-preference in LLM evaluators.
  - Differs: our reviewers are other models than the solver (Qwen3 30B Thinking solves; Olmo 3.1
    32B Instruct and Qwen3 30B Instruct review), so self-preference is not the mechanism.
- **Sharma et al. (2024).** "Towards Understanding Sycophancy in Language Models." ICLR 2024.
  arXiv:2310.13548. https://arxiv.org/abs/2310.13548
  - Did: assistants tailor answers to a user's stated views; preference data rewards it.
  - Differs: our reviewer's deference is to a tool's answer key read in a trace, with no user
    opinion in the prompt. Our user-hint channel (F1) is the sycophancy-like case, and it moves
    thinking models *less* than the tool.

## 7. Automation bias (human factors)

- **Skitka, Mosier, Burdick (1999).** "Does automation bias decision-making?" International Journal of
  Human-Computer Studies 51(5), 991–1006. doi:10.1006/ijhc.1999.0252
  https://doi.org/10.1006/ijhc.1999.0252
  - Did: people with a highly but not perfectly reliable aid made omission and commission errors
    that unaided people didn't.
  - Differs: our "operator" is a model reviewer. We use the term for the pattern, not a shared
    cause (F18).
- **Parasuraman, Manzey (2010).** "Complacency and Bias in Human Use of Automation: An Attentional
  Integration." Human Factors 52(3), 381–410. doi:10.1177/0018720810376055
  https://pubmed.ncbi.nlm.nih.gov/21077562/
  - A review and model linking complacency and automation bias through attention.
- **Goddard, Roudsari, Wyatt (2012).** "Automation bias: a systematic review of frequency, effect
  mediators, and mitigators." JAMIA 19(1), 121–127. doi:10.1136/amiajnl-2011-000089
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3240751
  - Did: a systematic review of automation bias in clinical decision support, with mediators and
    mitigations.
  - Relevant: the human literature studies mitigations. We tested two prompt-level ones on an LLM
    reviewer (a warning, and committing to its own answer first); both failed (F19, F21).

## 8. Fine-tuning

- **Hu et al. (2022).** "LoRA: Low-Rank Adaptation of Large Language Models." ICLR 2022.
  arXiv:2106.09685. https://arxiv.org/abs/2106.09685
  - Our lora versions. lora_attn3 restricts LoRA to the attention of layers 15, 19 and 23
    (1,572,864 parameters vs 39,976,960 for full LoRA; F20).

## Not verified tonight (don't cite until checked)

- Olmo 3 and Olmo 3.1 model reports (the models we use); Qwen3 technical report.
- Any "answer before seeing the evidence" mitigation study for LLM judges, if one exists (we looked
  only in the human-factors literature).
- Mechanistic studies of tool-output processing in LLMs (none found and checked tonight).
- Venue notes resting on secondary listings: ISE at ICLR 2025 (the authors' repository and DBLP, not
  OpenReview); IOI at ICLR 2023 (mlanthology).
