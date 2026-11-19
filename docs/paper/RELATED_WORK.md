# Related work (verified references only)

**Edited by:** Ritik.

Each entry was checked against its arXiv, proceedings or publisher page on 2026-10-29. **The Nov 19 additions
(marked "Relates:", nine references, the table at the end) were checked on 2026-11-19, 10:21 to 10:26 MST, against
each paper's arXiv abstract page (title, authors, v1 date), with details beyond the abstract taken from its arXiv HTML
version through a summarizing fetch; see "Not verified" for what that covers.** The link given
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
  https://arxiv.org/abs/2505.05410 (first author Yanda Chen; 15 authors; v1 May 2025; checked 2026-11-19)
  - Did: pairs questions with and without one of six hint types and asks whether reasoning models'
    CoT mentions a hint they used. Their abstract: CoTs revealed hint use in at least 1% of cases where the hint
    was used, but often in fewer than 20%; outcome-based RL improved faithfulness at first, then levelled off.
  - Differs: our hint sources include tools and real tool calls. We report the private reasoning against the
    final answer separately (F3, F15). We add a localization (F11, F26, F32, F36) and tested fixes (F28, F41-F44).
    (Corrected Nov 19: this entry said their setup doesn't separate private from final "in the same way"; not checked.)
  - **Their own future-work directions** (Section 8, their Conclusion; read in the arXiv HTML version on
    2026-11-19; all three are stated there, and each is kept):
    - *Tool use:* "tasks that involve tool use". **Relates: extends.** Gate 2 and Track B put the hint in a tool
      channel, including the model's own call: following by channel in F15, F16, F17, F29, F37, FB1; the final
      answer after a call is a bare letter (F15, F16; Nemotron and Granite in FB1); one instruction brings the tool
      back into the answer without changing following (F25).
    - *Training for faithful CoT:* "supervised finetuning or reinforcement learning". **Relates: extends** (SFT
      only; no RL): fine-tuning (LoRA, F20, F28, F44), consistency training (A40, F41-F43) and hand labels of what
      the answer says (L4 part 1, F28; L6, F45). Our result is a trade, not a fix: no trained version beats the
      one-line instruction without a cost to correct hints (F41, F43, F44).
    - *Probing activations:* "internal activations" (they name sparse-autoencoder features and circuits as
      examples). **Relates: extends**, with patching and attention instead of SAE features: layers 15, 19 and 23
      read the hint (F11, F26) and three heads separate followed from resisted runs (F12, F32), replicated in
      Qwen3-8B (F36). We use no SAE features and claim no circuit.
- **Chua, Evans (2025).** "Are DeepSeek R1 And Other Reasoning Models More Faithful?" arXiv:2501.08156
  (ICLR 2025 workshop FM-Wild). https://arxiv.org/abs/2501.08156
  - Did: reasoning models describe a cue that changed their MMLU answer far more often than
    non-reasoning models (e.g. DeepSeek-R1 59% vs DeepSeek-V3 7%).
  - Differs: we find the mention is in the private reasoning (F3), while the final answer, which
    is what a user or reviewer sees, almost never carries it. After a tool call the final answer
    is a bare letter (F15).

- **Walden, Wanner (2026).** "Reasoning Models Will Sometimes Lie About Their Reasoning." arXiv:2601.07663.
  https://arxiv.org/abs/2601.07663 (v1 January 2026; checked 2026-11-19)
  - Did: tests reasoning models when warned that unusual content may appear; new, more detailed metrics show models
    often acknowledge a hint is present yet deny using it, even when they may use it and the authors can show they
    did. Argues this complicates CoT monitoring.
  - Relates: **agrees** that what a reasoning model says about its hint use can mislead (our F3, F15, F29: the
    tool in the private reasoning, not in the final answer). **differs** in setting and measure: we give no warning
    and count keyword mentions (F3), not denials. Our one hand-labelled look at final answers of followed runs found
    almost no claimed disagreement: `rejects_hint` in 1 to 2 of LoRA's 147 candidates (F28) and 0 of 42 (F45).
    We don't show "lying" or denial.
- **Marioriyad et al. (2025).** "Unspoken Hints: Accuracy Without Acknowledgement in LLM Reasoning."
  arXiv:2509.26041. https://arxiv.org/abs/2509.26041 (first author Arash Marioriyad; 5 authors; v1 September 2025;
  checked 2026-11-19)
  - Did: GPT-4o and Gemini-2-Flash on four datasets with correct and incorrect hints: models mention equation-style
    hints often but tend to use raw answer hints silently; leak-style prompts raise accuracy and encourage hidden
    reliance, sycophancy-style prompts lead to acknowledgement.
  - Relates: **agrees** that a raw answer hint is used without being named (our hint is a raw answer letter: F3's
    final answers, F15). **differs**: our models show a private reasoning, which does name the hint (F3), and our
    hint comes by a tool as well as the user (F1). Their presentation effect (leak vs sycophancy) is a cousin of our
    channel effect (F1, F15); we did not test their presentations.
