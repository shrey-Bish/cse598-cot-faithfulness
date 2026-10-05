// Wrong-hint demo. Left: the example, question, hint and model. Center: one run without the hint
// and one with it, side by side: private reasoning, final answer, and the letter the parser read.
// Above each column, one small letter per run of this exact prompt (saved runs plus live ones);
// click a letter to show that run.
const $ = (id) => document.getElementById(id);
const LETTERS = "ABCDEFGHIJ";
const ROWS = ["without", "with"];
let D = null, ex = null, hintEdited = false, busy = false, timer = null;
let rows = { with: [], without: [] }, shown = { with: null, without: null }, msgs = { with: [], without: [] };
const views = {}, cols = {};

const esc = (s) => (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (n) => (n ?? 0).toLocaleString("en-US");
const model = () => D.models.find((m) => m.id === $("model").value);
const hintType = () => document.querySelector("#htype .on").dataset.t;
const hintLetter = () => (hintType() === "none" ? null : $("hletter").value);
const correct = () => $("correct").value || null;
const pat = (t) => (t === "tool" ? "cue_tool" : "cue");

// ---------------------------------------------------------------- controls
function nOptions(text) {
  const m = [...(text || "").matchAll(/^\(([A-J])\)/gm)].map((x) => x[1]);
  return m.length ? LETTERS.indexOf(m.sort().pop()) + 1 : 4;
}
function letterSelects() {
  const n = nOptions($("qtext").value), keepH = $("hletter").value, keepC = $("correct").value;
  const opts = LETTERS.slice(0, n).split("").map((l) => `<option value="${l}">(${l})</option>`).join("");
  $("hletter").innerHTML = opts;
  $("correct").innerHTML = `<option value="">unknown</option>` + opts;
  if (keepH && LETTERS.indexOf(keepH) < n) $("hletter").value = keepH;
  $("correct").value = keepC && LETTERS.indexOf(keepC) < n ? keepC : "";
}
function template() {
  return D.hint_templates[hintType()].replaceAll("{letter}", $("hletter").value).replaceAll("{qid}", ex.qid);
}
function setHintType(t) {
  document.querySelectorAll("#htype button").forEach((b) => b.classList.toggle("on", b.dataset.t === t));
  const none = t === "none";
  $("hletter-row").classList.toggle("hidden", none);
  $("htext").classList.toggle("hidden", none);
  if (!none && !hintEdited) $("htext").value = template();
  $("cols").classList.toggle("one", none);
  cols.with.el.classList.toggle("hidden", none);
  ["run-with", "run-both"].forEach((b) => ($(b).disabled = busy || none));
}
function selectExample(id) {
  ex = D.examples.find((e) => e.id === id);
  $("example").value = id;
  $("qtext").value = ex.question;
  letterSelects();
  $("correct").value = ex.correct;
  $("hletter").value = ex.hint_letter;
  hintEdited = false;
  setHintType(ex.hint_type);
  $("htext").value = ex.hint_text || "";
  $("model").value = ex.model;
  modelDefaults();
  shown = { with: ex.featured, without: null };
  refresh(true);
}
// thinking models take 1-3 min a run, so fewer runs per click and room for long reasoning
function modelDefaults() {
  $("maxtok").value = model().thinking ? 16000 : 2000;
  $("nruns").value = model().thinking ? 2 : 8;
}
function changed() { clearTimeout(timer); timer = setTimeout(() => refresh(false), 350); }

// ---------------------------------------------------------------- saved runs of this exact prompt
async function refresh(first) {
  const req = { model: $("model").value, question: $("qtext").value, hint_type: hintType(), hint_text: $("htext").value };
  const r = await (await fetch("/api/runs", { method: "POST", body: JSON.stringify(req) })).json();
  if (busy) return;
  rows = { with: r.with, without: r.without };
  msgs = { with: r.messages_with, without: r.messages_without };
  const m = hintType() === "none" ? msgs.without : msgs.with;
  $("preview").textContent = m.map((x) => `[${x.role}]\n${x.content}`).join("\n\n");
  for (const row of ROWS) {
    const ids = rows[row].map((c) => c.run_id);
    if (!ids.includes(shown[row])) shown[row] = ids[0] || null;
    shown[row] ? await showRun(row, shown[row]) : paintEmpty(row);
  }
}

// ---------------------------------------------------------------- columns
function initCol(row) {
  const el = $(`col-${row}`);
  el.appendChild($("col-tpl").content.cloneNode(true));
  const q = (s) => el.querySelector(s);
  cols[row] = { el, title: q(".col-title"), status: q(".col-status"), rchips: q(".rchips"), tally: q(".tally"),
                blue: q(".blue-p"), priv: q(".private"), privN: q(".blue-p .count"), fin: q(".final"),
                finN: q(".orange-p .count"), parsed: q(".parsed") };
}
function title(row) {
  cols[row].title.innerHTML = row === "with" ? `With the hint <span class="pink">(${esc(hintLetter())})</span>` : "Without the hint";
}
function strip(row) {
  const c = cols[row], H = hintLetter(), C = correct();
  c.rchips.innerHTML = "";
  const done = rows[row].filter((x) => !x.wait && x.run_id !== "error");
  for (const x of rows[row]) {
    if (x.run_id === "error") continue;
    const el = document.createElement("div");
    if (x.wait) { el.className = "rchip wait"; el.textContent = "…"; c.rchips.appendChild(el); continue; }
    const cls = x.cut ? "cut" : row === "with" && x.letter && x.letter === H ? "hint" : x.letter && x.letter === C ? "right" : "";
    el.className = `rchip ${cls}${x.live ? " live" : ""}${x.run_id === shown[row] ? " sel" : ""}${x.fresh ? " pop" : ""}`;
    el.textContent = x.cut ? "✂" : x.letter || "–";
    el.title = `run ${x.run_id}${x.cut ? " · cut off: no answer" : ""}${x.live ? " · made in this demo" : ""}`;
    el.onclick = () => showRun(row, x.run_id);
    c.rchips.appendChild(el);
    x.fresh = false;
  }
  const n = done.length, count = (L) => done.filter((x) => x.letter === L).length;
  if (!n) c.tally.textContent = "";
  else if (row === "with") c.tally.textContent = `${count(H)} of ${n} run${n > 1 ? "s" : ""} picked (${H})`;
  else {
    const top = Object.entries(done.reduce((a, x) => (x.letter && (a[x.letter] = (a[x.letter] || 0) + 1), a), {}))
      .sort((a, b) => b[1] - a[1])[0];
    c.tally.textContent = top ? `${top[1]} of ${n} run${n > 1 ? "s" : ""} answered (${top[0]})` : `${n} runs, no answer`;
  }
}
function paintEmpty(row) {
  const c = cols[row];
  title(row); strip(row);
  c.status.textContent = model().name;
  c.blue.classList.add("hidden");
  c.fin.innerHTML = `<span class="none">No runs of this prompt yet. Press Run.</span>`; c.finN.textContent = "";
  c.parsed.innerHTML = "";
  banner();
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
function paintRun(row, v) {
  const c = cols[row], a = v.analysis, rec = v.record, hinted = row === "with", p = pat(v.hint_type);
  const H = rec.cue_letter || hintLetter(), C = correct();
  title(row); strip(row);
  c.status.innerHTML = `${esc(D.models.find((m) => m.id === rec.model)?.name || rec.model)} · ${v.live ? "live" : "saved"}` +
    (rec.latency_s ? ` · ${Math.round(rec.latency_s)} s` : "");
  // private reasoning (thinking models)
  const priv = v.private || "";
  c.blue.classList.toggle("hidden", !priv);
  c.priv.innerHTML = highlight(priv, hinted ? a.private_hits[p].map((h) => ({ ...h, cls: "kw" })) : []);
  c.privN.textContent = `${fmt(priv.length)} characters`;
  // final answer, leading blank lines trimmed (highlight ranges shifted with it)
  const fin = v.final || "", lead = fin.length - fin.trimStart().length;
  const fr = (hinted ? a.final_hits[p].map((h) => ({ ...h, cls: "kw" })) : []);
  if (a.span) fr.push({ start: a.span[0], end: a.span[1], cls: "ans" });
  c.fin.innerHTML = fin ? highlight(fin.slice(lead), fr.map((r) => ({ ...r, start: r.start - lead, end: r.end - lead })))
                        : `<span class="none">(empty)</span>`;
  c.finN.textContent = `${fmt(fin.length)} characters`;
  c.fin.style.maxHeight = priv ? "" : "36vh";
  c.priv.scrollTop = 0;
  c.fin.scrollTop = a.span && a.span[0] > fin.length / 2 ? 1e9 : 0;   // the answer line is usually at the end
  // what the parser read
  const L = a.letter;
  const chip = (txt, cls, label) => `<div class="chipbox"><div class="chip ${cls}">${txt}</div>${label}</div>`;
  const lcls = !L ? "" : hinted && L === H ? "hint" : C && L === C ? "right" : C ? "wrong" : "";
  let html = `<div class="chips">${chip(a.cut_off ? "✂" : L || "–", lcls, "The model answered")}` +
    (hinted ? chip(H, "hint", "The hint said") : "") + (C ? chip(C, "right", "The correct answer") : "") + "</div>";
  let vcls = "meh", vtxt;
  if (a.cut_off) vtxt = "Cut off at the token limit: counts as no answer.";
  else if (!L) vtxt = "No answer letter found.";
  else if (hinted && L === H) { vcls = "bad"; vtxt = `Picked the hint’s letter (${L})` + (C && C !== H ? ", a wrong answer." : "."); }
  else if (C && L === C) { vcls = "good"; vtxt = `Correct answer (${L}).`; }
  else if (C) { vcls = "bad"; vtxt = `Wrong answer (${L})` + (hinted ? ", not the hint’s letter." : "."); }
  else vtxt = `Answered (${L}).`;
  html += `<div class="verdict ${vcls}">${vtxt}</div>`;
  if (a.span) html += `<div class="facts">Letter read from <mark class="ans">${esc(fin.slice(a.span[0], a.span[1]))}</mark></div>`;
  if (hinted) {
    const n = (h) => (h.length ? `<b>${h.length} keyword match${h.length > 1 ? "es" : ""}</b>` : "<b>none</b>");
    html += `<div class="facts">Mentions the hint: ` + (priv ? `private reasoning ${n(a.private_hits[p])} · ` : "") +
            `final answer ${n(a.final_hits[p])}</div>`;
  }
  const u = rec.usage || {}, prm = rec.params || {};
  html += `<details class="raw"><summary>Run details, prompt sent and saved record</summary><pre>` +
    esc(`run ${rec.run_id} · seed ${prm.seed ?? "–"} · temperature ${prm.temperature ?? "–"} · ` +
        `${fmt(u.completion_tokens)} output tokens · ${rec.latency_s ?? "–"} s · finish: ${rec.finish_reason}\n\n` +
        rec.prompt_messages.map((m) => `[${m.role}]\n${m.content}`).join("\n\n") +
        "\n\n---- saved record ----\n" + JSON.stringify(rec, null, 1)) + `</pre></details>`;
  c.parsed.innerHTML = html;
  banner();
}
async function showRun(row, runId) {
  shown[row] = runId;
  if (!views[runId]) {
    const v = await (await fetch(`/api/record?run_id=${runId}`)).json();
    if (v.error) { cols[row].parsed.innerHTML = `<span class="err">${esc(v.error)}</span>`; return; }
    views[runId] = v;
  }
  if (shown[row] === runId) paintRun(row, views[runId]);
}

// ---------------------------------------------------------------- the banner over both columns
function banner() {
  const box = $("compare");
  if (hintType() === "none") { box.innerHTML = ""; return; }
  const w = views[shown.with], o = views[shown.without], H = hintLetter();
  if (!w || shown.with === "__live__") { box.innerHTML = ""; return; }
  const a = w.analysis, p = pat(w.hint_type), wl = a.letter, ol = o && shown.without !== "__live__" ? o.analysis.letter : null;
  const ph = a.private_hits[p].length, fh = a.final_hits[p].length, hasPriv = !!w.private;
  const said = !hasPriv ? (fh ? "The answer mentions the hint." : "The answer doesn’t mention the hint.")
             : !ph && !fh ? "Neither text mentions the hint."
             : !fh ? "Only the private reasoning mentions the hint." : "The final answer mentions the hint.";
  let cls = "meh", txt;
  if (!wl) txt = a.cut_off ? "The run with the hint was cut off: no answer." : "The run with the hint gave no answer letter.";
  else if (wl === H && ol && ol !== H) { cls = "bad"; txt = `The hint changed the answer: (${ol}) without it, (${H}) with it. ${said}`; }
  else if (wl === H && ol === H) txt = `(${H}) with and without the hint.`;
  else if (wl === H) { cls = "bad"; txt = `Picked the hint’s (${H}). ${said}`; }
  else {
    cls = "good";
    txt = (ol === wl ? `Not fooled: (${wl}) with and without the hint.` : `Not fooled: (${wl}) with the hint` + (ol ? `, (${ol}) without it.` : "."))
        + (ph || fh ? " It mentions the hint." : "");
  }
  const dw = rows.with.filter((x) => !x.wait && x.run_id !== "error"), dn = rows.without.filter((x) => !x.wait && x.run_id !== "error");
  const all = dw.length > 1 || dn.length > 1
    ? `All runs of this prompt: (${H}) in ${dw.filter((x) => x.letter === H).length} of ${dw.length} with the hint, ` +
      `${dn.filter((x) => x.letter === H).length} of ${dn.length} without it.` : "";
  box.innerHTML = `<div class="msg ${cls}">${esc(txt)}${all ? `<span class="all">${esc(all)}</span>` : ""}</div>`;
}

// ---------------------------------------------------------------- live runs
async function liveRun(row, slot, stream, of) {
  const withHint = row === "with", c = cols[row];
  const req = { model: $("model").value, question: $("qtext").value, correct: correct(),
                hint_type: withHint ? hintType() : "none", hint_text: withHint ? $("htext").value : null,
                hint_letter: withHint ? hintLetter() : null, instruction: D.instruction,
                temperature: $("temp").value, max_tokens: $("maxtok").value, seed: "", source_id: ex.id };
  let priv = "", fin = "", result = null;
  const t0 = Date.now();
  const status = () => (c.status.innerHTML = `<span class="dot"></span>live · ${Math.round((Date.now() - t0) / 1000)} s` +
                                             (of > 1 ? ` · showing run 1 of ${of}` : ""));
  let tick = null;
  if (stream) {
    shown[row] = "__live__"; title(row); strip(row);
    c.blue.classList.toggle("hidden", !model().thinking);
    c.priv.textContent = ""; c.fin.innerHTML = ""; c.privN.textContent = ""; c.finN.textContent = "";
    c.parsed.innerHTML = `<div class="facts" style="color:var(--grey)">Asking ${esc(model().name)}…</div>`;
    banner(); status(); tick = setInterval(() => shown[row] === "__live__" && status(), 250);
  }
  try {
    const resp = await fetch("/api/run", { method: "POST", body: JSON.stringify(req) });
    const reader = resp.body.getReader(), dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n")) >= 0) {
        const ev = JSON.parse(buf.slice(0, i)); buf = buf.slice(i + 1);
        if (ev.type === "reasoning") priv += ev.text;
        else if (ev.type === "content") fin += ev.text;
        else if (ev.type === "result") result = ev;
        else if (ev.type === "error") throw new Error(ev.error);
      }
      if (stream && shown[row] === "__live__") {
        if (priv) { c.blue.classList.remove("hidden"); c.priv.textContent = priv; c.priv.scrollTop = 1e9; c.privN.textContent = `${fmt(priv.length)} characters`; }
        c.fin.textContent = fin; c.fin.scrollTop = 1e9; c.finN.textContent = fin ? `${fmt(fin.length)} characters` : "";
      }
    }
    if (!result || result.record.status !== "ok") throw new Error((result && result.record.error_type) || "the call failed");
    const a = result.analysis, rec = result.record, p = pat(req.hint_type);
    views[rec.run_id] = { private: priv, final: fin, analysis: a, record: rec, hint_type: req.hint_type, live: true };
    slot.c = { run_id: rec.run_id, letter: a.letter, cut: a.cut_off, live: true, fresh: true,
               mentions: a.private_hits[p].length + a.final_hits[p].length };
    if (stream && shown[row] === "__live__") { shown[row] = rec.run_id; paintRun(row, views[rec.run_id]); }
    else { strip(row); banner(); }
  } catch (e) {
    slot.c = { run_id: "error" };
    if (stream && shown[row] === "__live__") {
      c.parsed.innerHTML = `<span class="err">Live call failed (${esc(e.message)}).</span> The letters above are saved real runs: click one.`;
      shown[row] = null;
    }
    strip(row);
  } finally {
    if (tick) clearInterval(tick);
  }
}
async function run(which) {
  const n = Math.max(1, Math.min(8, +$("nruns").value || 4));
  busy = true;
  ["run-with", "run-without", "run-both", "example"].forEach((b) => ($(b).disabled = true));
  const jobs = [];
  for (const row of which) {
    const slots = Array.from({ length: n }, () => ({ c: { wait: true } }));
    // each placeholder reads its slot, so a finished run replaces it in place
    slots.forEach((s) => rows[row].push(new Proxy({}, { get: (_, k) => s.c[k], set: (_, k, v) => ((s.c[k] = v), true) })));
    slots.forEach((s, i) => jobs.push(() => liveRun(row, s, i === 0, n)));
  }
  await Promise.all(jobs.map((j) => j()));
  for (const row of which) rows[row] = rows[row].filter((x) => x.run_id !== "error");
  busy = false;
  ["run-without", "example"].forEach((b) => ($(b).disabled = false));
  setHintType(hintType());
  ROWS.forEach(strip); banner();
}

