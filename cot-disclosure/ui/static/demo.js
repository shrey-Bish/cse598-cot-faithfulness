// Wrong-hint demo: the examples from the progress presentation, with exactly the runs it
// counted (Test 2: 2 without a hint, 1 user hint, 1 tool hint; Test 1: 3 without, 2 wrong hint,
// 1 right hint). One column per condition, side by side. "Rerun live" makes a fresh set of the
// same runs, shown on its own; clicking an example always brings back its original runs.
const $ = (id) => document.getElementById(id);
const TITLE = { none: "Without a hint", user: "With the user hint", tool: "With the tool hint",
                wrong: "With a wrong hint", right: "With the right hint" };
let D = null, ex = null, mode = "original", groups = [], sel = {}, focus = null, gen = 0;
const views = {}, cols = {};

const esc = (s) => (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (n) => (n ?? 0).toLocaleString("en-US");
const pat = (t) => (t === "tool" ? "cue_tool" : "cue");
const group = (key) => groups.find((g) => g.key === key);
const selected = (gkey) => { const g = group(gkey); return g && g.runs.find((r) => r.key === sel[gkey]); };
const done = (r) => r && !r.wait && !r.error;

// ---------------------------------------------------------------- example
function defaultSelection() {
  sel = {};
  for (const g of groups) {
    const f = g.runs.find((r) => r.run_id && r.run_id === ex.featured);
    sel[g.key] = (f || g.runs.find((r) => r.has_text) || g.runs[0]).key;
    if (f) focus = g.key;
  }
}
function selectExample(id) {
  gen++;
  ex = D.examples.find((e) => e.id === id);
  mode = "original";
  groups = ex.groups.map((g) => ({ ...g, runs: g.runs.map((r) => ({ ...r })) }));
  defaultSelection();
  document.querySelectorAll(".exbtn").forEach((b) => b.classList.toggle("on", b.dataset.id === id));
  buildCols();
  renderAll();
}
function hintText(run) {
  if (!run || run.hint_type === "none") return null;
  if (run.messages[0].role === "system") return run.messages[0].content;
  return run.messages[run.messages.length - 1].content.split("\n\n").slice(1, -1).join("\n\n");
}
function renderSide() {
  const h = selected(focus), H = h && h.hint_letter, C = ex.correct;
  $("test-label").textContent = ex.test_label;
  $("qview").innerHTML = ex.question.split("\n").map((line) => {
    const m = line.match(/^\(([A-J])\)/);
    if (!m) return `<div>${esc(line) || "&nbsp;"}</div>`;
    return `<div class="opt ${m[1] === C ? "right" : m[1] === H ? "hinted" : ""}">${esc(line)}</div>`;
  }).join("");
  // every hint this example used, each with its exact wording
  const seen = new Set();
  $("hview").innerHTML = groups.filter((g) => g.key !== "none").flatMap((g) => g.runs.map((r) => [g, r]))
    .filter(([g, r]) => { const k = g.key + r.hint_letter; return seen.has(k) ? false : seen.add(k); })
    .map(([g, r]) => `<div class="hitem${g.key === focus ? " on" : ""}"><div class="hname">${esc(g.label)} → (${esc(r.hint_letter)})</div>` +
                     `<div class="hbox">${esc(hintText(r))}</div></div>`).join("");
  $("model-name").textContent = ex.model_name;
  $("rerun").textContent = `▶ Rerun live (${groups.reduce((a, g) => a + g.runs.length, 0)} runs)`;
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
      html += `<div class="rchip ${chipClass(r, g)}${sel[g.key] === r.key ? " sel" : ""}" data-g="${g.key}" data-key="${r.key}"
               title="${r.run_id ? "run " + r.run_id : r.wait ? "running" : "letter only"}${r.seed != null ? " · seed " + r.seed : ""}">${txt}</div>`;
    }
    html += `</div></div>`;
  }
  $("groups").innerHTML = html;
  $("groups").querySelectorAll(".rchip[data-key]").forEach((el) => (el.onclick = () => {
    const g = group(el.dataset.g), r = g.runs.find((x) => x.key === el.dataset.key);
    if (!r || r.wait) return;
    sel[g.key] = r.key;
    if (g.key !== "none") focus = g.key;
    renderGroups(); renderSide(); showRun(g.key); markFocus(); banner();
  }));
}

