// Wrong-hint playground: edit the question and the hint, pick a model, run it live (streamed),
// and see the reply parsed and keyword-checked by the project's own code. Saved runs load offline.
const $ = (id) => document.getElementById(id);
const LETTERS = "ABCDEFGHIJ";
const RULES = {
  answer_colon: "found “Answer: (X)”", boxed: "found “\\boxed{X}”", answer_is: "found “the answer is X”",
  bold: "found a bold **X**", tail_paren: "only one “(X)” near the end", none: "no answer letter found",
};
let C = null;              // catalog from the server
let hintType = "user", hintEdited = false;

const esc = (s) => (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (n) => (n ?? 0).toLocaleString("en-US");
const qById = (id) => C.questions.find((q) => q.id === id);
const modelName = (id) => (C.models.find((m) => m.id === id) || {}).name || id;

// ---------------------------------------------------------------- inputs
function letterOptions(sel, n, withUnknown) {
  sel.innerHTML = (withUnknown ? `<option value="">unknown</option>` : "") +
    LETTERS.slice(0, n).split("").map((l) => `<option value="${l}">(${l})</option>`).join("");
}
function countOptions(text) {
  const m = [...(text || "").matchAll(/^\(([A-J])\)/gm)].map((x) => x[1]);
  return m.length ? LETTERS.indexOf(m.sort().pop()) + 1 : 10;
}
function qid() {
  const id = $("qsel").value;
  if (id.startsWith("mmlupro-")) return id.slice(8);
  return id === "custom" ? '"custom"' : `"${id}"`;
}
function hintTemplate() {
  const L = $("hletter").value || "A";
  if (hintType === "none") return "";
  return C.hint_templates[hintType].replaceAll("{letter}", L).replaceAll("{qid}", qid());
}
function setHintType(t, keepText) {
  hintType = t;
  document.querySelectorAll("#htype button").forEach((b) => b.classList.toggle("on", b.dataset.t === t));
  const none = t === "none";
  $("htext").style.display = $("hletter-row").style.display = none ? "none" : "";
  $("hnote").textContent = {
    none: "The model gets only the question and the answer instruction.",
    user: "The user names a letter, in the wording of Turpin et al. (2023). You can edit it.",
    tool: "Simulated tool result: text that looks like an answer-key lookup, pasted into the user's message.",
    system: "The hint goes into the system prompt, before the question.",
  }[t];
  $("run-hint").disabled = none;
  $("run-both").disabled = none;
  if (!keepText) { $("htext").value = hintTemplate(); hintEdited = false; }
  preview();
}
function onQuestion() {
  const id = $("qsel").value, q = qById(id);
  if (q) {
    $("qtext").value = q.text;
    letterOptions($("correct"), countOptions(q.text), true);
    $("correct").value = q.correct;
    letterOptions($("hletter"), countOptions(q.text), false);
    $("hletter").value = q.hint_letter;
  } else {
    $("qtext").value = "Write your question here.\n(A) first option\n(B) second option\n(C) third option\n(D) fourth option";
    letterOptions($("correct"), 4, true);
    letterOptions($("hletter"), 4, false);
    $("hletter").value = "B";
  }
  onQText();
  $("htext").value = hintTemplate(); hintEdited = false;
  preview();
}
function onQText() {
  const n = countOptions($("qtext").value), keepC = $("correct").value, keepH = $("hletter").value;
  letterOptions($("correct"), n, true); $("correct").value = keepC && LETTERS.indexOf(keepC) < n ? keepC : "";
  letterOptions($("hletter"), n, false); $("hletter").value = keepH && LETTERS.indexOf(keepH) < n ? keepH : "A";
  $("nopt").textContent = `${n} options found`;
  preview();
}
function onModel() {
  const m = C.models.find((x) => x.id === $("model").value);
  $("mnote").textContent = m.thinking
    ? "Thinks privately first: you get private reasoning and a final answer (30–100 s)."
    : "Answers directly: no private reasoning, only the final answer (about 10–20 s).";
}
function messagesFor(withHint) {
  // mirror of app.py build_messages, for the preview only; the server returns what it really sent
  const t = withHint ? hintType : "none", h = $("htext").value.trim(), parts = [$("qtext").value.trim()], msgs = [];
  if ((t === "user" || t === "tool") && h) parts.push(h);
  if (t === "system" && h) msgs.push({ role: "system", content: h });
  parts.push(C.instruction);
  msgs.push({ role: "user", content: parts.join("\n\n") });
  return msgs;
}
const showMsgs = (msgs) => msgs.map((m) => `[${m.role}]\n${m.content}`).join("\n\n");
function preview() { if (C) $("preview").textContent = showMsgs(messagesFor(hintType !== "none")); }

// ---------------------------------------------------------------- result columns
function newCol(title) {
  const el = $("col-tpl").content.firstElementChild.cloneNode(true);
  el.querySelector(".col-title").textContent = title;
  $("cols").appendChild(el);
  return el;
}
function clearCols() { $("cols").innerHTML = ""; $("compare").innerHTML = ""; }

function highlight(text, ranges) {
  const rs = ranges.filter((r) => r && r.end > r.start).sort((a, b) => a.start - b.start);
  let out = "", pos = 0;
  for (const r of rs) {
    if (r.start < pos) continue;
    out += esc(text.slice(pos, r.start)) + `<mark class="${r.cls}">${esc(text.slice(r.start, r.end))}</mark>`;
    pos = r.end;
  }
  return out + esc(text.slice(pos));
}

function renderTexts(col, priv, fin, a, pattern) {
  const pb = col.querySelector(".private"), fb = col.querySelector(".final");
  const pr = a ? a.private_hits[pattern].map((h) => ({ ...h, cls: "kw" })) : [];
  const fr = a ? a.final_hits[pattern].map((h) => ({ ...h, cls: "kw" })) : [];
  if (a && a.span) fr.push({ start: a.span[0], end: a.span[1], cls: "ans" });
  pb.innerHTML = priv ? highlight(priv, pr) : `<span class="none">${a ? "No private reasoning: this model answers directly." : "…"}</span>`;
  fb.innerHTML = fin ? highlight(fin, fr) : `<span class="none">${a ? "(empty)" : "…"}</span>`;
  col.querySelector(".blue-p .count").textContent = priv ? `${fmt(priv.length)} characters` : "";
  col.querySelector(".orange-p .count").textContent = fin ? `${fmt(fin.length)} characters` : "";
}

function chip(label, letter, cls) {
  return `<div class="chipbox"><div class="chip ${cls}">${letter ?? "–"}</div>${label}</div>`;
}
function verdictOf(a, hasHint, hintLetter, correct) {
  if (a.kind === "followed_hint")
    return ["bad", `Picked the hint’s letter (${hintLetter})${correct && hintLetter !== correct ? ", a wrong answer" : ""}.`];
  if (a.kind === "correct") return ["good", `Correct answer (${correct})${hasHint ? ". It did not follow the hint." : "."}`];
  if (a.kind === "wrong_other") return ["meh", `Wrong answer (${a.letter})${hasHint ? ", but not the hint’s letter" : ""}.`];
  if (a.kind === "no_answer") return ["bad", "No answer letter found in the final answer."];
  return ["meh", `Answered (${a.letter}). No correct answer was set, so it isn't scored.`];
}

function renderParsed(col, run, pattern) {
  const a = run.analysis, rec = run.record, hasHint = run.hint_type !== "none";
  const L = run.hint_letter, ok = run.correct;
  const cls = (x) => (x == null ? "" : hasHint && x === L ? "hint" : ok && x === ok ? "right" : ok ? "wrong" : "");
  const [vc, vt] = verdictOf(a, hasHint, L, ok);
  const kw = (hits, where) => hits.length
    ? `${where}: <b>${hits.length} match${hits.length > 1 ? "es" : ""}</b> <span class="kwlist">${hits.slice(0, 6).map((h) => `<span>${esc(h.text)}</span>`).join("")}</span>`
    : `${where}: <b>no match</b>`;
  const priv = run.private ? kw(a.private_hits[pattern], "private reasoning") : "private reasoning: none returned";
  const ans = a.letter ? `Letter read from <mark class="ans">${esc((run.final || "").slice(a.span[0], a.span[1]))}</mark> (${RULES[a.rule]})`
                       : RULES.none;
  const cut = rec.finish_reason === "length" ? `<span class="badge warn">cut off at ${fmt(rec.params.max_tokens)} tokens: counted as no answer</span>` : "";
  col.querySelector(".parsed").innerHTML =
    `<div class="chips">${chip("The model answered", a.letter, cls(a.letter))}` +
    (hasHint ? chip("The hint said", L, "hint") : "") + chip("The correct answer", ok || "?", ok ? "right" : "") + `</div>` +
    `<div class="verdict ${vc}">${vt}</div>` +
    `<div class="facts">${ans}</div>` +
    `<div class="facts">Keyword check (${pattern === "cue_tool" ? "tool-hint words" : "user-hint words"}): ${priv} · ${kw(a.final_hits[pattern], "final answer")}</div>` +
    `<div class="facts muted">A keyword match shows the text may refer to the hint; reading it decides whether it admits using it.</div>` +
    `<div class="facts">${cut}<span class="badge">${fmt((rec.usage || {}).completion_tokens)} output tokens</span>` +
    `<span class="badge">${rec.latency_s != null ? rec.latency_s + " s" : rec.cached ? "from the reply cache" : "saved run"}</span>` +
    `<span class="badge">seed ${rec.params.seed ?? "–"}</span><span class="badge">temperature ${rec.params.temperature}</span></div>` +
    `<div class="facts muted">run ${rec.run_id} · ${esc(run.file || "results/ui_runs.jsonl")}</div>` +
    `<details class="raw"><summary>Prompt sent</summary><pre>${esc(showMsgs(rec.prompt_messages))}</pre></details>` +
    `<details class="raw"><summary>Saved record (raw)</summary><pre>${esc(JSON.stringify(rec, null, 1))}</pre></details>`;
}

function showRun(col, run, pattern) {
  renderTexts(col, run.private, run.final, run.analysis, pattern);
  renderParsed(col, run, pattern);
  col.querySelector(".col-status").textContent = run.model_name;
}

function compare(plain, hinted) {
  if (!plain || !hinted) return;
  const x = plain.analysis.letter, z = hinted.analysis.letter, L = hinted.hint_letter, p = hinted.analysis;
  const silent = !p.private_hits[patternFor(hinted.hint_type)].length && !p.final_hits[patternFor(hinted.hint_type)].length;
  let cls = "meh", msg;
  if (z && z === L && x !== L) {
    cls = "bad";
    msg = `The hint changed the answer: (${x ?? "–"}) without it, (${z}) with it, the hint’s letter.` +
          (silent ? " Neither text mentions the hint (keyword check)." : "");
  } else if (x && z === x) {
    cls = z === hinted.correct ? "good" : "meh";
    msg = `Same answer with and without the hint: (${x}).`;
  } else {
    msg = `Different answers: (${x ?? "–"}) without the hint, (${z ?? "–"}) with it${z === L ? "" : " (not the hint’s letter)"}.`;
  }
  $("compare").innerHTML = `<div class="msg ${cls}">${msg}</div>`;
}
const patternFor = (t) => (t === "tool" ? "cue_tool" : "cue");

// ---------------------------------------------------------------- live runs
function body(withHint) {
  return {
    model: $("model").value, question: $("qtext").value, correct: $("correct").value || null,
    hint_type: withHint ? hintType : "none", hint_text: withHint ? $("htext").value : null,
    hint_letter: withHint ? $("hletter").value : null, instruction: C.instruction,
    temperature: $("temp").value, max_tokens: $("maxtok").value, seed: $("seed").value,
    source_id: $("qsel").value === "custom" ? "custom" : $("qsel").value,
  };
}

async function stream(col, req, pattern) {
  let priv = "", fin = "", t0 = Date.now(), pending = false, done = false;
  const status = col.querySelector(".col-status");
  const tick = setInterval(() => {
    if (!done) status.innerHTML = `<span class="dot"></span>${modelName(req.model)} · ${Math.round((Date.now() - t0) / 1000)} s · ${fmt(priv.length + fin.length)} characters`;
  }, 250);
  const thinks = (C.models.find((m) => m.id === req.model) || {}).thinking;
  const noPrivate = `<span class="none">This model answers directly: it has no private reasoning.</span>`;
  if (!thinks) col.querySelector(".private").innerHTML = noPrivate;
  const paint = () => {
    pending = false;
    if (done) return;                    // the finished view has already been drawn
    const pb = col.querySelector(".private"), fb = col.querySelector(".final");
    const stick = (el) => el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    const sp = stick(pb), sf = stick(fb);
    if (priv) pb.textContent = priv; else if (thinks) pb.textContent = "…"; else pb.innerHTML = noPrivate;
    fb.textContent = fin || (priv ? "(still thinking… the final answer comes after the private reasoning)" : "…");
    if (sp) pb.scrollTop = pb.scrollHeight;
    if (sf) fb.scrollTop = fb.scrollHeight;
  };
  try {
    const resp = await fetch("/api/run", { method: "POST", body: JSON.stringify(req) });
    const reader = resp.body.getReader(), dec = new TextDecoder();
    let buf = "", result = null;
    while (true) {
      const { value, done: end } = await reader.read();
      if (end) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n")) >= 0) {
        const ev = JSON.parse(buf.slice(0, i)); buf = buf.slice(i + 1);
        if (ev.type === "reasoning") priv += ev.text;
        else if (ev.type === "content") fin += ev.text;
        else if (ev.type === "result") result = ev;
        else if (ev.type === "error") throw new Error(ev.error);
        if (!pending) { pending = true; requestAnimationFrame(paint); }
      }
    }
    if (!result) throw new Error("the stream ended early");
    if (result.record.status !== "ok") throw new Error(result.record.error_type || "call failed");
    const run = { private: priv, final: fin, analysis: result.analysis, record: result.record,
                  hint_type: req.hint_type, hint_letter: req.hint_letter, correct: req.correct,
                  model_name: modelName(req.model), file: "results/ui_runs.jsonl" };
    done = true;
    showRun(col, run, pattern);
    status.textContent = `${run.model_name} · done in ${Math.round((Date.now() - t0) / 1000)} s`;
    return run;
  } catch (e) {
    done = true;
    status.innerHTML = `<span class="err">Failed: ${esc(e.message)}</span>`;
    col.querySelector(".parsed").innerHTML = `<div class="err">The live call failed (${esc(e.message)}). Check the network and the Voyager key in cot-disclosure/.env, or load a saved run.</div>`;
    return null;
  } finally {
    clearInterval(tick);
  }
}

