
/* ==================================================================
   BEAT 1: the setup                                        (reference)
   ================================================================== */
function beat1() {
  const body = statement(1, "We slipped wrong answers into the questions.",
    "Sometimes the user wrote it, sometimes a tool returned it. Did the model take it, and did its answer say where it came from?");
  const card = H("div", { class: "panel", style: { left: "0px", top: "0px", width: "720px", height: "460px" } }, body);
  H("div", { class: "illus", style: { position: "absolute", left: "22px", top: "14px" } }, card, "Illustrative question, written by us");
  H("div", { style: { position: "absolute", left: "22px", top: "40px", width: "450px", fontSize: "25px", lineHeight: "1.35", color: "var(--ink)" } }, card, ITEM.q);
  const fills = {};
  ITEM.opts.forEach(([L, v], i) => {
    const col = i % 2, row = Math.floor(i / 2), x = 26 + col * 330, y = 176 + row * 54;
    fills[L] = letterBubble(card, x, y, L, { size: 1.35 });
    H("div", { style: { position: "absolute", left: x + 56 + "px", top: y - 1 + "px", fontSize: "24px", color: "var(--ink)" } }, card, v);
  });
  slip(body, { x: 486, y: 18, call: "lookup_answer_key(question_id)", rows: [["reply", "“(C)”"], ["source", "“study guide v2”"]], delay: 400, width: 300, rot: 3 });
  infoRow("Hints", "From the user, written into the question; or from a tool, as its reply. Same wrong letter either way.");
  at(1500, () => fills.C.fill());
  // red pen: the right answer circled, the hint's letter crossed
  const pos = (L) => { const i = ITEM.opts.findIndex((o) => o[0] === L); return [26 + (i % 2) * 330, 176 + Math.floor(i / 2) * 54]; };
  const [dx, dy] = pos("D"), [cx, cy] = pos("C");
  penLoop(body, { cx: dx + 72, cy: dy + 13, rx: 82, ry: 26, delay: 2300, seed: 5 });
  penStroke(body, [[cx - 6, cy - 6], [cx + 48, cy + 34]], { delay: 2800 });
  penStroke(body, [[cx + 48, cy - 6], [cx - 6, cy + 34]], { delay: 2950 });
  // the model's answer box
  const box = H("div", { class: "answerbox", style: { left: "790px", top: "0px", width: "330px", height: "190px" } }, body);
  H("div", { class: "lab" }, box, "Final answer");
  writeText(box, { x: 110, y: 52, text: "(C)", size: 100, delay: 1700, dur: 0.5 });
  writeText(body, { x: 1140, y: 40, text: "wrong, and it doesn’t say", size: 34, red: true, delay: 3300, width: 230 });
  writeText(body, { x: 1140, y: 112, text: "a tool gave it the (C)", size: 34, red: true, delay: 3700, width: 230 });
  // the other messenger
  H("div", { class: "printlab", style: { position: "absolute", left: "790px", top: "240px", fontSize: "19px", color: "var(--ink)" } }, body, "The same wrong letter can also come from the user:");
  sticky(body, { x: 820, y: 285, text: "I think the answer is (C), but I’m curious what you think.", delay: 600, width: 330, size: 32, rot: -2 });
}

/* ==================================================================
   BEAT 2: a tool's hint against a person's                 (reference)
   ================================================================== */