- **Gema et al. (2026).** "Chain-of-Thought Faithfulness of Reasoning Models Varies with Where and How Preference
  Cues Are Delivered" (introduces FACE-Eval). arXiv:2608.29464. https://arxiv.org/abs/2608.29464 (first author
  Aryo Pradipta Gema; 5 authors; v1 August 2026; checked 2026-11-19; chosen among the search results because its
  abstract introduces FACE-Eval and is about CoT faithfulness; the other hits were other papers)
  - Did: a 5,100-sample benchmark varying where a preference cue appears (user message or tool return) and how
    explicit it is, over 15 open-weight reasoning models from eight families (4B to 1.60T; Olmo 3 Think and gpt-oss
    among them). Models state the cue's influence less often when it comes through a tool, yet adopt it without
    saying so more often; a prompt asking for the source narrows the gap on some models. Tool returns are prefilled
    (the model does not choose the call), and the cue is a preference, not a wrong factual answer.
  - Relates: **agrees**, and this takes away any "first" for the disclosure side: a cue delivered by a tool is
    said less than the same cue from the user (our F15, F16, F29, FB1). **differs** in measure and setting: our hint
    is a wrong answer to a question with a right one, we measure following and not only verbalization, and our tool
    channels include the model's own call (F15, F16, F29, FB1). **extends** on two points: the same weights with
    thinking on and off (F29; a text search of their full paper finds no on/off comparison), and whether the final
    answer names the source (their reasoning judge reads the reasoning only, and their answer judge labels only the side
    the answer takes; our F3, F15). **Not ours (corrected Nov 19, 10:31):** they already vary reasoning effort (on
    GPT-OSS, "higher reasoning effort raises VCR in every condition without closing either gap") and test a
    source-attribution prompt (it narrows the channel gap on seven models). On effort ours **differs** in measure:
    gpt-oss-20b shows no change detected in following or in the bare final answer (F37). Our instruction (B15, F25) is
    read on the final answer and on following: it brings the tool back into the answer and does not change following.

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

- **Syed, Yasaei (2026).** "Same Payload, Different Channel: Measuring Trust Asymmetry in Tool-Using Language
  Models." arXiv:2606.00566. https://arxiv.org/abs/2606.00566 (first author Mohammed Sameer Syed; v1 May 2026;
  arXiv title as shown, which is longer than the short title we were given; checked 2026-11-19)
  - Did: the same malicious instruction in the user message, tool metadata or tool output; across 10 production LLMs
    general-purpose models discount instructions in tool metadata much more than the same instructions in user
    messages; activation patching recovers the signal at mid-to-late layers in Llama 3.3-70B and GPT-OSS-120B.
  - Relates: **differs** in what is carried: an instruction, not a wrong fact. In their setting tool content is
    discounted against the user's; with a wrong answer key the tool's hint moved our models more than the user's
    (Gate 2: F15, F16, F17, F29, F37, FB1). We did not test an instruction through our channels, so the two aren't
    reconciled. **agrees** loosely on where: patching points to mid-to-late layers (ours: 15, 19, 23; F11, F26).

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

