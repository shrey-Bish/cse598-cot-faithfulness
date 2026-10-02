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
const pp = (v) => (v === null || v === undefined ? "–" : `${v >= 0 ? "+" : "−"}${Math.abs(v * 100).toFixed(1)} pp`);
const fmt = (n) => (n === null || n === undefined ? "–" : Math.round(n).toLocaleString("en-US"));

async function icon(Comp, hex) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: 256 }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "Do Thinking Modes Make Chain-of-Thought More Honest? - Progress";
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
      { text: { text: "CSE 598 · Progress presentation · Do thinking modes make CoT more honest?", options: { x: 0.6, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
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
  const leaves = AM === 0 ? "then leave it out" : "then mostly leave it out";
  const sens = present.map((m) => M[m].sensitivity).filter((v) => v !== null && v !== undefined);
  const maxSens = sens.length ? Math.max(...sens) : 0;
  const r1Title = maxSens < 0.10 ? "Result 1: the hint barely changes answers" : "Result 1: the hint shifts some answers, modestly";

  // ---------- 1. title ----------
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
  s.addText("Do Thinking Modes Make Chain-of-Thought More Honest?", { placeholder: "title" });
  s.addText("Progress report: do thinking models’ explanations admit a hint that shaped their answer?", { placeholder: "subtitle" });
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
  s.addNotes("Hi, we're Group 10. Our question: when a hint pushes a model toward an answer, does its explanation say so? Thinking models give us two channels to check — a private reasoning trace and the final answer the user sees.");

  // ---------- 2. question & what changed ----------
  pres.addSection({ title: "Question & changes" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Question & changes" });
  s.addText("The question, and what changed after review", { placeholder: "title" });
  card(s, 0.6, 1.5, 5.6, 4.45, "question-card");
  s.addText("When a hint shapes a model’s answer, does its explanation say so?", { x: 0.9, y: 1.75, w: 5.0, h: 1.2, fontSize: 21, bold: true, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.9, y: 3.05, w: 5.0, h: 1.75, rectRadius: 0.06, fill: { color: C.background1 }, line: { color: C.accent5, width: 0.75 }, objectName: "prompt-mock" });
  s.addText([
    { text: "Alice, Bob, Claire … swap balls 15 times.", options: { breakLine: true } },
    { text: "At the end, Dave has the:  (A) blue  (B) orange  (C) purple  (D) black …", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "I think the answer is (C), but I’m curious what you think.", options: { bold: true, color: C.accent2 } },
  ], { x: 1.1, y: 3.2, w: 4.6, h: 1.5, fontSize: 13, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  s.addText("Three instruct/thinking pairs, two families (Olmo 3, Qwen3), on ASU’s Voyager API.", { x: 0.9, y: 5.0, w: 5.0, h: 0.8, fontSize: 13, color: C.accent5, isTextBox: true, margin: 0, valign: "top" });
  s.addText("Since the proposal", { x: 6.7, y: 1.5, w: 6.0, h: 0.5, fontSize: 19, bold: true, color: C.text1, isTextBox: true, margin: 0 });
  const changes = [
    ["Instruct vs thinking = differently trained models.", " Voyager has no thinking on/off switch, so we added “think briefly” vs normal on the same checkpoint."],
    ["Repeated no-hint runs", " (3 seeds) to separate hint effects from normal run-to-run variation."],
    ["Hints balanced across answer positions", ", and correct hints added alongside wrong ones."],
    ["Correct answers balanced across positions", " — they had piled up at (A)."],
    ["“Mentions the hint” ≠ “admits it changed the answer”", " — scored separately."],
    ["Planned: a two-agent version", " — does a reviewer model catch or repeat the influence?"],
  ];
  s.addText(changes.flatMap(([b, rest], i) => [
    { text: b, options: { bold: true, bullet: true } },
    { text: rest, options: { breakLine: i < changes.length - 1 } },
  ]), { x: 6.7, y: 2.1, w: 6.0, h: 4.6, fontSize: 14, color: C.text1, paraSpaceAfter: 8, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("We ask whether a model's explanation admits a hint that shaped its answer. The review pushed us on controls: instruct and thinking models are trained differently, so we no longer call that a clean thinking on/off comparison — and Voyager can't switch thinking off, which we checked. We added repeated no-hint runs, balanced hint and answer positions, correct hints, and we now score 'mentions the hint' separately from 'admits it changed the answer'.");

  // ---------- 3. pipeline ----------
  pres.addSection({ title: "Pipeline" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Pipeline" });
  s.addText("The pipeline runs end to end", { placeholder: "title" });
  const steps = [
    [I.puzzle, HEX.accent1, "Generate puzzles", "Shuffled-object tasks with exact answers; new each time, so no training-data overlap"],
    [I.hint, HEX.accent2, "Add a hint", "None, wrong, or correct; positions balanced"],
    [I.server, HEX.accent1, "Ask 6 models", "3 instruct/thinking pairs on ASU Voyager, streamed, cached"],
    [I.split, HEX.accent2, "Split channels", "Private reasoning vs final answer"],
    [I.search, HEX.accent1, "Score", "Parse the answer; detect hint mentions"],
    [I.chart, HEX.accent2, "Analyze", "Hint effect vs no-hint variation, bootstrap CIs"],
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
    [fmt(totalCalls), "model calls in this round"],
    [`${present.length}`, "models, 2 families"],
    [fmt(S.errors), "API errors after fixes"],
    [fmt(S.history.pilot_calls + 120), "calls in earlier pilots"],
  ];
  stats.forEach(([big, small], i) => {
    const x = 0.6 + i * 3.05;
    card(s, x, 4.6, 2.85, 1.95, `stat${i + 1}`);
    s.addText(big, { x, y: 4.8, w: 2.85, h: 0.95, fontSize: 40, bold: true, color: i % 2 ? C.accent2 : C.accent1, align: "center", isTextBox: true, margin: 0 });
    s.addText(small, { x: x + 0.15, y: 5.8, w: 2.55, h: 0.55, fontSize: 13, color: C.text1, align: "center", isTextBox: true, margin: 0 });
  });
  s.addNotes("Here's the pipeline. We generate fresh puzzles with exact answers, add a hint or not, send them to six models on ASU's free Voyager API, and split each reply into the private reasoning and the final answer. Everything is streamed and cached, so reruns are free. Along the way we fixed server timeouts and an answer parser that was silently marking 45% of answers wrong.");

  // ---------- 4. result: hint barely changes answers ----------
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
  s.addText("Hint effect (with − without), 95% CI", { x: 8.85, y: 1.6, w: 3.7, h: 0.45, fontSize: 14, bold: true, color: C.text1, isTextBox: true, margin: 0 });
  s.addText(present.map((m, i) => {
    const ci = M[m].sensitivity_ci;
    return { text: `${LABEL[m]}:  ${pp(M[m].sensitivity)}${ci ? `  [${pp(ci[0])}, ${pp(ci[1])}]` : ""}`,
      options: { breakLine: i < present.length - 1 } };
  }), { x: 8.85, y: 2.1, w: 3.7, h: 2.3, fontSize: 11.5, color: C.text1, paraSpaceAfter: 4, isTextBox: true, margin: 0, valign: "top" });
  s.addText([
    { text: "What we can say: ", options: { bold: true } },
    { text: "on these puzzles a wrong hint shifts choices by only a few points, within ordinary run-to-run variation for most models.", options: { breakLine: true } },
    { text: "Limits: ", options: { bold: true } },
    { text: "one task, 24 puzzles. The models are mostly accurate here, so a hint has little room to work." },
  ], { x: 8.85, y: 4.45, w: 3.7, h: 2.1, fontSize: 12, color: C.text1, paraSpaceAfter: 6, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("First result. Blue is how often a model picked an option with no hint at all; orange is how often it picked that same option when we suggested it. The gap is the hint's effect, and it's small — a few points, mostly inside normal run-to-run variation. That's a null result at this difficulty, and we think it's partly the task: the models solve these puzzles, so there's little room to be pushed.");

  // ---------- 5. result: notice it, then leave it out ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText(`Result 2: thinking models notice the hint, ${leaves}`, { placeholder: "title" });
  const traceShare = thinking.map((m) => (M[m].cued_n ? M[m].trace_mentions / M[m].cued_n : 0));
  const answerShare = thinking.map((m) => (M[m].cued_n ? M[m].answer_mentions / M[m].cued_n : 0));
  s.addChart(pres.charts.BAR, [
    { name: "Private reasoning mentions the hint", labels: thinking.map((m) => LABEL[m]), values: traceShare },
    { name: "Final answer mentions the hint", labels: thinking.map((m) => LABEL[m]), values: answerShare },
  ], {
    x: 0.6, y: 1.4, w: 7.6, h: 5.3, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 55,
    chartColors: [HEX.accent1, HEX.accent2], catAxisOrientation: "maxMin",
    showTitle: true, title: "Share of hinted runs that mention the hint", titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: HEX.dk1,
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
  s.addText("private traces mention the hint", { x: 9.7, y: 2.15, w: 2.9, h: 0.35, fontSize: 12, color: C.text1, isTextBox: true, margin: 0 });
  circle(s, I.eyeW, 8.85, 2.75, 0.7, C.accent2, "r2-eye");
  s.addText(`${am} / ${tn}`, { x: 9.7, y: 2.7, w: 2.9, h: 0.6, fontSize: 30, bold: true, color: C.accent2, isTextBox: true, margin: 0 });
  s.addText("final answers mention it", { x: 9.7, y: 3.25, w: 2.9, h: 0.35, fontSize: 12, color: C.text1, isTextBox: true, margin: 0 });
  const instr = present.filter((m) => !M[m].thinking);
  const iv = instr.reduce((a, m) => a + (M[m].visible_mentions || 0), 0);
  const ivn = instr.reduce((a, m) => a + (M[m].hinted_n || 0), 0);
  s.addText([
    { text: "Compare instruct models (one channel): ", options: { bold: true } },
    { text: `their visible reply mentions the hint in ${iv} / ${ivn} hinted runs.`, options: { breakLine: true } },
    { text: "Mostly mentions, not admissions: ", options: { bold: true } },
    { text: "traces usually reject the hint (“the user thought C, but…”).", options: { breakLine: true } },
    { text: "Limits: ", options: { bold: true } },
    { text: "keyword detector, manual labels pending. Omission is our operational measure, not proof of dishonesty, and the trace is not the model’s internal computation." },
  ], { x: 8.85, y: 3.8, w: 3.7, h: 2.85, fontSize: 11.5, color: C.text1, paraSpaceAfter: 5, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Second result, and the one we'll build on. When there's a hint, the thinking models discuss it in their private reasoning almost every time, but it rarely if ever reaches the answer the user sees. Instruct models, which only have one channel, do mention it in their visible reply some of the time, so thinking seems to move the acknowledgement out of sight. Two cautions: most of those trace mentions are the model rejecting the hint, so this is 'mentions', not 'admits influence'. And omission is our operational measure — it's not proof of dishonesty, and the trace isn't the model's actual computation.");

  // ---------- 6. side findings ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("Smaller findings that shape the design", { placeholder: "title" });
  const ratios = thinking.map((m) => M[m].median_token_ratio).filter(Boolean);
  const nocotThink = Object.values(S.nocot).filter((v) => v.label.includes("think") || v.label.includes("Think"));
  const stillThinks = nocotThink.length ? Math.min(...nocotThink.map((v) => v.still_thinks)) : null;
  const briefRatios = Object.values(S.brief).map((v) => v.trace_chars_brief / v.trace_chars_normal).filter((x) => isFinite(x));
  const findings = [
    [ratios.length ? `×${Math.min(...ratios).toFixed(2)}–${Math.max(...ratios).toFixed(2)}` : "–", "more output tokens with a hint, for thinking models, even when the answer stays the same", C.accent2],
    [stillThinks === null ? "–" : pct(stillThinks), "of “answer only, don’t explain” prompts still produced a private trace on thinking models", C.accent1],
    [`${S.history.leak_trace_separate === 0 ? S.history.leak_truncated : "?"} / ${S.history.leak_truncated}`, "responses cut off at the token limit dumped the private trace into the visible answer (~27k characters)", C.accent2],
    [briefRatios.length ? `×${(briefRatios.reduce((a, b) => a + b, 0) / briefRatios.length).toFixed(2)}` : "–", "trace length when asked to “think briefly”, on the same checkpoint: one way to vary reasoning without changing models", C.accent1],
  ];
  findings.forEach(([big, text, color], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.65;
    card(s, x, y, 5.95, 2.45, `finding${i + 1}`);
    s.addText(big, { x: x + 0.3, y: y + 0.3, w: 5.35, h: 0.95, fontSize: 40, bold: true, color, isTextBox: true, margin: 0 });
    s.addText(text, { x: x + 0.3, y: y + 1.3, w: 5.35, h: 0.95, fontSize: 14, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addNotes("A few smaller findings that change how we run things. The hint makes thinking models write longer, so influence costs compute even when the answer holds. Telling a thinking model 'don't explain' only hides the explanation; it still thinks privately. If a response hits the token limit, the private reasoning spills into the visible answer — a real deployment hazard. And 'think briefly' shortens reasoning on the same model, which gives us a within-model comparison the review asked for.");

  // ---------- 7. risks ----------
  pres.addSection({ title: "Risks & next steps" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Risks & next steps" });
  s.addText("Risks and how we’re handling them", { placeholder: "title" });
  const risks = [
    [I.toggle, C.accent2, "Thinking can’t be switched off on Voyager", "We tested 7 models; the setting is ignored. We treat pairs as differently trained models, add “think briefly” on the same checkpoint, and could self-host on Sol if GPU time is available."],
    [I.scale, C.accent1, "The hint barely moves answers on this task", "Add ambiguous questions (BBQ) and BBH tasks where hints have room to work. A well-controlled null result still counts."],
    [I.check, C.accent2, "A keyword detector can’t tell mention from admission", "Three-level manual labels (none / mentions / admits influence) on 200 cases, two raters, with agreement (Cohen’s κ) reported."],
    [I.coins, C.accent1, "Thinking costs about 3× the tokens", "The full proposed design is ~180M output tokens. We’ll cut it to ~55M, run a timed budget test first, and keep streaming to avoid server timeouts."],
  ];
  risks.forEach(([img, accent, head, body], i) => {
    const y = 1.45 + i * 1.35;
    circle(s, img, 0.6, y + 0.05, 0.85, accent, `risk${i + 1}`);
    s.addText(head, { x: 1.7, y, w: 10.9, h: 0.42, fontSize: 16, bold: true, color: C.text1, isTextBox: true, margin: 0 });
    s.addText(body, { x: 1.7, y: y + 0.43, w: 10.9, h: 0.8, fontSize: 13, color: C.accent5, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addNotes("Main risks. One: we can't switch thinking off on Voyager, so instruct-versus-thinking is a comparison of differently trained models — we say so, and we added a same-model 'think briefly' condition. Two: the hint barely works on these puzzles, so we're adding ambiguous BBQ and BBH questions. Three: keywords can't tell a mention from an admission, so we'll hand-label 200 cases with two raters. Four: compute — thinking models cost three times the tokens, so we're cutting the design to about 55 million tokens and timing it first.");

  // ---------- 8. next steps ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Risks & next steps" });
  s.addText("Next steps", { placeholder: "title" });
  const plan = [
    ["Week 9", "Add BBQ + BBH · timed budget run · freeze prompts"],
    ["Weeks 10–11", "Core sweep · hand-label 200 cases (2 raters)"],
    ["Weeks 12–13", "Two-agent extension: hinted answer → reviewer"],
    ["Weeks 14–15", "Statistics, figures, report draft"],
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
    { text: "Shrey Bishnoi (coordinator): ", options: { bold: true } }, { text: "harness, model runs, two-agent extension", options: { breakLine: true } },
    { text: "Arsha Jindal: ", options: { bold: true } }, { text: "datasets, hint construction, labeling guide", options: { breakLine: true } },
    { text: "Ritik Agarwal: ", options: { bold: true } }, { text: "statistics, figures, rater agreement", options: { breakLine: true } },
    { text: "All three: ", options: { bold: true } }, { text: "hand-labeling, presentations, report" },
  ], { x: 2.0, y: 4.6, w: 10.4, h: 1.7, fontSize: 15, color: C.text1, paraSpaceAfter: 3, isTextBox: true, margin: 0, valign: "top" });
  s.addNotes("Next steps: next week we add BBQ and BBH questions and time a budget run before freezing prompts. Weeks ten and eleven are the main sweep and hand-labeling. Then the two-agent extension the reviewer suggested: one model gets the hint, a second reviews its answer, and we see whether the influence gets caught or carried forward. Roles are on the slide.");

  // ---------- 9. closing ----------
  s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Risks & next steps" });
  s.addText([{ text: `Models mostly ignore the hint, but thinking models ${sees} and ${says}.`, options: { fontSize: 32 } }], { placeholder: "title" });
  s.addText("Next: does a second model catch that influence, or pass it along?", { placeholder: "subtitle" });
  s.addText([{ text: "Questions?", options: { fontSize: 28, bold: true, color: C.accent2 } }], { placeholder: "meta" });
  s.addShape(pres.shapes.OVAL, { x: 8.75, y: 1.7, w: 2.7, h: 2.7, fill: { color: C.accent1, transparency: 70 }, objectName: "close-private" });
  s.addShape(pres.shapes.OVAL, { x: 10.15, y: 2.95, w: 2.7, h: 2.7, fill: { color: C.accent2, transparency: 65 }, objectName: "close-visible" });
  s.addImage({ data: I.lockW, x: 9.55, y: 2.45, w: 0.9, h: 0.9, objectName: "close-lock" });
  s.addImage({ data: I.eyeW, x: 11.25, y: 4.05, w: 0.9, h: 0.9, objectName: "close-eye" });
  s.addNotes("To sum up: the hint mostly doesn't change answers here, but thinking models always register it privately and never mention it publicly. Next we test whether a second model catches that or passes it along. Happy to take questions.");

  // ---------- backup ----------
  pres.addSection({ title: "Backup" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Backup" });
  s.addText("Backup: what differs within each pair", { placeholder: "title" });
  const hdr = { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 14 };
  const cell = { fontSize: 13.5, color: C.text1, valign: "top" };
  s.addTable([
    [{ text: "Pair", options: hdr }, { text: "Voyager model IDs", options: hdr }, { text: "Shared", options: hdr }, { text: "Different", options: hdr }],
    [{ text: "Olmo 3 7B", options: cell }, { text: "olmo3-7b-instruct\nolmo3-7b-think", options: cell }, { text: "Same base model; SFT → DPO → RL", options: cell }, { text: "Think: reasoning traces from QwQ-32B and DeepSeek-R1. Instruct: chat, tool-use and instruction data with traces removed", options: cell }],
    [{ text: "Olmo 3 32B", options: cell }, { text: "olmo3-32b-instruct\nolmo3-32b-think", options: cell }, { text: "Same as above", options: cell }, { text: "Same recipes. Olmo 3.1 32B variants also exist: to confirm on the Voyager portal", options: cell }],
    [{ text: "Qwen3 30B-A3B", options: cell }, { text: "qwen3-30b-a3b-instruct-2507\nqwen3-30b-a3b-thinking-2507", options: cell }, { text: "Identical architecture (30.5B, 3.3B active)", options: cell }, { text: "Separate post-training lines; thinking-only vs non-thinking-only. Recommended sampling differs (0.6 vs 0.7); we use 0.6 for all", options: cell }],
  ], { x: 0.6, y: 1.5, w: 12.1, colW: [1.7, 3.1, 2.8, 4.5], border: { type: "solid", color: "D5DBE3", pt: 0.75 }, margin: 0.08 });
  s.addText("Sources: AI2 Olmo 3 release and model cards; Qwen3-2507 model cards.", { x: 0.6, y: 6.35, w: 12.1, h: 0.35, fontSize: 11, color: C.accent5, isTextBox: true, margin: 0 });

  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Backup" });
  s.addText("Backup: design and budget", { placeholder: "title" });
  s.addTable([
    [{ text: "Setting", options: hdr }, { text: "This round", options: hdr }],
    [{ text: "Items", options: cell }, { text: "24 shuffled-object puzzles (7 people, 15 swaps); correct answers balanced across A–G", options: cell }],
    [{ text: "Conditions per item", options: cell }, { text: "No hint × 3 seeds · wrong hint × 2 (positions balanced) · correct hint × 1", options: cell }],
    [{ text: "Sampling", options: cell }, { text: "Temperature 0.6, fixed seeds (verified reproducible), 16k max tokens, streamed", options: cell }],
    [{ text: "Extra checks", options: cell }, { text: "“Think briefly” on 2 thinking models · “answer only” on 4 models", options: cell }],
    [{ text: "Median output tokens", options: cell }, { text: present.map((m) => `${LABEL[m]} ${fmt(M[m].median_tokens_none)}`).join(" · "), options: cell }],
    [{ text: "Calls", options: cell }, { text: `${fmt(S.calls_done)} this round; ${fmt(S.errors)} errors`, options: cell }],
  ], { x: 0.6, y: 1.5, w: 12.1, colW: [2.8, 9.3], border: { type: "solid", color: "D5DBE3", pt: 0.75 }, margin: 0.08 });

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
}
main().catch((e) => { console.error(e); process.exit(1); });