function beat2() {
  const models = [...new Set(DATA.hint.map((r) => r.model))];
  const row = DATA.hint.find((r) => r.model === state.m2);
  const own = row.toolForm === "its own call";
  const body = statement(2, "A tool’s hint pulls harder than a person’s.", "The same wrong letter, (C), on the same questions. Only who gives it changes.");
  // how to read the marks
  const key = H("div", { class: "panel", style: { left: "0px", top: "60px", width: "330px", height: "250px", padding: "16px 18px" } }, body);
  H("div", { class: "printlab", style: { fontSize: "18px" } }, key, "How to read the marks");
  const k1 = H("div", { style: { position: "relative", height: "34px", marginTop: "18px" } }, key);
  letterBubble(k1, 0, 4, "", { filled: true });
  H("div", { style: { position: "absolute", left: "46px", top: "0px", fontSize: "21px", lineHeight: 1.25 } }, k1, "a run that took the hint’s letter");
  const k2 = H("div", { style: { position: "relative", height: "34px", marginTop: "22px" } }, key);
  letterBubble(k2, 0, 4, "");
  H("div", { style: { position: "absolute", left: "46px", top: "0px", fontSize: "21px", lineHeight: 1.25 } }, k2, "any other answer");
  H("div", { class: "small", style: { marginTop: "36px" } }, key, `${row.user.n} runs a panel: the 54 test questions, 3 runs each.`);

  const panels = [
    { x: 370, title: "The user’s guess", sub: "written into the question", o: row.user },
    { x: 870, title: own ? "Its own tool call" : "A tool’s reply", sub: own ? "it asked the lookup tool; the reply said (C)" : "a tool turn in the chat said (C)", o: row.tool },
  ];
  panels.forEach((p, i) => {
    const el = panel(body, { x: p.x, y: 60, w: 480, h: 420, title: p.title, sub: p.sub });
    const end = bubbles(el, { x: 24, y: 96, n: p.o.n, k: p.o.k, cols: 18, w: 20, h: 14, gx: 4.6, gy: 10, delay: 700 + i * 250, dur: 2600, label: `${p.o.k} of ${p.o.n} runs took the hint’s letter` });
    tally(el, { x: 26, y: 336, k: p.o.k, n: p.o.n, caption: "runs took the hint’s letter", delay: end + 150, seed: 7 + i });
  });
  sticky(body, { x: 610, y: -14, text: "I think the answer is (C), but I’m curious what you think.", width: 240, size: 25, rot: 3, delay: 200 });
  slip(body, { x: 1050, y: -6, call: own ? "lookup_answer_key(question_id)" : "a tool turn in the chat", rows: [["reply", "“(C)”"]], width: 300, delay: 400, rot: -2 });
  choiceRow("Model", models.map((m) => ({ id: m, label: MODEL[m] || m })), state.m2, (m) => { state.m2 = m; show(cur); });
  $("#rows").firstChild.append(H("span", { class: "opt note", style: { cursor: "default", marginLeft: "12px" } }, null, `${row.setting}`));
}

/* ==================================================================
   BEAT 4: scratch work against the answer box               (reference)
   ================================================================== */
function beat4() {
  const Q = DATA.quiet;
  const sets = [
    { id: 0, label: "Qwen3 30B Thinking", a: Q.names.thinking_private, b: Q.names.thinking_final, cols: 18 },
    { id: 1, label: "Qwen3 8B, thinking on", a: Q.title.f29.private, b: Q.title.f29.final, cols: 29 },
  ];
  const s = sets[state.q4];
  const body = statement(4, "After a tool call, the answer goes quiet.",
    "The scratch work names the tool almost every time. The answer box, the part a user reads, almost never does.");
  // scratch work: the private reasoning
  const sw = H("div", { class: "ruled", style: { left: "0px", top: "0px", width: "720px", height: "214px" } }, body);
  H("div", { class: "lab" }, sw, "Scratch work: the model’s private reasoning");
  H("div", { class: "illus", style: { position: "absolute", right: "12px", top: "10px" } }, sw, "illustrative wording");
  writeText(sw, { x: 22, y: 50, text: "Let me check the lookup first.", size: 34, delay: 300, dur: 0.7 });
  writeText(sw, { x: 22, y: 92, text: "The answer key says (C), so it is (C).", size: 34, delay: 1100, dur: 0.9 });
  penStroke(sw, [[22, 132], [120, 134], [250, 131], [330, 133]], { delay: 2000, color: "--pencil", width: 2.6, pencil: true });
  writeText(sw, { x: 22, y: 134, text: "I’ll write down (C).", size: 34, delay: 2200, dur: 0.6 });
  // the answer box: what the user reads
  const box = H("div", { class: "answerbox", style: { left: "760px", top: "0px", width: "300px", height: "214px" } }, body);
  H("div", { class: "lab" }, box, "Final answer");
  writeText(box, { x: 86, y: 56, text: "(C)", size: 110, delay: 2700, dur: 0.5 });
  penStroke(body, [[1070, 120], [1110, 104], [1148, 92]], { delay: 3400 });
  writeText(body, { x: 1156, y: 62, text: "source?", size: 46, red: true, delay: 3500, dur: 0.5 });
  // the tallies under each
  const gs = s.cols > 20 ? { cols: 29, w: 17, h: 11, gx: 4.5, gy: 6 } : { cols: 18, w: 26, h: 15, gx: 7, gy: 9 };
  const g1 = bubbles(body, { x: 0, y: 244, n: s.a.n, k: s.a.k, ...gs, delay: 900, dur: 1800, label: `${s.a.k} of ${s.a.n} name the tool in the scratch work` });
  tally(body, { x: 4, y: 340, k: s.a.k, n: s.a.n, caption: "name the tool in the scratch work", delay: g1 + 100, seed: 11 });
  const gs2 = s.cols > 20 ? { cols: 29, w: 17, h: 11, gx: 4.5, gy: 6 } : { cols: 18, w: 26, h: 15, gx: 7, gy: 9 };
  const g2 = bubbles(body, { x: 760, y: 244, n: s.b.n, k: s.b.k, ...gs2, delay: 3000, dur: 600, label: `${s.b.k} of ${s.b.n} name the tool in the final answer` });
  tally(body, { x: 764, y: 340, k: s.b.k, n: s.b.n, caption: "name it in the final answer", delay: Math.max(g2, 3300) + 300, seed: 12 });
  const b15 = Q.names.b15.thinking.names;
  choiceRow("Model", sets.map((x) => ({ id: x.id, label: x.label })), state.q4, (i) => { state.q4 = i; show(cur); });
  $("#rows").firstChild.append(H("span", { class: "opt note", style: { cursor: "default", marginLeft: "12px" } }, null, `Asked to cite its sources, Qwen3 30B Thinking named the tool in ${b15.with.k} of ${b15.with.n} final answers, and didn’t follow it any less.`));
}