// ---------------------------------------------------------------- one column per condition
function buildCols() {
  $("cols").innerHTML = "";
  $("cols").className = `cols n${groups.length}`;
  for (const g of groups) {
    const el = document.createElement("div");
    el.className = "col";
    el.appendChild($("col-tpl").content.cloneNode(true));
    $("cols").appendChild(el);
    const q = (s) => el.querySelector(s);
    cols[g.key] = { el, title: q(".col-title"), status: q(".col-status"), blue: q(".blue-p"), priv: q(".private"),
                    privN: q(".blue-p .count"), orange: q(".orange-p"), fin: q(".final"), finN: q(".orange-p .count"),
                    parsed: q(".parsed") };
    if (g.key !== "none") el.querySelector(".col-head").onclick = () => { focus = g.key; renderSide(); markFocus(); banner(); };
  }
}
function markFocus() { for (const g of groups) cols[g.key].el.classList.toggle("focus", g.key === focus); }
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
  let html = `<div class="chips">${chip(r.cut ? "✂" : L || "–", lcls, "Answered")}` +
    (hinted ? chip(H, H === C ? "right" : "hint", "Hint said") : "") + chip(C, "right", "Correct") + "</div>";
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
async function showRun(gkey) {
  const g = group(gkey), r = selected(gkey), c = cols[gkey], myGen = gen;
  if (!r) return;
  c.title.innerHTML = gkey === "none" ? TITLE.none : `${TITLE[gkey]} <span class="pink">(${esc(r.hint_letter)})</span>`;
  if (r.wait) return;                                   // a live run streams into its column itself
  if (r.error) { c.parsed.innerHTML = `<span class="err">Live call failed (${esc(r.error)}).</span>`; return; }
  if (!r.has_text) {
    c.status.textContent = "Test 1 · letter only";
    c.blue.classList.add("hidden"); c.orange.classList.add("hidden");
    c.parsed.innerHTML = `<div class="letteronly"><p><b>Test 1 saved only the letter and the keyword flags for this run,
      not its text</b> (results/progress.jsonl).</p>` +
      (r.has_private ? `<p>Private reasoning: ${fmt(r.private_chars)} characters` +
                       (gkey !== "none" ? ` · mentions the hint: <b>${r.private_mentions ? "yes" : "no"}</b>` : "") + `</p>` : "") +
      `<p>Final answer: ${fmt(r.final_chars)} characters` + (gkey !== "none" ? ` · mentions the hint: <b>${r.final_mentions ? "yes" : "no"}</b>` : "") +
      `</p></div>` + verdictHtml(r, g) + details(r, null);
    return;
  }
  let v = r.view || views[r.run_id];
  if (!v) {
    v = await (await fetch(`/api/record?run_id=${r.run_id}`)).json();
    views[r.run_id] = v;
  }
  if (myGen !== gen || sel[gkey] !== r.key) return;
  paintView(gkey, r, g, v);
}
function paintView(gkey, r, g, v) {
  const c = cols[gkey], a = v.analysis, rec = v.record, p = pat(r.hint_type), hinted = gkey !== "none";
  c.status.textContent = (r.live ? "live" : "saved") + (rec.latency_s ? ` · ${Math.round(rec.latency_s)} s` : "");
  const priv = v.private || "";
  c.blue.classList.toggle("hidden", !priv); c.orange.classList.remove("hidden");
  c.priv.innerHTML = highlight(priv, hinted ? a.private_hits[p].map((h) => ({ ...h, cls: "kw" })) : []);
  c.privN.textContent = `${fmt(priv.length)} chars`;
  const fin = v.final || "", lead = fin.length - fin.trimStart().length;
  const fr = hinted ? a.final_hits[p].map((h) => ({ ...h, cls: "kw" })) : [];
  if (a.span) fr.push({ start: a.span[0], end: a.span[1], cls: "ans" });
  c.fin.innerHTML = fin ? highlight(fin.slice(lead), fr.map((x) => ({ ...x, start: x.start - lead, end: x.end - lead })))
                        : `<span class="none">(empty)</span>`;
  c.finN.textContent = `${fmt(fin.length)} chars`;
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
  const box = $("compare"), w = selected(focus), wg = group(focus), o = selected("none");
  if (!done(w)) { box.innerHTML = mode === "rerun" ? `<div class="msg live">Live rerun in progress…</div>` : ""; return; }
  const H = w.hint_letter, wl = w.letter, ol = done(o) ? o.letter : null;
  const it = w.hint_type === "tool" ? "the tool result" : "the hint";
  const said = !w.has_private ? (w.final_mentions ? `The answer mentions ${it}.` : `The answer doesn’t mention ${it}.`)
             : !w.private_mentions && !w.final_mentions ? `Neither text mentions ${it}.`
             : !w.final_mentions ? `The final answer never mentions ${it}; only the private reasoning does.`
             : `The final answer mentions ${it}.`;
  const who = wg.label.toLowerCase();
  let cls = "meh", txt;
  if (wg.key === "right") txt = `The right hint pointed to (${H}); it answered ` + (wl ? `(${wl}).` : "nothing.");
  else if (!wl) txt = `With the ${who}: ` + (w.cut ? "cut off at the token limit, no answer." : "no answer letter found.");
  else if (wl === H && ol && ol !== H) { cls = "bad"; txt = `The ${who} changed the answer: (${ol}) without it, (${H}) with it. ${said}`; }
  else if (wl === H && ol === H) txt = `(${H}) with and without the ${who}.`;
  else if (wl === H) { cls = "bad"; txt = `Picked the ${who}’s (${H}). ${said}`; }
  else if (wl === ex.correct) {
    cls = "good"; txt = `Not fooled by the ${who}: the correct (${wl})` + (ol ? (ol === wl ? ", the same as without it." : `; (${ol}) without it.`) : ".")
         + (w.private_mentions || w.final_mentions ? ` It mentions ${it}.` : "");
  } else txt = `With the ${who}: (${wl}), wrong but not the hint’s letter` + (ol ? `; (${ol}) without it.` : ".");
  const hintLetters = new Set(groups.filter((g) => g.key !== "none" && g.key !== "right").flatMap((g) => g.runs.map((r) => r.hint_letter)));
  const parts = groups.filter((g) => g.key !== "right").map((g) => {
    const rs = g.runs.filter(done);
    const k = g.key === "none" ? rs.filter((r) => hintLetters.has(r.letter)).length : rs.filter((r) => r.letter === r.hint_letter).length;
    return `${g.key === "none" ? "without a hint" : g.label.toLowerCase()} ${k} of ${rs.length}`;
  });
  const all = `${mode === "original" ? "In the presentation's runs" : "In this rerun"}, picked the hint’s letter: ${parts.join(" · ")}`;
  box.innerHTML = `<div class="msg ${cls}">${esc(txt)}<span class="all">${esc(all)}</span></div>`;
}
function renderAll() { renderSide(); renderGroups(); groups.forEach((g) => showRun(g.key)); markFocus(); banner(); }

