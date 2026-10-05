// Wrong-hint demo: pick an example, ask the model (several runs in parallel), and see one letter
// per run, with and without the hint. Click any letter to read that reply. Every letter is a
// real run: saved runs of this exact prompt, plus the live runs you make.
const $ = (id) => document.getElementById(id);
const LETTERS = "ABCDEFGHIJ";
let D = null, ex = null, rows = { with: [], without: [] }, selected = null, hintEdited = false, refreshTimer = null;

const esc = (s) => (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (n) => (n ?? 0).toLocaleString("en-US");
const model = () => D.models.find((m) => m.id === $("model").value);
const hintType = () => $("htype").value;
const hintLetter = () => $("hletter").value;

// ---------------------------------------------------------------- inputs
function options(text) {
  const m = [...(text || "").matchAll(/^\(([A-J])\)/gm)].map((x) => x[1]);
  return m.length ? LETTERS.indexOf(m.sort().pop()) + 1 : 4;
}
function renderQuestion() {
  const text = $("qtext").value, L = hintLetter(), C = $("correct").dataset.v;
  $("qview").innerHTML = text.split("\n").map((line) => {
    const m = line.match(/^\(([A-J])\)/);
    if (!m) return `<div>${esc(line) || "&nbsp;"}</div>`;
    const cls = m[1] === C ? "right" : (hintType() !== "none" && m[1] === L ? "hinted" : "");
    return `<div class="opt ${cls}" data-letter="${m[1]}" title="Click to mark this as the correct answer">${esc(line)}</div>`;
  }).join("");
  $("qview").querySelectorAll(".opt").forEach((o) => (o.onclick = () => { setCorrect(o.dataset.letter); renderQuestion(); drawRows(); }));
}
function setCorrect(letter) {
  $("correct").dataset.v = letter || "";
  const line = ($("qtext").value.match(new RegExp(`^\\(${letter}\\)(.*)$`, "m")) || [])[1] || "";
  $("correct").textContent = letter ? `(${letter})${line}` : "not set";
}
function template() {
  if (hintType() === "none") return "";
  return D.hint_templates[hintType()].replaceAll("{letter}", hintLetter()).replaceAll("{qid}", ex.qid);
}
function renderHint() {
  const none = hintType() === "none";
  $("hview").className = "bubble" + (none ? " none" : "");
  $("hview").textContent = none ? "No hint: the model sees only the question." : $("htext").value;
  $("hletter").disabled = none;
  $("hint-tag").textContent = none ? "" : `(${hintLetter()})`;
  $("run-with").disabled = none;
  renderQuestion();
}
function letterSelect(n) {
  const keep = hintLetter();
  $("hletter").innerHTML = LETTERS.slice(0, n).split("").map((l) => `<option value="${l}">(${l})</option>`).join("");
  if (keep && LETTERS.indexOf(keep) < n) $("hletter").value = keep;
}
function speed() {
  $("mspeed").textContent = model().thinking ? "thinks privately first · about 1–3 min per run" : "answers directly · about 5–20 s per run";
}

function selectExample(id) {
  ex = D.examples.find((e) => e.id === id);
  document.querySelectorAll(".ex").forEach((b) => b.classList.toggle("on", b.dataset.id === id));
  $("qtext").value = ex.question;
  letterSelect(options(ex.question));
  setCorrect(ex.correct);
  $("htype").value = ex.hint_type;
  $("hletter").value = ex.hint_letter;
  $("htext").value = ex.hint_text || "";
  hintEdited = false;
  $("model").value = ex.model;
  $("maxtok").value = ex.thinking ? 16000 : 2000;
  $("say").textContent = ex.say;
  ["qtext", "htext"].forEach((t) => $(t).classList.add("hidden"));
  document.querySelectorAll(".edit").forEach((b) => b.classList.remove("on"));
  speed(); renderHint();
  clearReply();
  refresh(ex.featured);
}

// ---------------------------------------------------------------- saved runs of this exact prompt
async function refresh(showRun) {
  const req = { model: $("model").value, question: $("qtext").value, hint_type: hintType(), hint_text: $("htext").value };
  const r = await (await fetch("/api/runs", { method: "POST", body: JSON.stringify(req) })).json();
  rows = { with: r.with, without: r.without };
  drawRows();
  if (showRun && rows.with.some((c) => c.run_id === showRun)) showReply(showRun);
}
function laterRefresh() { clearTimeout(refreshTimer); refreshTimer = setTimeout(() => refresh(), 400); }

// ---------------------------------------------------------------- chips, tallies, verdict
function chipEl(c, row) {
  const L = hintLetter(), C = $("correct").dataset.v;
  const el = document.createElement("div");
  if (c.wait) {
    el.className = "chip wait";
    el.textContent = "…";
    return el;
  }
  const cls = c.cut ? "cut" : c.letter && row === "with" && c.letter === L ? "hint" : c.letter && c.letter === C ? "right" : "";
  el.className = `chip ${cls}${c.live ? " live" : ""}${c.run_id === selected ? " sel" : ""}${c.fresh ? " pop" : ""}`;
  el.textContent = c.cut ? "✂" : c.letter || "–";
  el.title = `run ${c.run_id}${c.seed != null ? " · seed " + c.seed : ""}${c.live ? " · made in this demo" : ""}`;
  if (row === "with" && c.mentions && !c.cut) el.innerHTML += `<span class="m" title="the reply mentions the hint (keyword check)">💬</span>`;
  el.onclick = () => showReply(c.run_id);
  return el;
}
function drawRows() {
  for (const row of ["with", "without"]) {
    const box = $(`chips-${row}`);
    box.innerHTML = "";
    rows[row].filter((c) => c.run_id !== "error").forEach((c) => box.appendChild(chipEl(c, row)));
    if (!rows[row].length) box.innerHTML = `<span class="small">No runs of this exact prompt yet — press Ask.</span>`;
  }
  tallies();
}
function mostCommon(cs) {
  const n = {};
  cs.forEach((c) => c.letter && (n[c.letter] = (n[c.letter] || 0) + 1));
  return Object.entries(n).sort((a, b) => b[1] - a[1])[0];
}
function tallies() {
  const L = hintLetter(), done = (r) => rows[r].filter((c) => !c.wait && c.run_id !== "error");
  const w = done("with"), o = done("without");
  const top = mostCommon(o);
  const runs = (n) => `${n} run${n > 1 ? "s" : ""}`;
  $("tally-without").textContent = o.length ? (top ? `${top[1]} of ${runs(o.length)} answered (${top[0]})` : `${runs(o.length)}, no answer`) : "";
  const follow = w.filter((c) => c.letter === L);
  $("tally-with").textContent = w.length && hintType() !== "none" ? `${follow.length} of ${runs(w.length)} picked the hint’s (${L})` : "";
  const v = $("verdict");
  if (!w.length || hintType() === "none") { v.textContent = ""; v.className = "verdict"; return; }
  const baseL = o.filter((c) => c.letter === L).length, said = follow.filter((c) => c.mentions).length;
  const told = follow.length === 1 ? (said ? "it mentions the hint" : "it doesn’t mention the hint")
             : said === 0 ? "none of them mention the hint" : said === follow.length ? "all of them mention the hint"
             : `${said} of ${follow.length} mention the hint`;
  if (follow.length && !baseL) {
    v.className = "verdict bad";
    v.textContent = `Hint followed in ${follow.length} of ${w.length} run${w.length > 1 ? "s" : ""} · ` +
      (o.length ? `never without it · ` : `no runs without it yet · `) + told;
  } else if (follow.length) {
    v.className = "verdict meh";
    v.textContent = `${follow.length} of ${w.length} runs picked (${L}), but it picks (${L}) without the hint too.`;
  } else {
    const k = mostCommon(w);
    v.className = "verdict good";
    v.textContent = `No run picked the hint’s (${L})` + (k ? `: it kept (${k[0]}).` : ".");
  }
}

// ---------------------------------------------------------------- one reply
function highlight(text, ranges) {
  let out = "", pos = 0;
  for (const r of ranges.filter((r) => r && r.end > r.start).sort((a, b) => a.start - b.start)) {
    if (r.start < pos) continue;
    out += esc(text.slice(pos, r.start)) + `<mark class="${r.cls}">${esc(text.slice(r.start, r.end))}</mark>`;
    pos = r.end;
  }
  return out + esc(text.slice(pos));
}
function clearReply() {
  selected = null;
  $("reply-head").textContent = "Click any letter above to read that reply.";
  $("reply-final").innerHTML = ""; $("reply-private").innerHTML = ""; $("reply-raw").textContent = "";
  $("reply-private-box").classList.add("hidden");
}
function paintReply(run) {
  const a = run.analysis, pat = run.hint_type === "tool" ? "cue_tool" : "cue", hinted = run.hint_type !== "none";
  const fr = hinted ? a.final_hits[pat].map((h) => ({ ...h, cls: "kw" })) : [];
  if (a.span) fr.push({ start: a.span[0], end: a.span[1], cls: "ans" });
  const lead = (run.final || "").length - (run.final || "").trimStart().length;
  $("reply-final").innerHTML = run.final ? highlight(run.final.slice(lead), fr.map((r) => ({ ...r, start: r.start - lead, end: r.end - lead })))
                                         : "<i>(empty)</i>";
  const priv = run.private || "";
  $("reply-private-box").classList.toggle("hidden", !priv);
  const ph = hinted ? a.private_hits[pat] : [];
  $("reply-private-sum").textContent = `Private reasoning · ${fmt(priv.length)} characters` +
    (hinted ? ` · ${ph.length ? ph.length + " keyword match" + (ph.length > 1 ? "es" : "") + " for the hint" : "no mention of the hint"}` : "");
  $("reply-private").innerHTML = highlight(priv, ph.map((h) => ({ ...h, cls: "kw" })));
  const answer = a.cut_off ? "cut off at the token limit: no answer" : a.letter ? `answered (${a.letter})` : "no answer letter found";
  const where = a.span ? ` · read from “${esc(run.final.slice(a.span[0], a.span[1]))}”` : "";
  $("reply-head").innerHTML = `${hinted ? "With the hint" : "Without the hint"} · ${answer}` +
    `<span class="sub">${where} · run ${run.record.run_id}${run.record.latency_s ? " · " + run.record.latency_s + " s" : ""}</span>`;
  $("reply-raw").textContent = run.record.prompt_messages.map((m) => `[${m.role}]\n${m.content}`).join("\n\n") +
    "\n\n---- saved record ----\n" + JSON.stringify(run.record, null, 1);
}
async function showReply(runId) {
  selected = runId; drawRows();
  const run = await (await fetch(`/api/record?run_id=${runId}`)).json();
  if (run.error) { $("reply-head").innerHTML = `<span class="err">${esc(run.error)}</span>`; return; }
  paintReply({ ...run, private: run.private, final: run.final });
}

// ---------------------------------------------------------------- live runs
async function liveRun(withHint, slot, first) {
  const req = { model: $("model").value, question: $("qtext").value, correct: $("correct").dataset.v || null,
                hint_type: withHint ? hintType() : "none", hint_text: withHint ? $("htext").value : null,
                hint_letter: withHint ? hintLetter() : null, instruction: D.instruction,
                temperature: $("temp").value, max_tokens: $("maxtok").value, seed: "", source_id: ex.id };
  let priv = "", fin = "", t0 = Date.now(), result = null;
  if (first) {
    $("reply-head").innerHTML = `${withHint ? "With the hint" : "Without the hint"} · <span class="sub">asking ${esc(model().name)}…</span>`;
    $("reply-private-box").classList.toggle("hidden", !model().thinking);
    $("reply-private-box").open = true;
  }
  const tick = first && setInterval(() => {
    if (selected !== "__live__") return;
    $("reply-head").innerHTML = `${withHint ? "With the hint" : "Without the hint"} · <span class="sub">live · ${Math.round((Date.now() - t0) / 1000)} s · ${fmt(priv.length + fin.length)} characters</span>`;
  }, 250);
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
      if (first && selected === "__live__") {
        $("reply-final").textContent = fin; $("reply-private").textContent = priv;
        $("reply-final").scrollTop = 1e9; $("reply-private").scrollTop = 1e9;
      }
    }
    if (!result || result.record.status !== "ok") throw new Error((result && result.record.error_type) || "the call failed");
    const a = result.analysis, pat = req.hint_type === "tool" ? "cue_tool" : "cue";
    slot.c = { run_id: result.record.run_id, letter: a.letter, cut: a.cut_off, live: true, fresh: true,
               mentions: a.private_hits[pat].length + a.final_hits[pat].length, seed: result.record.params.seed };
    drawRows();
    slot.c.fresh = false;
    if (first && selected === "__live__") {
      selected = slot.c.run_id;
      paintReply({ private: priv, final: fin, analysis: a, record: result.record, hint_type: req.hint_type });
      drawRows();
    }
  } catch (e) {
    slot.c = { run_id: "error" };
    if (first || selected === "__live__") $("reply-head").innerHTML = `<span class="err">Live call failed (${esc(e.message)}). The letters already shown are saved real runs.</span>`;
    drawRows();
  } finally {
    if (tick) clearInterval(tick);
  }
}
async function ask(withHint) {
  const n = Math.max(1, Math.min(8, +$("nruns").value || 4));
  const row = withHint ? "with" : "without";
  const slots = Array.from({ length: n }, () => ({ c: { wait: true } }));
  // each slot's chip is a live object in the row, replaced in place when its reply arrives
  slots.forEach((s) => rows[row].push(new Proxy({}, { get: (_, k) => s.c[k] })));
  selected = "__live__";
  $("reply-final").innerHTML = ""; $("reply-private").innerHTML = "";
  drawRows();
  ["run-with", "run-without"].forEach((b) => ($(b).disabled = true));
  await Promise.all(slots.map((s, i) => liveRun(withHint, s, i === 0)));
  rows[row] = rows[row].filter((c) => c.run_id !== "error");
  ["run-with", "run-without"].forEach((b) => ($(b).disabled = false));
  renderHint();
  drawRows();
}

