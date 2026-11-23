# Session log: the demo's Sol copy in: tests 3 and 4 replay, step 4's total, step 7's curves (2026-11-22 18:48 MST)

**By:** Ritik. Branch `trackA-nosol`, from `69fff21` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). Started Nov 22 at 18:48; stopped mid-screenshots that evening; finished Nov 23, 08:22–08:31 (the clock read
each time). The daily: [DAILY_2026-11-22](2026-11-22/DAILY_2026-11-22.md). The previous session: [16:44](2026-11-22/2026-11-22_1644_ALL_demo-build.md).
The results are frozen: the tag `results-freeze-2026-11-18` on `7e1fdc0`. Presentation work after the freeze.

## 0. Input

A pasted prompt, acted on as Ritik's, with his Terminal output: the Sol copy fetched from his Mac
(`results/demo/sol/fetch.out`, 43 MB, Nov 22 18:38), unpacked and rebuilt. The training folders on Sol (his listing):
`a40`, `lora`, `lora_attn3`, `lora_tags`, `tags` (and console logs). Asked: check the unpacked files are complete; wire
the loss curves to those folders; confirm tests 3 and 4 replay recorded runs and step 4 shows the GPU-hour total; retake
those screenshots; the demo's tests; push.

## 1. What was done

**The copy is complete** (`results/demo/sol/`, gitignored; checked against `plan.json`):

| group | planned | fetched | note |
|---|---|---|---|
| the fixes on the 120 | 252 run ids | 252 | one run on two lines (`c43d897ec5a49dd1`), kept once, as the Mac index does |
| the fixes on the 30 | 492 | 492 | |
| Qwen3-8B, thinking on and off | 90 | 90 | |
| gpt-oss-20b | 135 | 135 | |
| Nemotron 3 Nano | the 3 drawn questions | 108 | 36 a question |
| training logs and `chosen.json` | every version | 5 and 5 | `a40`, `lora`, `lora_attn3`, `lora_tags`, `tags` |
| sacct since Oct 1 | Ritik's account | 287 jobs | 271 used a GPU: 352.47 GPU-hours |

No errors in the manifest; no file not in the index. **The logs agree with the frozen numbers:** `lora`'s epoch
validation losses (0.18567, 0.18537) are `val_loss.json`'s; `a40` kept epoch 1 at 0.198727, as the A40 log reads.

**Wired:**
- **Step 4** (`map.js`): "352 GPU-hours, 271 GPU jobs since Oct 1, on Ritik's account" (`method.py` adds `gpu_jobs`);
  the three per-experiment pieces stay under it.
- **Step 7:** training loss per optimizer step from the Sol logs, epoch 2's start marked, the kept epoch noted. The
  fine-tuning view chooses among the four versions trained on its data (LoRA, + tags, 3 layers, tags only; each
  button's tooltip names it in full); consistency training draws `a40`. `method.json` carries the five curves (222–260
  points each, numbers only) and the total.
- **Tests 3 and 4** replay recorded text: test 3 Qwen3-8B on and off, gpt-oss, Nemotron (333 runs); test 4 the fixes
  (744). Test 1 gains the same three models (441 runs with text). Gemma and Granite stay frozen numbers only.

**Fixed on the way** (found in the screenshots and by the test):
- Test 4's record line named the fix by its internal name: now its plain name (`runs.py` `FIX_NAME`).
- Step 7's local build showed the training pair's seed name, an internal name: now "drawn by a stored seed", the seed in
  the tooltip.
- The test's check for internal names now also catches plain `lora`.
- Step 4's total overlapped its label (box widened).
- Step 7's "kept" note waited for every point's delay (capped).
- In compare, "took the hint's letter?" ran into the next mark: shorter labels in the two-column view.

**Correction to the 16:44 log** (§1, the page): test 6 has **10** per-question cut rows, not 12. The 12 was the count
before the switch to the analysis's `per_cut` rows, the same session; the page has had 10 since.

**After the freeze (Nov 23, 08:31): presentation work only.** No number, figure or verdict changed. The new figures (the
GPU total, the training curves) are records from Sol, shown as such; where they overlap a frozen number they agree.

**Screenshots** (`cot-disclosure/results/demo/screens_sol/`, gitignored; 26 at 1920×1080, both themes, no console
error):
- the bench, tests 1, 3 and 4, each after a run, a compare and "Run 20 more";
- step 4;
- step 7 in three views: LoRA, 3 layers, consistency.

Looked at: tests 3 and 4 after a run; four bench states tiled; steps 4 and 7 cropped, all views.

## 2. Waiting for Ritik

- Look at the page (`cot-disclosure/results/demo/demo.html`; the tracked `docs/demo/index.html` carries the total and
  the curves, not run text).
- As before: the four files and the final check; Gate 3's approval; the contributions; the AI-use lines and
  `AI_USE.md`; the rehearsal today; the presentation and report Nov 24.

## 3. Checks and push

- The demo's tests, the method tests, the explainer's tour, hygiene and links: **182 passed**. This includes the new
  test that the Sol copy is complete and agrees with the frozen numbers. The internal-name check failed on the old
  build and passed after the fixes.
- `tools/check_links.py`: 0 broken links. `tools/make_supplement.py --check` and `tools/export_summaries.py --check`:
  pass.
- No account name, email or scratch path in the tracked files (grep).
- STATUS and the Gantt regenerated; the pre-push check.
- The push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
