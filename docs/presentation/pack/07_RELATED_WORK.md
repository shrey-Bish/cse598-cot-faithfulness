# 07. Related work

Each paper: the full reference, what it found, and how our result relates (agrees, extends, differs), condensed from
[`docs/paper/RELATED_WORK.md`](../../paper/RELATED_WORK.md), where each entry was checked against its arXiv,
proceedings or publisher page (Oct 29; the nine marked "Nov 19" on Nov 19, 10:21–10:31 MST). Nothing is added here
that RELATED_WORK doesn't say. Our findings are cited by their ids ([02_NUMBERS](02_NUMBERS.md)).

**Checked, not a literature search:** nine papers were added on Nov 19 and four of them rest on their abstracts only
(Walden and Wanner; Unspoken Hints; Zhao et al.; Syed and Yasaei). No paper's venue is claimed beyond what is listed.
Not cited until checked: the Olmo 3 / 3.1 and Qwen3 model reports.

## The table (for a backup slide)

| paper | found | relation | our findings |
|---|---|---|---|
| Turpin et al. 2023 | biased prompts shift answers; explanations rarely say so | differs: tool channels, private vs final, the layers | F1, F3, F11 |
| Lanham et al. 2023 | intervening on the CoT measures dependence | differs: early answering as a probe of when the hint takes over | F4, F5, F7 |
| Chen et al. 2025 | reasoning models reveal hint use rarely | extends their three future-work directions (tools, training, activations) | F15–F17, F28, F41, F11 |
| Chua and Evans 2025 | reasoning models describe cues more than non-reasoning ones | differs: the mention is in the private reasoning, not the final answer | F3, F15 |
| Walden and Wanner 2026 (Nov 19) | models acknowledge a hint yet deny using it | agrees that what a model says can mislead; differs: we show no lying or denial | F3, F15, F29, F28, F45 |
| Marioriyad et al. 2025, Unspoken Hints (Nov 19) | raw answer hints used silently | agrees; differs: private reasoning names it; tool channels | F3, F15, F1 |
| Gema et al. 2026, FACE-Eval (Nov 19) | tool-delivered cues stated less than user cues; effort and a source prompt tested | agrees (no "first" for us); extends: same weights on/off, the final answer; differs in measure on effort | F15, F16, F29, FB1, F3, F37, F25 |
| Meng et al. 2022 (ROME) | causal tracing localizes facts in mid-layer MLPs | differs: attention in three full-attention layers at the hint's tokens | F11 |
| Wang et al. 2022 (IOI) | a circuit of heads by path patching | differs: heads ranked by attention, confirmed by layer patching; no full circuit | F12 |
| Zhang and Nanda 2024 | corruption and metric change patching results | a choice we report: one-token swap, logit difference | F11 |
| Heimersheim and Nanda 2024 | how to use activation patching | cited for the method | — |
| Li et al. 2023 (ITI) | shift activations in a few heads; strength trades truthfulness | differs: rescale attention to a provenance span; we report the trade | F38 |
| Zhang et al. 2024 (PASTA) | upweight user-emphasized tokens' attention | differs: closest mechanism; we downweight an untrusted span and measure the cost | F38 |
| Wallace et al. 2024 (Instruction Hierarchy) | train to ignore lower-privilege instructions | differs: our threat is a wrong fact, not an instruction | — |
| Wu et al. 2025 (ISE) | a learned segment embedding per role | differs: our input source tags, same design, did nothing measurable | F20 |
| Hines et al. 2024 (Spotlighting) | prompt-level provenance marking cuts injection | differs: prompt-level; instructions, not facts | — |
| Chen et al. 2025 (StruQ) | separate channels plus fine-tuning | differs: an input-level source signal alone did nothing for wrong tool facts | F20 |
| Chen et al. 2025 (SecAlign) | preference optimization against injections | differs: training objective vs attention-level intervention | — |
| Greshake et al. 2023 | tool data can carry instructions that take over apps | differs: motivates untrusted tool output; ours carry no instruction | — |
| Syed and Yasaei 2026 (Nov 19) | instructions in tool metadata discounted against the user's; patching at mid-to-late layers | differs: an instruction, not a wrong fact; not reconciled; agrees loosely on where | F15–F17, F29, F37, FB1, F11, F26 |
| Xie et al. 2024 | models receptive to coherent conflicting evidence | differs: a terse tool reply; tool vs user; the hidden deference | F1, F3, F15 |
| Wu, Wu and Zou 2024 (ClashEval) | models adopt incorrect retrieved content | differs: deference at the oversight step | F18, F19, F21 |
| Kumar and Chopra 2026, Authority Bias (Nov 19) | source notes flip answers, more so the more authoritative | agrees (the ladder is not new in kind); extends: user claims against tool channels, same day; differs in mechanism and fix | F1, F35, F40, F11, F38, F44 |
| Waqas et al. 2025, A-CC (Nov 19) | user assertions followed more than function-sourced ones | agrees tool assertions are followed; differs in direction; not reconciled | F15, F16, F29, FB1 |
| Zhao et al. 2025, When Tools Hurt (Nov 19) | tool evidence can flip right answers; a controller arbitrates | agrees; extends only with a seeded wrong tool and tested fixes | F18, F15, F41, F24 |
| Zheng et al. 2023 (LLM-as-a-judge) | GPT-4 judges agree with humans; biases | differs: deference to the solver's tool trace | F18 |
| Panickssery et al. 2024 | evaluators favor their own generations | differs: our reviewers aren't the solver | F18 |
| Sharma et al. 2024 | sycophancy toward a user's view | differs: our user channel moves thinking models less than the tool | F1 |
| Skitka et al. 1999 | automation bias in people | differs: the term for the pattern, not a shared cause | F18 |
| Parasuraman and Manzey 2010 | complacency and automation bias, through attention | a review and model | — |
| Goddard et al. 2012 | automation bias in clinical support; mitigations | two prompt-level mitigations failed on an LLM reviewer | F19, F21 |
| Hu et al. 2022 (LoRA) | low-rank adaptation | our LoRA versions | F20 |
| Chua et al. 2024 (BCT, Nov 19) | consistency training cuts biased reasoning; cost on correct cues unmeasured | agrees with the direction; extends: tool channels, 120 fresh questions, the cost to right hints, where training acts; we don't claim the method | F41, F42, F43 |

