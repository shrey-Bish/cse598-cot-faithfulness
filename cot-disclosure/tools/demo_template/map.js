/* ===================================================================
   Part 1, how we did it: the project map (page 0) and its eleven steps (pages 1-11).
   Facts come from METHOD (method.json: each {v, src, at, what}) or DATA (the frozen summaries); nothing is typed here
   except plain wording. Marks come from marks.js; new ones are drawn in the same style.
   =================================================================== */
const MX = (typeof METHOD !== "undefined" && METHOD) || {};
const mv = (f, d) => (f && f.v !== undefined ? f.v : d);
const fmt = (n) => (typeof n === "number" ? n.toLocaleString("en-US") : String(n));
const ML = typeof RUNS !== "undefined" && RUNS && RUNS.method_local;     // the local build's two real training pairs
const MS = { page: -1, q: 0, hint: "user", hintMode: "wrong", model: 0, layer: 15, swapped: new Set(), view: "layer", fx: "lora", pair: 0, train: "lora", tv: "lora",
  dial: 1, rev: "plus_tool_log", boot: null, tl: null, sel: 0 };

/* step names: the strip and the map's buttons */
const STEPNAME = [null,
  { s: "Questions", t: "The questions" }, { s: "The hint", t: "The hint" }, { s: "Models", t: "The models" }, { s: "Running it", t: "Running it" },
  { s: "Architecture", t: "The architecture" }, { s: "The layers", t: "Checking the layers" }, { s: "Fine-tuning", t: "Fine-tuning" },
  { s: "Changes", t: "Training, inside" }, { s: "Other fixes", t: "The other fixes" }, { s: "Review team", t: "The review team" }, { s: "Checking", t: "Checking ourselves" },
];

function mpage(i, title, sub) {
  if (MS.page !== i) { MS.page = i; MS.swapped = new Set(); MS.layer = 15; MS.view = "layer"; MS.pair = 0; MS.boot = null; MS.sel = 0; }
  const beat = $("#beat");
  const strip = H("div", { class: "mstrip" }, beat);
  for (let k = 1; k <= 11; k++) {
    const b = H("button", { type: "button", class: "mcell", "aria-current": k === i ? "step" : "false", title: STEPNAME[k].t }, strip, `<span class="mnum">${k}</span><span>${STEPNAME[k].s}</span>`);
    b.addEventListener("click", () => show(k));
  }
  const body = statement(i, title, sub);
  const s = beat.querySelector(".sub"); if (s) { s.style.maxWidth = "1270px"; s.style.marginTop = "6px"; }
  const h = beat.querySelector(".stmt"); if (h) h.style.marginTop = "2px";
  return body;
}
function ptext(parent, x, y, w, html, size) {
  return H("div", { class: "ptext", style: { left: x + "px", top: y + "px", width: w + "px", ...(size ? { fontSize: size + "px" } : {}) } }, parent, html);
}
function plab(parent, x, y, w, html, cls = "plab", size) {
  return H("div", { class: cls, style: { left: x + "px", top: y + "px", ...(w ? { width: w + "px" } : {}), ...(size ? { fontSize: size + "px" } : {}) } }, parent, html);
}
/* a printed score box: a number written in pencil, its caption printed under it */
function sbox(parent, { x, y, w = 150, h = 84, n, label, delay = 0, red = false }) {
  const b = H("div", { class: "sbox", style: { left: x + "px", top: y + "px", width: w + "px", height: h + "px" } }, parent);
  writeText(b, { x: 12, y: 2, text: String(n), size: 46, red, delay, dur: 0.5 });
  H("div", { class: "l" }, b, label);
  return b;
}
function mpick(parent, { x, y, label, on, fn, disabled = false, w }) {
  const b = H("button", { type: "button", class: "mpick", "aria-pressed": String(!!on), "aria-disabled": String(disabled), style: { left: x + "px", top: y + "px", ...(w ? { width: w + "px" } : {}) } }, parent, `<span class="bub"></span>${label}`);
  if (!disabled) b.addEventListener("click", fn);
  return b;
}
function mbtn(parent, { x, y, w, text, fn, disabled = false }) {
  const b = H("button", { type: "button", class: "mbtn", style: { left: x + "px", top: y + "px", ...(w ? { width: w + "px" } : {}) } }, parent, text);
  b.disabled = disabled; if (!disabled) b.addEventListener("click", fn);
  return b;
}
function line(parent, x1, y1, x2, y2) {
  const svg = S("svg", { width: Math.abs(x2 - x1) + 16, height: Math.abs(y2 - y1) + 16, "aria-hidden": "true" });
  const mnx = Math.min(x1, x2) - 8, mny = Math.min(y1, y2) - 8;
  svg.setAttribute("viewBox", `${mnx} ${mny} ${Math.abs(x2 - x1) + 16} ${Math.abs(y2 - y1) + 16}`);
  Object.assign(svg.style, { position: "absolute", left: mnx + "px", top: mny + "px", overflow: "visible", pointerEvents: "none" });
  parent.appendChild(svg);
  S("line", { x1, y1, x2, y2, style: "stroke:var(--print)", "stroke-width": 1.6 }, svg);
  const a = Math.atan2(y2 - y1, x2 - x1), hx = 9;
  S("path", { d: `M${x2 - hx * Math.cos(a - 0.5)},${y2 - hx * Math.sin(a - 0.5)} L${x2},${y2} L${x2 - hx * Math.cos(a + 0.5)},${y2 - hx * Math.sin(a + 0.5)}`, fill: "none", style: "stroke:var(--print)", "stroke-width": 1.6 }, svg);
}

/* a pencilled bar: a filled stripe of graphite that draws from its start (a new mark, in the pencil style) */
function pbar(parent, { x, y, w, h, delay = 0 }) {
  const aw = Math.max(1, Math.abs(w)), svg = S("svg", { width: aw + 4, height: h + 4, viewBox: `-2 -2 ${aw + 4} ${h + 4}`, "aria-hidden": "true" });
  Object.assign(svg.style, { position: "absolute", left: (w < 0 ? x + w : x) - 2 + "px", top: y - 2 + "px", overflow: "visible", pointerEvents: "none" });
  parent.appendChild(svg);
  const r = S("rect", { x: 0, y: 0, width: aw, height: h, rx: 2, filter: "url(#pencil)", style: `fill:var(--pencil);transform-box:fill-box;transform-origin:${w < 0 ? "right" : "left"} center;transform:scaleX(${INSTANT || REDUCE ? 1 : 0});transition:transform .5s ease-out` }, svg);
  at(delay, () => { r.style.transform = "scaleX(1)"; });
  return r;
}

/* ------------------------------------------------------------------ page 0: the map */
function mapPage() {
  const beat = $("#beat");
  const body = statement("", "Every result here came through six stops.", "Click a step to open it. Esc comes back to this map; ← → move between steps.");
  beat.querySelector(".sub").style.maxWidth = "1270px";
  beat.querySelector(".stmt .no").textContent = "";
  const W = 190, GAP = (1374 - 6 * W) / 5, Y = 8, NH = 190;
  const nodes = [
    { t: "The questions", c: `${mv(MX.hint && MX.hint.options, []).length} options each`, steps: [1] },
    { t: "The hint", c: "one wrong letter", steps: [2] },
    { t: "The models", c: `${mv(MX.counts && MX.counts.models, "")} of them`, steps: [3, 4] },
    { t: "Inside the model", c: `${mv(MX.arch && MX.arch.layers, "")} layers`, steps: [5, 6] },
    { t: "What it wrote", c: "reasoning, then an answer", steps: [] },
    { t: "How we checked", c: "labels and statistics", steps: [11] },
  ];
  const X = (k) => k * (W + GAP);
  nodes.forEach((n, k) => {
    const box = H("div", { class: "mnode" + (n.steps.length ? "" : " plain"), style: { left: X(k) + "px", top: Y + "px", width: W + "px", height: NH + "px" } }, body, `<h3>${n.t}</h3><div class="cap">${n.c}</div>`);
    const rows = H("div", { class: "rows", style: { top: "112px" } }, box);
    n.steps.forEach((s) => {
      const b = H("button", { type: "button", class: "mstep", "aria-pressed": "false" }, rows, `<span class="mnum">${s}</span><span class="lab">${STEPNAME[s].s}</span>`);
      b.addEventListener("click", () => show(s));
    });
    if (k < 5) line(body, X(k) + W + 4, Y + 38, X(k + 1) - 4, Y + 38);
  });
  // branches
  const fx = H("div", { class: "mbox", style: { left: X(3) - 40 + "px", top: "262px", width: "270px", height: "180px" } }, body, `<h3>The fixes</h3><div class="cap">training and no-training fixes</div>`);
  const fr = H("div", { class: "rows", style: { top: "62px" } }, fx);
  [7, 8, 9].forEach((s) => H("button", { type: "button", class: "mstep" }, fr, `<span class="mnum">${s}</span><span class="lab">${STEPNAME[s].s}</span>`).addEventListener("click", () => show(s)));
  const rv = H("div", { class: "mbox", style: { left: X(5) - 80 + "px", top: "262px", width: "270px", height: "180px" } }, body, `<h3>The review team</h3><div class="cap">a second model checks the first</div>`);
  const rr = H("div", { class: "rows", style: { top: "62px" } }, rv);
  H("button", { type: "button", class: "mstep" }, rr, `<span class="mnum">10</span><span class="lab">${STEPNAME[10].s}</span>`).addEventListener("click", () => show(10));
  line(body, X(3) + W / 2, Y + NH + 4, X(3) + W / 2, 258);
  line(body, X(5) + W / 2, Y + NH + 4, X(5) + W / 2, 258);
  plab(body, 0, 262, 560, "Pencil brackets below mark the three tracks of work: <b>what each one looked at</b>. Steps 7 to 9 are fixes to the model; step 10 is a review team built around it.", "plab", 19);
  // the three tracks, marked in pencil
  const tracks = [
    { x1: X(1), x2: X(2) + W, label: "models and sources" },
    { x1: X(3) - 40, x2: X(3) + 230, label: "inside the model and the fixes" },
    { x1: X(5) - 80, x2: X(5) + 190, label: "downstream review" },
  ];
  tracks.forEach((t, j) => {
    penStroke(body, [[t.x1, 448], [t.x1 + 8, 457], [t.x2 - 8, 456], [t.x2, 448]], { delay: 500 + j * 500, color: "--pencil", pencil: true, width: 2.6 });
    writeText(body, { x: t.x1 + 6, y: 452, text: t.label, size: 36, delay: 800 + j * 500, dur: 0.8 });
  });
    infoRow("Map", `Each run reads left to right: a question, a hint, a model, what the model wrote, and how we checked it. ${mv(MX.counts && MX.counts.models, "")} models in all.`);
}