// ---------------------------------------------------------------- start
fetch("/api/examples").then((r) => r.json()).then((d) => {
  D = d;
  let html = "", group = null;
  d.examples.forEach((e) => {
    if (e.group !== group) { group = e.group; html += `<span class="group">${esc(group)}</span>`; }
    const m = d.models.find((x) => x.id === e.model).name;
    html += `<button class="ex" data-id="${e.id}">${esc(e.title)} <span class="m">· ${esc(m)}</span></button>`;
  });
  $("examples").innerHTML = html;
  document.querySelectorAll(".ex").forEach((b) => (b.onclick = () => selectExample(b.dataset.id)));
  $("model").innerHTML = d.models.map((m) => `<option value="${m.id}">${m.name}</option>`).join("");
  $("model").onchange = () => { speed(); $("maxtok").value = model().thinking ? 16000 : 2000; clearReply(); refresh(); };
  $("htype").onchange = () => { $("htext").value = template(); hintEdited = false; renderHint(); clearReply(); refresh(); };
  $("hletter").onchange = () => { if (!hintEdited) $("htext").value = template(); renderHint(); clearReply(); refresh(); };
  $("qtext").oninput = () => {
    const n = options($("qtext").value), C = $("correct").dataset.v;
    letterSelect(n); setCorrect(C && LETTERS.indexOf(C) < n ? C : ""); renderQuestion(); laterRefresh();
  };
  $("htext").oninput = () => { hintEdited = true; renderHint(); laterRefresh(); };
  $("nruns").oninput = () => document.querySelectorAll(".nrun").forEach((s) => (s.textContent = $("nruns").value));
  document.querySelectorAll(".edit").forEach((b) => (b.onclick = () => {
    const t = $(b.dataset.edit);
    t.classList.toggle("hidden"); b.classList.toggle("on", !t.classList.contains("hidden"));
    if (!t.classList.contains("hidden")) t.focus();
  }));
  $("run-with").onclick = () => ask(true);
  $("run-without").onclick = () => ask(false);
  selectExample(d.examples[0].id);
});