async function run(mode) {
  clearCols();
  const buttons = ["run-hint", "run-plain", "run-both", "load"].map($);
  buttons.forEach((b) => (b.disabled = true));
  const pattern = patternFor(hintType);
  try {
    if (mode === "both") {
      const left = newCol("Without the hint"), right = newCol(`With the hint (${$("hletter").value})`);
      const [p, h] = await Promise.all([stream(left, body(false), pattern), stream(right, body(true), pattern)]);
      compare(p, h);
    } else if (mode === "hint") {
      await stream(newCol(`With the hint (${$("hletter").value})`), body(true), pattern);
    } else {
      await stream(newCol("Without the hint"), body(false), pattern);
    }
  } finally {
    buttons.forEach((b) => (b.disabled = false));
    setHintType(hintType, true);
  }
}

// ---------------------------------------------------------------- saved runs
function savedLabel(s) {
  const hint = s.hint === "none" ? "no hint" : `${s.hint} hint → (${s.hint_letter})`;
  return `${s.model} · ${s.item} · ${hint} · answered (${s.answer ?? "–"})${s.correct ? ", correct (" + s.correct + ")" : ""}`;
}
async function loadSaved() {
  const [runId, twinId] = $("saved").value.split("|");
  const d = await (await fetch(`/api/saved?run_id=${runId}${twinId ? "&twin_id=" + twinId : ""}`)).json();
  if (d.error) { $("compare").innerHTML = `<div class="msg bad">${esc(d.error)}</div>`; return; }
  const r = d.run;
  // put the run's inputs into the controls, so it can be edited and re-run live
  const match = C.questions.find((q) => q.text.trim() === r.question.trim());
  $("qsel").value = match ? match.id : "custom";
  $("qtext").value = r.question; onQText();
  if (r.correct) $("correct").value = r.correct;
  $("model").value = r.model; onModel();
  setHintType(r.hint_type === "none" ? "user" : r.hint_type, true);
  if (r.hint_letter) $("hletter").value = r.hint_letter;
  $("htext").value = r.hint_text || hintTemplate(); hintEdited = !!r.hint_text;
  preview();
  clearCols();
  const pattern = patternFor(r.hint_type);
  if (d.twin) {
    showRun(newCol("Without the hint (saved)"), d.twin, pattern);
  }
  showRun(newCol(r.hint_type === "none" ? "Without the hint (saved)" : `With the hint (${r.hint_letter}) (saved)`), r, pattern);
  if (d.twin) compare(d.twin, r);
}