/* ------------------------------------------------------------------ step 1: the questions */
function step1() {
  const Q = MX.questions || {}, flip = mv(Q.flip, []);
  const body = mpage(1, "We drew the questions by seed, not by result.", "Ten options each. Every set was fixed before its runs, and the draws are reproducible.");
  const t54 = Q.test54 || {}, h30 = Q.heldout30 || {}, f120 = Q.fresh120 || {}, n16 = Q.new16 || {};
  ptext(body, 0, 0, 440, `Questions come from MMLU-Pro, a public benchmark, and from ${mv(t54.puzzles)} puzzles we generated. Each test used its own set, drawn once, with the seed kept.`);
  const bx = [
    [mv(t54.total), "test questions, 3 runs each"], [mv(h30.size), "held-out, for the first test of the fixes"],
    [mv(f120.size), "fresh, for the fixes"], [mv(n16.questions), "new, for the layer test"],
  ];
  bx.forEach(([n, l], k) => sbox(body, { x: (k % 2) * 220, y: 176 + Math.floor(k / 2) * 104, w: 206, h: 94, n: fmt(n), label: l, delay: 300 + k * 200 }));
  plab(body, 0, 394, 440, `The ${fmt(mv(f120.size))} were drawn by seed <b>${mv(f120.seed)}</b>: ${mv(f120.per_category)} each of ${mv(f120.categories, []).join(", ")}, none of them in the other sets.`);
  const r = flip[MS.q] || flip[0];
  if (r) {
    const pn = H("div", { class: "panel", style: { left: "470px", top: "0px", width: "904px", height: "482px" } }, body);
    H("div", { class: "illus", style: { position: "absolute", left: "16px", top: "10px" } }, pn, `A real question, unedited: ${r.set}. Drawn by seed.`);
    const qp = H("div", { class: "qpane", style: { left: "16px", top: "40px", width: "400px", height: "430px" } }, pn);
    H("div", { style: { fontSize: "21px", lineHeight: 1.36, color: "var(--ink)" } }, qp, r.question);
    H("div", { class: "pmuted", style: { position: "static", marginTop: "10px" } }, qp, `${r.category}, id ${r.id}`);
    const op = H("div", { class: "qpane", style: { left: "440px", top: "40px", width: "448px", height: "430px", paddingRight: "8px" } }, pn);
    r.options.forEach((o, k) => H("div", { class: "qopt" }, op, `<span class="lt">${"ABCDEFGHIJ"[k]}</span><span>${o.replace(/</g, "&lt;")}</span>`));
    at(0, () => { if (op.scrollHeight > op.clientHeight + 4) plab(pn, 700, 10, 190, "↓ scroll the options", "illus"); });
  }
  choiceRow("Question", flip.map((q, k) => ({ id: k, label: String(k + 1) })), MS.q, (k) => { MS.q = k; show(cur); }, "flip through six drawn at random with our seed");
}

/* ------------------------------------------------------------------ step 2: the hint */
function splitUser(text) {
  const parts = text.split("\n\n"), lines = parts[0].split("\n");
  return { q: lines[0], opts: lines.slice(1), hint: parts.length > 2 ? parts.slice(1, -1).join("\n\n") : null, ins: parts[parts.length - 1] };
}
function step2() {
  const Hn = MX.hint || {};
  const body = mpage(2, "The same wrong letter, seven ways in.", "Switch the source and read the exact prompt. Only who says it changes.");
  const srcs = Hn.sources || [], cur_ = srcs.find((s) => s.id === MS.hint) || srcs[0];
  const canRight = !!(Hn.right_hints && Hn.right_hints[cur_.id]);
  if (!canRight) MS.hintMode = "wrong";
  const turnsX = canRight && MS.hintMode === "right" ? Hn.right_hints[cur_.id].right.turns : (canRight ? Hn.right_hints[cur_.id].wrong.turns : cur_.turns);
  const u = splitUser(turnsX[0].text);
  const letter = MS.hintMode === "right" ? mv(Hn.right_letter) : mv(Hn.wrong_letter);
  ptext(body, 0, 0, 410, `Each test put the <b>same wrong letter</b>, (${mv(Hn.wrong_letter)}), in front of the model, from a different source: a person, a claim of authority, or a tool. These are the experiments' own templates, filled in with our illustrative question.`, 21);
  plab(body, 0, 236, 410, `The fixes also saw <b>right</b> hints (${mv(Hn.right_letter)}). Those were tool outputs only.`, "plab", 19);
  mpick(body, { x: 0, y: 300, label: `Wrong hint, (${mv(Hn.wrong_letter)})`, on: MS.hintMode === "wrong", fn: () => { MS.hintMode = "wrong"; show(cur); } });
  mpick(body, { x: 0, y: 336, label: `Right hint, (${mv(Hn.right_letter)})${canRight ? "" : "  (tool outputs only)"}`, on: MS.hintMode === "right", disabled: !canRight, fn: () => { MS.hintMode = "right"; show(cur); } });
  plab(body, 0, 396, 410, `<span style="color:var(--muted)">${cur_.what || ""}.</span>`, "plab", 16);
  // the exact prompt, as sent
  const pr = H("div", { class: "prompt", style: { left: "440px", top: "0px", width: "600px", height: "482px" } }, body);
  H("div", { class: "illus", style: { position: "absolute", right: "10px", top: "6px" } }, pr, "Illustrative question, written by us");
  H("div", { class: "role" }, pr, "user");
  H("div", { class: "t" }, pr, u.q);
  H("div", { class: "opts" }, pr, u.opts.map((o) => `<div>${o}</div>`).join(""));
  if (u.hint) H("div", { class: "t", style: { marginTop: "8px" } }, pr, `<mark>${u.hint.replace(/\n/g, "<br>")}</mark>`);
  H("div", { class: "t", style: { marginTop: "8px", color: "var(--muted)" } }, pr, u.ins);
  turnsX.slice(1).forEach((t) => {
    H("div", { class: "role", style: { marginTop: "8px" } }, pr, t.role === "tool reply" ? "tool" : "assistant");
    H("div", { class: "t", style: { fontFamily: "var(--print-font)" } }, pr, `<mark>${t.text.replace(/</g, "&lt;")}</mark>`);
  });
  // the hint's own marks: a sticky for a person, a slip for a tool
  const hintWords = u.hint || (turnsX[turnsX.length - 1] || {}).text || "";
  if (cur_.kind === "sticky") {
    sticky(body, { x: 1074, y: 40, text: hintWords, delay: 200, width: 300, size: 32, rot: -2 });
    plab(body, 1074, 230, 300, "A person's words, written into the question.", "plab", 17);
  } else if (cur_.id === "pasted") {
    slip(body, { x: 1074, y: 40, call: "pasted into the question", rows: [["text", hintWords.replace(/\n/g, " ")]], delay: 200, width: 300, rot: 2 });
    plab(body, 1074, 230, 300, "A tool's output, pasted in. No tool is called.", "plab", 17);
  } else if (cur_.id === "call") {
    slip(body, { x: 1074, y: 40, call: (cur_.call || "") || "lookup_answer_key", rows: [["reply", cur_.reply || ""]], delay: 200, width: 300, rot: 2 });
    plab(body, 1074, 232, 300, "The model chooses to call the lookup tool; the reply says the letter.", "plab", 17);
  } else {
    slip(body, { x: 1074, y: 40, call: "a tool turn in the chat", rows: [["reply", (turnsX[turnsX.length - 1] || {}).text || ""]], delay: 200, width: 300, rot: 2 });
    plab(body, 1074, 232, 300, "We write the call and the reply into the chat, as if the tool had run.", "plab", 17);
  }
  if (letter) { const L = writeText(body, { x: 1090, y: 330, text: `the letter: (${letter})`, size: 40, red: true, delay: 900, dur: 0.6 }); }
  choiceRow("Source", srcs.map((s) => ({ id: s.id, label: s.label.replace("The model's own tool call", "Its own tool call").replace("An inserted tool turn", "Inserted tool turn") })), MS.hint, (id) => { MS.hint = id; show(cur); });
}