## The entries

### Chain-of-thought faithfulness under hints

- **Turpin, Michael, Perez, Bowman (2023).** "Language Models Don't Always Say What They Think: Unfaithful
  Explanations in Chain-of-Thought Prompting." NeurIPS 2023. arXiv:2305.04388. https://arxiv.org/abs/2305.04388
  - Found: biasing features (e.g. a user's suggested answer) shift GPT-3.5's and Claude 1.0's answers, and the
    explanations rarely mention them.
  - Relates: **differs.** Our hint also comes through a tool (pasted block, inserted turn, real call); we separate the
    private reasoning from the final answer; we locate where the hint is read (F11).
- **Lanham et al. (2023).** "Measuring Faithfulness in Chain-of-Thought Reasoning." arXiv:2307.13702.
  https://arxiv.org/abs/2307.13702
  - Found: intervening on the CoT (early answering, mistakes, paraphrase, filler) shows how much answers depend on it.
  - Relates: **differs.** We use early answering to see when the hinted answer takes over (F4, F5), with deletion of
    the hint's mentions (F7) and patching.
- **Chen et al. (2025).** "Reasoning Models Don't Always Say What They Think." arXiv:2505.05410.
  https://arxiv.org/abs/2505.05410
  - Found: reasoning models' CoTs reveal a hint they used in at least 1% of cases, often fewer than 20%; outcome-based
    RL helped at first, then levelled off.
  - Relates: **extends** their three future-work directions: tool use (Gate 2, Track B: F15, F16, F17, F29, F37, FB1;
    the bare answer after a call, F15, F16; F25), training for faithful CoT (SFT only: F20, F28, F44; consistency
    training F41–F43; labels F28, F45; a trade, not a fix), and activations (patching and attention, not SAE features:
    F11, F26, F12, F32, F36).
- **Chua, Evans (2025).** "Are DeepSeek R1 And Other Reasoning Models More Faithful?" arXiv:2501.08156 (ICLR 2025
  workshop FM-Wild). https://arxiv.org/abs/2501.08156
  - Found: reasoning models describe a cue that changed their answer far more often than non-reasoning models.
  - Relates: **differs.** The mention is in the private reasoning (F3); the final answer almost never carries it, and
    after a tool call it is a bare letter (F15).
- **Walden, Wanner (2026).** "Reasoning Models Will Sometimes Lie About Their Reasoning." arXiv:2601.07663.
  https://arxiv.org/abs/2601.07663 (abstract only)
  - Found: warned models often acknowledge a hint yet deny using it.
  - Relates: **agrees** that what a reasoning model says can mislead (F3, F15, F29); **differs** in setting and measure
    (no warning; keyword mentions, not denials); our hand labels found almost no claimed disagreement (F28, F45). We
    don't show lying or denial.
- **Marioriyad et al. (2025).** "Unspoken Hints: Accuracy Without Acknowledgement in LLM Reasoning." arXiv:2509.26041.
  https://arxiv.org/abs/2509.26041 (abstract only)
  - Found: raw answer hints are used silently; leak-style prompts encourage hidden reliance.
  - Relates: **agrees** (our hint is a raw letter: F3, F15); **differs**: our models' private reasoning names it (F3)
    and the hint also comes by a tool (F1).
- **Gema et al. (2026).** "Chain-of-Thought Faithfulness of Reasoning Models Varies with Where and How Preference Cues
  Are Delivered" (FACE-Eval). arXiv:2608.29464. https://arxiv.org/abs/2608.29464
  - Found: over 15 open-weight reasoning models, a cue from a tool return is stated less than from the user, yet adopted
    silently more; they vary reasoning effort and test a source-attribution prompt.
  - Relates: **agrees**, so no "first" on the disclosure side (F15, F16, F29, FB1); **extends**: the same weights with
    thinking on and off (F29) and whether the final answer names the source (F3, F15); **differs**: our hint is a wrong
    answer, we measure following, our channels include the model's own call; on effort we find no change detected
    (F37); our instruction is read on the final answer and on following (F25).

### Localization: activation patching

- **Meng, Bau, Andonian, Belinkov (2022).** "Locating and Editing Factual Associations in GPT." NeurIPS 2022.
  arXiv:2202.05262. https://arxiv.org/abs/2202.05262. **Differs:** we restore at the hint's tokens, layer by layer, at
  the takeover; the readout is attention in three full-attention layers, not MLPs (F11).
- **Wang, Variengien, Conmy, Shlegeris, Steinhardt (2022).** "Interpretability in the Wild: a Circuit for Indirect
  Object Identification in GPT-2 small." arXiv:2211.00593 (ICLR 2023). https://arxiv.org/abs/2211.00593.
  **Differs:** our heads (L19H31, L23H17, L15H31) are ranked by attention and confirmed by layer patching; no full
  circuit claimed (F12).
- **Zhang, Nanda (2024).** "Towards Best Practices of Activation Patching in Language Models: Metrics and Methods."
  ICLR 2024. arXiv:2309.16042. https://arxiv.org/abs/2309.16042. **A choice we report:** a one-token swap (the hint
  letter for the own answer) and the logit difference between the two letters (F11).