- **Kumar, Chopra (2026).** "Authority Bias in Language Models: Source Deference and User Agreement Are Not
  Interchangeable." arXiv:2609.37616. https://arxiv.org/abs/2609.37616 (first author Abhinav Rajeev Kumar; 2 authors;
  v1 September 2026; checked 2026-11-19)
  - Did: across five open-weight families and three closed APIs a source note endorsing a wrong answer flipped 45-88%
    of baseline-correct answers in seven of eight models; compliance rose with how authoritative the note sounded
    (four wordings, hedged to "verified source"); source deference and user agreement separate inside the models
    (fitted linear directions; removing the source direction cut wrong-source compliance in most families). Their
    removal experiment "does not test whether the models still benefit from correct source information after the
    intervention" (their words); Qwen3.5 ran with thinking off because its reasoning often looped.
  - Relates: **agrees** with F1, F35 and F40 in kind: a claimed source moves answers more than a user's opinion,
    and the pull grows with the source's authority. **So the authority ladder is not new in kind.** **extends**:
    our ladder is the user's own claim (classmate, answer key, official manual) set against tool channels in the
    same model, same day (B19, B24; F35, F40), in reasoning models, and it shows where the claim matches or passes
    the tool and where the tool's own call goes beyond it (Instruct's own call, F40). **differs** in mechanism and
    fix: they remove a direction fitted at one layer per model; we locate where the hint's letter is read (layers
    15, 19, 23; F11, F26, F32, F36) and scale attention to tool-span keys (B1, F38), and we measure the cost to
    correct hints (F38, F44), which they leave untested.
- **Waqas et al. (2025).** "Assertion-Conditioned Compliance: A Provenance-Aware Vulnerability in Multi-Turn
  Tool-Calling Agents." arXiv:2512.00332. https://arxiv.org/abs/2512.00332 (first author Daud Waqas; 4 authors; v1
  November 2025; checked 2026-11-19)
  - Did: A-CC tests tool-calling models (Berkeley function-calling multi-turn) with misleading assertions from the
    user and from function outputs; models are highly vulnerable to both. Per the HTML text, confident user assertions
    were followed more than function-sourced ones (36.3% against 27.8%, macro-averaged); no mechanism, no fix.
  - Relates: **agrees** that tool-sourced assertions are followed (F15, F16, F29). **differs in direction** from
    our tool-over-user result: theirs are function-calling models on policy hints, ours are answer keys on
    questions, in thinking and instruct models (Gate 2); we don't reconcile the two. We don't claim tools beat
    users in general, only in our five Track B models and B20's three families (FB1).
- **Zhao et al. (2025).** "When Tools Hurt LLM Reasoning: State-Dependent Belief Revision under External
  Evidence." arXiv:2508.15754. https://arxiv.org/abs/2508.15754 (first author Yufeng Zhao; 7 authors; v1 August
  2025; checked 2026-11-19; arXiv title as shown, the subtitle is part of it)
  - Did: with Python and Wikipedia tools, external evidence helps when the model's beliefs are weak and can flip
    already-correct answers when they are strong; frames it as misallocated revision authority; a label-free
    controller (CASE) chooses between no-tool and tool trajectories.
  - Relates: **agrees**: deferring to a tool can overturn a right answer (F18: Olmo 3.1 32B reviewer; F15: Qwen3 30B
    Thinking followed in 54 of 54 runs where it called). **agrees** that the problem is arbitration, which our
    trade-off bullet states for the fixes (F41, F43, F44; REPORT §7, post hoc). **extends** only in that our tool
    is wrong by a seeded oracle and we test fixes. Our independent checker (re-solves without the tool, F18, F24)
    is an arbitration of the same family; we did not compare it with CASE.

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

- **Chua et al. (2024).** "Bias-Augmented Consistency Training Reduces Biased Reasoning in Chain-of-Thought."
  arXiv:2403.05518. https://arxiv.org/abs/2403.05518 (first author James Chua; 7 authors; v1 March 2024; ID
  confirmed on 2026-11-19)
  - Did: BCT, supervised fine-tuning so the model gives the same reasoning with and without a biasing feature in the
    prompt (target: its own reasoning from the unbiased prompt). With one bias it cut biased reasoning on held-out
    tasks by 86% for GPT-3.5-Turbo and by about 37% on other held-out biases; no gold reasoning needed.
    Behavioral only; their evaluation biases only toward wrong answers ("we always bias towards incorrect answers"),
    so a cost on correct cues isn't measured there.
  - Relates: **agrees** with the direction: consistency training (A40) follows far fewer wrong hints than base
    (−30 [−35, −26], F41). **A40 is in BCT's family; we don't claim the method.** **extends**: (1) a reasoning model
    (Olmo 3 7B Think) and a hint through tool channels as well as the user; (2) 120 fresh questions, against the
    one-line instruction (following −21 [−26, −16]); (3) the cost to correct hints, which BCT leaves unmeasured:
    acceptance −15 [−20, −10], "fewer, but costs acceptance" (F41; F43 with the note); (4) where training acts:
    A41 on base's own reasoning, A40's weights remove part of the hint's pull from layers 0-14, before the readout
    layers (+0.68 logits [+0.17, +1.18]), more than LoRA (F42; LoRA acts in the reasoning, F39). A40's limit: trained on
    sure questions only (F41).

