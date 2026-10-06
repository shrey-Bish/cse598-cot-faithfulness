// Charts of the presentation's runs for all models. Every number comes from /api/charts, which
// reads docs/progress/RESULTS_SUMMARY.json (written by progress/analyze_progress.py). Plain SVG.
const $ = (id) => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const C = { user: "#8893A6", tool: "#C02F79", private: "#2F6FD6", final: "#E2622A" };
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pct = (x) => (x && x.n ? Math.round((100 * x.k) / x.n) : null);
const of = (x, unit = "") => (x ? `${x.k} of ${x.n}${unit} (${pct(x)}%)` : "–");

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}
// a bar anchored on the baseline (square) with a 4px rounded data end
function barPath(x, y, w, h, r = 4) {
  if (w <= 0) return "";
  r = Math.min(r, w, h / 2);
  return `M${x},${y}h${w - r}a${r},${r} 0 0 1 ${r},${r}v${h - 2 * r}a${r},${r} 0 0 1 -${r},${r}h-${w - r}z`;
}

// horizontal bars: one band per model, one bar per series; hover a band for its numbers
function hbar(box, rows, series) {
  box.innerHTML = "";
  const W = Math.max(box.clientWidth, 320), labelW = Math.min(170, W * 0.36), valueW = 118;
  const barH = 15, gap = 2, pad = 9, axisH = 20;
  const rowH = series.length * barH + (series.length - 1) * gap + pad * 2, H = rows.length * rowH + axisH + 4;
  const x0 = labelW, x1 = W - valueW, sx = (v) => x0 + v * (x1 - x0);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, height: H, role: "img" }, box);
  for (const t of [0, 0.25, 0.5, 0.75, 1]) {
    el("line", { x1: sx(t), x2: sx(t), y1: 0, y2: H - axisH, class: t === 0 ? "baseline" : "gridline" }, svg);
    el("text", { x: sx(t), y: H - 5, "text-anchor": "middle", class: "axis" }, svg).textContent = `${t * 100}%`;
  }
  rows.forEach((row, i) => {
    const y = i * rowH;
    const hit = el("rect", { x: 0, y, width: W, height: rowH, class: "hit" }, svg);
    const ly = y + rowH / 2 + (row.sub ? -2 : 4);
    el("text", { x: x0 - 10, y: ly, "text-anchor": "end", class: "label" }, svg).textContent = row.label;
    if (row.sub) el("text", { x: x0 - 10, y: ly + 14, "text-anchor": "end", class: "label-sub" }, svg).textContent = row.sub;
    series.forEach((s, j) => {
      const v = row.values[s.key], by = y + pad + j * (barH + gap);
      if (v && v.n) {
        const w = sx(v.k / v.n) - x0;
        if (s.dashed) {
          if (w > 0) el("path", { d: barPath(x0 + 0.75, by + 0.75, Math.max(w - 1.5, 0), barH - 1.5), fill: "#fff",
                                  stroke: C.user, "stroke-width": 1.5, "stroke-dasharray": "3 2" }, svg);
        } else if (w > 0) el("path", { d: barPath(x0, by, w, barH), fill: s.color }, svg);
        el("text", { x: x0 + Math.max(w, 0) + 6, y: by + barH - 3.5, class: "value" }, svg).textContent = `${pct(v)}%`;
      } else {
        el("text", { x: x0 + 6, y: by + barH - 3.5, class: "value na" }, svg).textContent = s.na || "n/a";
      }
    });
    hit.addEventListener("mousemove", (e) => showTip(e, row, series));
    hit.addEventListener("mouseleave", hideTip);
  });
  svg.setAttribute("aria-label", rows.map((r) => r.label + ": " + series.map((s) => `${s.name} ${of(r.values[s.key])}`).join(", ")).join("; "));
}
function showTip(e, row, series) {
  const t = $("tip");
  t.innerHTML = `<b>${esc(row.label)}${row.sub ? " " + esc(row.sub) : ""}</b>` +
    series.map((s) => `<div class="row"><i class="${s.dashed ? "dashed" : ""}" style="background:${s.color || "#fff"}"></i>` +
                      `${esc(s.name)}<span>${row.values[s.key] ? esc(of(row.values[s.key], s.unit)) : esc(s.na || "n/a")}</span></div>`).join("") +
    (row.extra || []).map(([k, v]) => `<div class="row">${esc(k)}<span>${esc(v)}</span></div>`).join("");
  t.classList.remove("hidden");
  const r = t.getBoundingClientRect();
  t.style.left = `${Math.min(e.clientX + 14, innerWidth - r.width - 8)}px`;
  t.style.top = `${Math.min(e.clientY + 14, innerHeight - r.height - 8)}px`;
}
function hideTip() { $("tip").classList.add("hidden"); }
function legend(box, series) {
  box.innerHTML = series.map((s) => `<span><i class="${s.dashed ? "dashed" : ""}" style="background:${s.color || "#fff"}"></i>${esc(s.name)}</span>`).join("");
}
function table(box, head, rows) {
  box.innerHTML = `<table><tr>${head.map((h, i) => `<th class="${i ? "num" : ""}">${esc(h)}</th>`).join("")}</tr>` +
    rows.map((r) => `<tr>${r.map((c, i) => `<td class="${i ? "num" : ""}">${esc(c)}</td>`).join("")}</tr>`).join("") + "</table>";
}