- **Heimersheim, Nanda (2024).** "How to use and interpret activation patching." arXiv:2404.15255.
  https://arxiv.org/abs/2404.15255. Cited for the method.

### Inference-time intervention and attention steering

- **Li, Patel, Viégas, Pfister, Wattenberg (2023).** "Inference-Time Intervention: Eliciting Truthful Answers from a
  Language Model." NeurIPS 2023. arXiv:2306.03341. https://arxiv.org/abs/2306.03341. **Differs:** we rescale
  attention to a provenance span in layers found by patching, and report following against acceptance (F38).
- **Zhang, Singh, Liu, Liu, Yu, Gao, Zhao (2024).** "Tell Your Model Where to Attend: Post-hoc Attention Steering for
  LLMs" (PASTA). ICLR 2024. arXiv:2311.02262. https://arxiv.org/abs/2311.02262. **Differs:** the closest mechanism; we
  downweight an untrusted span chosen by provenance and measure the cost when the tool is right (F38).

### Instruction hierarchy and provenance defenses

- **Wallace, Xiao, Leike, Weng, Heidecke, Beutel (2024).** "The Instruction Hierarchy: Training LLMs to Prioritize
  Privileged Instructions." arXiv:2404.13208. https://arxiv.org/abs/2404.13208. **Differs:** our threat is a wrong fact
  from a tool, not an injected instruction.