## Nov 19 verification record (arXiv abs pages, fetched 2026-11-19)

| id | title given | title on arXiv | first author | v1 | match |
|---|---|---|---|---|---|
| 2505.05410 | Reasoning Models Don't Always Say What They Think | same | Yanda Chen (15 authors) | May 2025 | yes |
| 2609.37616 | Authority Bias in Language Models: Source Deference and User Agreement Are Not Interchangeable | same | Abhinav Rajeev Kumar (+1) | Sep 2026 | yes |
| 2512.00332 | Assertion-Conditioned Compliance | Assertion-Conditioned Compliance: A Provenance-Aware Vulnerability in Multi-Turn Tool-Calling Agents | Daud Waqas (+3) | Nov 2025 | yes (short title) |
| 2606.00566 | Measuring Trust Asymmetry in Tool-Using Language Models | Same Payload, Different Channel: Measuring Trust Asymmetry in Tool-Using Language Models | Mohammed Sameer Syed (+1) | May 2026 | yes (title given was its second half) |
| 2508.15754 | When Tools Hurt LLM Reasoning | When Tools Hurt LLM Reasoning: State-Dependent Belief Revision under External Evidence | Yufeng Zhao (+6) | Aug 2025 | yes (short title) |
| 2601.07663 | Reasoning Models Will Sometimes Lie About Their Reasoning | same | William Walden (+1) | Jan 2026 | yes |
| 2509.26041 | Unspoken Hints | Unspoken Hints: Accuracy Without Acknowledgement in LLM Reasoning | Arash Marioriyad (+4) | Sep 2025 | yes (short title) |
| 2608.29464 (found by search) | FACE-Eval | Chain-of-Thought Faithfulness of Reasoning Models Varies with Where and How Preference Cues Are Delivered (introduces FACE-Eval) | Aryo Pradipta Gema (+4) | Aug 2026 | yes |
| 2403.05518 (believed) | Bias-Augmented Consistency Training (Chua et al. 2024) | Bias-Augmented Consistency Training Reduces Biased Reasoning in Chain-of-Thought | James Chua (+6) | Mar 2024 | yes |

## Not verified tonight (don't cite until checked)

- Olmo 3 and Olmo 3.1 model reports (the models we use); Qwen3 technical report.
- Any "answer before seeing the evidence" mitigation study for LLM judges, if one exists (we looked
  only in the human-factors literature).
- Mechanistic studies of tool-output processing in LLMs: none found on Oct 29. **Corrected Nov 19:** Syed and Yasaei (2026; patching) and Kumar and Chopra (2026; fitted directions) are two, both now in this file (§4, §5); a wider search wasn't done.
- Venue notes resting on secondary listings: ISE at ICLR 2025 (the authors' repository and DBLP, not
  OpenReview); IOI at ICLR 2023 (mlanthology).
- **Nov 19, what the checks did not cover:** all nine ids match their arXiv pages (title, authors, v1 date), so none is
  unverified. Statements beyond a paper's abstract (A-CC's 36.3% and 27.8%; Authority Bias's layers, wordings and
  untested cost; FACE-Eval's channels and on/off; BCT's untested cost on helpful cues; Chen's Section 8) first came from
  a summarizing fetch of the arXiv HTML, which for Authority Bias, FACE-Eval and BCT covered only the first 100,000
  characters of 167,000, 194,000 and 154,000. No PDF was read. We read no paper's venue; none of the nine is claimed
  to be peer reviewed.
- **Re-checked Nov 19, 10:29–10:31, by a second pass:** the nine titles, author lists and v1 dates from the arXiv API
  (BCT has 7 authors, not 8: corrected); then a text search of each of five papers' full arXiv HTML: Chen's three
  directions are verbatim in its Conclusion; A-CC's 36.3% (confident user assertions) and 27.8% (function-sourced) are
  in its §5; Authority Bias's four wordings, its untested benefit of correct sources (quoted above) and Qwen3.5's
  thinking off; BCT's "we always bias towards incorrect answers"; FACE-Eval's judges, its reasoning-effort test on
  GPT-OSS and its source-attribution prompt, which corrected its entry (effort and the prompt are theirs, not our
  extensions). Walden and Wanner, Unspoken Hints, Zhao et al. and Syed and Yasaei rest on their abstracts only.