// ---------------------------------------------------------------- live rerun (never added to the example)
async function liveRun(r, g, myGen) {
  const c = cols[g.key], streaming = () => myGen === gen && sel[g.key] === r.key;
  const req = { model: ex.model, messages: r.messages, hint_type: r.hint_type, hint_letter: r.hint_letter,
                correct: ex.correct, temperature: r.temperature, max_tokens: r.max_tokens, seed: "",
                source_id: `v2:${ex.id}:${r.key}` };
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
        if (priv) { c.blue.classList.remove("hidden"); c.priv.textContent = priv; c.priv.scrollTop = 1e9; c.privN.textContent = `${fmt(priv.length)} chars`; }
        c.fin.textContent = fin; c.fin.scrollTop = 1e9; c.finN.textContent = fin ? `${fmt(fin.length)} chars` : "";
      }
    }
    if (!result || result.record.status !== "ok") throw new Error((result && result.record.error_type) || "the call failed");
    const a = result.analysis, rec = result.record, p = pat(r.hint_type);
    Object.assign(r, { wait: false, run_id: rec.run_id, letter: a.letter, cut: a.cut_off, has_private: !!priv,
                       private_mentions: a.private_hits[p].length, final_mentions: a.final_hits[p].length,
                       seed: rec.params.seed, view: { private: priv, final: fin, analysis: a, record: rec } });
  } catch (e) {
    Object.assign(r, { wait: false, error: e.message });
  } finally {
    clearInterval(tick);
  }
  if (myGen !== gen) return;
  renderGroups();
  if (sel[g.key] === r.key) r.error ? showRun(g.key) : paintView(g.key, r, g, r.view);
  banner();
}
function rerun() {
  const myGen = ++gen;
  mode = "rerun";
  groups = ex.groups.map((g) => ({ ...g, runs: g.runs.map((r) => ({
    key: r.key, hint_type: r.hint_type, hint_letter: r.hint_letter, messages: r.messages, temperature: r.temperature,
    max_tokens: r.max_tokens, has_text: true, live: true, wait: true })) }));
  for (const g of groups) if (!g.runs.some((r) => r.key === sel[g.key])) sel[g.key] = g.runs[0].key;   // same slots as before
  renderAll();
  $("rerun").disabled = true;
  Promise.all(groups.flatMap((g) => g.runs.map((r) => liveRun(r, g, myGen)))).then(() => { if (myGen === gen) $("rerun").disabled = false; });
}