let DATA = null;
function render() {
  const d = DATA;
  // how many runs each question got (counted from the result files)
  const p1 = d.protocol.test1, p2 = d.protocol.test2, n = (xs) => xs.join("–");
  $("proto").innerHTML =
    `<div><div class="t">Test 1 · ${p1.puzzles} easy puzzles × ${p1.models} models</div><div class="runs">` +
    `<span><b>${n(p1.per_question.none)}</b> without a hint</span><span><b>${n(p1.per_question.wrong)}</b> with a wrong hint</span>` +
    `<span><b>${n(p1.per_question.right)}</b> with the right hint</span></div>` +
    `<div class="tot">${p1.runs} runs in all; ${p1.runs_with_hint_thinking} of them are thinking-model runs with a hint (the 216 below)</div></div>` +
    `<div><div class="t">Test 2 · ${p2.questions} harder exam questions × ${p2.models} models</div><div class="runs">` +
    `<span><b>${n(p2.per_question.none)}</b> without a hint</span><span><b>${n(p2.per_question.user)}</b> with the user hint</span>` +
    `<span><b>${n(p2.per_question.tool)}</b> with the tool hint</span></div>` +
    `<div class="tot">${p2.runs_without} runs without a hint (every question); ${p2.runs_with} with a hint, on the questions each model was unsure about</div></div>`;

  // Test 1: one series, all six models
  const s1 = [{ key: "followed", name: "Picked the hint’s wrong option", color: C.user }];
  hbar($("c-test1"), d.test1.map((m) => ({ label: m.name, values: { followed: m.followed },
    extra: [["Without a hint, picked that letter", of(m.same_letter_no_hint)], ["Correct without a hint", of(m.accuracy_no_hint)],
            ["Correct with the right hint", of(m.right_hint_accuracy)]] })), s1);
  const zero = d.test1.every((m) => m.same_letter_no_hint.k === 0);
  $("n-test1").textContent = zero ? `Without a hint: 0 of ${d.test1[0].same_letter_no_hint.n} runs per model picked the hint’s letter.`
                                  : "Without a hint: see the table.";
  table($("t-test1"), ["Model", "Picked the hint’s wrong option", "Same letter without a hint", "Correct without a hint"],
        d.test1.map((m) => [m.name, of(m.followed), of(m.same_letter_no_hint), of(m.accuracy_no_hint)]));

  // Test 2: user hint vs tool hint, plus the same letter without a hint
  const s2 = [{ key: "user", name: "User hint", color: C.user, unit: " questions" },
              { key: "tool", name: "Tool hint", color: C.tool, unit: " questions" },
              { key: "without", name: "Without a hint (same letter)", dashed: true, unit: " runs" }];
  legend($("l-test2"), s2);
  hbar($("c-test2"), d.test2.map((m) => ({ label: m.name, sub: `(${m.questions} questions)`,
    values: { user: m.user, tool: m.tool, without: m.without },
    extra: [["Final answer mentions the user hint", of(m.user_final_mention)], ["Final answer mentions the tool hint", of(m.tool_final_mention)]]
      .concat(m.tool_private_mention ? [["Private reasoning mentions the tool hint", of(m.tool_private_mention)]] : []) })), s2);
  table($("t-test2"), ["Model", "Questions", "User hint", "Tool hint", "Without a hint (runs)"],
        d.test2.map((m) => [m.name, m.questions, of(m.user), of(m.tool), of(m.without)]));

  // mentions: private reasoning vs final answer, all six models
  const s3 = [{ key: "private", name: "Private reasoning mentions the hint", color: C.private, na: "no private reasoning" },
              { key: "final", name: "Final answer mentions the hint", color: C.final }];
  legend($("l-ment"), s3);
  hbar($("c-ment"), d.mentions.map((m) => ({ label: m.name, values: { private: m.private, final: m.final } })), s3);
  $("n-ment").textContent = `The three thinking models together: private reasoning ${of(d.mention_totals.private)}, ` +
                            `final answer ${of(d.mention_totals.final)}. Instruct models have no private reasoning.`;
  table($("t-ment"), ["Model", "Private reasoning", "Final answer"], d.mentions.map((m) => [m.name, of(m.private), of(m.final)]));

  // thinking models: tool vs user, and what the tool-steered runs say
  const tt = d.thinking_tools;
  $("tiles").innerHTML = [
    ["tool", tt.tool_hint_followed, "questions where they picked the <b>tool</b> hint’s wrong option"],
    ["user", tt.user_hint_followed, "questions where they picked the <b>user</b> hint’s wrong option"],
    ["private", tt.tool_steered_private_mention, "tool-steered runs whose <b>private reasoning</b> mentions the tool"],
    ["final", tt.tool_steered_final_mention, "tool-steered runs whose <b>final answer</b> mentions the tool"],
  ].map(([cls, x, what]) => `<div class="tile ${cls}"><div class="k">${x.k} <small>of ${x.n} · ${pct(x)}%</small></div>` +
                            `<div class="what">${what}</div></div>`).join("");
}

fetch("/api/charts").then((r) => r.json()).then((d) => {
  DATA = d;
  const files = Object.values(d.inputs_unchanged), ok = files.every((x) => x === true);
  $("source").innerHTML = `All numbers come from <code>${esc(d.summary)}</code>, computed by <code>${esc(d.generated_by)}</code> ` +
    `from the saved runs. ` + (ok ? `Its ${files.length} input files are unchanged on disk (SHA-256 checked).`
                                  : `<span class="warn">Some input files changed since the summary was written; rerun analyze_progress.py.</span>`);
  render();
  let t = null;
  addEventListener("resize", () => { clearTimeout(t); t = setTimeout(render, 150); });
});