/* ------------------------------------------------------------------ step 3: the models */
const MTESTS = ["Tool vs person", "Authority", "Thinking on and off", "The fixes", "Review teams", "Inside the model"];
function step3() {
  const Mo = MX.models || {}, list = Mo.models || [];
  const n = mv(MX.counts && MX.counts.models, list.length);
  const body = mpage(3, `${n} models, each at its own settings.`, `${mv(Mo.answering)} answered the questions and ${mv(Mo.reviewers)} only reviewed. Pick one.`);
  list.forEach((m, k) => {
    mpick(body, { x: 0, y: k * 40, label: m.name + (m.role === "reviewer" ? "  (reviewer)" : ""), on: MS.model === k, fn: () => { MS.model = k; show(cur); }, w: 420 });
    if (k === 7) H("div", { class: "mrule", style: { left: "0px", top: k * 40 + 38 + "px", width: "420px" } }, body);
  });
  const m = list[MS.model] || list[0];
  if (m) {
    const pn = H("div", { class: "panel", style: { left: "470px", top: "0px", width: "904px", height: "482px" } }, body);
    H("div", { style: { position: "absolute", left: "22px", top: "14px", fontSize: "34px", fontWeight: 600, color: "var(--ink)" } }, pn, m.name);
    const tb = (m.table && m.table.v) || {};
    const lines = [
      ["Thinking", !m.settings && tb.thinking && tb.thinking !== "—" ? tb.thinking.replace(/^none$/, "off (an instruct model)").replace(/^always$/, "always on") : (m.role === "reviewer" ? "not a thinking model" : "")],
      ["Temperature", m.temperature ? String(m.temperature.v) : (m.role === "reviewer" ? "the reviewer's default" : "")],
      ["Size", m.size ? m.size.v : null],
      ["Version", m.revision ? m.revision.v.slice(0, 8) + "…, pinned" : "the server's model id, recorded in every run"],
      ["Settings run", m.settings ? m.settings.v.map((x) => "thinking " + x).join(" and ") : null],
    ].filter((r) => r[1]);
    lines.forEach(([k, v], i) => {
      plab(pn, 22, 78 + i * 38, 150, k);
      H("div", { class: "ptext", style: { left: "170px", top: 72 + i * 38 + "px", width: "700px", fontSize: "21px", lineHeight: 1.25 } }, pn, v);
    });
    // where it ran
    const ranL = (m.ran && m.ran.v) || [];
    const whereSet = [["Voyager", ranL.includes("Voyager")], ["Sol, our vLLM server", ranL.includes("Sol (vLLM)")], ["Sol, Hugging Face (training, layers)", ranL.includes("Sol (Hugging Face)")]];
    plab(pn, 22, 276, 200, "Where it ran");
    whereSet.forEach(([l, on], i) => { const b = mpick(pn, { x: 170 + i * 240, y: 272, label: l, on, disabled: true, fn: () => {} }); b.style.opacity = on ? 1 : 0.5; b.style.cursor = "default"; b.style.maxWidth = "232px"; b.style.whiteSpace = "normal"; b.style.alignItems = "flex-start"; });
    // which of our six tests
    plab(pn, 22, 350, 200, "Used in these tests");
    const tests = (m.tests && m.tests.v) || [];
    MTESTS.forEach((t, i) => { const on = tests.some((x) => x.startsWith(t)); const b = mpick(pn, { x: 170 + (i % 3) * 240, y: 346 + Math.floor(i / 3) * 40, label: t, on, disabled: true, fn: () => {} }); b.style.opacity = on ? 1 : 0.5; b.style.cursor = "default"; });
    plab(pn, 22, 438, 850, `Every run records the model's version and where it ran. One budget of ${fmt(mv(Mo.budget))} tokens a run, prompt and every reply.`, "plab", 17);
  }
  infoRow("Sampling", `Temperature ${mv(Mo.temperatures, {}).olmo_qwen} for Olmo and Qwen3, ${mv(Mo.temperatures, {}).gpt_oss_b20} for gpt-oss and the three newer families (each model's recommended setting).`);
}

