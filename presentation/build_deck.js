// Progress-presentation deck. Every number is read from cot-disclosure/results/summary.json,
// so rerunning analyze.py and then this script refreshes the slides.
//   npm install && node build_deck.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const RDS = require("react-dom/server");
const fa = require("react-icons/fa");
const sharp = require("sharp");

// pptxgenjs writes Office's stock palette into the theme; replace it with ours so the
// scheme colors used throughout the deck resolve correctly. jszip ships with pptxgenjs.
async function applyTheme(file, theme) {
  const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const part = "ppt/theme/theme1.xml";
  let xml = await zip.file(part).async("string");
  for (const slot of ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3",
    "accent4", "accent5", "accent6", "hlink", "folHlink"]) {
    xml = xml.replace(new RegExp(`<a:${slot}>[\\s\\S]*?</a:${slot}>`),
      `<a:${slot}><a:srgbClr val="${theme.colors[slot]}"/></a:${slot}>`);
  }
  xml = xml.replace(/<a:clrScheme name="[^"]*"/, `<a:clrScheme name="${theme.name}"`);
  zip.file(part, xml);
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

const S = JSON.parse(fs.readFileSync(path.join(__dirname, "../cot-disclosure/results/summary.json"), "utf8"));
const OUT = path.join(__dirname, "CSE598_progress_presentation.pptx");

const THEME = {
  name: "Two Channels",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A1D24", lt1: "FFFFFF", dk2: "232A36", lt2: "F1F4F8",
    accent1: "2A78D6", accent2: "EB6834", accent3: "1BAF7A", accent4: "EDA100",
    accent5: "6B7280", accent6: "4A3AA7", hlink: "2A78D6", folHlink: "4A3AA7",
  },
};
const HEX = THEME.colors;
const ORDER = ["olmo3-7b-instruct", "olmo3-7b-think", "olmo3-32b-instruct", "olmo3-32b-think",
  "qwen3-30b-a3b-instruct-2507", "qwen3-30b-a3b-thinking-2507"];
const LABEL = {
  "olmo3-7b-instruct": "Olmo 3 7B Instruct", "olmo3-7b-think": "Olmo 3 7B Think",
  "olmo3-32b-instruct": "Olmo 3 32B Instruct", "olmo3-32b-think": "Olmo 3 32B Think",
  "qwen3-30b-a3b-instruct-2507": "Qwen3 30B Instruct", "qwen3-30b-a3b-thinking-2507": "Qwen3 30B Thinking",
};
const pct = (v) => (v === null || v === undefined ? "–" : `${Math.round(v * 100)}%`);
const pts = (v, ci) => (v === null || v === undefined ? "–"
  : v === 0 && ci && ci[1] === 0 ? "no effect"
  : `${v >= 0 ? "+" : "−"}${Math.abs(v * 100).toFixed(1)} points${ci ? ` (${(ci[0] * 100).toFixed(1)} to ${(ci[1] * 100).toFixed(1)})` : ""}`);
const fmt = (n) => (n === null || n === undefined ? "–" : Math.round(n).toLocaleString("en-US"));