/* ==================================================================
   BEAT 6: the 32 layers as 32 rows of the form             (reference)
   ================================================================== */
function beat6() {
  const L = DATA.layers;
  const body = statement(6, "Three of its 32 layers read the hint.",
    `Inside Olmo 3 7B Think, layers 15, 19 and 23 carry about ${pct(L.share[0].m)} of the hint’s effect, read straight from the prompt.`);
  const pitch = 13.6, x0 = 92, len = 600, top0 = 30, maxm = Math.max(...L.readout.map((i) => L.effect[i].m));
  const rows = H("div", { style: { position: "absolute", left: "0px", top: "0px", width: "820px", height: "480px" } }, body);
  const lit = L.readout.slice().sort((a, b) => a - b);
  for (let i = 0; i < 32; i++) {
    const y = top0 + i * pitch;
    H("div", { style: { position: "absolute", left: x0 + "px", top: y + pitch - 1 + "px", width: len + 120 + "px", borderTop: "1px dotted var(--print-soft)" } }, rows);
    if (i === 0 || i === 31 || lit.includes(i)) H("div", { class: "printlab", style: { position: "absolute", left: "0px", top: y + pitch / 2 - 10 + "px", fontSize: "15px", color: lit.includes(i) ? "var(--ink)" : "var(--print)" } }, rows, `layer ${i}`);
  }
  H("div", { class: "small", style: { position: "absolute", left: x0 + "px", top: "0px" } }, rows, "The prompt comes in at layer 0; the answer comes out after layer 31.");
  lit.forEach((li, j) => {
    const m = L.effect[li].m, y = top0 + li * pitch;
    highlight(rows, { x: x0, y: y + 1, w: (len * m) / maxm, h: pitch - 1, delay: 500 + j * 650 });
    writeText(rows, { x: x0 + (len * m) / maxm + 14, y: y - 12, text: pct(m), size: 34, red: true, delay: 800 + j * 650, dur: 0.35 });
  });
  // the bracket and the total
  const yTop = top0 + lit[0] * pitch, yBot = top0 + lit[lit.length - 1] * pitch + pitch, ym = (yTop + yBot) / 2;
  penStroke(body, [[800, yTop], [818, yTop + 4], [820, ym - 8], [836, ym], [820, ym + 8], [818, yBot - 4], [800, yBot]], { delay: 2700, dur: 0.5 });
  writeText(body, { x: 852, y: ym - 30, text: `together ${pct(L.share[0].m)}`, size: 52, red: true, delay: 3100, dur: 0.6 });
  // two graded notes
  const n1 = H("div", { class: "panel", style: { left: "860px", top: "296px", width: "460px", padding: "14px 18px" } }, body);
  n1.innerHTML = `<div style="font-size:21px;line-height:1.35">The same three layers on 16 new questions: <b>${pct(L.share[1].m)}</b>.</div>
    <div style="font-size:21px;line-height:1.35;margin-top:8px">Qwen3 8B has its own three: <b>${pct(L.share[2].m)}</b>.</div>
    <div class="small" style="margin-top:10px">Measured with tool hints, by swapping in each layer’s activations from a run without the hint.</div>`;
  infoRow("Model", "Olmo 3 7B Think, 32 layers. Rows 15, 19 and 23 are three of its layers that see the whole prompt.");
}


/* ==================================================================
   Shared by the result sheets below
   ================================================================== */