- **Wu et al. (2025).** "Instructional Segment Embedding: Improving LLM Safety with Instruction Hierarchy." ICLR 2025
  (per the authors' repository and DBLP). arXiv:2410.09102. https://arxiv.org/abs/2410.09102. **Differs:** the design
  of our input source tags, which did nothing measurable in our setting (F20).
- **Hines et al. (2024).** "Defending Against Indirect Prompt Injection Attacks With Spotlighting." arXiv:2403.14720.
  https://arxiv.org/abs/2403.14720. **Differs:** prompt-level, for instructions, not facts.
- **Chen, Piet, Sitawarin, Wagner (2025).** "StruQ: Defending Against Prompt Injection with Structured Queries." USENIX
  Security 2025. arXiv:2402.06363. https://arxiv.org/abs/2402.06363. **Differs:** input-level channels plus training;
  an input-level source signal alone did nothing for wrong tool facts (F20).
- **Chen, Zharmagambetov, Mahloujifar, Chaudhuri, Wagner, Guo (2025).** "SecAlign: Defending Against Prompt Injection
  with Preference Optimization." ACM CCS 2025. arXiv:2410.05451. https://arxiv.org/abs/2410.05451. **Differs:**
  a training objective against instruction following, not factual deference.
- **Greshake, Abdelnabi, Mishra, Endres, Holz, Fritz (2023).** "Not what you've signed up for: Compromising Real-World
  LLM-Integrated Applications with Indirect Prompt Injection." arXiv:2302.12173. https://arxiv.org/abs/2302.12173.
  **Differs:** motivates untrusted tool output; our wrong lookups carry no instruction.
- **Syed, Yasaei (2026).** "Same Payload, Different Channel: Measuring Trust Asymmetry in Tool-Using Language Models."
  arXiv:2606.00566. https://arxiv.org/abs/2606.00566 (abstract only). **Differs:** they carry an instruction, which
  tool channels discount; our wrong fact moved models more from the tool (F15–F17, F29, F37, FB1); not reconciled.
  **Agrees** loosely on where (mid-to-late layers; F11, F26).

### Deference to external evidence

- **Xie, Zhang, Chen, Lou, Su (2024).** "Adaptive Chameleon or Stubborn Sloth: Revealing the Behavior of Large Language
  Models in Knowledge Conflicts." ICLR 2024. arXiv:2305.13300. https://arxiv.org/abs/2305.13300. **Differs:** a terse
  tool reply; the same hint from a tool against a user (F1); the final answer hides the deference (F3, F15).
- **Wu, Wu, Zou (2024).** "ClashEval: Quantifying the tug-of-war between an LLM's internal prior and external
  evidence." arXiv:2404.10198 (NeurIPS 2024 poster). https://arxiv.org/abs/2404.10198. **Differs:** a reviewer reading
  another model's trace defers to its tool (F18); two prompt fixes fail (F19, F21).
- **Kumar, Chopra (2026).** "Authority Bias in Language Models: Source Deference and User Agreement Are Not
  Interchangeable." arXiv:2609.37616. https://arxiv.org/abs/2609.37616
  - Found: a source note endorsing a wrong answer flipped many correct answers; compliance rose with authority; source
    deference and user agreement separate inside the models; removing the source direction's effect on correct sources
    untested (their words).
  - Relates: **agrees** in kind (F1, F35, F40): the authority ladder is not new in kind; **extends**: user claims
    against tool channels in the same model and day, in reasoning models (F35, F40); **differs**: we locate the readout
    (F11, F26, F32, F36), scale attention (F38) and measure the cost to correct hints (F38, F44).
- **Waqas et al. (2025).** "Assertion-Conditioned Compliance: A Provenance-Aware Vulnerability in Multi-Turn
  Tool-Calling Agents." arXiv:2512.00332. https://arxiv.org/abs/2512.00332
  - Found: tool-calling models follow misleading assertions from the user and from function outputs; confident user
    assertions more than function-sourced ones.
  - Relates: **agrees** tool assertions are followed (F15, F16, F29); **differs in direction** from our tool-over-user
    result; not reconciled. We don't claim tools beat users in general (Gate 2, FB1).
- **Zhao et al. (2025).** "When Tools Hurt LLM Reasoning: State-Dependent Belief Revision under External Evidence."
  arXiv:2508.15754. https://arxiv.org/abs/2508.15754 (abstract only)
  - Found: tool evidence helps weak beliefs and can flip correct ones; a controller chooses between trajectories.
  - Relates: **agrees** (F18, F15; the trade-off, F41, F43, F44); **extends** only with a seeded wrong tool and
    tested fixes; our checker (F18, F24) is an arbitration of the same family, not compared with theirs.

### LLM judges, sycophancy

- **Zheng et al. (2023).** "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." NeurIPS 2023 Datasets and
  Benchmarks. arXiv:2306.05685. https://arxiv.org/abs/2306.05685. **Differs:** our reviewer checks one answer inside a
  pipeline; the bias is deference to the solver's tool trace (F18).
- **Panickssery, Bowman, Feng (2024).** "LLM Evaluators Recognize and Favor Their Own Generations." NeurIPS 2024.
  arXiv:2404.13076. https://arxiv.org/abs/2404.13076. **Differs:** our reviewers are other models than the solver.
- **Sharma et al. (2024).** "Towards Understanding Sycophancy in Language Models." ICLR 2024. arXiv:2310.13548.
  https://arxiv.org/abs/2310.13548. **Differs:** the reviewer defers to a tool's answer key, with no user opinion; our
  user channel moves thinking models less than the tool (F1).

### Automation bias (human factors)

- **Skitka, Mosier, Burdick (1999).** "Does automation bias decision-making?" International Journal of
  Human-Computer Studies 51(5), 991–1006. https://doi.org/10.1006/ijhc.1999.0252. **Differs:** our "operator" is a
  model; the term names the pattern, not a shared cause (F18).
- **Parasuraman, Manzey (2010).** "Complacency and Bias in Human Use of Automation: An Attentional Integration." Human
  Factors 52(3), 381–410. https://pubmed.ncbi.nlm.nih.gov/21077562/. A review and model.
- **Goddard, Roudsari, Wyatt (2012).** "Automation bias: a systematic review of frequency, effect mediators, and
  mitigators." JAMIA 19(1), 121–127. https://pmc.ncbi.nlm.nih.gov/articles/PMC3240751. We tested two prompt-level
  mitigations on an LLM reviewer; both failed (F19, F21).

### Fine-tuning

- **Hu et al. (2022).** "LoRA: Low-Rank Adaptation of Large Language Models." ICLR 2022. arXiv:2106.09685.
  https://arxiv.org/abs/2106.09685. Our LoRA versions; LoRA on layers 15, 19 and 23 restricts it to their attention
  (F20).
- **Chua et al. (2024).** "Bias-Augmented Consistency Training Reduces Biased Reasoning in Chain-of-Thought."
  arXiv:2403.05518. https://arxiv.org/abs/2403.05518
  - Found: training the model to reason the same with and without a biasing feature cut biased reasoning on held-out
    tasks; they bias only toward wrong answers, so a cost on correct cues isn't measured.
  - Relates: **agrees** with the direction (consistency training follows far fewer wrong hints than no fix, F41);
    **we don't claim the method**; **extends**: a reasoning model and tool channels; 120 fresh questions against the
    instruction (−21 [−26, −16]); the cost to right hints (−15 [−20, −10], F41; F43); where training acts (before the
    readout layers, F42; LoRA in the reasoning, F39).