/* ------------------------------------------------------------------ step 4: running it */
function step4() {
  const R = MX.running || {}, L = R.limits || {}, T = R.timeline || {}, C = MX.counts || {};
  const body = mpage(4, `${fmt(mv(C.runs_fresh_fixes))} runs for the fixes, fed through a queue.`, `${fmt(mv(C.runs_newer_families))} more on the newer model families. Everything is seeded and checksummed.`);
  ptext(body, 0, 0, 470, `Our class account on Sol, ASU's supercomputer, allows a few jobs at once. A small <b>feeder</b> script kept the queue full, one line at a time, and never ran a line twice.`, 21);
  // queue -> feeder -> jobs
  const bx = (x, t, c) => H("div", { class: "mbox", style: { left: x + "px", top: "6px", width: "190px", height: "100px" } }, body, `<h3 style="font-size:22px">${t}</h3><div class="cap">${c}</div>`);
  bx(510, "The queue", "a file of ordered lines");
  bx(756, "The feeder", `a tick every ${mv(R.feeder && R.feeder.tick_seconds)} s`);
  bx(1002, "Jobs on Sol", `${mv(L.gpu, "")}`.replace("NVIDIA ", "").replace("-SXM4-80GB", " 80 GB"));
  line(body, 704, 56, 752, 56); line(body, 950, 56, 998, 56);
  plab(body, 510, 116, 864, `Within the class limits: <b>${mv(L.jobs)}</b> jobs at once, <b>${fmt(mv(L.gpu_minutes))}</b> running GPU-minutes, up to <b>${mv(L.wall_hours)}</b> hours a job, up to ${mv(L.gpus)} GPUs.`, "plab", 18);
  // run counts
  const rc = R.runs || {};
  [[mv(rc.fresh_per_system), "runs a system, 120 fresh questions"], [mv(rc.on_the_30), "runs a system, 30 held-out"], [mv(rc.dial_per_setting), "runs a dial setting"], [mv(rc.b20_per_model_setting), "runs a setting, newer families"]].forEach(([n, l], k) => sbox(body, { x: 510 + k * 216, y: 158, w: 204, h: 92, n: fmt(n), label: l, delay: 300 + k * 180 }));
  // gpu time
  const pcs = R.gpu_pieces || [];
  const names = ["GPU-hours for the dial's first test", "GPU-hours planned for the 120's runs", "hours:minutes, consistency training"];
  const gt = R.gpu_total && R.gpu_total.v, py0 = gt ? 244 : 200;
  if (gt) sbox(body, { x: 0, y: 156, w: 470, h: 76, n: fmt(Math.round(gt.gpu_hours)), label: `GPU-hours, ${fmt(gt.gpu_jobs || gt.jobs)} GPU jobs since Oct 1, on Ritik's account`, delay: 300 });
  else plab(body, 0, 160, 470, "<b>GPU time</b>, by experiment: no project-wide total is on this machine.");
  pcs.forEach((p, k) => plab(body, 0, py0 + k * 26, 470, `<b style="font-size:20px;color:var(--ink)">${p.v}</b> ${names[k] || p.what}`, "plab", 17));
  // the timeline
  const rules = (T.rules && T.rules.v) || [];
  const d0 = new Date("2026-10-04"), d1 = new Date("2026-11-19"), span = (d1 - d0) / 864e5, AX = 60, AW = 1270, AY = 396;
  const px = (ds) => AX + ((new Date(ds.slice(0, 10)) - d0) / 864e5) / span * AW;
  H("div", { class: "mline", style: { left: AX + "px", top: AY + "px", width: AW + "px" } }, body);
  plab(body, 0, AY - 70, 400, "<b>The project, Oct 4 to Nov 18.</b> Click a mark.");
  for (let d = 0; d <= span; d += 7) { const x = AX + d / span * AW; H("div", { class: "mvline", style: { left: x + "px", top: AY - 5 + "px", height: "10px" } }, body); const dt = new Date(d0.getTime() + d * 864e5); plab(body, x - 18, AY + 8, 60, dt.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" }), "plab", 15); }
  const sel = rules.find((r) => r.n === MS.sel) || null;
  rules.filter((r) => r.fixed).forEach((r) => {
    const b = H("button", { type: "button", class: "mhit", title: `rule ${r.n}`, style: { left: px(r.fixed) - 7 + "px", top: AY - 40 + "px", width: "14px", height: "36px" } }, body);
    pbar(body, { x: px(r.fixed) - (r.plain ? 2 : 1), y: AY - 36, w: r.plain ? 4 : 2, h: 32, delay: 200 + r.n * 25 });
    b.addEventListener("click", () => { MS.sel = r.n; show(cur, { instant: true }); });
  });
  rules.filter((r) => r.result).forEach((r) => { H("div", { style: { position: "absolute", left: px(r.result) - 4 + "px", top: AY - 4 + "px", width: "8px", height: "8px", borderRadius: "50%", background: "var(--red)", opacity: 0.8 } }, body); });
  const fz = T.freeze && T.freeze.v;
  if (fz && fz.date) { const x = px(fz.date); penStroke(body, [[x - 2, AY - 60], [x + 2, AY + 4]], { delay: 300, width: 3 }); stamp(body, { x: x - 180, y: AY - 100, text: `frozen ${fz.date.slice(5).replace("-", "/")}`, delay: 700, rot: -4 }); }
  const n1 = (sel && sel.plain) || (sel && `rule ${sel.n}`) || null;
  H("div", { class: "ptext", style: { left: "0px", top: AY + 38 + "px", width: "1374px", fontSize: "21px", lineHeight: 1.3 } }, body,
    sel ? `<b>${n1 || ""}</b>: rule fixed ${sel.fixed}${sel.result ? `, first result committed ${sel.result}` : ", result not yet read"}.` :
      `<span style="color:var(--muted)">Each pencil mark is a rule written down before its runs (${mv(T.pre_registered)} of the ${mv(T.count)} were pre-registered); each red dot is the first result committed.</span>`);
  infoRow("Rules", `Seeds fixed (${mv(R.repro && R.repro.seed)}); the model's weights checked against one pinned revision, ${mv(R.repro && R.repro.checked_files)} files, by checksum.`);
}

/* ------------------------------------------------------------------ the layer column (steps 5, 6, 8) */
function layerColumn(parent, { x, y, pitch = 13.6, len = 360, onPick, sel, fullHl = true, labels = true }) {
  const A = MX.arch || {}, full = mv(A.full, []);
  const col = H("div", { style: { position: "absolute", left: x + "px", top: y + "px", width: len + 100 + "px", height: pitch * 32 + 20 + "px" } }, parent);
  const btns = [];
  for (let i = 0; i < 32; i++) {
    const yy = i * pitch;
    H("div", { style: { position: "absolute", left: "70px", top: yy + pitch - 1 + "px", width: len + "px", borderTop: "1px dotted var(--print-soft)" } }, col);
    if (labels && (i === 0 || i === 31 || full.includes(i))) H("div", { class: "printlab", style: { position: "absolute", left: "0px", top: yy + pitch / 2 - 10 + "px", fontSize: "15px", color: full.includes(i) ? "var(--ink)" : "var(--print)" } }, col, `layer ${i}`);
    if (fullHl && full.includes(i)) highlight(col, { x: 70, y: yy + 1, w: len, h: pitch - 1, delay: 200 + full.indexOf(i) * 90 });
    const b = H("button", { type: "button", class: "lbtn", "aria-label": `layer ${i}`, "aria-pressed": String(sel === i), style: { left: "70px", top: yy + "px", width: len + "px", height: pitch + "px" } }, col);
    if (onPick) b.addEventListener("click", () => onPick(i, b, btns)); else b.style.cursor = "default";
    btns.push(b);
  }
  return { col, btns, pitch, x0: 70, len };
}

/* ------------------------------------------------------------------ step 5: the architecture */
function step5() {
  const A = MX.arch || {}, full = mv(A.full, []);
  const body = mpage(5, `${mv(A.layers)} layers; only ${mv(A.n_full)} see the whole prompt.`, "Olmo 3 7B Think, the model we trained and opened up. Click a layer to see what kind it is.");
  const pitch = 13.6;
  const lc = layerColumn(body, { x: 0, y: 14, pitch, len: 330, sel: MS.layer, onPick: (i, b, btns) => { MS.layer = i; btns.forEach((x, j) => x.setAttribute("aria-pressed", String(j === i))); detail(); } });
  H("div", { class: "small", style: { position: "absolute", left: "70px", top: "-6px" } }, body, "Prompt in at layer 0");
  H("div", { class: "small", style: { position: "absolute", left: "70px", top: 14 + pitch * 32 + 4 + "px" } }, body, "Answer out after layer 31");
  ptext(body, 470, 0, 880, `A transformer reads the prompt through ${mv(A.layers)} layers stacked like a form's rows. In this model, <b>every fourth layer</b> can look back over the whole prompt; the other ${mv(A.n_window)} look back only ${fmt(mv(A.window))} tokens, a <b>sliding window</b>.`);
  const dp = H("div", { class: "panel", style: { left: "470px", top: "150px", width: "620px", height: "170px" } }, body);
  const dt = H("div", { style: { position: "absolute", left: "20px", top: "12px", right: "20px" } }, dp);
  function detail() {
    const isFull = full.includes(MS.layer);
    dt.innerHTML = `<div style="font-size:34px;font-weight:600;color:var(--ink)">Layer ${MS.layer}</div>
      <div style="font-size:24px;margin-top:4px;color:var(--ink)">${isFull ? "Sees the whole prompt." : `Sees the last ${fmt(mv(A.window))} tokens only.`}</div>
      <div class="small" style="margin-top:8px">${isFull ? "A full-attention layer: one of the " + mv(A.n_full) + ". Highlighted on the column." : "A sliding-window layer: one of the " + mv(A.n_window) + "."}</div>`;
  }
  detail();
  [[mv(A.layers), "layers"], [mv(A.heads), "attention heads a layer"], [fmt(mv(A.hidden)), "hidden size"], [fmt(mv(A.window)), "window, in tokens"]].forEach(([n, l], k) => sbox(body, { x: 470 + k * 224, y: 346, w: 210, h: 92, n, label: l, delay: 400 + k * 150 }));
  plab(body, 470, 450, 880, `Revision ${mv(A.revision, "").slice(0, 8)}…, pinned; the same weights on every machine.`, "pmuted");
  infoRow("Note", "A hint near the start of a long prompt can fall outside a sliding window. Only full-attention layers can still read it.");
}

/* ------------------------------------------------------------------ step 6: how we checked the layers */
function step6() {
  const L = DATA.layers, P = MX.patching || {};
  const body = mpage(6, "We swapped in one layer at a time.", "Activation patching: copy a layer's work from a run without the hint into the run with it, and measure what changes.");
  const steps = [["1", "Run the question with the hint."], ["2", "Run it again, the hint's letter changed to the model's own."], ["3", "Swap one layer's work from run 2 into run 1, at the answer."], ["4", "Measure how much of the pull toward the hint's letter disappears."]];
  steps.forEach(([n, t], k) => { writeText(body, { x: 0, y: k * 58 - 4, text: n, size: 44, red: true, delay: 200 + k * 350, dur: 0.3 }); ptext(body, 36, k * 58, 380, t, 21).style.lineHeight = "1.2"; });
  plab(body, 0, 250, 400, `Cut points where the two runs differ by less than <b>${mv(P.min_gap)}</b> are left out, because the ratio is noise.`, "plab", 17);
  const maxm = Math.max(...L.readout.map((i) => L.effect[i].m)), pitch = 13.6, lenb = 300, X0 = 440;
  const draw = (i) => {
    const m = L.effect[i].m, yc = 14 + i * pitch + pitch / 2;
    if (m > 0.004) pbar(body, { x: X0 + 70, y: yc - (pitch - 3) / 2, w: lenb * m / maxm, h: pitch - 3 });
    writeText(body, { x: X0 + 70 + Math.max(0, lenb * m / maxm) + 12, y: yc - 17, text: m > 0.004 ? pct(m) : "none", size: 32, red: true, delay: 250, dur: 0.3 });
  };
  const lc = layerColumn(body, { x: X0, y: 14, pitch, len: lenb, sel: -1, fullHl: false, onPick: (i, b) => { if (MS.swapped.has(i)) return; MS.swapped.add(i); MS.view = "layer"; MS.last = i; draw(i); side(); } });
  H("div", { class: "small", style: { position: "absolute", left: X0 + 70 + "px", top: "-6px" } }, body, "Click a layer to swap it.");
  [...MS.swapped].forEach(draw);
  const sd = H("div", { class: "panel", style: { left: "900px", top: "0px", width: "474px", height: "482px" } }, body);
  const inner = H("div", { style: { position: "absolute", left: "18px", right: "18px", top: "14px", bottom: "12px" } }, sd);
  function side() {
    const sh = (k) => L.share[k], v = MS.view;
    let h = "";
    const pc = (o) => `${pct(o.m)} <span style="font-size:19px;color:var(--muted)">[${pct(o.lo)}, ${pct(Math.min(o.hi, 1))}]</span>`;
    if (v === "layer") {
      const i = MS.last ?? MS.layer, e = L.effect[i];
      h = `<div class="small">Measured, one layer swapped</div><div style="font-size:30px;font-weight:600;color:var(--ink);margin-top:6px">Layer ${i}</div>
        <div style="font-size:21px;line-height:1.35;margin-top:6px;color:var(--ink)">${MS.swapped.size ? `Swapping it removes <b>${pc(e)}</b> of the hint's pull.` : "Click a layer on the column to swap it in."}</div>
        <div class="small" style="margin-top:12px">${MS.swapped.size ? `${MS.swapped.size} layer${MS.swapped.size > 1 ? "s" : ""} swapped so far. Most do almost nothing; a few carry the hint.` : ""}</div>`;
    } else if (v === "together") {
      const s = sh(0);
      h = `<div class="small">Measured: ${s.what}</div><div style="font-size:21px;line-height:1.35;margin-top:10px;color:var(--ink)">Layers ${s.at.join(", ")} swapped <b>together</b> remove</div>
        <div style="font-family:var(--hand-font);font-size:84px;color:var(--red);line-height:1;margin-top:6px">${pc(s)}</div><div class="small" style="margin-top:8px">${s.questions} questions, ${s.cuts} cut points.</div>`;
    } else if (v === "heads") {
      const hd = L.heads;
      h = `<div class="small">Measured: three attention heads (${mv(P.heads, []).join(", ")})</div><div style="font-size:21px;line-height:1.35;margin-top:10px;color:var(--ink)">At the answer, how much more attention they give the hint's letter when the model <b>followed</b> the hint than when it resisted:</div>
        <div style="font-family:var(--hand-font);font-size:84px;color:var(--red);line-height:1;margin-top:6px">+${hd.d.toFixed(3)}</div><div class="small" style="margin-top:8px">95% interval [${hd.lo.toFixed(3)}, ${hd.hi.toFixed(3)}], ${hd.questions} questions; it ${hd.reading}.</div>`;
    } else if (v === "new16") {
      const s = sh(1);
      h = `<div class="small">Measured: ${s.what}</div><div style="font-size:21px;line-height:1.35;margin-top:10px;color:var(--ink)">The same three layers, on questions not used to find them:</div>
        <div style="font-family:var(--hand-font);font-size:84px;color:var(--red);line-height:1;margin-top:6px">${pc(s)}</div><div class="small" style="margin-top:8px">${s.questions} questions, ${s.cuts} cut points.</div>`;
    } else {
      const s = sh(2);
      h = `<div class="small">Measured: ${s.what}</div><div style="font-size:21px;line-height:1.35;margin-top:10px;color:var(--ink)">A different model, Qwen3 8B, has its own three layers (${s.at.join(", ")}) out of ${mv(P.qwen && P.qwen.n_layers)}:</div>
        <div style="font-family:var(--hand-font);font-size:84px;color:var(--red);line-height:1;margin-top:6px">${pc(s)}</div><div class="small" style="margin-top:8px">${s.questions} questions, ${s.cuts} cut points; it ${s.reading}.</div>`;
    }
    inner.innerHTML = h;
  }
  side();
  const opts = [["layer", "One layer"], ["together", "The three together"], ["heads", "The heads"], ["new16", "16 new questions"], ["qwen", "Qwen3 8B"]];
  choiceRow("Readout", opts.map(([id, label]) => ({ id, label })), MS.view, (id) => { MS.view = id; if (id === "together") L.readout.forEach((i) => { MS.swapped.add(i); }); show(cur, { instant: false }); });
}

/* ------------------------------------------------------------------ step 7: fine-tuning */
function lossChart(parent, { x, y, w, h, pts, marks }) {
  // graph paper, pencil points joined by a faint pencil line; pts: [{x, y, label, ring}]
  const g = H("div", { style: { position: "absolute", left: x + "px", top: y + "px", width: w + "px", height: h + "px", border: "1.5px solid var(--print)", backgroundImage: "linear-gradient(var(--print-soft) 1px, transparent 1px), linear-gradient(90deg, var(--print-soft) 1px, transparent 1px)", backgroundSize: "24px 24px" } }, parent);
  const ys = pts.map((p) => p.y), lo = 0, hi = Math.max(...ys) * 1.08, xs = pts.map((p) => p.x), x0 = Math.min(...xs), x1 = Math.max(...xs);
  const px = (v) => 26 + ((v - x0) / (x1 - x0 || 1)) * (w - 80), py = (v) => 22 + (1 - (v - lo) / (hi - lo || 1)) * (h - 56);
  const P = pts.map((p) => [px(p.x), py(p.y)]);
  (marks || []).forEach((m) => { H("div", { class: "mvline", style: { left: px(m.x) + "px", top: "8px", height: h - 20 + "px", opacity: .6 } }, g); if (m.label) H("div", { class: "plab", style: { left: px(m.x) + 4 + "px", top: "2px", fontSize: "13px" } }, g, m.label); });
  if (P.length > 1) penStroke(g, P.map((p) => [p[0].toFixed(1), p[1].toFixed(1)].map(Number)), { color: "--pencil", pencil: true, width: pts.length > 20 ? 1.6 : 1.4, delay: 200, dur: pts.length > 20 ? 1.2 : 0.5 });
  pts.forEach((p, i) => {
    if (pts.length <= 8) { S("svg", {}, g); const d = H("div", { style: { position: "absolute", left: P[i][0] - 5 + "px", top: P[i][1] - 5 + "px", width: "10px", height: "10px", borderRadius: "50%", background: "var(--pencil)", filter: "url(#pencil)" } }, g); }
    if (p.label) writeText(g, { x: Math.min(P[i][0] - 30, w - 160), y: P[i][1] + 6, text: p.label, size: 26, delay: 500 + Math.min(i, 6) * 200, dur: 0.4 });
    if (p.ring) penLoop(g, { cx: P[i][0], cy: P[i][1], rx: 15, ry: 11, delay: 900, seed: 4 });
  });
  return g;
}
function step7() {
  const Ft = MX.finetune || {}, lo = Ft.lora || {}, ld = Ft.lora_data || {}, bc = Ft.bct || {}, ll = Ft.lora_loss || {}, cu = Ft.curves || {};
  const isL = MS.train === "lora";
  const body = mpage(7, "Two ways to train it not to follow the hint.", isL ? "Fine-tuning shows it hinted prompts and a target that names the hint's source, then decides." : "Consistency training shows it hinted prompts and its own reasoning from the same question with no hint.");
  if (isL) {
    ptext(body, 0, 0, 440, `<b>LoRA</b> trains small add-on weights, not the whole model. Each example is a hinted prompt; its target opens by saying where the hint came from, then reasons to a decision.`, 21);
    [[mv(lo.rank), "LoRA rank"], [mv(lo.alpha), "alpha"], [fmt(mv(lo.steps)), `steps, ${mv(lo.epochs)} epochs of ${mv(lo.per_step)} examples`], [mv(lo.lr), "learning rate"]].forEach(([n, l], k) => sbox(body, { x: (k % 2) * 220, y: 128 + Math.floor(k / 2) * 90, w: 206, h: 82, n: String(n), label: l, delay: 300 + k * 150 }));
    plab(body, 0, 312, 440, `<b>${fmt(mv(ld.examples))}</b> examples = ${fmt(mv(ld.train))} to train on + ${fmt(mv(ld.validation))} held back to choose the epoch, from ${fmt(mv(ld.kept))} of ${fmt(mv(ld.questions_run))} questions the model already got right. ${mv(ld.neither)} were dropped: the reasoning neither followed nor rejected the hint.`, "plab", 16);
  } else {
    ptext(body, 0, 0, 440, `<b>Consistency training</b>: for each hinted prompt, the target is the model's own reasoning on the <b>same question with no hint</b>, so it learns to reason as if the hint were absent, and to say the hint was there.`, 21);
    [[fmt(mv(bc.examples)), "examples in all"], [fmt(mv(bc.train)), "to train on"], [fmt(mv(bc.validation)), "held back to choose the epoch"], [fmt(mv(bc.hinted)), "of them with a hint (the rest, none)"]].forEach(([n, l], k) => sbox(body, { x: (k % 2) * 220, y: 156 + Math.floor(k / 2) * 90, w: 206, h: 82, n, label: l, delay: 300 + k * 150 }));
    const dr = mv(bc.dropped, {});
    plab(body, 0, 340, 440, `${mv(bc.dropped_total)} prompts dropped: ${Object.entries(dr).map(([k, v]) => `${v}, ${k}`).join("; ")}. ${mv(bc.steps)} steps over 2 epochs.`, "plab", 16);
  }
  // validation loss: the chosen epoch ringed; per-step curves replace the epoch points when the Sol logs are present
  const lp = isL ? [{ x: 0, y: mv(ll.base), label: `start ${mv(ll.base).toFixed(3)}` }, { x: 1, y: mv(ll.epoch1), label: `e1 ${mv(ll.epoch1).toFixed(3)}` }, { x: 2, y: mv(ll.epoch2), label: `e2 ${mv(ll.epoch2).toFixed(3)}` }]
    : [{ x: 1, y: mv(bc.epoch_loss && bc.epoch_loss.epoch1), label: `e1 ${mv(bc.epoch_loss.epoch1).toFixed(3)}`, ring: true }, { x: 2, y: mv(bc.epoch_loss && bc.epoch_loss.epoch2), label: `e2 ${mv(bc.epoch_loss.epoch2).toFixed(3)}` }];
  // the Sol training logs, one folder a version: LoRA's data trained four ways (lora, lora_tags, lora_attn3, tags), consistency training's (a40)
  const LV = [["lora", "LoRA"], ["lora_tags", "+ tags"], ["lora_attn3", "3 layers"], ["tags", "tags only"]].filter(([k]) => cu[k]);
  const tv = isL ? (cu[MS.tv] ? MS.tv : "lora") : "a40", chosen = cu[tv];
  const LVT = { lora: "LoRA on every layer", lora_tags: "LoRA with source tags", lora_attn3: "LoRA on layers 15, 19 and 23 only", tags: "source tags only, the model frozen", a40: "consistency training" };
  if (chosen && isL && LV.length > 1) {
    plab(body, 0, 380, 120, "Loss per step:", "plab", 16);
    LV.forEach(([k, l], j) => { const b = mbtn(body, { x: 112 + j * 82, y: 376, w: 78, text: l, fn: () => { MS.tv = k; show(cur, { instant: true }); } }); b.classList.add("msm"); if (k === tv) b.classList.add("on"); b.title = LVT[k]; });
  } else plab(body, 0, 384, 440, chosen ? `Training loss, step by step (from 0): ${LVT[tv]}` : (isL ? "Validation loss: start, e1, e2 (from 0)" : `Validation loss: e1, e2 (from 0); epoch ${mv(bc.chosen)}, the lower, kept`), "plab", 16);
  if (chosen) {
    const cv = chosen.v, pts = cv.points.map((p) => ({ x: p[0], y: p[1] })), ch = cv.chosen;
    if (ch) pts[pts.length - 1].label = `epoch ${ch.epoch} kept`;
    lossChart(body, { x: 0, y: 404, w: 440, h: 78, pts, marks: (cv.epochs || []).slice(0, -1).map((e) => ({ x: e.step, label: `epoch ${e.epoch + 1}` })) });
  } else lossChart(body, { x: 0, y: 404, w: 440, h: 78, pts: lp });
  // the pair
  const pr = ML && ML[isL ? "lora" : "bct"];
  const PX = 470, PW = 904;
  const ill = H("div", { class: "illus", style: { position: "absolute", left: PX + "px", top: "0px" } }, body, pr ? "A real training example, drawn by a stored seed (this build only)." : "A training example's structure.");
  if (pr) ill.title = `seed ${pr.seed}`;
  const half = 438;
  const ip = H("div", { class: "ruledp", style: { left: PX + "px", top: "26px", width: half + "px", height: "372px" } }, body);
  H("div", { class: "lab" }, ip, "Input: what the model sees");
  const tp = H("div", { class: "ruledp", style: { left: PX + half + 28 + "px", top: "26px", width: half + "px", height: "372px" } }, body);
  H("div", { class: "lab" }, tp, "Target: what it is trained to write");
  const stepsN = 3, k = MS.pair;
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  if (pr) {
    const u = pr.input.find((t) => t.role === "user") || pr.input[0], sp = splitUser(u.text);
    const hintHtml = (sp.hint ? `<mark>${esc(sp.hint)}</mark>\n` : "") + pr.input.slice(1).map((t) => `<mark>${esc(t.text)}</mark>`).join("\n");
    const qshort = esc(sp.q.length > 200 ? sp.q.slice(0, 200) + "…" : sp.q);
    ip.insertAdjacentHTML("beforeend", `${qshort}\n[the ten options]\n${hintHtml}`);
    const tgt = pr.target;
    const piece = k === 0 ? "" : k === 1 ? tgt.slice(0, 380) + (tgt.length > 380 ? "…" : "") : "…" + tgt.slice(-380);
    tp.insertAdjacentHTML("beforeend", esc(piece) || "<span style='color:var(--muted)'>Press Next to write the target.</span>");
    plab(body, PX, 404, PW, `The hint came as: ${pr.hint_channel.replace("tool_pasted", "pasted tool output").replace("tool_injected", "an inserted tool turn").replace("user", "the user's guess")}. Letter (${pr.hint_letter}), a wrong hint. ${fmt(pr.tokens || 0)} tokens in all.`, "plab", 16);
  } else {
    ip.insertAdjacentHTML("beforeend", `[the question and its ten options]\n<mark>[the hint, as in step 2: a user's guess, pasted tool output, or an inserted tool turn]</mark>\n[the instruction to think step by step]`);
    tp.insertAdjacentHTML("beforeend", k === 0 ? "<span style='color:var(--muted)'>Press Next.</span>" : isL ? (k === 1 ? "[an opener that notes the hint's source, then decides whether to trust it]" : "[the model's reasoning, then its final answer]") : (k === 1 ? "[the model's own reasoning on the same question, with no hint in it]" : "[a final answer that names the hint]"));
    plab(tp, 16, 170, 400, "Recorded text appears in the local build.", "illus").style.fontSize = "17px";
  }
  mbtn(body, { x: PX, y: 442, text: "‹ Previous", fn: () => { MS.pair = Math.max(0, MS.pair - 1); show(cur, { instant: true }); }, disabled: k === 0 });
  mbtn(body, { x: PX + 130, y: 442, text: "Next ›", fn: () => { MS.pair = Math.min(stepsN - 1, MS.pair + 1); show(cur, { instant: true }); }, disabled: k === stepsN - 1 });
  plab(body, PX + 260, 446, 600, ["the input", "its first words", "its last words"][k] + `  (${k + 1} of ${stepsN})`, "plab", 17);
  choiceRow("Training", [{ id: "lora", label: "Fine-tuning (LoRA)" }, { id: "bct", label: "Consistency training" }], MS.train, (id) => { MS.train = id; MS.pair = 0; show(cur); }, "step through a pair with Next");
}

/* ------------------------------------------------------------------ step 8: what training changed inside */
function step8() {
  const S_ = DATA.layers.swap, rows = S_.rows, who = MS.fx;
  const body = mpage(8, "Training changed it in two different places.", "Swap the trained model's layers into the original, a group at a time, and see how much of the hint's pull goes away.");
  const nm = { lora: "Fine-tuned (LoRA)", a40: "Consistency-trained" }[who];
  ptext(body, 0, 0, 430, `Same cases, same hints. Each bar: how much the hint's <b>direct effect</b> shrinks when <b>${nm}</b>'s layers replace the original's in that group. Right of zero means the group carries the change.`, 21);
  const parts = { before: [0, 14], readout: [15, 23], after: [24, 31], through: [0, 23], every: [0, 31] };
  const names = { every: "every layer", before: "layers 0 to 14, before the readout", readout: "layers 15, 19, 23, the readout", through: "layers 0 to 23, through the readout", after: "layers 24 to 31, after it" };
  const order = ["before", "readout", "through", "after", "every"];
  const x0 = 700, sc = 150;
  order.forEach((p, k) => {
    const r = rows.find((q) => q.part === p), v = r[who], y = 4 + k * 92;
    plab(body, 440, y, 420, names[p], "plab", 18);
    H("div", { class: "mvline", style: { left: x0 + "px", top: y + 24 + "px", height: "44px" } }, body);
    const w = v.m * sc;
    pbar(body, { x: x0, y: y + 34, w, h: 24, delay: 300 + k * 250 });
    writeText(body, { x: w >= 0 ? x0 + w + 12 : x0 + 12, y: y + 30, text: `${v.m >= 0 ? "+" : "−"}${Math.abs(v.m).toFixed(2)}`, size: 38, red: v.lo > 0 || v.hi < 0, delay: 600 + k * 250, dur: 0.4 });
    plab(body, w >= 0 ? x0 + w + 100 : x0 + 100, y + 38, 200, `[${v.lo.toFixed(2)}, ${v.hi.toFixed(2)}]`, "pmuted");
  });
  plab(body, x0 - 150, 464, 400, "← hint's pull grows | shrinks →", "pmuted");
  // the layer column, with the groups bracketed
  const CX = 1130, CP = 12.4;
  layerColumn(body, { x: CX - 70, y: 14, pitch: CP, len: 150, fullHl: false, labels: false });
  [["before", "before"], ["readout", "readout"], ["after", "after"]].forEach(([p, lab], j) => {
    const [a, b] = parts[p], y1 = 14 + a * CP, y2 = 14 + (b + 1) * CP;
    penStroke(body, [[CX + 100, y1 + 2], [CX + 112, y1 + 3], [CX + 111, y2 - 3], [CX + 100, y2 - 2]], { delay: 400 + j * 300, width: 2.4 });
    plab(body, CX + 122, (y1 + y2) / 2 - 12, 120, lab, "plab", 17);
  });
  const reading = who === "lora" ? S_.lora_reading : `${S_.a40_reading}; ${S_.a40_where}`;
  const note = H("div", { class: "panel", style: { left: "0px", top: "262px", width: "420px", padding: "14px 18px" } }, body);
  note.innerHTML = `<div class="small">What we read</div><div style="font-size:23px;line-height:1.3;margin-top:4px;color:var(--ink)">${nm}: <b>${who === "lora" ? "acts in the reasoning" : "acts before the readout layers"}</b>.</div>
    <div class="small" style="margin-top:8px">${S_.cases} cases, ${S_.questions} questions. In the fine-tuned model no group removes the hint's pull on the original's tokens; consistency training removes it before the readout.</div>`;
  choiceRow("Model", [{ id: "lora", label: "Fine-tuned (LoRA)" }, { id: "a40", label: "Consistency-trained" }], who, (id) => { MS.fx = id; show(cur); }, "measured, base's cases at the answer");
}

/* ------------------------------------------------------------------ step 9: the other fixes */
function step9() {
  const F_ = MX.fixes || {}, d = F_.dial || {}, ms = d.measured || [];
  const body = mpage(9, "Three fixes that need no training.", "A sentence, a label, and a dial on how much the readout layers read the tool's turn.");
  sticky(body, { x: 0, y: 4, text: mv(F_.instruction, ""), delay: 200, width: 430, size: 25, rot: -1 });
  plab(body, 0, 232, 420, "<b>The one-line instruction</b>, exact text, added to the system prompt.", "plab", 17);
  const sl = slip(body, { x: 8, y: 290, call: `${mv(F_.label, "").trim()} {"question_id": 7, …}`, rows: [["labelled", "every tool output, inserted tool turns only"]], delay: 500, width: 410, rot: 1 });
  plab(body, 0, 400, 420, "<b>The “unverified” label</b>: exact text, put in front of every tool output.", "plab", 17);
  // the dial
  const sel = MS.dial, cx = 1000, cy = 190, R = 150;
  const svg = S("svg", { width: 520, height: 230, viewBox: "0 0 520 230" }); Object.assign(svg.style, { position: "absolute", left: cx - 260 + "px", top: "0px", overflow: "visible" }); body.appendChild(svg);
  const ang = (t) => Math.PI * (1 - t);       // t: 0 left .. 1 right
  const pt = (t, r) => [260 + r * Math.cos(ang(t)), 190 - r * Math.sin(ang(t))];
  S("path", { d: `M${pt(0, R)[0]},${pt(0, R)[1]} A${R},${R} 0 0 1 ${pt(1, R)[0]},${pt(1, R)[1]}`, fill: "none", style: "stroke:var(--print)", "stroke-width": 2 }, svg);
  const ticks = [[0, ms[0] && mv(ms[0].alpha)], [0.78, ms[1] && mv(ms[1].alpha)]];
  ticks.forEach(([t, a], j) => { const [x1, y1] = pt(t, R - 12), [x2, y2] = pt(t, R + 12), [tx, ty] = pt(t, R + 34); S("line", { x1, y1, x2, y2, style: "stroke:var(--print)", "stroke-width": 2.4 }, svg); S("text", { x: tx, y: ty + 6, "text-anchor": "middle", "font-size": 22, style: "fill:var(--ink)", text: String(a) }, svg); });
  const [mx_, my_] = pt(0.39, R + 6); S("text", { x: mx_, y: my_ - 6, "text-anchor": "middle", "font-size": 16, style: "fill:var(--muted);font-style:italic", text: "not measured" }, svg);
  const nt = sel === 1 ? ticks[0][0] : ticks[1][0], [nx, ny] = pt(nt, R - 20);
  S("path", { d: `M260,186 L${nx},${ny} L260,194 Z`, style: "fill:var(--pencil)", filter: "url(#pencil)" }, svg);
  S("circle", { cx: 260, cy: 190, r: 9, style: "fill:var(--pencil)", filter: "url(#pencil)" }, svg);
  plab(body, cx - 250, 204, 500, `Attention to the tool turn, scaled by <b>${sel}</b> at layers ${mv(d.layers, []).join(", ")}. ${sel === 1 ? "1 = the model itself." : "A quarter of its usual weight."}`, "plab", 17).style.textAlign = "center";
  const cur_ = ms.find((m) => mv(m.alpha) === sel) || ms[0], rows = [
    ["Wrong hints followed", cur_.following, 240, "of the runs with a wrong hint"], ["Right hints taken", cur_.accepted, 240, "of the runs with a right hint"], ["No-hint accuracy", cur_.accuracy, 120, "of the runs with no hint"]];
  rows.forEach(([lab, o, n, cap], k) => {
    const y = 232 + k * 74, v = o.v;
    plab(body, 470, y, 400, `${lab} <span style="color:var(--muted)">${cap}</span>`, "plab", 18);
    const end = bubbles(body, { x: 470, y: y + 28, n: v.n, k: v.k, cols: 60, w: 8, h: 7, gx: 2.4, gy: 3, delay: 300 + k * 300, dur: 900, label: `${v.k} of ${v.n}` });
    tally(body, { x: 1130, y: y + 6, k: v.k, n: v.n, caption: "", delay: end + 100, size: 38, seed: 20 + k });
  });
  plab(body, 470, 458, 900, `Only these two settings were run, on the ${mv(d.questions)} fresh questions, ${mv(d.runs)} runs each. Nothing in between was measured.`, "pmuted");
  choiceRow("Dial", ms.map((m) => ({ id: mv(m.alpha), label: mv(m.alpha) === 1 ? "1, the model itself" : String(mv(m.alpha)) })), sel, (a) => { MS.dial = a; show(cur); }, "measured settings only");
}

/* ------------------------------------------------------------------ step 10: the review team */
function step10() {
  const R = MX.review || {}, Ag = DATA.agents, ck = Ag.checker;
  const body = mpage(10, "Solver, reviewer, then a checker.", "A model with the lookup tool answers; a second model reviews it; a third pass solves the question again without the tool.");
  const W = 250, Y = 6, X = [0, 370, 740, 1110];
  const names = [["The solver", "uses the lookup tool"], ["The reviewer", "decides if the answer is right"], ["The checker", "solves again, with no tool"], ["The user", "gets the final answer"]];
  names.forEach(([t, c], k) => { H("div", { class: "mbox", style: { left: X[k] + "px", top: Y + "px", width: W + "px", height: "92px" } }, body, `<h3 style="font-size:23px">${t}</h3><div class="cap">${c}</div>`); if (k < 3) line(body, X[k] + W + 6, Y + 46, X[k + 1] - 6, Y + 46); });
  ptext(body, 0, 118, 500, `The solver's tool is sometimes wrong on purpose. What does the reviewer see? Switch it below: the page it receives changes, and so does how many wrong tool answers it corrects.`, 21);
  // the reviewer's page, by variant
  const v = MS.rev, vi = ["answer_only", "plus_private", "plus_tool_log"].indexOf(v);
  const pg = H("div", { class: "prompt", style: { left: "0px", top: "270px", width: "500px", height: "212px" } }, body);
  H("div", { class: "role" }, pg, "what the reviewer is given");
  H("div", { class: "t" }, pg, "The question.<br>Proposed answer: (X)");
  if (vi >= 1) H("div", { class: "t", style: { marginTop: "6px" } }, pg, `<mark>${mv(R.private_header)}</mark> …`);
  if (vi >= 2) H("div", { class: "t", style: { marginTop: "6px" } }, pg, `<mark>${mv(R.log_header)}</mark> the tool's call and reply`);
  // results
  const rv = Ag.reviewers.filter((r) => ["Olmo 3.1 32B Instruct", "Qwen3 30B Instruct"].includes(r.name));
  plab(body, 540, 118, 800, `Wrong tool answers corrected, of the ${mv(R.bad_lookups)} the reviewers graded:`, "plab", 19);
  rv.forEach((r, k) => {
    const o = r[v], y = 152 + k * 112;
    plab(body, 540, y, 220, r.name, "plab", 19);
    const end = bubbles(body, { x: 540, y: y + 34, n: o.n, k: o.k, cols: 37, w: 14, h: 10, gx: 3, gy: 5, delay: 300, dur: 900, label: `${o.k} of ${o.n}` });
    tally(body, { x: 1196, y: y + 10, k: o.k, n: o.n, caption: "", delay: end + 100, size: 42, seed: 30 + k });
  });
  H("div", { class: "mrule", style: { left: "540px", top: "374px", width: "834px" } }, body);
  stamp(body, { x: 548, y: 396, text: "Checked without the tool", delay: 900, rot: -3 });
  writeText(body, { x: 1000, y: 388, text: `${ck.caught.k} of ${ck.caught.n} caught`, size: 38, red: true, delay: 1400, dur: 0.6 });
  writeText(body, { x: 1000, y: 428, text: `${ck.false_alarms.k} of ${ck.false_alarms.n} false alarms`, size: 38, red: true, delay: 1800, dur: 0.6 });
  plab(body, 540, 462, 830, "The checker's numbers are on a different set of 100 items.", "pmuted");
  choiceRow("Reviewer", [{ id: "answer_only", label: "Answer only" }, { id: "plus_private", label: "+ its private reasoning" }, { id: "plus_tool_log", label: "+ the tool's log" }], v, (id) => { MS.rev = id; show(cur); }, "Olmo reviewers defer to the tool's log; Qwen3 does not");
}

/* ------------------------------------------------------------------ step 11: checking ourselves */
function bootRow(rng_, vals) { const n = vals.length, s = []; for (let i = 0; i < n; i++) s.push(vals[Math.floor(rng_() * n)]); return s; }
function step11() {
  const K = MX.checking || {}, T = (MX.running || {}).timeline || {}, Lb = K.labels || {}, rules = (T.rules && T.rules.v) || [], pn = (T.plain_names && T.plain_names.v) || {};
  const body = mpage(11, "We wrote the rules down before the runs.", "Dates, a count that shows its doubt, and labels two judges checked.");
  // column 1: dates
  plab(body, 0, 0, 420, "<b>Written down first</b>: the rule's date, then its first result", "plab", 18);
  const shown = rules.filter((r) => pn[r.n] && r.fixed && r.result).slice(0, 7);
  shown.forEach((r, k) => {
    const y = 34 + k * 44;
    ptext(body, 0, y, 270, pn[r.n], 17).style.lineHeight = "1.15";
    writeText(body, { x: 280, y: y - 2, text: r.fixed.slice(5, 10).replace("-", "/"), size: 32, delay: 300 + k * 150, dur: 0.3 });
    writeText(body, { x: 350, y: y - 2, text: r.result.slice(5, 10).replace("-", "/"), size: 32, red: true, delay: 500 + k * 150, dur: 0.3 });
  });
  plab(body, 280, 0 + 18, 150, "", "plab");
  plab(body, 0, 350, 430, `${mv(T.pre_registered)} of ${mv(T.count)} rules in the ledger were pre-registered.`, "plab", 17);
  const fz = (K.freeze && K.freeze.v) || {};
  stamp(body, { x: 0, y: 396, text: `Frozen ${fz.date || ""}`, delay: 1400, rot: -3 });
  plab(body, 0, 456, 430, `Tag ${fz.tag || ""}: no number changes after it.`, "pmuted");
  // column 2: the statistics
  const X2 = 470;
  plab(body, X2, 0, 420, "<b>A count that shows its doubt</b>", "plab", 18);
  ptext(body, X2, 28, 420, `Every rate is <b>k of n</b> runs with a 95% Wilson interval. A difference is a bootstrap, <b>paired by question</b>: ${fmt(mv(K.bootstrap && K.bootstrap.resamples))} resamples, seed ${mv(K.bootstrap && K.bootstrap.seed)}. Try one, with eight illustrative questions:`, 21).style.lineHeight = "1.3";
  const out = [1, 1, 0, 1, 0, 0, 1, 0];      // illustrative question outcomes
  const BX = X2, BY = 190;
  out.forEach((o, k) => { const el = H("div", { style: { position: "absolute", left: BX + k * 52 + "px", top: BY + "px", width: "44px", height: "34px", border: "1.5px solid var(--print)" } }, body); if (o) { const t = S("svg", { width: 44, height: 34, viewBox: "0 0 44 34" }); t.style.position = "absolute"; el.appendChild(t); S("ellipse", { cx: 22, cy: 17, rx: 16, ry: 9, style: "fill:var(--pencil)", filter: "url(#pencil)" }, t); } });
  plab(body, BX, BY + 40, 420, `Illustrative: ${out.reduce((a, b) => a + b, 0)} of ${out.length} questions followed the hint.`, "pmuted");
  if (!MS.boot) MS.boot = { r: rng(11), draws: [] };
  const draws = MS.boot.draws;
  mbtn(body, { x: BX, y: BY + 74, text: "Draw again", fn: () => { for (let i = 0; i < 5; i++) { const s = bootRow(MS.boot.r, out); draws.push(s.reduce((a, b) => a + b, 0) / s.length); } show(cur, { instant: true }); } });
  mbtn(body, { x: BX + 130, y: BY + 74, text: "Start over", fn: () => { MS.boot = null; show(cur, { instant: true }); }, disabled: !draws.length });
  H("div", { class: "mline", style: { left: BX + "px", top: BY + 200 + "px", width: "416px" } }, body);
  for (let k = 0; k <= 8; k++) { H("div", { class: "mvline", style: { left: BX + (k / 8) * 416 + "px", top: BY + 195 + "px", height: "10px" } }, body); if (k % 2 === 0) plab(body, BX + (k / 8) * 416 - 10, BY + 208, 40, `${k / 8 * 100}%`, "plab", 15); }
  const cnt = {};
  draws.forEach((v) => { const k = Math.round(v * 8); cnt[k] = (cnt[k] || 0) + 1; });
  const top = Math.max(1, ...Object.values(cnt)), stepH = Math.min(8, 110 / top);
  Object.entries(cnt).forEach(([k, c]) => { const x = BX + (k / 8) * 416; for (let h = 1; h <= c; h++) H("div", { style: { position: "absolute", left: x - 5 + "px", top: BY + 190 - h * stepH + "px", width: "10px", height: Math.max(3, stepH - 1) + "px", borderRadius: "50%", background: "var(--pencil)", filter: "url(#pencil)" } }, body); });
  if (draws.length >= 20) {
    const s = draws.slice().sort((a, b) => a - b), lo = s[Math.floor(0.025 * s.length)], hi = s[Math.ceil(0.975 * s.length) - 1];
    penStroke(body, [[BX + lo * 416, BY + 222], [BX + hi * 416, BY + 222]], { width: 3.4, delay: 0, dur: 0.3 });
    plab(body, BX, BY + 232, 420, `${draws.length} draws; the middle 95% reach ${pct(lo)} to ${pct(hi)}.`, "plab", 16);
  } else plab(body, BX, BY + 232, 420, `${draws.length} draws so far. Each redraws eight questions with repeats.`, "pmuted");
  // column 3: checks and labels
  const X3 = 940;
  plab(body, X3, 0, 430, "<b>Did we check ourselves?</b>", "plab", 18);
  const e2 = mv(K.e2_checks, []), hc = mv(K.heldout_checks, []);
  plab(body, X3, 26, 430, "The 120 fresh questions, exclusion checks:", "plab", 16);
  e2.forEach((t, k) => { const y = 48 + k * 24; plab(body, X3, y, 400, `✓ ${t}`, "plab", 16).style.color = "var(--ink)"; });
  plab(body, X3, 200, 430, "The training examples, held-out leak checks:", "plab", 16);
  hc.forEach((t, k) => plab(body, X3, 222 + k * 24, 400, `✓ ${t}`, "plab", 16).style.color = "var(--ink)");
  const n = mv(Lb.l3) + mv(Lb.l4) + mv(Lb.l6);
  ptext(body, X3, 352, 430, `<b>${fmt(n)}</b> answers labelled by hand. On the last sheet a blind AI judge agreed on <b>${mv(Lb.agree_rows)} of ${mv(Lb.l6)}</b>, kappa ${mv(Lb.kappa, 0).toFixed(2)}.`, 21).style.lineHeight = "1.3";
  plab(body, X3, 436, 430, "The AI-use disclosure is in the project's submission folder.", "pmuted");
  infoRow("Ledger", `${mv(K.prereg_count)} rules in the ledger; the label judges and their protocol were pre-registered on Nov 4, before any judging.`);
}

/* ------------------------------------------------------------------ the pages */
const MAP_STEPS = [
  { title: "The map", run: mapPage },
  { title: "The questions", run: step1 }, { title: "The hint", run: step2 }, { title: "The models", run: step3 }, { title: "Running it", run: step4 },
  { title: "The architecture", run: step5 }, { title: "Checking the layers", run: step6 }, { title: "Fine-tuning", run: step7 }, { title: "Training, inside", run: step8 },
  { title: "The other fixes", run: step9 }, { title: "The review team", run: step10 }, { title: "Checking ourselves", run: step11 },
];