// ---------------------------------------------------------------- start
fetch("/api/examples").then((r) => r.json()).then((d) => {
  D = d;
  ROWS.forEach(initCol);
  $("example").innerHTML = d.examples.map((e) =>
    `<option value="${e.id}">${esc(e.title)} · ${esc(d.models.find((m) => m.id === e.model).name)}</option>`).join("");
  $("example").onchange = () => selectExample($("example").value);
  $("model").innerHTML = d.models.map((m) => `<option value="${m.id}">${esc(m.name)}</option>`).join("");
  $("model").onchange = () => { modelDefaults(); refresh(false); };
  document.querySelectorAll("#htype button").forEach((b) => (b.onclick = () => {
    hintEdited = false; setHintType(b.dataset.t); refresh(false);
  }));
  $("hletter").onchange = () => { if (!hintEdited) $("htext").value = template(); refresh(false); };
  $("hreset").onclick = (e) => { e.preventDefault(); hintEdited = false; $("htext").value = template(); refresh(false); };
  $("htext").oninput = () => { hintEdited = true; changed(); };
  $("qtext").oninput = () => { letterSelects(); changed(); };
  $("correct").onchange = () => { ROWS.forEach((r) => (shown[r] && views[shown[r]] ? paintRun(r, views[shown[r]]) : strip(r))); };
  $("run-with").onclick = () => run(["with"]);
  $("run-without").onclick = () => run(["without"]);
  $("run-both").onclick = () => run(["without", "with"]);
  selectExample(d.examples[0].id);
});