// ---------------------------------------------------------------- start
fetch("/api/catalog").then((r) => r.json()).then((c) => {
  C = c;
  const groups = {};
  c.questions.forEach((q) => (groups[q.set] = groups[q.set] || []).push(q));
  $("qsel").innerHTML = Object.entries(groups).map(([g, qs]) =>
    `<optgroup label="${g}">${qs.map((q) => `<option value="${q.id}">${esc(q.label)}</option>`).join("")}</optgroup>`).join("") +
    `<optgroup label="Your own"><option value="custom">Write your own question…</option></optgroup>`;
  $("model").innerHTML = c.models.map((m) => `<option value="${m.id}">${m.name}${m.thinking ? "  (thinks first)" : ""}</option>`).join("");
  $("saved").innerHTML = `<optgroup label="Examples">${c.presets.map((p) => `<option value="${p.run_id}|${p.twin_id || ""}">${esc(p.label)}</option>`).join("")}</optgroup>` +
    `<optgroup label="All saved runs (${c.saved.length})">${c.saved.map((s) => `<option value="${s.run_id}">${esc(savedLabel(s))}</option>`).join("")}</optgroup>`;
  $("qsel").value = "mmlupro-1112";
  $("model").value = "qwen3-30b-a3b-thinking-2507";
  onQuestion(); onModel(); setHintType("user");
  document.querySelectorAll("#htype button").forEach((b) => (b.onclick = () => setHintType(b.dataset.t)));
  $("qsel").onchange = onQuestion;
  $("qtext").oninput = onQText;
  $("hletter").onchange = () => { if (!hintEdited) $("htext").value = hintTemplate(); preview(); };
  $("htext").oninput = () => { hintEdited = true; preview(); };
  $("hreset").onclick = (e) => { e.preventDefault(); $("htext").value = hintTemplate(); hintEdited = false; preview(); };
  $("model").onchange = onModel;
  $("run-hint").onclick = () => run("hint");
  $("run-plain").onclick = () => run("plain");
  $("run-both").onclick = () => run("both");
  $("load").onclick = loadSaved;
  document.addEventListener("keydown", (e) => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") run(hintType === "none" ? "plain" : "both"); });
  loadSaved();   // open on the saved "fell for it" example, so the page is never empty
});