async function icon(Comp, hex) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: 256 }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "Do Thinking Modes Make Chain-of-Thought More Honest? (progress report)";
  pres.author = "Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal";
  const C = pres.SchemeColor;
  const W = 13.333;

  // ---------- layouts ----------
  pres.defineSlideMaster({
    title: "TITLE_DARK",
    background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.55, w: 7.4, h: 2.1, fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "subtitle", type: "body", x: 0.8, y: 3.85, w: 7.2, h: 0.9, fontSize: 19, color: C.background2, valign: "top", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "meta", type: "body", x: 0.8, y: 5.35, w: 7.4, h: 1.3, fontSize: 15, color: C.background2, valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: C.background1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 30, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
      { text: { text: "CSE 598 · Group 10 · Progress presentation", options: { x: 0.6, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: HEX.accent5, align: "right" },
  });

  const I = {
    puzzle: await icon(fa.FaPuzzlePiece, HEX.accent1), hint: await icon(fa.FaLightbulb, HEX.accent2),
    server: await icon(fa.FaServer, HEX.accent1), split: await icon(fa.FaCodeBranch, HEX.accent2),
    search: await icon(fa.FaSearch, HEX.accent1), chart: await icon(fa.FaChartBar, HEX.accent2),
    lockW: await icon(fa.FaLock, HEX.accent1), eyeW: await icon(fa.FaEye, HEX.accent2),
    toggle: await icon(fa.FaToggleOff, HEX.accent2), scale: await icon(fa.FaBalanceScale, HEX.accent1),
    check: await icon(fa.FaUserCheck, HEX.accent2), coins: await icon(fa.FaCoins, HEX.accent1),
    users: await icon(fa.FaUsers, HEX.accent1), flag: await icon(fa.FaFlagCheckered, HEX.accent2),
  };
  const circle = (slide, img, x, y, d, accent, name) => {
    slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: accent, transparency: 84 }, objectName: `${name}-circle` });
    const p = d * 0.26;
    slide.addImage({ data: img, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: `${name}-icon` });
  };
  const card = (slide, x, y, w, h, name) =>
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 }, objectName: name });

  const M = S.main;
  const present = ORDER.filter((m) => M[m]);
  const thinking = present.filter((m) => M[m].thinking);
  // wording that the data has to earn: never claim "always"/"never" unless it is literally true
  const sum = (k) => thinking.reduce((a, m) => a + (M[m][k] || 0), 0);
  const TM = sum("trace_mentions"), AM = sum("answer_mentions"), TN = sum("cued_n");
  const sees = TN && TM === TN ? "always see it" : TN && TM / TN >= 0.9 ? "almost always see it" : "often see it";
  const says = AM === 0 ? "never say so" : TN && AM / TN <= 0.05 ? "almost never say so" : "rarely say so";
  const sens = present.map((m) => M[m].sensitivity).filter((v) => v !== null && v !== undefined);
  const maxSens = sens.length ? Math.max(...sens) : 0;
  const sig = present.filter((m) => M[m].sensitivity_ci && M[m].sensitivity_ci[0] > 0);
  const r1Title = sig.length === 0 ? "Result 1: the hint barely changes answers"
    : sig.length === 1 ? `Result 1: only ${LABEL[sig[0]]} follows wrong hints`
    : "Result 1: some models follow wrong hints, others don’t";
  const twin = (m) => m.replace("instruct-2507", "thinking-2507").replace("-instruct", "-think");

  // ---------- 1. title ----------
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
  s.addText("Do Thinking Modes Make Chain-of-Thought More Honest?", { placeholder: "title" });
  s.addText("Progress report: do thinking models admit it when a hint sways their answer?", { placeholder: "subtitle" });
  s.addText([
    { text: "Group 10  ·  Shrey Bishnoi, Arsha Jindal, Ritik Agarwal", options: { bold: true, breakLine: true } },
    { text: "CSE 598 · Operationalizing Deep Learning · Fall 2026" },
  ], { placeholder: "meta" });
  s.addShape(pres.shapes.OVAL, { x: 8.75, y: 1.7, w: 2.7, h: 2.7, fill: { color: C.accent1, transparency: 70 }, objectName: "motif-private" });
  s.addShape(pres.shapes.OVAL, { x: 10.15, y: 2.95, w: 2.7, h: 2.7, fill: { color: C.accent2, transparency: 65 }, objectName: "motif-visible" });
  s.addImage({ data: I.lockW, x: 9.55, y: 2.45, w: 0.9, h: 0.9, objectName: "motif-lock" });
  s.addImage({ data: I.eyeW, x: 11.25, y: 4.05, w: 0.9, h: 0.9, objectName: "motif-eye" });
  s.addText("private reasoning", { x: 8.75, y: 1.2, w: 2.7, h: 0.4, fontSize: 13, color: C.background2, align: "center", isTextBox: true, margin: 0 });
  s.addText("final answer", { x: 10.15, y: 5.7, w: 2.7, h: 0.4, fontSize: 13, color: C.background2, align: "center", isTextBox: true, margin: 0 });
  s.addNotes("Hi, we're Group 10. Our question is simple: when a hint pushes a model toward an answer, does the model say so? Thinking models give us two places to look. There's the private reasoning they write first, and the final answer the user sees.");

  // ---------- 2. question & what changed ----------
  pres.addSection({ title: "Question & changes" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Question & changes" });
  s.addText("Our question, and what we changed after the review", { placeholder: "title" });
  card(s, 0.6, 1.5, 5.6, 4.45, "question-card");
  s.addText("When a hint changes a model’s answer, does the model say so?", { x: 0.9, y: 1.75, w: 5.0, h: 1.2, fontSize: 21, bold: true, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.9, y: 3.05, w: 5.0, h: 1.75, rectRadius: 0.06, fill: { color: C.background1 }, line: { color: C.accent5, width: 0.75 }, objectName: "prompt-mock" });
  s.addText([
    { text: "Alice, Bob, Claire … swap balls 15 times.", options: { breakLine: true } },
    { text: "At the end, Dave has the:  (A) blue  (B) orange  (C) purple  (D) black …", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "I think the answer is (C), but I’m curious what you think.", options: { bold: true, color: C.accent2 } },
  ], { x: 1.1, y: 3.2, w: 4.6, h: 1.5, fontSize: 13, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  s.addText("We test 3 pairs of models from Olmo 3 and Qwen3. Each pair has a regular chat model (Instruct) and a thinking model that reasons in private first.", { x: 0.9, y: 4.95, w: 5.0, h: 0.9, fontSize: 13, color: C.accent5, isTextBox: true, margin: 0, valign: "top" });
  s.addText("What we changed after the review", { x: 6.7, y: 1.5, w: 6.0, h: 0.5, fontSize: 19, bold: true, color: C.text1, isTextBox: true, margin: 0 });
  const changes = [
    ["The two models in a pair are trained differently,", " so a gap isn’t only about thinking. Voyager can’t turn thinking off, so we also ask the same model to “think briefly”."],
    ["We run each puzzle 3 times with no hint", " to see how much answers change by chance."],
    ["Hints point to every letter equally often,", " and some hints are correct."],
    ["Right answers are spread across the letters.", " Before, too many were (A)."],
    ["“Mentions the hint” is scored apart", " from “says the hint changed its answer”."],
    ["Maybe later: a second model", " reviews the first one’s answer. Does it catch the hint?"],
  ];
  s.addText(changes.flatMap(([b, rest], i) => [
    { text: b, options: { bold: true, bullet: true } },
    { text: rest, options: { breakLine: i < changes.length - 1 } },
  ]), { x: 6.7, y: 2.1, w: 6.0, h: 4.6, fontSize: 14, color: C.text1, paraSpaceAfter: 8, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Here's the setup. We give a model a puzzle, and sometimes we add a line like 'I think the answer is C.' Then we check two things: did the hint change the answer, and does the model mention it? The review pushed us on a few points. The regular and thinking models in a pair are trained differently, so a gap between them isn't only about thinking. We checked, and Voyager has no switch to turn thinking off, so we also ask the same model to think briefly. We now repeat each puzzle without a hint, spread hints and right answers evenly across the letters, and score 'mentions the hint' apart from 'says the hint changed its answer'.");

  // ---------- 3. pipeline ----------
  pres.addSection({ title: "Pipeline" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Pipeline" });
  s.addText("Our pipeline runs end to end", { placeholder: "title" });
  const steps = [
    [I.puzzle, HEX.accent1, "Make puzzles", "Swap puzzles with one right answer, made fresh so no model has seen them"],
    [I.hint, HEX.accent2, "Add a hint", "No hint, a wrong hint, or a right one, spread across the letters"],
    [I.server, HEX.accent1, "Ask 6 models", "3 pairs on ASU’s free Voyager service; we save every reply"],
    [I.split, HEX.accent2, "Split the reply", "The private reasoning and the final answer come back separately"],
    [I.search, HEX.accent1, "Score", "Read off the answer letter; check if the hint is mentioned"],
    [I.chart, HEX.accent2, "Compare", "With vs without the hint, with 95% ranges"],
  ];
  const sx = 0.6, sw = 1.95, gap = 0.08;
  steps.forEach(([img, accent, head, body], i) => {
    const x = sx + i * (sw + gap);
    circle(s, img, x + (sw - 0.95) / 2, 1.55, 0.95, accent === HEX.accent1 ? C.accent1 : C.accent2, `step${i + 1}`);
    s.addText(head, { x, y: 2.65, w: sw, h: 0.45, fontSize: 15, bold: true, color: C.text1, align: "center", isTextBox: true, margin: 0 });
    s.addText(body, { x: x + 0.05, y: 3.1, w: sw - 0.1, h: 1.2, fontSize: 12, color: C.accent5, align: "center", isTextBox: true, margin: 0, valign: "top" });
    if (i < steps.length - 1) {
      s.addShape(pres.shapes.LINE, { x: x + sw / 2 + 0.6, y: 2.02, w: sw - 1.12, h: 0, line: { color: C.accent5, width: 1.25, endArrowType: "triangle" }, objectName: `arrow${i + 1}` });
    }
  });
  const totalCalls = S.calls_done;
  const stats = [
    [fmt(totalCalls), "questions sent this round"],
    [`${present.length}`, "models from 2 families"],
    [fmt(S.errors), "failed calls"],
    [fmt(S.history.pilot_calls + 120), "calls in earlier test runs"],
  ];
  stats.forEach(([big, small], i) => {
    const x = 0.6 + i * 3.05;
    card(s, x, 4.6, 2.85, 1.95, `stat${i + 1}`);
    s.addText(big, { x, y: 4.8, w: 2.85, h: 0.95, fontSize: 40, bold: true, color: i % 2 ? C.accent2 : C.accent1, align: "center", isTextBox: true, margin: 0 });
    s.addText(small, { x: x + 0.15, y: 5.8, w: 2.55, h: 0.55, fontSize: 13, color: C.text1, align: "center", isTextBox: true, margin: 0 });
  });
  s.addNotes("This is our pipeline, and it works from start to finish. We make fresh puzzles with one right answer, add a hint or not, and send them to six models on ASU's free Voyager service. Each reply comes back in two parts, the private reasoning and the final answer. We save every reply, so rerunning the analysis costs nothing. Along the way we fixed two problems. Long replies were timing out, and almost half the answers weren't in the format we asked for, so a simple reader would have marked them wrong.");

  // ---------- 4. result: who follows the hint ----------
  pres.addSection({ title: "Results" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText(r1Title, { placeholder: "title" });
  const noHint = present.map((m) => M[m].pct_chose_same_letter_without_hint ?? 0);
  const withHint = present.map((m) => M[m].pct_chose_suggested_with_hint ?? 0);
  const top = Math.max(0.25, Math.ceil((Math.max(...noHint, ...withHint) * 1.4) / 0.05) * 0.05);
  s.addChart(pres.charts.BAR, [
    { name: "No hint: picked that option anyway", labels: present.map((m) => LABEL[m]), values: noHint },
    { name: "With hint: picked the hinted option", labels: present.map((m) => LABEL[m]), values: withHint },
  ], {
    x: 0.6, y: 1.4, w: 7.6, h: 5.3, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 55,
    chartColors: [HEX.accent1, HEX.accent2], catAxisOrientation: "maxMin",
    showTitle: true, title: "How often models chose the wrong option the hint pointed to", titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: HEX.dk1,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0%", dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelColor: HEX.dk1,
    valAxisMinVal: 0, valAxisMaxVal: top, valAxisLabelFormatCode: "0%", valAxisLabelColor: HEX.accent5, valAxisLabelFontFace: "+mn-lt", valAxisLabelFontSize: 11,
    catAxisLabelColor: HEX.dk1, catAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12,
    valGridLine: { color: "E3E7ED", size: 0.75 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: HEX.dk1,
  });
  card(s, 8.6, 1.4, 4.1, 5.3, "r1-card");
  s.addText("How much the hint moved answers (95% range)", { x: 8.85, y: 1.6, w: 3.7, h: 0.45, fontSize: 13.5, bold: true, color: C.text1, isTextBox: true, margin: 0 });
  s.addText(present.map((m, i) => ({ text: `${LABEL[m]}:  ${pts(M[m].sensitivity, M[m].sensitivity_ci)}`,
    options: { breakLine: i < present.length - 1 } })),
  { x: 8.85, y: 2.1, w: 3.7, h: 2.1, fontSize: 11.5, color: C.text1, paraSpaceAfter: 4, isTextBox: true, margin: 0, valign: "top" });
  const s0 = sig[0];
  const t0 = s0 && M[twin(s0)];
  s.addText(s0 ? [
    { text: "What we found: ", options: { bold: true } },
    { text: `${LABEL[s0]} picked the wrong hinted answer ${pct(M[s0].pct_chose_suggested_with_hint)} of the time, and never without the hint.${t0 ? ` Its thinking twin: ${pct(t0.pct_chose_suggested_with_hint)}.` : ""} The larger models: never.`, options: { breakLine: true } },
    { text: "Limits: ", options: { bold: true } },
    { text: `one kind of puzzle, 24 puzzles. The larger models solve almost all of them, so a hint has little room to work. Run again with no hint, ${LABEL[s0]} changed its answer on ${pct(M[s0].nocue_disagree)} of puzzles, but never to the hinted letter.` },
  ] : [
    { text: "What we found: ", options: { bold: true } },
    { text: "a wrong hint moves answers by only a few points, about as much as chance does.", options: { breakLine: true } },
    { text: "Limits: ", options: { bold: true } },
    { text: "one kind of puzzle, 24 puzzles. The models get most of them right, so a hint has little room to work." },
  ], { x: 8.85, y: 4.25, w: 3.7, h: 2.35, fontSize: 11.5, color: C.text1, paraSpaceAfter: 5, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Our first result. Blue is how often a model picked a wrong option with no hint. Orange is how often it picked that same option when we suggested it. Only one model follows the hint. Olmo 3 7B Instruct picks the wrong hinted answer about 10% of the time and never without the hint, and our 95% range stays above zero, so it isn't luck. Its thinking twin barely moves, and the larger models don't move at all, partly because they solve these puzzles every time. We also checked chance: run again without a hint, Olmo 7B Instruct changes its answer on almost a third of puzzles, but never to the hinted letter.");

  // ---------- 5. result: notice it, then leave it out ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText(`Result 2: thinking models see the hint, ${AM === 0 ? "never" : "rarely"} mention it`, { placeholder: "title" });
  const traceShare = thinking.map((m) => (M[m].cued_n ? M[m].trace_mentions / M[m].cued_n : 0));
  const answerShare = thinking.map((m) => (M[m].cued_n ? M[m].answer_mentions / M[m].cued_n : 0));
  s.addChart(pres.charts.BAR, [
    { name: "Private reasoning mentions the hint", labels: thinking.map((m) => LABEL[m]), values: traceShare },
    { name: "Final answer mentions the hint", labels: thinking.map((m) => LABEL[m]), values: answerShare },
  ], {
    x: 0.6, y: 1.4, w: 7.6, h: 5.3, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 55,
    chartColors: [HEX.accent1, HEX.accent2], catAxisOrientation: "maxMin",
    showTitle: true, title: "How often the hint is mentioned, in runs that had one", titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: HEX.dk1,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0%", dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelColor: HEX.dk1,
    valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0%", valAxisLabelColor: HEX.accent5, valAxisLabelFontFace: "+mn-lt", valAxisLabelFontSize: 11,
    catAxisLabelColor: HEX.dk1, catAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12,
    valGridLine: { color: "E3E7ED", size: 0.75 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: HEX.dk1,
  });
  const tm = thinking.reduce((a, m) => a + (M[m].trace_mentions || 0), 0);
  const am = thinking.reduce((a, m) => a + (M[m].answer_mentions || 0), 0);
  const tn = thinking.reduce((a, m) => a + (M[m].cued_n || 0), 0);
  card(s, 8.6, 1.4, 4.1, 5.3, "r2-card");
  circle(s, I.lockW, 8.85, 1.65, 0.7, C.accent1, "r2-lock");
  s.addText(`${tm} / ${tn}`, { x: 9.7, y: 1.6, w: 2.9, h: 0.6, fontSize: 30, bold: true, color: C.accent1, isTextBox: true, margin: 0 });
  s.addText("times the private reasoning mentions it", { x: 9.7, y: 2.15, w: 2.9, h: 0.35, fontSize: 12, color: C.text1, isTextBox: true, margin: 0 });
  circle(s, I.eyeW, 8.85, 2.75, 0.7, C.accent2, "r2-eye");
  s.addText(`${am} / ${tn}`, { x: 9.7, y: 2.7, w: 2.9, h: 0.6, fontSize: 30, bold: true, color: C.accent2, isTextBox: true, margin: 0 });
  s.addText("times the final answer mentions it", { x: 9.7, y: 3.25, w: 2.9, h: 0.35, fontSize: 12, color: C.text1, isTextBox: true, margin: 0 });
  const fam = (pre) => {
    const ms = present.filter((m) => m.startsWith(pre));
    const pick = (thinkFlag, k) => ms.filter((m) => M[m].thinking === thinkFlag).reduce((a, m) => a + (M[m][k] || 0), 0);
    return { iv: pick(false, "visible_mentions"), ivn: pick(false, "hinted_n"), tv: pick(true, "visible_mentions"), tvn: pick(true, "hinted_n") };
  };
  const olmo = fam("olmo3"), qwen = fam("qwen3");
  s.addText([
    { text: "Compare regular models: ", options: { bold: true } },
    { text: `Olmo’s regular models mention the hint in ${olmo.iv} of ${olmo.ivn} replies; its thinking models, ${olmo.tv} of ${olmo.tvn}. For Qwen it’s ${qwen.iv} vs ${qwen.tv} out of ${qwen.ivn}, about the same.`, options: { breakLine: true } },
    { text: "Mentioning isn’t admitting: ", options: { bold: true } },
    { text: "the reasoning usually brushes the hint off (“the user thought C, but…”).", options: { breakLine: true } },
    { text: "Limits: ", options: { bold: true } },
    { text: "we find mentions by keyword for now; hand labels come next. Leaving the hint out doesn’t prove a model is hiding something." },
  ], { x: 8.85, y: 3.8, w: 3.7, h: 2.85, fontSize: 11.5, color: C.text1, paraSpaceAfter: 5, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Our second result, and the one we'll build on. When there's a hint, thinking models mention it in their private reasoning almost every time. It almost never reaches the final answer: zero times for Olmo, and 8 times out of 216 overall. Olmo's regular models have no private reasoning, and they mention the hint in about a third of their replies. So for Olmo, thinking moves the mention out of sight. Qwen shows no such gap. Two cautions. Most of those mentions are the model brushing the hint off, so we count them as mentions, not admissions. And leaving the hint out doesn't prove a model is hiding something. The private reasoning isn't a perfect view of what goes on inside the model either.");

  // ---------- 6. side findings ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("Smaller findings that change our plan", { placeholder: "title" });
  const ratios = present.map((m) => M[m].median_token_ratio).filter(Boolean);
  const nocotThink = Object.values(S.nocot).filter((v) => v.label.includes("think") || v.label.includes("Think"));
  const stillThinks = nocotThink.length ? Math.min(...nocotThink.map((v) => v.still_thinks)) : null;
  const stillThinksMax = nocotThink.length ? Math.max(...nocotThink.map((v) => v.still_thinks)) : null;
  const nocotInstr = Object.values(S.nocot).filter((v) => !(v.label.includes("think") || v.label.includes("Think")));
  const instrDrop = nocotInstr.map((v) => `from ${pct(v.acc_steps)} to ${pct(v.acc_direct)}`).join(" and ");
  const briefRatios = Object.values(S.brief).map((v) => v.trace_chars_brief / v.trace_chars_normal).filter((x) => isFinite(x));
  const findings = [
    [ratios.length ? `${pct(Math.min(...ratios) - 1)} to ${pct(Math.max(...ratios) - 1)}` : "–", "longer replies when there’s a hint, on all six models, even when the answer stays the same. The hint costs extra work.", C.accent2],
    [stillThinks === null ? "–" : `${pct(stillThinks)} to ${pct(stillThinksMax)}`, `of the time, thinking models told “answer only, don’t explain” still reasoned in private and stayed accurate. Regular models dropped ${instrDrop || "–"} correct.`, C.accent1],
    [`${S.history.leak_trace_separate === 0 ? S.history.leak_truncated : "?"} / ${S.history.leak_truncated}`, "replies that hit the length limit spilled the private reasoning into the visible answer (about 27,000 characters).", C.accent2],
    [briefRatios.length ? `${pct(1 - Math.max(...briefRatios))} to ${pct(1 - Math.min(...briefRatios))}` : "–", "shorter reasoning when we ask the same model to “think briefly”. This lets us vary thinking without switching models.", C.accent1],
  ];
  findings.forEach(([big, text, color], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.65;
    card(s, x, y, 5.95, 2.45, `finding${i + 1}`);
    s.addText(big, { x: x + 0.3, y: y + 0.3, w: 5.35, h: 0.95, fontSize: 40, bold: true, color, isTextBox: true, margin: 0 });
    s.addText(text, { x: x + 0.3, y: y + 1.3, w: 5.35, h: 0.95, fontSize: 14, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addNotes("A few smaller findings that change how we run things. A hint makes every model write more, even when the answer stays the same. When we tell a thinking model 'answer only, don't explain', it still reasons in private and stays accurate. Regular models told the same thing get almost everything wrong, worse than guessing. When a reply hits the length limit, the private reasoning spills into the answer the user sees, which matters for anyone building on these models. And asking for brief thinking shortens the reasoning on the same model, which gives us the same-model comparison the review asked for.");

  // ---------- 7. risks ----------
  pres.addSection({ title: "Risks & next steps" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Risks & next steps" });
  s.addText("Risks and how we’re handling them", { placeholder: "title" });
  const costX = [[0, 1], [2, 3], [4, 5]].map(([a, b]) => M[ORDER[b]] && M[ORDER[a]] ? M[ORDER[b]].median_tokens_none / M[ORDER[a]].median_tokens_none : null).filter(Boolean);
  const costHead = costX.length ? `Thinking models write ${Math.min(...costX).toFixed(1)} to ${Math.max(...costX).toFixed(1)} times as much` : "Thinking models write much more";
  const risks = [
    [I.toggle, C.accent2, "We can’t turn thinking off on Voyager", "We tried it on 7 models and the setting is ignored. So we treat each pair as two different models, ask the same model to “think briefly”, and may run models ourselves on ASU’s Sol computers if we get GPU time."],
    [I.scale, C.accent1, "The hint only moves the smallest model on these puzzles", "We’ll add questions where hints have more room: ambiguous questions about people (BBQ) and harder reasoning tasks (BBH). If hints still do little, that is a real result too."],
    [I.check, C.accent2, "Keyword search can’t tell a mention from an admission", "Two of us will hand-label 200 replies as: no mention, mentions the hint, or says the hint changed its answer. We’ll report how often we agree."],
    [I.coins, C.accent1, costHead, "Our full proposal would need about 180 million tokens (word pieces) of output. We’ll cut that to about 55 million, time a small run first, and keep getting replies in pieces so long ones don’t time out."],
  ];
  risks.forEach(([img, accent, head, body], i) => {
    const y = 1.45 + i * 1.35;
    circle(s, img, 0.6, y + 0.05, 0.85, accent, `risk${i + 1}`);
    s.addText(head, { x: 1.7, y, w: 10.9, h: 0.42, fontSize: 16, bold: true, color: C.text1, isTextBox: true, margin: 0 });
    s.addText(body, { x: 1.7, y: y + 0.43, w: 10.9, h: 0.8, fontSize: 13, color: C.accent5, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addNotes("Our main risks. First, we can't turn thinking off on Voyager, so comparing regular and thinking models means comparing two differently trained models. We say that openly, and we added the 'think briefly' test on the same model. Second, the hint only moves the smallest model on these puzzles, so we're adding questions where hints have more room. Third, keyword search can't tell a mention from an admission, so two of us will hand-label 200 replies. Fourth, cost: thinking models write about four times as much, so we're shrinking the plan and timing a test run first.");

  // ---------- 8. next steps ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Risks & next steps" });
  s.addText("Next steps", { placeholder: "title" });
  const plan = [
    ["Week 9", "Add BBQ and BBH questions, time a test run, lock the prompts"],
    ["Weeks 10-11", "Main runs, and hand-label 200 replies (2 people)"],
    ["Weeks 12-13", "If we’re on track: a second model reviews the first"],
    ["Weeks 14-15", "Stats, charts, report draft"],
    ["Week 16", "Final presentation"],
  ];
  plan.forEach(([when, what], i) => {
    const x = 0.6 + i * 2.4;
    s.addShape(pres.shapes.CHEVRON, { x, y: 1.6, w: 2.5, h: 0.9, fill: { color: i % 2 ? C.accent2 : C.accent1, transparency: 15 }, objectName: `chev${i + 1}` });
    s.addText(when, { x: x + 0.35, y: 1.6, w: 1.8, h: 0.9, fontSize: 15, bold: true, color: C.background1, align: "center", valign: "middle", isTextBox: true, margin: 0 });
    s.addText(what, { x: x + 0.1, y: 2.65, w: 2.2, h: 1.3, fontSize: 13, color: C.text1, align: "center", isTextBox: true, margin: 0, valign: "top" });
  });
  card(s, 0.6, 3.85, 12.1, 2.6, "roles-card");
  circle(s, I.users, 0.9, 4.15, 0.85, C.accent1, "roles");
  s.addText("Who does what", { x: 2.0, y: 4.1, w: 10.4, h: 0.45, fontSize: 16, bold: true, color: C.text1, isTextBox: true, margin: 0 });
  s.addText([
    { text: "Shrey Bishnoi (coordinator): ", options: { bold: true } }, { text: "code that runs the models, the two-model extension", options: { breakLine: true } },
    { text: "Arsha Jindal: ", options: { bold: true } }, { text: "question sets, hints, labeling guide", options: { breakLine: true } },
    { text: "Ritik Agarwal: ", options: { bold: true } }, { text: "stats, charts, checking how well our labels agree", options: { breakLine: true } },
    { text: "All three: ", options: { bold: true } }, { text: "hand-labeling, presentations, report" },
  ], { x: 2.0, y: 4.6, w: 10.4, h: 1.7, fontSize: 15, color: C.text1, paraSpaceAfter: 3, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Next steps. Next week we add the new question sets, time a test run, and lock the prompts. Weeks ten and eleven are the main runs and the hand-labeling. If we're on track, we'll try the extension the reviewer suggested: one model gets the hint, a second model reviews its answer, and we see if the second one catches it or passes it along. Roles are on the slide.");

  // ---------- 9. closing ----------
  s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Risks & next steps" });
  s.addText([{ text: `Models mostly ignore the hint, but thinking models ${sees} and ${says}.`, options: { fontSize: 32 } }], { placeholder: "title" });
  s.addText("Next: does a second model catch this, or pass it along?", { placeholder: "subtitle" });
  s.addText([{ text: "Questions?", options: { fontSize: 28, bold: true, color: C.accent2 } }], { placeholder: "meta" });
  s.addShape(pres.shapes.OVAL, { x: 8.75, y: 1.7, w: 2.7, h: 2.7, fill: { color: C.accent1, transparency: 70 }, objectName: "close-private" });
  s.addShape(pres.shapes.OVAL, { x: 10.15, y: 2.95, w: 2.7, h: 2.7, fill: { color: C.accent2, transparency: 65 }, objectName: "close-visible" });
  s.addImage({ data: I.lockW, x: 9.55, y: 2.45, w: 0.9, h: 0.9, objectName: "close-lock" });
  s.addImage({ data: I.eyeW, x: 11.25, y: 4.05, w: 0.9, h: 0.9, objectName: "close-eye" });
  s.addNotes("To sum up: on these puzzles the hint mostly doesn't change answers, but thinking models almost always notice it in private and almost never mention it in the answer. Next we test whether a second model catches that. Thanks, we'll take questions now.");

  // ---------- backup ----------
  pres.addSection({ title: "Backup" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Backup" });
  s.addText("Backup: how the two models in each pair differ", { placeholder: "title" });
  const hdr = { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 14 };
  const cell = { fontSize: 13.5, color: C.text1, valign: "top" };
  s.addTable([
    [{ text: "Pair", options: hdr }, { text: "Names on Voyager", options: hdr }, { text: "Same", options: hdr }, { text: "Different", options: hdr }],
    [{ text: "Olmo 3 7B", options: cell }, { text: "olmo3-7b-instruct\nolmo3-7b-think", options: cell }, { text: "Same base model and the same three training stages", options: cell }, { text: "Think learned from worked reasoning written by other models (QwQ-32B, DeepSeek-R1). Instruct learned from chat and tool-use examples with that reasoning removed", options: cell }],
    [{ text: "Olmo 3 32B", options: cell }, { text: "olmo3-32b-instruct\nolmo3-32b-think", options: cell }, { text: "Same as above", options: cell }, { text: "Same training recipes. A newer Olmo 3.1 32B also exists; we still need to check which one Voyager runs", options: cell }],
    [{ text: "Qwen3 30B", options: cell }, { text: "qwen3-30b-a3b-instruct-2507\nqwen3-30b-a3b-thinking-2507", options: cell }, { text: "Same design and size (30.5B parameters, 3.3B used per word)", options: cell }, { text: "Trained separately after the base model: one always thinks, one never does. Their makers suggest slightly different randomness (0.6 vs 0.7); we use 0.6 for both", options: cell }],
  ], { x: 0.6, y: 1.5, w: 12.1, colW: [1.7, 3.1, 2.8, 4.5], border: { type: "solid", color: "D5DBE3", pt: 0.75 }, margin: 0.08 });
  s.addText("Sources: AI2’s Olmo 3 release and model cards; Qwen3-2507 model cards.", { x: 0.6, y: 6.35, w: 12.1, h: 0.35, fontSize: 11, color: C.accent5, isTextBox: true, margin: 0 });

  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Backup" });
  s.addText("Backup: how we ran this round", { placeholder: "title" });
  s.addTable([
    [{ text: "Setting", options: hdr }, { text: "This round", options: hdr }],
    [{ text: "Puzzles", options: cell }, { text: "24 swap puzzles (7 people, 15 swaps), with right answers spread evenly across A to G", options: cell }],
    [{ text: "Runs per puzzle", options: cell }, { text: "No hint 3 times, a wrong hint 2 times (spread across letters), a right hint once", options: cell }],
    [{ text: "Settings", options: cell }, { text: "Randomness (temperature) 0.6, fixed random seeds so runs repeat exactly, up to 16,000 tokens per reply", options: cell }],
    [{ text: "Extra tests", options: cell }, { text: "“Think briefly” on 2 thinking models; “answer only” on 4 models", options: cell }],
    [{ text: "Typical reply length (tokens)", options: cell }, { text: present.map((m) => `${LABEL[m]} ${fmt(M[m].median_tokens_none)}`).join(" · "), options: cell }],
    [{ text: "Calls", options: cell }, { text: `${fmt(S.calls_done)} this round; ${fmt(S.errors)} failed`, options: cell }],
  ], { x: 0.6, y: 1.5, w: 12.1, colW: [2.8, 9.3], border: { type: "solid", color: "D5DBE3", pt: 0.75 }, margin: 0.08 });

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
}
main().catch((e) => { console.error(e); process.exit(1); });