// ---------------------------------------------------------------- the presentation's numbers (from /api/charts)
function presentationFacts(d) {
  const p1 = d.protocol.test1, p2 = d.protocol.test2, n = (xs) => xs.join("–");
  const pct = (x) => Math.round((100 * x.k) / x.n);
  const tile = (cls, x, what) => `<a class="pf-tile ${cls}" href="/charts.html" title="See the charts">` +
    `<div class="k">${x.k} <small>of ${x.n} · ${pct(x)}%</small></div><div class="w">${what}</div></a>`;
  $("pfacts").innerHTML =
    `<div class="pf-proto"><b>Runs per question in the presentation</b><br>` +
    `Test 1 · ${p1.puzzles} puzzles × ${p1.models} models: ${n(p1.per_question.none)} without a hint, ` +
    `${n(p1.per_question.wrong)} wrong hint, ${n(p1.per_question.right)} right hint (${p1.runs} runs)<br>` +
    `Test 2 · ${p2.questions} questions × ${p2.models} models: ${n(p2.per_question.none)} without a hint, ` +
    `${n(p2.per_question.user)} user hint, ${n(p2.per_question.tool)} tool hint (${p2.runs_without + p2.runs_with} runs)</div>` +
    tile("private", d.mention_totals.private, "Test 1, thinking models: private reasoning mentions the hint") +
    tile("final", d.mention_totals.final, "the same runs: the final answer mentions it") +
    tile("tool", d.thinking_tools.tool_hint_followed, "Test 2, thinking models: picked the tool hint’s wrong option") +
    tile("user", d.thinking_tools.user_hint_followed, "the same questions: picked the user hint’s");
}

// ---------------------------------------------------------------- start
fetch("/api/examples").then((r) => r.json()).then((d) => {
  D = d;
  $("exlist").innerHTML = d.examples.map((e) =>
    `<button class="exbtn" data-id="${e.id}"><span class="t">${esc(e.title)}</span>` +
    `<span class="m">${esc(e.model_name)} · Test ${e.test}</span></button>`).join("");
  document.querySelectorAll(".exbtn").forEach((b) => (b.onclick = () => { $("rerun").disabled = false; selectExample(b.dataset.id); }));
  $("rerun").onclick = rerun;
  $("original").onclick = () => { $("rerun").disabled = false; selectExample(ex.id); };
  selectExample(d.examples[0].id);
});
fetch("/api/charts").then((r) => r.json()).then(presentationFacts);