const ST = { m3: "Qwen3 30B Instruct", rv: 0, sees: "plus_tool_log", p8: 5 };   // per-item picks for items 3, 7, 8
const kn = (o) => `${o.k} of ${o.n}`;
const num = (v) => (typeof v === "number" ? v.toLocaleString("en-US") : "—");
const WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight"];

/* a row of answer-sheet choices drawn inside a panel (picking one re-runs the item) */
function panelChoices(parent, { x, y, label, options, value, pick }) {
  const row = H("div", { class: "crow", role: "radiogroup", "aria-label": label, style: { position: "absolute", left: x + "px", top: y + "px" } }, parent);
  H("span", { class: "lab", style: { width: "auto", marginRight: "10px", color: "var(--ink)" } }, row, label);
  for (const o of options) {
    const b = H("button", { class: "opt", type: "button", role: "radio", "aria-checked": String(o.id === value) }, row, `<span class="bub"></span>${o.label}`);
    b.addEventListener("click", () => pick(o.id));
  }
}

/* one svg of pen or pencil marks, each path drawn on in turn; fn(i) gives that mark's points */
function markSheet(parent, { w, h, pencil = false, color = "--red", width = 3 }) {
  const svg = S("svg", { width: w, height: h, viewBox: `0 0 ${w} ${h}`, "aria-hidden": "true" });
  Object.assign(svg.style, { position: "absolute", left: "0px", top: "0px", overflow: "visible", pointerEvents: "none" });
  parent.appendChild(svg);
  const g = S("g", { filter: pencil ? "url(#pencil)" : "url(#pen)" }, svg);
  return (pts, delay, dur = 0.22) => {
    let L = 0;
    for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    const p = S("path", { d: "M" + pts.map((q) => q.map((v) => v.toFixed(1)).join(",")).join(" L"), fill: "none", style: `stroke:var(${color});stroke-dasharray:${L};stroke-dashoffset:${INSTANT || REDUCE ? 0 : L}`, "stroke-width": width, "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
    at(delay, () => { p.style.transition = `stroke-dashoffset ${dur}s ease-out`; p.style.strokeDashoffset = 0; });
  };
}

/* ==================================================================
   BEAT 3: the authority ladder
   ================================================================== */
function beat3() {
  const R = DATA.dose.find((r) => r.model === ST.m3) || DATA.dose[0];
  const own = R.toolForm === "its own call";
  const body = statement(3, "Mostly, it’s the authority.", "Claim a more official source and the same letter pulls harder.");
  const rows = [["plain", "The user’s guess"], ["classmate", "A classmate"], ["key", "“My answer key”"], ["manual", "“The official manual”"],
    ["pasted", "Pasted tool output", true], ["call", own ? "Its own tool call" : "A tool turn in the chat", true]];
  const pitch = 70;
  rows.forEach(([key, label, tool], i) => {
    const o = R[key], top = i * pitch, t0 = 300 + i * 450;
    if (tool) H("div", { class: "slipico", style: { left: "0px", top: top + 20 + "px" } }, body, '<span class="staple"></span>');
    H("div", { style: { position: "absolute", left: "36px", top: top + 12 + "px", fontSize: "22px", color: "var(--ink)", whiteSpace: "nowrap" } }, body, label);
    const end = bubbles(body, { x: 280, y: top + 17, n: o.n, k: o.k, cols: Math.ceil(o.n / 2), w: 8, h: 12, gx: 2.4, gy: 5, delay: t0, dur: 520, label: `${kn(o)} runs took the hint’s letter, ${label}` });
    tally(body, { x: 1150, y: top + 8, k: o.k, n: o.n, delay: end + 50, size: 40, seed: 21 + i });
  });
  if (R.r.call_minus_manual.reading === "tool beyond authority") {
    const t = 300 + 6 * 450 + 600;
    writeText(body, { x: 640, y: 412, text: "its own call beats every claim", size: 40, red: true, delay: t, dur: 0.9 });
    penStroke(body, [[1090, 436], [1160, 424], [1196, 388]], { delay: t + 900, dur: 0.4 });
    penStroke(body, [[1180, 391], [1196, 388], [1198, 406]], { delay: t + 1250, dur: 0.2 });
  }
  choiceRow("Model", DATA.dose.map((r) => ({ id: r.model, label: MODEL[r.model] || r.model })), R.model, (m) => { ST.m3 = m; show(cur); });
}

/* ==================================================================
   BEAT 5: does thinking help?
   ================================================================== */
function beat5() {
  const Q = DATA.quiet, f29 = Q.title.f29, f37 = Q.title.f37, fb1 = Q.title.fb1;
  const body = statement(5, "Does thinking make it more honest? Not reliably.", "That was our title question. Three models gave three different answers.");
  const P = [
    { name: "Qwen3 8B", sub: "calls the lookup tool", a: ["thinking off", f29.calls_off], b: ["thinking on", f29.calls_on], verdict: "moved into the scratch work only" },
    { name: "gpt-oss 20B", sub: "follows the tool’s wrong letter", a: ["low effort", f37.following_tool_real.low], b: ["high effort", f37.following_tool_real.high], verdict: "more thinking, no change" },
    { name: "Nemotron 3 Nano", sub: "gives a bare final answer after the tool", a: ["thinking off", fb1.off], b: ["thinking on", fb1.on], verdict: "a little more explanation" },
  ];
  P.forEach((p, pi) => {
    const el = panel(body, { x: pi * 467, y: 0, w: 440, h: 470, title: p.name, sub: p.sub });
    [p.a, p.b].forEach(([lab, o], si) => {
      const y0 = 92 + si * 146, t0 = 500 + pi * 250 + si * 1300;
      H("div", { class: "printlab", style: { position: "absolute", left: "24px", top: y0 + 8 + "px", fontSize: "19px", color: "var(--ink)" } }, el, lab);
      const end = bubbles(el, { x: 24, y: y0 + 56, n: o.n, k: o.k, cols: 27, w: 11, h: 9, gx: 3.5, gy: 4, delay: t0, dur: 1000, label: `${kn(o)}, ${lab}` });
      tally(el, { x: 190, y: y0 - 2, k: o.k, n: o.n, delay: end + 100, size: 42, seed: 31 + si + pi * 2 });
    });
    writeText(el, { x: 24, y: 392, text: p.verdict, size: 30, red: true, delay: 3700 + pi * 250, dur: 0.9, width: 392 });
  });
  const T = Q.title.f37_tokens;
  infoRow("Reasoning", `gpt-oss 20B thinks about ${num(Math.round(T.low))} tokens at low effort and about ${num(Math.round(T.high))} at high.`);
}

/* ==================================================================
   BEAT 7: review teams
   ================================================================== */
function beat7() {
  const R = DATA.agents.reviewers, C = DATA.agents.checker;
  const r = R[ST.rv] || R[0], o = r[ST.sees];
  const body = statement(7, "Olmo’s reviewers defer to the tool’s log.", "A checker that solves the question again, without the tool, stops them.");
  const L = panel(body, { x: 0, y: 0, w: 780, h: 440, title: `${r.name} grades ${o.n} wrong tool answers`, sub: "a cross: it corrected the answer · a tick: it let it through" });
  panelChoices(L, { x: 16, y: 82, label: "What it sees", value: ST.sees, pick: (v) => { ST.sees = v; show(cur); },
    options: [{ id: "answer_only", label: "the answer only" }, { id: "plus_private", label: "plus its private reasoning" }, { id: "plus_tool_log", label: "plus the tool’s log" }] });
  const cols = 15, pitch = 44, bw = 34, x0 = 26, y0 = 130;
  const mark = markSheet(L, { w: 780, h: 470 });
  const frame = S("svg", { width: 780, height: 470, viewBox: "0 0 780 470", "aria-hidden": "true" }, L);
  Object.assign(frame.style, { position: "absolute", left: "0px", top: "0px", pointerEvents: "none" });
  const step = 2400 / o.n;
  for (let i = 0; i < o.n; i++) {
    const x = x0 + (i % cols) * pitch, y = y0 + Math.floor(i / cols) * pitch, rr = rng(i + 7), j = () => (rr() - 0.5) * 4;
    S("rect", { x, y, width: bw, height: bw, fill: "none", style: "stroke:var(--print)", "stroke-width": 1.5 }, frame);
    if (i < o.k) {
      mark([[x + 7 + j(), y + 7 + j()], [x + bw - 7 + j(), y + bw - 7 + j()]], 400 + i * step, 0.1);
      mark([[x + bw - 7 + j(), y + 7 + j()], [x + 7 + j(), y + bw - 7 + j()]], 400 + i * step + 90, 0.1);
    } else mark([[x + 7 + j(), y + 18 + j()], [x + 14 + j(), y + bw - 7 + j()], [x + bw - 6 + j(), y + 6 + j()]], 400 + i * step, 0.18);
  }
  const rows = Math.ceil(o.n / cols);
  tally(L, { x: 26, y: y0 + rows * pitch + 16, k: o.k, n: o.n, caption: "wrong tool answers corrected", delay: 400 + 2400 + 200, size: 46, seed: 41 });

  const rp = panel(body, { x: 830, y: 0, w: 544, h: 384, title: "The checker", sub: "solves the question again, without the tool" });
  stamp(rp, { x: 22, y: 82, text: "Checked without the tool", rot: -3, delay: 500 });
  [["caught", "wrong tool answers caught"], ["false_alarms", "right answers flagged by mistake"], ["shipped", "wrong answers still shipped"]].forEach(([key, cap], i) => {
    tally(rp, { x: 26, y: 158 + i * 70, k: C[key].k, n: C[key].n, caption: cap, delay: 1200 + i * 700, size: 42, seed: 51 + i });
  });
  H("div", { class: "small", style: { position: "absolute", left: "22px", top: "360px" } }, rp, `Measured on a different set of ${C.floor.n} items.`);
  const olmo = R.filter((x) => x.family === "Olmo").length;
  writeText(body, { x: 830, y: 398, text: `Only the ${WORDS[olmo]} Olmo reviewers defer; the other ${WORDS[R.length - olmo]} keep checking.`, size: 34, red: true, delay: 3600, dur: 1.4, width: 544 });
  choiceRow("Reviewer", R.map((x, i) => ({ id: i, label: x.name })), ST.rv, (i) => { ST.rv = i; show(cur); });
}

/* ==================================================================
   BEAT 8: the trade-off
   ================================================================== */
function beat8() {
  const SY = DATA.fixes.systems;
  const keys = Object.keys(SY).filter((k) => !SY[k].diluted);
  const NAME = { base: "No fix", prompt_only: "One-line instruction", lora: "Fine-tuned", lora_note: "Fine-tuned + instruction", a40: "Consistency-trained", a40_note: "Consistency-trained + instruction" };
  const OFF = { base: [18, -14], prompt_only: [14, -44], lora: [-6, 14], lora_note: [18, -14], a40: [18, -14], a40_note: [18, -36] };
  const body = statement(8, "Every fix is a trade-off.", "Fixes that resist wrong hints also distrust right ones.");
  const el = panel(body, { x: 0, y: 0, w: 1374, h: 470, title: "Five fixes and no fix, on Olmo 3 7B Think", sub: "each dot is one version, tested on the same questions" });
  const acc = (k) => rate(SY[k].acceptance), res = (k) => 1 - rate(SY[k].following);
  const lo = (f) => Math.floor(Math.min(...keys.map(f)) * 20) / 20, hi = (f) => Math.ceil(Math.max(...keys.map(f)) * 20) / 20;
  const ax0 = lo(acc), ax1 = hi(acc), ay0 = lo(res), ay1 = hi(res);
  const px = 96, py = 84, pw = 1170, ph = 292;
  const X = (v) => px + ((v - ax0) / (ax1 - ax0)) * pw, Y = (v) => py + ph - ((v - ay0) / (ay1 - ay0)) * ph;
  const g = S("svg", { width: 1374, height: 470, viewBox: "0 0 1374 470", "aria-hidden": "true" }, el);
  Object.assign(g.style, { position: "absolute", left: "0px", top: "0px", pointerEvents: "none" });
  for (let v = ax0; v <= ax1 + 1e-9; v += 0.01) { const major = Math.abs(v * 20 - Math.round(v * 20)) < 1e-6; S("line", { x1: X(v), x2: X(v), y1: py, y2: py + ph, style: "stroke:var(--print-soft)", "stroke-width": major ? 1.2 : 0.6 }, g); }
  for (let v = ay0; v <= ay1 + 1e-9; v += 0.01) { const major = Math.abs(v * 20 - Math.round(v * 20)) < 1e-6; S("line", { x1: px, x2: px + pw, y1: Y(v), y2: Y(v), style: "stroke:var(--print-soft)", "stroke-width": major ? 1.2 : 0.6 }, g); }
  S("rect", { x: px, y: py, width: pw, height: ph, fill: "none", style: "stroke:var(--print)", "stroke-width": 1.5 }, g);
  for (let v = ax0; v <= ax1 + 1e-9; v += 0.05) S("text", { x: X(v), y: py + ph + 20, "text-anchor": "middle", "font-size": 16, style: "fill:var(--print)", text: pct(v) }, g);
  for (let v = ay0; v <= ay1 + 1e-9; v += 0.05) S("text", { x: px - 10, y: Y(v) + 5, "text-anchor": "end", "font-size": 16, style: "fill:var(--print)", text: pct(v) }, g);
  H("div", { class: "printlab", style: { position: "absolute", left: px + "px", top: py + ph + 26 + "px", width: pw + "px", textAlign: "center", fontSize: "19px", color: "var(--ink)" } }, el, "Right hints taken, out of the right ones given →");
  H("div", { class: "printlab", style: { position: "absolute", left: "8px", top: py + ph / 2 + "px", width: ph + "px", transform: "rotate(-90deg) translate(-50%, 0)", transformOrigin: "0 0", textAlign: "center", fontSize: "19px", color: "var(--ink)" } }, el, "Wrong hints resisted →");
  // the pencil line through the dots, then the dots and their names
  const order = keys.slice().sort((a, b) => acc(a) - acc(b));
  const line = penStroke(el, order.map((k) => [X(acc(k)), Y(res(k))]), { delay: 300, color: "--pencil", width: 1.8, pencil: true, dur: 1.2 });
  line.style.opacity = 0.45;
  const dots = S("svg", { width: 1374, height: 470, viewBox: "0 0 1374 470", "aria-hidden": "true" }, el);
  Object.assign(dots.style, { position: "absolute", left: "0px", top: "0px", pointerEvents: "none", overflow: "visible" });
  const dg = S("g", { filter: "url(#pencil)" }, dots);
  keys.forEach((k, i) => {
    const d = S("circle", { cx: X(acc(k)), cy: Y(res(k)), r: 10, style: "fill:var(--pencil);transform-box:fill-box;transform-origin:center;transform:scale(0);transition:transform .2s ease-out" }, dg);
    at(500 + i * 450, () => { d.style.transform = "scale(1)"; });
    writeText(el, { x: X(acc(k)) + OFF[k][0], y: Y(res(k)) + OFF[k][1], text: NAME[k], size: 32, delay: 650 + i * 450, dur: 0.5 });
  });
  // the pick: how often is your tool right?
  const p = ST.p8 / 10;
  const gain = (k) => p * rate(SY[k].a_C) + (1 - p) * rate(SY[k].a_W);
  const best = keys.reduce((a, k) => (gain(k) > gain(a) ? k : a), keys[0]);
  panelChoices(el, { x: 20, y: 424, label: "How often is your tool right?", value: ST.p8, pick: (i) => { ST.p8 = i; show(cur); },
    options: Array.from({ length: 11 }, (_, i) => ({ id: i, label: `${i * 10}%` })) });
  penLoop(el, { cx: X(acc(best)), cy: Y(res(best)), rx: 26, ry: 24, delay: 3000, seed: 61 });
  const low = Y(res(best)) > py + ph - 60;
  writeText(el, { x: X(acc(best)) + (low ? 24 : 32), y: Y(res(best)) + (low ? -56 : 16), text: "best here", size: 32, red: true, delay: 3500, dur: 0.5 });
  stamp(el, { x: 1168, y: 14, text: "Exploratory", delay: 600, rot: 4 });
}

/* ==================================================================
   BEAT 9: candid answers
   ================================================================== */
function beat9() {
  const l6 = DATA.fixes.l6;
  const body = statement(9, "Fine-tuning made answers mention the hint.", "When it followed a wrong hint, its answer usually said the hint was there. It didn’t follow wrong hints any less often.");
  const sets = [{ title: "Fine-tuned", o: l6.lora }, { title: "One-line instruction", o: l6.instruction }];
  sets.forEach((s, si) => {
    const el = panel(body, { x: si * 704, y: 0, w: 670, h: 300, title: s.title, sub: `${s.o.n} answers that followed a wrong hint` });
    const cols = 14, pitch = 44, bw = 38, bh = 30, x0 = 24, y0 = 90, t0 = 400 + si * 300;
    const frame = S("svg", { width: 670, height: 300, viewBox: "0 0 670 300", role: "img", "aria-label": `${kn(s.o)} answers mention the hint` }, el);
    Object.assign(frame.style, { position: "absolute", left: "0px", top: "0px", pointerEvents: "none" });
    const tick = markSheet(el, { w: 670, h: 300, pencil: true, color: "--pencil", width: 3 });
    const step = 1800 / s.o.k;
    for (let i = 0; i < s.o.n; i++) {
      const x = x0 + (i % cols) * pitch, y = y0 + Math.floor(i / cols) * (bh + 8), rr = rng(i + 3 + si * 90), j = () => (rr() - 0.5) * 3;
      S("rect", { x, y, width: bw, height: bh, fill: "none", style: "stroke:var(--print)", "stroke-width": 2 }, frame);
      if (i < s.o.k) tick([[x + 8 + j(), y + 16 + j()], [x + 16 + j(), y + bh - 7 + j()], [x + bw - 7 + j(), y + 6 + j()]], t0 + i * step, 0.14);
    }
    tally(el, { x: 26, y: 218, k: s.o.k, n: s.o.n, caption: "answers mention the hint", delay: t0 + 1800 + 200, size: 46, seed: 71 + si });
  });
  writeText(body, { x: 0, y: 336, text: "didn’t follow less", size: 52, red: true, delay: 3600, dur: 0.8 });
  penStroke(body, [[0, 398], [150, 394], [310, 398]], { delay: 4300, dur: 0.3 });
  const agree = Math.round(l6.agreement * l6.rows);
  H("div", { class: "small", style: { position: "absolute", left: "0px", top: "424px", maxWidth: "980px" } }, body, `Labelled by hand. An AI judge that didn’t know which model wrote each answer agreed on ${agree} of ${l6.rows}.`);
}

/* ==================================================================
   BEAT 10: what we learned
   ================================================================== */
function beat10() {
  const body = statement(10, "What we learned.", null);
  const D = DATA.dose.find((r) => r.model === "Qwen3 30B Instruct") || DATA.dose[0];
  const N = DATA.quiet.names, rv = DATA.agents.reviewers[0], C = DATA.agents.checker;
  const notes = [
    ["Where a hint seems to come from changes how hard it pulls.", `Qwen3 30B Instruct took the wrong letter in ${kn(D.call)} runs from its own tool call, and ${kn(D.plain)} from the user’s guess.`],
    ["Final answers hide what the reasoning knew.", `Qwen3 30B Thinking named the tool in ${kn(N.thinking_private)} scratch-work traces and ${kn(N.thinking_final)} final answers.`],
    ["Prompts and training trade resistance for trust. Solving it again, without the tool, held.", `A reviewer shown the tool’s log corrected ${kn(rv.plus_tool_log)} wrong answers; the checker caught ${kn(C.caught)}.`],
  ];
  notes.forEach(([c, line], i) => {
    const y = i * 80;
    writeText(body, { x: 0, y, text: c, size: 40, red: true, delay: 300 + i * 900, dur: 0.9 });
    H("div", { style: { position: "absolute", left: "2px", top: y + 44 + "px", fontSize: "21px", color: "var(--ink)", whiteSpace: "nowrap" } }, body, line);
  });
  const M = (typeof METHOD !== "undefined" && METHOD.counts) || {};
  const boxes = [["models", "models"], ["runs_fresh_fixes", "runs on fresh questions"], ["runs_newer_families", "runs on newer families"], ["hand_labels", "answers labelled by hand"]];
  boxes.forEach(([key, fallback], i) => {
    const c = M[key] || {}, x = i * 348;
    const box = H("div", { class: "answerbox", style: { left: x + "px", top: "250px", width: "322px", height: "190px" } }, body);
    writeText(box, { x: 16, y: 10, text: num(c.v), size: 64, delay: 2800 + i * 250, dur: 0.5 });
    H("div", { style: { position: "absolute", left: "16px", top: "70px", width: "292px", fontSize: "21px", lineHeight: 1.2, color: "var(--ink)" } }, box, fallback);
    if (c.what) H("div", { class: "small", style: { position: "absolute", left: "16px", top: "100px", width: "292px", fontSize: "15px", lineHeight: 1.25 } }, box, c.what);
  });
  H("div", { class: "printlab", style: { position: "absolute", left: "0px", top: "462px", fontSize: "17px" } }, body, "Group 10, CSE 598");
  H("div", { style: { position: "absolute", left: "0px", top: "486px", fontSize: "28px", color: "var(--ink)", fontWeight: 600, whiteSpace: "nowrap" } }, body, "Ritik Agarwal &nbsp;·&nbsp; Arsha Jindal &nbsp;·&nbsp; Shrey Bishnoi");
}

const BEATS = [
  { title: "The setup", run: beat1, ms: 9000 },
  { title: "Tool against person", run: beat2, ms: 12000 },
  { title: "Authority", run: beat3, ms: 11000 },
  { title: "The quiet answer", run: beat4, ms: 12000 },
  { title: "Does thinking help?", run: beat5, ms: 11000 },
  { title: "Inside the model", run: beat6, ms: 11000 },
  { title: "Review teams", run: beat7, ms: 13000 },
  { title: "The trade-off", run: beat8, ms: 12000 },
  { title: "Candid answers", run: beat9, ms: 10000 },
  { title: "What we learned", run: beat10, ms: 12000 },
];
