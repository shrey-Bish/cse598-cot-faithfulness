// Wrong-hint demo v2: the examples from the progress presentation, with exactly the runs it
// counted (Test 2: 2 without a hint, 1 user hint, 1 tool hint; Test 1: 3 without, 2 wrong hint,
// 1 right hint). "Rerun live" makes a fresh set of the same runs, shown on its own; clicking an
// example always brings back its original runs.
const $ = (id) => document.getElementById(id);
const LETTERS = "ABCDEFGHIJ";
const TITLE = { none: "Without a hint", user: "With the user hint", tool: "With the tool hint",
                wrong: "With a wrong hint", right: "With the right hint" };
let D = null, ex = null, mode = "original", groups = [], sel = { base: null, hint: null }, gen = 0;
const views = {}, cols = {};

const esc = (s) => (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (n) => (n ?? 0).toLocaleString("en-US");
const pat = (t) => (t === "tool" ? "cue_tool" : "cue");
const runOf = (key) => { for (const g of groups) for (const r of g.runs) if (r.key === key) return [r, g]; return [null, null]; };
const done = (r) => !r.wait && !r.error;

// ---------------------------------------------------------------- example
function selectExample(id) {
  gen++;
  ex = D.examples.find((e) => e.id === id);
  mode = "original";
  groups = ex.groups.map((g) => ({ ...g, runs: g.runs.map((r) => ({ ...r })) }));
  const none = groups.find((g) => g.key === "none").runs;
  sel.base = (none.find((r) => r.has_text) || none[0]).key;
  sel.hint = runOf(groups.flatMap((g) => g.runs).find((r) => r.run_id === ex.featured).key)[0].key;
  document.querySelectorAll(".exbtn").forEach((b) => b.classList.toggle("on", b.dataset.id === id));
  renderAll();
}
function hintText(run) {
  if (!run || run.hint_type === "none") return null;
  if (run.messages[0].role === "system") return run.messages[0].content;
  const parts = run.messages[run.messages.length - 1].content.split("\n\n");
  return parts.slice(1, -1).join("\n\n");
}
function renderSide() {
  const [h, hg] = runOf(sel.hint);
  const H = h && h.hint_letter, C = ex.correct;
  $("test-label").textContent = ex.test_label;
  $("qview").innerHTML = ex.question.split("\n").map((line) => {
    const m = line.match(/^\(([A-J])\)/);
    if (!m) return `<div>${esc(line) || "&nbsp;"}</div>`;
    return `<div class="opt ${m[1] === C ? "right" : m[1] === H ? "hinted" : ""}">${esc(line)}</div>`;
  }).join("");
  $("hint-label").textContent = hg ? `${hg.label} → (${H})` : "Hint";
  $("hview").textContent = hintText(h) || "No hint";
  $("model-name").textContent = ex.model_name;
  const n = groups.reduce((a, g) => a + g.runs.length, 0);
  $("rerun").textContent = `▶ Rerun live (${n} runs)`;
  $("original").classList.toggle("hidden", mode !== "rerun");
}

// ---------------------------------------------------------------- the runs, one row per condition
function chipClass(r, g) {
  if (r.wait) return "wait";
  if (r.cut) return "cut";
  const cls = g.key !== "none" && g.key !== "right" && r.letter && r.letter === r.hint_letter ? "hint"
            : r.letter && r.letter === ex.correct ? "right" : "";
  return cls + (r.has_text ? "" : " notext") + (r.live ? " live" : "");
}
function renderGroups() {
  const counts = groups.map((g) => `${g.runs.length} ${g.key === "none" ? "without a hint" : g.label.toLowerCase()}`).join(", ");
  const anyNoText = groups.some((g) => g.runs.some((r) => !r.has_text));
  $("ghead").innerHTML = mode === "original"
    ? `<b>The presentation's runs</b> · Test ${ex.test}: ${counts}` + (anyNoText ? " · dashed = Test 1 saved only the letter" : "")
    : `<b>Live rerun</b> · same prompts, new runs (${counts}) · not added to the example`;
  let html = "";
  for (const g of groups) {
    const hl = [...new Set(g.runs.map((r) => r.hint_letter).filter(Boolean))].map((l) => `(${l})`).join(", ");
    html += `<div class="grow"><div class="glabel">${esc(g.label)}${hl ? ` → ${hl}` : ""}
             <span class="n">· ${g.runs.length} run${g.runs.length > 1 ? "s" : ""}</span></div><div class="gchips">`;
    for (const r of g.runs) {
      if (r.error) { html += `<span class="rchip" title="${esc(r.error)}">!</span>`; continue; }
      const txt = r.wait ? "…" : r.cut ? "✂" : r.letter || "–";
      const isSel = r.key === sel.base || r.key === sel.hint;
      html += `<div class="rchip ${chipClass(r, g)}${isSel ? " sel" : ""}" data-key="${r.key}"
               title="${r.run_id ? "run " + r.run_id : r.wait ? "running" : "letter only"}${r.seed != null ? " · seed " + r.seed : ""}">${txt}</div>`;
    }
    html += `</div></div>`;
  }
  $("groups").innerHTML = html;
  $("groups").querySelectorAll(".rchip[data-key]").forEach((el) => (el.onclick = () => {
    const [r, g] = runOf(el.dataset.key);
    if (!r || r.wait) return;
    if (g.key === "none") sel.base = r.key; else sel.hint = r.key;
    renderGroups(); renderSide(); showRun(g.key === "none" ? "base" : "hint"); banner();
  }));
}

// ---------------------------------------------------------------- one run per column
function initCol(name) {
  const el = $(`col-${name}`);
  el.appendChild($("col-tpl").content.cloneNode(true));
  const q = (s) => el.querySelector(s);
  cols[name] = { el, title: q(".col-title"), status: q(".col-status"), blue: q(".blue-p"), priv: q(".private"),
                 privN: q(".blue-p .count"), orange: q(".orange-p"), fin: q(".final"), finN: q(".orange-p .count"),
                 parsed: q(".parsed") };
}
function highlight(text, ranges) {
  let out = "", pos = 0;
  for (const r of ranges.filter((r) => r && r.end > r.start).sort((a, b) => a.start - b.start)) {
    if (r.start < pos) continue;
    out += esc(text.slice(pos, r.start)) + `<mark class="${r.cls}">${esc(text.slice(r.start, r.end))}</mark>`;
    pos = r.end;
  }
  return out + esc(text.slice(pos));
}
function verdictHtml(r, g) {
  const L = r.letter, H = r.hint_letter, C = ex.correct, hinted = g.key !== "none";
  const chip = (txt, cls, label) => `<div class="chipbox"><div class="chip ${cls}">${txt}</div>${label}</div>`;
  const lcls = !L ? "" : hinted && g.key !== "right" && L === H ? "hint" : L === C ? "right" : "wrong";
  let html = `<div class="chips">${chip(r.cut ? "✂" : L || "–", lcls, "The model answered")}` +
    (hinted ? chip(H, H === C ? "right" : "hint", "The hint said") : "") + chip(C, "right", "The correct answer") + "</div>";
  let vcls = "meh", vtxt;
  if (r.cut) vtxt = "Cut off at the token limit: counts as no answer.";
  else if (!L) vtxt = "No answer letter found.";
  else if (hinted && g.key !== "right" && L === H) { vcls = "bad"; vtxt = `Picked the hint’s letter (${L}), a wrong answer.`; }
  else if (L === C) { vcls = "good"; vtxt = `Correct answer (${L}).`; }
  else { vcls = "bad"; vtxt = `Wrong answer (${L})` + (hinted ? ", not the hint’s letter." : "."); }
  html += `<div class="verdict ${vcls}">${vtxt}</div>`;
  if (hinted) {
    const n = (k) => (k ? `<b>${k} keyword match${k > 1 ? "es" : ""}</b>` : "<b>none</b>");
    html += `<div class="facts">Mentions the hint: ` + (r.has_private ? `private reasoning ${n(r.private_mentions)} · ` : "") +
            `final answer ${n(r.final_mentions)}</div>`;
  }
  return html;
}
function details(r, rec) {
  const prm = (rec && rec.params) || {}, u = (rec && rec.usage) || {};
  const head = rec ? `run ${rec.run_id} · seed ${prm.seed ?? "–"} · temperature ${prm.temperature ?? "–"} · ` +
                     `${fmt(u.completion_tokens)} output tokens · ${rec.latency_s ?? "–"} s · ${r.file || "results/ui_runs.jsonl"}`
                   : `Test 1 run · seed ${r.seed} · temperature ${r.temperature} · ${fmt(r.out_tokens)} output tokens · results/progress.jsonl`;
  const msgs = (rec ? rec.prompt_messages : r.messages).map((m) => `[${m.role}]\n${m.content}`).join("\n\n");
  return `<details class="raw"><summary>Run details and prompt sent</summary><pre>` +
    esc(head + "\n\n" + msgs + (rec ? "\n\n---- saved record ----\n" + JSON.stringify(rec, null, 1) : "")) + `</pre></details>`;
}
async function showRun(which) {
  const [r, g] = runOf(sel[which]), c = cols[which], myGen = gen;
  if (!r) return;
  c.title.innerHTML = g.key === "none" ? TITLE.none : `${TITLE[g.key]} <span class="pink">(${esc(r.hint_letter)})</span>`;
  if (r.wait) return;                                   // a live run streams into its column itself
  if (!r.has_text) {
    c.status.textContent = `${ex.model_name} · Test 1 · letter only`;
    c.blue.classList.add("hidden"); c.orange.classList.add("hidden");
    c.parsed.innerHTML = `<div class="letteronly"><p><b>Test 1 saved only the letter and the keyword flags for this run,
      not its text</b> (results/progress.jsonl).</p>` +
      (r.has_private ? `<p>Private reasoning: ${fmt(r.private_chars)} characters · mentions the hint: <b>${r.private_mentions ? "yes" : "no"}</b></p>` : "") +
      `<p>Final answer: ${fmt(r.final_chars)} characters` + (g.key !== "none" ? ` · mentions the hint: <b>${r.final_mentions ? "yes" : "no"}</b>` : "") +
      `</p></div>` + verdictHtml(r, g) + details(r, null);
    return;
  }
  let v = r.view || views[r.run_id];
  if (!v) {
    v = await (await fetch(`/api/record?run_id=${r.run_id}&strict=1`)).json();
    views[r.run_id] = v;
  }
  if (myGen !== gen || sel[which] !== r.key) return;
  paintView(which, r, g, v);
}
function paintView(which, r, g, v) {
  const c = cols[which], a = v.analysis, rec = v.record, p = pat(r.hint_type), hinted = g.key !== "none";
  c.status.textContent = `${ex.model_name} · ${r.live ? "live" : "saved"}` + (rec.latency_s ? ` · ${Math.round(rec.latency_s)} s` : "");
  const priv = v.private || "";
  c.blue.classList.toggle("hidden", !priv); c.orange.classList.remove("hidden");
  c.priv.innerHTML = highlight(priv, hinted ? a.private_hits[p].map((h) => ({ ...h, cls: "kw" })) : []);
  c.privN.textContent = `${fmt(priv.length)} characters`;
  const fin = v.final || "", lead = fin.length - fin.trimStart().length;
  const fr = hinted ? a.final_hits[p].map((h) => ({ ...h, cls: "kw" })) : [];
  if (a.span) fr.push({ start: a.span[0], end: a.span[1], cls: "ans" });
  c.fin.innerHTML = fin ? highlight(fin.slice(lead), fr.map((x) => ({ ...x, start: x.start - lead, end: x.end - lead })))
                        : `<span class="none">(empty)</span>`;
  c.finN.textContent = `${fmt(fin.length)} characters`;
  c.fin.style.maxHeight = priv ? "" : "40vh";
  const kw = c.priv.querySelector("mark.kw");               // open the reasoning at its first mention of the hint
  c.priv.scrollTop = kw ? Math.max(0, kw.offsetTop - 40) : 0;
  c.fin.scrollTop = a.span && a.span[0] > fin.length / 2 ? 1e9 : 0;
  c.parsed.innerHTML = verdictHtml(r, g) +
    (a.span ? `<div class="facts">Letter read from <mark class="ans">${esc(fin.slice(a.span[0], a.span[1]))}</mark></div>` : "") +
    details(r, rec);
}

// ---------------------------------------------------------------- banner
function banner() {
  const box = $("compare");
  const [w, wg] = runOf(sel.hint), [o] = runOf(sel.base);
  if (!w || !done(w)) { box.innerHTML = mode === "rerun" ? `<div class="msg live">Live rerun in progress…</div>` : ""; return; }
  const H = w.hint_letter, wl = w.letter, ol = o && done(o) ? o.letter : null;
  const it = w.hint_type === "tool" ? "the tool result" : "the hint";
  const said = !w.has_private ? (w.final_mentions ? `The answer mentions ${it}.` : `The answer doesn’t mention ${it}.`)
             : !w.private_mentions && !w.final_mentions ? `Neither text mentions ${it}.`
             : !w.final_mentions ? `The final answer never mentions ${it}; only the private reasoning does.`
             : `The final answer mentions ${it}.`;
  let cls = "meh", txt;
  if (wg.key === "right") txt = `The hint pointed to the right answer (${H}); it answered ` + (wl ? `(${wl}).` : "nothing.");
  else if (!wl) txt = w.cut ? "The run with the hint was cut off at the token limit: no answer." : "No answer letter found.";
  else if (wl === H && ol && ol !== H) { cls = "bad"; txt = `The hint changed the answer: (${ol}) without it, (${H}) with it. ${said}`; }
  else if (wl === H && ol === H) txt = `(${H}) with and without the hint.`;
  else if (wl === H) { cls = "bad"; txt = `Picked the hint’s (${H}). ${said}`; }
  else { cls = "good"; txt = `Not fooled: (${wl}) with the hint` + (ol ? (ol === wl ? ", the same as without it." : `, (${ol}) without it.`) : ".")
         + (w.private_mentions || w.final_mentions ? ` It mentions ${it}.` : ""); }
  const hintLetters = new Set(groups.filter((g) => g.key !== "none" && g.key !== "right").flatMap((g) => g.runs.map((r) => r.hint_letter)));
  const parts = groups.filter((g) => g.key !== "right").map((g) => {
    const rs = g.runs.filter(done);
    const k = g.key === "none" ? rs.filter((r) => hintLetters.has(r.letter)).length : rs.filter((r) => r.letter === r.hint_letter).length;
    return `${g.key === "none" ? "without a hint" : g.label.toLowerCase()} ${k} of ${rs.length}`;
  });
  const all = `${mode === "original" ? "In the presentation's runs" : "In this rerun"}, picked the hint’s letter: ${parts.join(" · ")}`;
  box.innerHTML = `<div class="msg ${cls}">${esc(txt)}<span class="all">${esc(all)}</span></div>`;
}
function renderAll() { renderSide(); renderGroups(); showRun("base"); showRun("hint"); banner(); }

// ---------------------------------------------------------------- live rerun (never added to the example)
async function liveRun(r, g, myGen) {
  const which = g.key === "none" ? "base" : "hint", c = cols[which], streaming = () => myGen === gen && sel[which] === r.key;
  const req = { model: ex.model, messages: r.messages, hint_type: r.hint_type, hint_letter: r.hint_letter,
                correct: ex.correct, temperature: r.temperature, max_tokens: r.max_tokens, seed: "",
                source_id: `v2:${ex.id}:${r.key}`, experiment: "ui_v2_rerun", strict: true };
  let priv = "", fin = "", result = null;
  const t0 = Date.now();
  const tick = setInterval(() => { if (streaming()) c.status.innerHTML = `<span class="dot"></span>live · ${Math.round((Date.now() - t0) / 1000)} s`; }, 250);
  if (streaming()) {
    c.blue.classList.toggle("hidden", !ex.thinking); c.orange.classList.remove("hidden");
    c.priv.textContent = ""; c.fin.textContent = ""; c.privN.textContent = ""; c.finN.textContent = "";
    c.parsed.innerHTML = `<div class="facts" style="color:var(--grey)">Asking ${esc(ex.model_name)}…</div>`;
  }
  try {
    const resp = await fetch("/api/run", { method: "POST", body: JSON.stringify(req) });
    const reader = resp.body.getReader(), dec = new TextDecoder();
    let buf = "";
    for (;;) {
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
      }
      if (streaming()) {
        if (priv) { c.blue.classList.remove("hidden"); c.priv.textContent = priv; c.priv.scrollTop = 1e9; c.privN.textContent = `${fmt(priv.length)} characters`; }
        c.fin.textContent = fin; c.fin.scrollTop = 1e9; c.finN.textContent = fin ? `${fmt(fin.length)} characters` : "";
      }
    }
    if (!result || result.record.status !== "ok") throw new Error((result && result.record.error_type) || "the call failed");
    const a = result.analysis, rec = result.record, p = pat(r.hint_type);
    Object.assign(r, { wait: false, run_id: rec.run_id, letter: a.letter, cut: a.cut_off, has_private: !!priv,
                       private_mentions: a.private_hits[p].length, final_mentions: a.final_hits[p].length,
                       seed: rec.params.seed, view: { private: priv, final: fin, analysis: a, record: rec } });
  } catch (e) {
    Object.assign(r, { wait: false, error: e.message });
    if (streaming()) c.parsed.innerHTML = `<span class="err">Live call failed (${esc(e.message)}).</span>`;
  } finally {
    clearInterval(tick);
  }
  if (myGen !== gen) return;
  renderGroups();
  if (sel[which] === r.key && !r.error) paintView(which, r, g, r.view);
  banner();
}
function rerun() {
  const myGen = ++gen;
  mode = "rerun";
  groups = ex.groups.map((g) => ({ ...g, runs: g.runs.map((r) => ({
    key: r.key, hint_type: r.hint_type, hint_letter: r.hint_letter, messages: r.messages, temperature: r.temperature,
    max_tokens: r.max_tokens, has_text: true, live: true, wait: true })) }));
  sel.base = groups.find((g) => g.key === "none").runs[0].key;   // sel.hint keeps the same slot as the original
  renderAll();
  $("rerun").disabled = true;
  Promise.all(groups.flatMap((g) => g.runs.map((r) => liveRun(r, g, myGen)))).then(() => { if (myGen === gen) $("rerun").disabled = false; });
}

// ---------------------------------------------------------------- start
fetch("/api/v2/examples").then((r) => r.json()).then((d) => {
  D = d;
  ["base", "hint"].forEach(initCol);
  $("exlist").innerHTML = d.examples.map((e) =>
    `<button class="exbtn" data-id="${e.id}"><span class="t">${esc(e.title)}</span>` +
    `<span class="m">${esc(e.model_name)} · Test ${e.test}</span></button>`).join("");
  document.querySelectorAll(".exbtn").forEach((b) => (b.onclick = () => { $("rerun").disabled = false; selectExample(b.dataset.id); }));
  $("rerun").onclick = rerun;
  $("original").onclick = () => { $("rerun").disabled = false; selectExample(ex.id); };
  selectExample(d.examples[0].id);
});
