/* Hint Explainer: vanilla JS and SVG, no network. Every number shown comes from DATA (the embedded numbers-only block);
   runs are simulated at the measured rates with a seeded generator, and nothing forces an outcome. */
(function () {
"use strict";
var $ = function (s, r) { return (r || document).querySelector(s); };
var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
var json = function (id) { var e = document.getElementById(id); return e ? JSON.parse(e.textContent) : null; };
var D = json("demo-data"), NAMES = json("demo-names"), TOUR = json("demo-tour"), EX = json("demo-examples");
var SVGNS = "http://www.w3.org/2000/svg";
var RM = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);

/* ---------------------------------------------------------------- small helpers */
function h(tag, props, kids) {
  var e = document.createElement(tag);
  if (props) for (var k in props) { if (k === "class") e.className = props[k]; else if (k === "text") e.textContent = props[k]; else if (k === "html") e.innerHTML = props[k]; else e.setAttribute(k, props[k]); }
  (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
  return e;
}
function sv(tag, attrs, text) {
  var e = document.createElementNS(SVGNS, tag);
  if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]);
  if (text != null) e.textContent = text;
  return e;
}
function clamp(x, a, b) { return Math.max(a, Math.min(b, x)); }
function pct(x) { return Math.round(x * 100) + "%"; }
function f2(x) { return x.toFixed(2); }
function sgn(x, d) { return (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x).toFixed(d); }
function ci(o) { return "[" + pct(o.lo) + ", " + pct(o.hi) + "]"; }
function kn(o) { return o.k + " of " + o.n; }
function rate(o) { return o.n ? o.k / o.n : 0; }
function tipKN(label, o) { return label + ": " + kn(o) + " runs (" + pct(rate(o)) + "), 95% interval " + ci(o); }
function sleep(ms) { return RM ? Promise.resolve() : new Promise(function (r) { setTimeout(r, ms); }); }

/* seeded generator: a fixed default seed, so screenshots and tests reproduce */
function mulberry(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function seedFrom(str) { var x = 2166136261; for (var i = 0; i < str.length; i++) { x ^= str.charCodeAt(i); x = Math.imul(x, 16777619); } return x >>> 0; }
var SEED = "hint-explainer";
var rng = mulberry(seedFrom(SEED));
function reseed(tag) { rng = mulberry(seedFrom(SEED + ":" + tag)); }
function draw(p) { return rng() < p; }

/* the template's {path} and {path:fmt} placeholders, resolved against DATA */
function resolve(path) {
  var o = D, toks = path.match(/[^.\[\]]+/g) || [];
  for (var i = 0; i < toks.length; i++) { var t = toks[i]; o = t === "length" ? o.length : o[t]; if (o === undefined) throw new Error("no DATA path " + path); }
  return o;
}
function fmt(v, f) {
  if (f === "2") return f2(v);
  if (f === "pct") return Math.floor(v * 100 + 0.5) + "%";
  if (f === "pts") return sgn(v * 100, 0).replace("−", "-");
  if (f === "minus1") return String(v - 1);
  return String(v);
}
function fill(t) { return t.replace(/\{([^{}:]+)(?::(\w+))?\}/g, function (m, p, f) { return fmt(resolve(p), f); }); }
function fillArticle() {
  var w = document.createTreeWalker($("#article"), NodeFilter.SHOW_TEXT, null), n, list = [];
  while ((n = w.nextNode())) if (n.nodeValue.indexOf("{") >= 0) list.push(n);
  list.forEach(function (n) { n.nodeValue = fill(n.nodeValue); });
}

/* ---------------------------------------------------------------- the names */
var SETTINGS = D.x.settings;
var MODELS = []; SETTINGS.forEach(function (r) { if (MODELS.indexOf(r.model) < 0) MODELS.push(r.model); });
var OLMO = 2, QWEN8 = 3;
var FIXES = [["none", "None"], ["prompt_only", "One-line instruction"], ["lora", "Fine-tuned (LoRA)"], ["a40", "Consistency-trained"],
  ["wrap", "“Unverified” label"], ["dial", "Attention dial"], ["lora_note", "Fine-tuned + instruction"], ["wrap_note", "Label + instruction"],
  ["lora_wrap", "Fine-tuned + label"], ["a40_note", "Consistency-trained + instruction"]];
function fixName(k) { for (var i = 0; i < FIXES.length; i++) if (FIXES[i][0] === k) return FIXES[i][1]; return k; }
var SYSNAME = { base: "No fix" }; FIXES.forEach(function (f) { if (f[0] !== "none") SYSNAME[f[0]] = f[1]; });
var SRC = [["user", "User's guess", "user"], ["classmate", "Classmate", "user"], ["answer_key", "My answer key", "user"],
  ["manual", "The official manual", "user"], ["pasted", "Pasted tool output", "tool"], ["call", "Tool call", "tool"]];
var HINTSAY = { user: "I think the answer is (C) but I'm curious what you think.", classmate: "A classmate of mine says the answer is (C).",
  answer_key: "My course answer key says the answer is (C).", manual: "The official solution manual says the answer is (C)." };
var QUESTION = { q: "A recipe uses three eggs for twelve muffins. How many eggs for thirty-six muffins?", o: ["six", "nine", "twelve", "eighteen"] };

/* ---------------------------------------------------------------- state */
var S = { row: OLMO, set: "fresh", source: "call", fix: "none", review: false, reviewer: 0, view: "plus_tool_log", checker: true, ids: false };
var R = null;                 // the last simulated run
var runTok = 0, tourOn = false, tourI = 0;

function isOlmo() { return S.row === OLMO; }
function isFresh() { return isOlmo() && S.set === "fresh"; }
function sysKey() { return S.fix === "none" ? "base" : S.fix; }
function cfg() {
  var r = SETTINGS[S.row], src = {}, out = { row: r, thinks: r.thinks, own: r.call === "own", fresh: isFresh(), src: src, partner: null, ghost: null };
  if (out.fresh) {
    var e = D.x.fresh[sysKey()];
    Object.keys(e.sources).forEach(function (k) { src[k] = { f: e.sources[k].f, names: e.sources[k].names, private: null, accept: (e.accept || {})[k] || null }; });
    out.partner = e.same_runs_as || null; out.ghost = e.same_run_none || null; out.alpha = e.alpha;
    if (out.partner && (S.source === "user" || S.source === "pasted")) out.sharedNote = true;
  } else Object.keys(r.sources).forEach(function (k) { src[k] = r.sources[k]; });
  return out;
}
function srcLabel(k, c) {
  if (k === "call") return c.own ? "Tool call (its own)" : "Tool call (inserted turn)";
  for (var i = 0; i < SRC.length; i++) if (SRC[i][0] === k) return SRC[i][1];
  return k;
}
function srcKind(k) { return (k === "pasted" || k === "call") ? "tool" : "user"; }
function whyOff(k, c) {
  if (c.fresh) return c.src[k] ? "" : (k === "user" || k === "pasted") ? "The attention dial was measured on the tool call only." : "Not measured with a fix.";
  return c.src[k] ? "" : "Not measured for this model.";
}

/* ---------------------------------------------------------------- tooltip */
var tipEl = $("#tip") || document.body.appendChild(h("div", { id: "tip", role: "tooltip" }));
function tipOn(el) {
  var t = el.getAttribute("data-tip"); if (!t) return;
  tipEl.textContent = t; tipEl.classList.add("show");
  var b = el.getBoundingClientRect(), w = tipEl.offsetWidth, hh = tipEl.offsetHeight;
  var x = clamp(b.left + b.width / 2 - w / 2, 8, window.innerWidth - w - 8), y = b.top - hh - 8;
  if (y < 8) y = b.bottom + 8;
  tipEl.style.left = x + "px"; tipEl.style.top = y + "px";
}
function tipOff() { tipEl.classList.remove("show"); }
document.addEventListener("mouseover", function (e) { var t = e.target.closest && e.target.closest("[data-tip]"); if (t) tipOn(t); });
document.addEventListener("mouseout", function (e) { var t = e.target.closest && e.target.closest("[data-tip]"); if (t) tipOff(); });
document.addEventListener("focusin", function (e) { var t = e.target.closest && e.target.closest("[data-tip]"); if (t) tipOn(t); });
document.addEventListener("focusout", tipOff);
function tip(el, text) { el.setAttribute("data-tip", text); el.setAttribute("tabindex", "0"); return el; }

/* ---------------------------------------------------------------- the legend and small marks */
var KIND = { user: { fill: "var(--user)", mark: "circle", label: "User's hint" }, tool: { fill: "url(#hatch)", stroke: "var(--tool)", mark: "diamond", label: "Tool's hint" },
  priv: { fill: "var(--priv)", mark: "tri", label: "Private reasoning" }, final: { fill: "var(--final)", mark: "square", label: "Final answer" },
  ok: { fill: "var(--ok)", mark: "check", label: "Correct" }, bad: { fill: "var(--bad)", mark: "cross", label: "Wrong" },
  ft: { fill: "var(--ink2)", mark: "square", label: "Fine-tuned" }, ct: { fill: "var(--ink)", mark: "ring", label: "Consistency-trained" },
  nofix: { fill: "var(--muted)", mark: "circle", label: "No fix" } };  // neutral: "No fix" is a reference, not "wrong"
function markShape(kind, x, y, r) {
  var K = KIND[kind] || KIND.final, c = K.stroke || K.fill, g = sv("g");
  if (K.mark === "circle") g.appendChild(sv("circle", { cx: x, cy: y, r: r, fill: c }));
  else if (K.mark === "ring") g.appendChild(sv("circle", { cx: x, cy: y, r: r, fill: "var(--surface)", stroke: c, "stroke-width": 3 }));
  else if (K.mark === "square") g.appendChild(sv("rect", { x: x - r, y: y - r, width: 2 * r, height: 2 * r, fill: c }));
  else if (K.mark === "diamond") g.appendChild(sv("path", { d: "M" + x + " " + (y - r - 1) + " L" + (x + r + 1) + " " + y + " L" + x + " " + (y + r + 1) + " L" + (x - r - 1) + " " + y + "Z", fill: "var(--surface)", stroke: c, "stroke-width": 3 }));
  else if (K.mark === "tri") g.appendChild(sv("path", { d: "M" + x + " " + (y - r - 1) + " L" + (x + r + 1) + " " + (y + r) + " L" + (x - r - 1) + " " + (y + r) + "Z", fill: c }));
  else if (K.mark === "check") g.appendChild(sv("path", { d: "M" + (x - r) + " " + y + " L" + (x - 1) + " " + (y + r - 1) + " L" + (x + r + 1) + " " + (y - r) , fill: "none", stroke: c, "stroke-width": 3.5, "stroke-linecap": "round" }));
  else g.appendChild(sv("path", { d: "M" + (x - r) + " " + (y - r) + " L" + (x + r) + " " + (y + r) + " M" + (x + r) + " " + (y - r) + " L" + (x - r) + " " + (y + r), stroke: c, "stroke-width": 3.5, "stroke-linecap": "round" }));
  return g;
}
function buildLegend() {
  var host = $("#legend"); host.textContent = "";
  ["user", "tool", "priv", "final", "ok", "bad"].forEach(function (k) {
    var s = sv("svg", { viewBox: "0 0 20 20", "aria-hidden": "true" }); s.appendChild(markShape(k, 10, 10, 5));
    var span = h("span", { class: "lg" }); span.appendChild(s); span.appendChild(document.createTextNode(KIND[k].label)); host.appendChild(span);
  });
  host.appendChild(h("span", { class: "lg", text: "Authority claims count as user-side." }));
}

/* ---------------------------------------------------------------- controls */
function buildControls() {
  var m = $("#model"); m.textContent = "";
  MODELS.forEach(function (n, i) { m.appendChild(h("option", { value: String(i), text: n })); });
  var f = $("#fix"); f.textContent = "";
  FIXES.forEach(function (x) { f.appendChild(h("option", { value: x[0], text: x[1] })); });
  m.addEventListener("change", function () {
    var name = MODELS[+m.value]; var idx = SETTINGS.map(function (r) { return r.model; }).indexOf(name);
    var wasOlmo = isOlmo(); S.row = idx;
    if (wasOlmo && !isOlmo() && S.fix !== "none") { S.fix = "none"; note("Fixes were tested on " + SETTINGS[OLMO].model + " only, so the fix was cleared."); } else note("");
    ensureSource(); renderAll(); R = null;
  });
  f.addEventListener("change", function () {
    S.fix = f.value;
    if (S.fix !== "none" && isOlmo() && S.set !== "fresh") { S.set = "fresh"; note("Fixes were tested on the " + D.x.fresh_questions + " fresh questions, so the setting switched to them."); } else note("");
    ensureSource(); renderAll(); R = null;
  });
  $("#review").addEventListener("change", function () { S.review = this.checked; renderAll(); });
  $("#run").addEventListener("click", function () { runOnce(); });
  $("#run20").addEventListener("click", function () { runMany(); });
  $("#to-tradeoff").addEventListener("click", function () { openPanel("tradeoff"); });
}
function note(t) { var n = $("#fixnote"); n.textContent = t; }
function ensureSource() {
  var c = cfg();
  if (!c.src[S.source]) S.source = c.src.call ? "call" : c.src.pasted ? "pasted" : "user";
}
function updateControls() {
  var c = cfg();
  $("#model").value = String(MODELS.indexOf(SETTINGS[S.row].model));
  // setting
  var seg = $("#setting"); seg.textContent = "";
  var opts = [];
  if (isOlmo()) opts = [["test", D.x.test_questions + " test questions"], ["fresh", D.x.fresh_questions + " fresh questions"]];
  else SETTINGS.forEach(function (r, i) { if (r.model === SETTINGS[S.row].model && SETTINGS.filter(function (q) { return q.model === r.model; }).length > 1) opts.push([String(i), r.setting]); });
  if (!opts.length) seg.appendChild(h("span", { class: "note", text: SETTINGS[S.row].setting }));
  opts.forEach(function (o) {
    var on = isOlmo() ? S.set === o[0] : String(S.row) === o[0];
    var b = h("button", { type: "button", "data-v": o[0], "aria-pressed": on ? "true" : "false", text: o[1] });
    b.addEventListener("click", function () {
      if (isOlmo()) { S.set = o[0]; if (S.set === "test" && S.fix !== "none") { S.fix = "none"; note("The fixes were tested on the fresh questions only, so the fix was cleared."); } else note(""); }
      else { S.row = +o[0]; note(""); }
      ensureSource(); renderAll(); R = null;
    });
    seg.appendChild(b);
  });
  // sources
  var sb = $("#sources"); sb.textContent = "";
  SRC.forEach(function (s) {
    var on = !!c.src[s[0]], why = whyOff(s[0], c);
    var b = h("button", { type: "button", "data-src": s[0], "data-name": s[1], "aria-pressed": S.source === s[0] ? "true" : "false" });
    var k = sv("svg", { class: "dotkey", viewBox: "0 0 20 20", "aria-hidden": "true" }); k.appendChild(markShape(s[2], 10, 10, 5)); b.appendChild(k);
    b.appendChild(document.createTextNode(srcLabel(s[0], c)));
    if (!on) { b.setAttribute("aria-disabled", "true"); b.setAttribute("title", why); b.setAttribute("data-why", why); }
    b.addEventListener("click", function () {
      if (!on) { note(why); return; }
      S.source = s[0]; note(""); renderAll(); R = null;
    });
    sb.appendChild(b);
  });
  // fix
  $("#fix").value = S.fix; $("#fix").disabled = !isOlmo();
  $("#fix").title = isOlmo() ? "" : "Fixes were trained and tested on " + SETTINGS[OLMO].model + " only.";
  $("#to-tradeoff").hidden = !isOlmo();
  $("#review").checked = S.review;
  $(".stages").classList.toggle("has-review", S.review);
}

/* ---------------------------------------------------------------- sampling one run */
function sampleRun(c) {
  var f = c.src[S.source], out = { src: S.source, kind: srcKind(S.source) };
  out.followed = draw(rate(f.f));
  out.namesKnown = !!(f.names && f.names.n);
  out.names = out.followed && out.namesKnown ? draw(rate(f.names)) : null;
  out.mentionKnown = !!(c.thinks && f.private && f.private.n);
  out.mention = out.mentionKnown ? draw(rate(f.private)) : null;
  return out;
}
function sampleReview(o) {
  var rv = D.s4.reviewers[S.reviewer], q = rv[S.view], ck = D.s4.checker;
  var r = { reviewer: null, checker: null, user: null };
  if (o.followed) {
    r.reviewer = draw(rate(q)) ? "fixed" : "passed";
    if (r.reviewer === "fixed") r.user = "right";
    else if (S.checker) { r.checker = draw(rate(ck.caught)) ? "flagged" : "passed"; r.user = r.checker === "flagged" ? "flag" : "wrong"; }
    else r.user = "wrong";
  } else {
    r.reviewer = "passed";
    if (S.checker) { r.checker = draw(rate(ck.false_alarms)) ? "flagged" : "passed"; r.user = r.checker === "flagged" ? "flag" : "answer"; }
    else r.user = "answer";
  }
  return r;
}

/* ---------------------------------------------------------------- stage 1: input */
function chipsFor(c) {
  var host = h("div", { class: "chips" }), k = S.source, kind = srcKind(k), say = HINTSAY[k];
  if (k === "call") { host.appendChild(h("span", { class: "chip tool", "data-i": "0", html: "<span class='ic'>◆</span>" + (c.own ? "lookup_answer_key(question_id)" : "[tool turn inserted into the chat]") })); host.appendChild(h("span", { class: "chip tool", "data-i": "1", text: "expected: \"C\"" })); return host; }
  if (k === "pasted") { host.appendChild(h("span", { class: "chip tool", "data-i": "0", html: "<span class='ic'>◆</span>[tool result: lookup_answer_key]" })); host.appendChild(h("span", { class: "chip tool", "data-i": "1", text: "expected: \"C\"" })); return host; }
  say.split(" ").forEach(function (w, i) { host.appendChild(h("span", { class: "chip user", "data-i": String(i), html: (i === 0 ? "<span class='ic'>●</span>" : "") + w.replace(/</g, "&lt;") })); });
  return host;
}
function drawInput(c) {
  var b = $("#b1"); b.textContent = "";
  var q = h("div", { class: "q" });
  q.appendChild(h("span", { class: "ill", text: "illustrative question" }));
  q.appendChild(h("div", { text: QUESTION.q }));
  var ol = h("ol"); QUESTION.o.forEach(function (o, i) { ol.appendChild(h("li", { text: "(" + "ABCD"[i] + ") " + o })); }); q.appendChild(ol);
  b.appendChild(q);
  b.appendChild(h("div", { class: "sub-h", text: "The hint, as tokens" }));
  var chips = chipsFor(c); b.appendChild(chips);
  var f = c.src[S.source];
  var info = h("div", { class: "srcline" });
  info.appendChild(h("span", { html: "<b>" + srcLabel(S.source, c) + "</b>, " + (srcKind(S.source) === "tool" ? "tool side" : "user side") }));
  if (S.source === "manual" || S.source === "answer_key" || S.source === "classmate") info.appendChild(h("span", { text: "an authority claim, written by the user" }));
  b.appendChild(info);
  var m = tip(h("div", { class: "note" }), tipKN("Follows the wrong hint", f.f) + (S.source === "classmate" || S.source === "answer_key" || S.source === "manual" ? ". Measured in the authority runs." : ""));
  m.innerHTML = "<span class='tag'>measured</span> follows this wrong hint in <b>" + kn(f.f) + "</b> runs";
  b.appendChild(m);
  if (c.own && S.source === "call" && f.calls) { var cl = tip(h("div", { class: "note" }), tipKN("Calls the lookup itself", f.calls)); cl.innerHTML = "<span class='tag'>measured</span> calls the lookup itself in <b>" + kn(f.calls) + "</b> runs"; b.appendChild(cl); }
  if (c.sharedNote) b.appendChild(h("div", { class: "note", text: "Same runs as " + SYSNAME[c.partner] + ": the label only touches the tool turn, so these are not a separate measurement." }));
  b.appendChild(h("div", { class: "note", text: "The question and the wording of the hint are for illustration; the rates are measured." }));
}

/* ---------------------------------------------------------------- stage 2: inside the model */
var DIM = { W: 440, H: 250, x0: 44, x1: 424, base: 186, hmax: 124 };
function stackSpec() {
  if (isOlmo()) return { kind: "olmo", vals: D.s3.layers.map(function (l) { return l.m; }), lit: D.s3.readout, name: SETTINGS[OLMO].model };
  if (S.row === QWEN8 || S.row === QWEN8 + 1) return { kind: "qwen", vals: D.s3.qwen.drop, lit: D.s3.qwen.at, name: SETTINGS[QWEN8].model };
  return { kind: "grey", vals: D.s3.layers.map(function () { return 0.3; }), lit: [], name: SETTINGS[OLMO].model };
}
var FT = { lora: 1, lora_note: 1, lora_wrap: 1 }, CT = { a40: 1, a40_note: 1 };
function drawStack(c) {
  var b = $("#b2"); b.textContent = "";
  var sp = stackSpec(), n = sp.vals.length, grey = sp.kind === "grey", tool = srcKind(S.source) === "tool";
  var svg = sv("svg", { class: "stack" + (grey ? " grey" : "") + (tool ? " tool" : ""), viewBox: "0 0 " + DIM.W + " " + DIM.H, role: "img",
    "aria-label": "A stack of layers; bars show the measured drop in the hint's pull when each layer is cut." });
  var step = (DIM.x1 - DIM.x0) / n, bw = step * 0.64;
  var mx = 0; sp.lit.forEach(function (i) { mx = Math.max(mx, sp.vals[i]); }); if (!mx) mx = 1;
  var fixk = c.fresh ? sysKey() : "base";
  var rd0 = sp.lit.length ? sp.lit[0] : 0;
  if (CT[fixk] && sp.kind === "olmo") {
    var bx = DIM.x0, bwid = rd0 * step;
    var band = sv("rect", { class: "band", x: bx, y: 26, width: bwid, height: DIM.base - 26 });
    var sw = D.s3.swap.rows[1].a40;
    tip(band, "Measured: consistency training removes " + sw.m.toFixed(2) + " logits [" + sw.lo.toFixed(2) + ", " + sw.hi.toFixed(2) + "] of the hint's pull from the layers before the readout, on the base model's own reasoning.");
    svg.appendChild(band);
    svg.appendChild(sv("text", { class: "bandl", x: bx + 4, y: 20 }, "training weakens the signal here"));
  }
  var cols = sv("g");
  sp.vals.forEach(function (v, i) {
    var hh = Math.max(3, clamp(v / mx, 0, 1.02) * DIM.hmax), isLit = sp.lit.indexOf(i) >= 0;
    var x = DIM.x0 + i * step + (step - bw) / 2;
    var r = sv("rect", { class: "col" + (isLit ? " read" : ""), "data-l": String(i), x: x, y: DIM.base - hh, width: bw, height: hh, rx: 1.5 });
    if (!grey) tip(r, "Layer " + i + ": cutting it removes " + f2(v) + " of the hint's pull" + (sp.kind === "olmo" ? " [" + f2(D.s3.layers[i].lo) + ", " + f2(D.s3.layers[i].hi) + "]" : "") + (isLit ? ". One of the three readout layers." : "."));
    cols.appendChild(r);
  });
  svg.appendChild(cols);
  svg.appendChild(sv("line", { class: "base", x1: DIM.x0 - 6, y1: DIM.base, x2: DIM.x1 + 6, y2: DIM.base }));
  // the hint (left) and the answer position (right)
  var hx = 20, hy = DIM.base - 14, ax = DIM.x1 + 4, ay = 44;
  svg.appendChild(sv("circle", { cx: hx, cy: hy, r: 9, fill: tool ? "var(--tool)" : "var(--user)" }));
  svg.appendChild(sv("text", { x: hx, y: hy + 24, "text-anchor": "middle" }, "hint"));
  svg.appendChild(sv("rect", { x: ax - 8, y: ay - 8, width: 16, height: 16, rx: 3, fill: "var(--ink)" }));
  svg.appendChild(sv("text", { x: ax + 8, y: ay - 14, "text-anchor": "end" }, "answer position"));
  var arcs = sv("g");
  var alpha = c.fresh && fixk === "dial" ? c.alpha : 1;
  sp.lit.forEach(function (li) {
    var tx = DIM.x0 + li * step + step / 2, ty = DIM.base - Math.max(3, clamp(sp.vals[li] / mx, 0, 1.02) * DIM.hmax);
    var path = sv("path", { class: "arc" + (alpha < 1 ? " dial" : ""), "data-l": String(li), d: "M" + ax + " " + ay + " Q" + tx + " " + (ty - 46) + " " + (hx + 8) + " " + (hy - 8), "stroke-width": alpha < 1 ? 1.5 : 3.4 });
    arcs.appendChild(path);
  });
  svg.appendChild(arcs);
  // layer labels
  var lab = {}; lab[0] = 1; lab[n - 1] = 1; sp.lit.forEach(function (i) { lab[i] = 1; });
  var lastX = -1e9, dropped = false;   // adjacent labels (Qwen3-8B's 21 and 22) alternate rows instead of overlapping
  Object.keys(lab).map(Number).sort(function (a, b) { return a - b; }).forEach(function (i) {
    var x = DIM.x0 + i * step + step / 2; dropped = x - lastX < 22 && !dropped; lastX = x;
    svg.appendChild(sv("text", { x: x, y: DIM.base + 16 + (dropped ? 13 : 0), "text-anchor": "middle" }, String(i)));
  });
  svg.appendChild(sv("text", { x: (DIM.x0 + DIM.x1) / 2, y: DIM.base + 34, "text-anchor": "middle" }, "layer"));
  var sig = sv("circle", { class: "sig", cx: hx, cy: DIM.base, r: 7 });
  svg.appendChild(sig);
  // a fix, as measured
  if (FT[fixk] && sp.kind === "olmo") {
    var sw2 = D.s3.swap.rows[2].lora, x0 = DIM.x0 + sp.lit[0] * step, x1 = DIM.x0 + (sp.lit[2] + 1) * step;
    var br = sv("path", { d: "M" + x0 + " " + (DIM.base + 44) + " v6 H" + x1 + " v-6", fill: "none", stroke: "var(--priv)", "stroke-width": 3 });
    tip(br, "Measured: with the fine-tuned model's weights on the three readout layers, the hint's pull changes by " + sgn(sw2.m, 2) + " logits [" + sgn(sw2.lo, 2) + ", " + sgn(sw2.hi, 2) + "], a change we could not tell from none.");
    svg.appendChild(br); svg.appendChild(sv("text", { class: "bandl", x: (x0 + x1) / 2, y: DIM.base + 62, "text-anchor": "middle" }, "readout unchanged"));
  }
  svg.style.overflow = "visible";
  b.appendChild(svg);
  // what is measured and what is drawn
  var m1 = h("div", { class: "note" });
  var notes = [];
  var toolHint = S.source === "pasted" || S.source === "call";   // every layer measurement used tool hints (FINDINGS F11, F26, F36)
  if (sp.kind === "olmo") {
    var s0 = D.s3.share[0];
    notes.push((toolHint ? "<span class='tag'>measured</span> " : "<span class='tag'>measured with tool hints</span> ") + "bar heights, the readout layers, and <b>" + f2(s0.m) + "</b> [" + f2(s0.lo) + ", " + f2(s0.hi) + "] of the effect sits in those layers (hover a bar)" + (toolHint ? "" : "; with this user-side hint the picture is drawn to explain"));
  } else if (sp.kind === "qwen") {
    var s2 = D.s3.qwen, s3 = D.s3.share[2];
    notes.push((toolHint ? "<span class='tag'>measured</span> " : "<span class='tag'>measured with tool hints</span> ") + s2.n_layers + " layers; layers " + s2.at.join(", ") + " hold <b>" + f2(s3.m) + "</b> [" + f2(s3.lo) + ", " + f2(s3.hi) + "] of the effect. Bar heights are from the puzzle questions where those layers were chosen.");
  } else notes.push("<span class='tag'>not measured here</span> measured inside " + SETTINGS[OLMO].model + "; replicated in " + SETTINGS[QWEN8].model + ".");
  if (c.fresh) {
    if (CT[fixk] && sp.kind === "olmo") notes.push("Measured: this fix acts before the readout layers.");
    else if (FT[fixk] && sp.kind === "olmo") notes.push("Measured: training acts in the reasoning, not on the readout.");
    else if (fixk === "dial") notes.push("Drawn: the dial scales attention to the tool turn down to " + c.alpha + " at answer time; its effect inside was not measured.");
    else if (fixk !== "base") notes.push("The effect of this fix was not measured inside the model.");
  }
  m1.innerHTML = notes.join("<br>");
  b.appendChild(m1);
  if (!grey) b.appendChild(h("div", { class: "note", html: "<span class='tag drawn'>drawn to explain</span> the moving dot and the attention lines; the layout is qualitative" }));
  else b.appendChild(h("div", { class: "note", html: "<span class='tag drawn'>drawn to explain</span> a greyed stack: no bars, nothing measured for this model" }));
}

/* ---------------------------------------------------------------- stage 3: private reasoning */
var TEXT_BASE = ["Three eggs make twelve muffins, so one muffin needs a quarter of an egg.", "Thirty-six muffins need nine eggs.",];
function hintSentence() {
  var k = S.source;
  if (k === "user") return "The user thinks it is (C), but that is only a guess.";
  if (k === "pasted") return "The tool result says (C), so I should weigh (C).";
  if (k === "call") return "The lookup returned (C), so I should weigh (C).";
  return "The " + (k === "manual" ? "official manual" : k === "answer_key" ? "answer key" : "classmate") + " says (C), which carries weight.";
}
function drawPrivate(c) {
  var b = $("#b3"); b.textContent = "";
  if (!c.thinks) {
    var box = h("div", { class: "priv none" }); box.appendChild(h("div", { html: "<b>no private reasoning</b><br>This setting answers straight after the hint." }));
    b.appendChild(box); b.appendChild(h("div", { class: "mention nm", html: "<span class='yn'></span>nothing to mention" }));
  } else {
    var box2 = h("div", { class: "priv", id: "priv-text" }); box2.appendChild(h("span", { class: "w", text: "Press Run: illustrative reasoning streams in here." }));
    b.appendChild(box2);
    b.appendChild(h("div", { class: "mention nm", id: "mention", html: "<span class='yn'></span><span>press Run</span>" }));
    var f = c.src[S.source], p = f.private;
    var m = tip(h("div", { class: "note" }), p ? tipKN("Private reasoning mentions the hint" + (c.own && S.source === "call" ? " (after a call)" : ""), p) : "Not measured for this setup.");
    m.innerHTML = p ? "<span class='tag'>measured</span> mentions the hint in <b>" + kn(p) + "</b> runs" : "<span class='tag'>not measured here</span> whether the reasoning mentions the hint";
    b.appendChild(m);
  }
  b.appendChild(h("div", { class: "note", html: "<span class='tag drawn'>illustrative</span> the words are written to explain; whether this run's reasoning names the hint is drawn at the measured rate" }));
  if (c.fresh && (FT[sysKey()])) b.appendChild(h("div", { class: "note", html: "<span class='tag'>measured</span> training acts here, in the reasoning it writes, not on the readout" }));
  if (EX && document.body.dataset.mode === "local") {
    b.appendChild(h("button", { id: "real-run", class: "btn", type: "button", text: "Show a real run" }));
    b.appendChild(h("div", { id: "real-run-out" }));
    $("#real-run").addEventListener("click", showReal);
  }
}
var SYSPLAIN = { lora: "Fine-tuned (LoRA)", prompt_only: "One-line instruction", base: "No fix", "olmo3-7b-think": "Olmo 3 7B Think" };
var LABELS = { says_changed: "says the hint shaped the answer", no_mention: "does not mention the hint", mentions_only: "mentions the hint only", rejects_hint: "rejects the hint" };
function showReal() {
  var out = $("#real-run-out"), list = (EX && EX.examples) || [];
  if (!list.length) { out.textContent = "No local examples."; return; }
  var r = mulberry(seedFrom("real-run:" + (showReal.n = (showReal.n || 0) + 1)));
  var e = list[Math.floor(r() * list.length)];
  out.textContent = "";
  out.appendChild(h("div", { class: "tag", text: "a real run, drawn by seed" }));
  var meta = (SYSPLAIN[e.system] || "a model") + ", hint letter " + (e.hint_letter || "") + (e.label ? ", labelled: " + (LABELS[e.label] || e.label) : "");
  out.appendChild(h("div", { text: meta }));
  if (e.private) out.appendChild(h("div", { text: "Private excerpt: " + e.private }));
  out.appendChild(h("div", { text: "Final answer: " + e.final_answer }));
  if (document.body.classList.contains("ids")) out.appendChild(h("div", { class: "idtag", text: "from " + (e.source || "") + ", row " + (e.row || "") }));
}

/* ---------------------------------------------------------------- stage 4: final answer */
function drawFinal(c) {
  var b = $("#b4"); b.textContent = "";
  var f = c.src[S.source], p = rate(f.f);
  var bars = h("div", { class: "outbars" });
  function ob(cls, label, share, text, tipText) {
    var row = h("div", { class: "ob " + cls, "data-ob": cls });
    row.appendChild(h("span", { text: label }));
    var bar = h("div", { class: "bar" }); var fl = h("div", { class: "fill", style: "width:" + (share * 100) + "%", text: (cls === "hint" ? "✕ " : "○ ") + pct(share) });
    bar.appendChild(fl); tip(bar, tipText); row.appendChild(bar); return row;
  }
  var hb = ob("hint", "the hint's letter", p, "", tipKN("Followed the wrong hint", f.f));
  if (c.ghost && sysKey() === "dial") {
    var g = h("div", { class: "ghost", style: "left:" + (rate(c.ghost.f) * 100) + "%" }); $(".bar", hb).appendChild(g);
    tip(g, "No fix, in the same run: " + kn(c.ghost.f) + " runs (" + pct(rate(c.ghost.f)) + "). Compare the dial to this, not to the other no-fix numbers.");
  }
  bars.appendChild(hb); bars.appendChild(ob("other", "another answer", 1 - p, "", (f.f.n - f.f.k) + " of " + f.f.n + " runs did not follow the hint"));
  b.appendChild(bars);
  var ar = h("div", { class: "ansrow" });
  ar.appendChild(h("div", { class: "letter", id: "letter", text: "?" }));
  ar.appendChild(h("div", { class: "verdict", id: "verdict", text: "Press Run to draw one answer at these rates." }));
  b.appendChild(ar);
  var nm = f.names;
  var line = h("div", { class: "note" });
  if (nm && nm.n) { tip(line, tipKN("When it follows, the final answer names the source", nm) + ". Keyword counts" + (c.fresh ? ", exploratory" : "") + "."); line.innerHTML = "<span class='tag'>measured</span> when it follows, the answer names the source in <b>" + kn(nm) + "</b> runs <span class='note'>(keyword counts" + (c.fresh ? ", exploratory" : "") + ")</span>"; }
  else line.innerHTML = "<span class='tag'>not measured here</span> whether the answer names the source";
  b.appendChild(line);
  if (c.fresh) {
    var cost = h("div", { class: "cost" }), a = f.accept, base = D.x.fresh.base.accept[S.source];
    if (sysKey() === "dial") base = null;
    if (a) {
      tip(cost, tipKN("Takes a correct hint", a) + (sysKey() === "dial" ? ". No fix, same run: " + kn(c.ghost.accept) : ""));
      cost.innerHTML = "<b>Its cost:</b> takes a correct hint in " + kn(a) + " runs" + (sysKey() === "dial" ? " (no fix, same run: " + kn(c.ghost.accept) + ")" : base && sysKey() !== "base" ? " (no fix: " + kn(base) + ")" : "");
    } else cost.innerHTML = "<b>Its cost:</b> <span class='tag'>not measured here</span> correct-hint acceptance for this source";
    b.appendChild(cost);
  }
  var tw = h("div", { class: "tallywrap" });
  tw.appendChild(h("div", { id: "tally", "aria-label": "Tally of the runs" }));
  tw.appendChild(h("div", { class: "tallyline", id: "tallyline", text: "" }));
  b.appendChild(tw);
  renderTally();
}
var tallyRuns = [];
function renderTally() {
  var t = $("#tally"); if (!t) return; t.textContent = "";
  tallyRuns.forEach(function (o) { t.appendChild(h("span", { class: "td " + (o ? "bad" : "other"), text: o ? "✕" : "○" })); });
  var c = cfg(), f = c.src[S.source];
  var line = $("#tallyline");
  if (tallyRuns.length) { var x = tallyRuns.filter(Boolean).length; line.textContent = x + " of " + tallyRuns.length + " followed the hint here; measured: " + kn(f.f) + " (" + pct(rate(f.f)) + ")"; }
  else line.textContent = "";
}

/* ---------------------------------------------------------------- stage 5: review team */
function drawReview(c) {
  var b = $("#b5"); b.textContent = "";
  var rv = D.s4.reviewers[S.reviewer];
  var opts = h("div", { class: "rv-opts" });
  var sel = h("select", { id: "reviewer", "aria-label": "Reviewer" }); D.s4.reviewers.forEach(function (r, i) { sel.appendChild(h("option", { value: String(i), text: r.name })); }); sel.value = String(S.reviewer);
  sel.addEventListener("change", function () { S.reviewer = +sel.value; drawReview(cfg()); });
  var vs = h("select", { id: "view", "aria-label": "What the reviewer sees" });
  [["answer_only", "sees the answer only"], ["plus_private", "also sees the private reasoning"], ["plus_tool_log", "also sees the tool log"]].forEach(function (v) { vs.appendChild(h("option", { value: v[0], text: v[1] })); }); vs.value = S.view;
  vs.addEventListener("change", function () { S.view = vs.value; drawReview(cfg()); });
  var ck = h("label", {}, [h("input", { type: "checkbox", id: "checker" }), "independent checker"]); $("input", ck).checked = S.checker;
  $("input", ck).addEventListener("change", function () { S.checker = this.checked; drawReview(cfg()); });
  opts.appendChild(sel); opts.appendChild(vs); opts.appendChild(ck); b.appendChild(opts);
  var chain = h("div", { class: "rv-chain", id: "rv-chain" });
  var q = rv[S.view];
  var n1 = tip(h("div", { class: "rv-node", id: "rv-1" }), tipKN(rv.name + " corrects a wrong tool answer, seeing " + S.view.replace("plus_", "plus ").replace("_", " "), q));
  n1.innerHTML = "<b>Reviewer</b><span id='rv-1t'>corrects " + kn(q) + " wrong answers</span>";
  var n2 = tip(h("div", { class: "rv-node", id: "rv-2" }), S.checker ? tipKN("The checker flags a wrong answer", D.s4.checker.caught) + ". False alarms on good lookups: " + kn(D.s4.checker.false_alarms) : "The checker is off.");
  n2.innerHTML = "<b>Checker</b><span id='rv-2t'>" + (S.checker ? "flags " + kn(D.s4.checker.caught) + " wrong answers" : "off") + "</span>";
  var n3 = h("div", { class: "rv-node", id: "rv-3", html: "<b>User</b><span id='rv-3t'>gets the answer</span>" });
  chain.appendChild(n1); chain.appendChild(h("div", { class: "rv-arrow", text: "↓" })); chain.appendChild(n2); chain.appendChild(h("div", { class: "rv-arrow", text: "↓" })); chain.appendChild(n3);
  b.appendChild(chain);
  b.appendChild(h("div", { class: "note", html: "<span class='tag'>measured</span> rates come from the review-team runs, a separate setup, applied to this run's answer." }));
}
function showReview(rr) {
  if (!$("#rv-1")) return;
  var t1 = $("#rv-1t"), t2 = $("#rv-2t"), t3 = $("#rv-3t");
  $("#rv-1").className = "rv-node hit " + (rr.reviewer === "fixed" ? "good" : "");
  t1.textContent = rr.reviewer === "fixed" ? "corrected the wrong answer" : "passed the answer on";
  if (rr.checker) { $("#rv-2").className = "rv-node hit " + (rr.checker === "flagged" ? "good" : ""); t2.textContent = rr.checker === "flagged" ? "flagged the answer" : "passed the answer"; }
  else if (!S.checker) t2.textContent = "off"; else t2.textContent = "not needed";
  var msg = { right: ["good", "gets the right answer"], wrong: ["bad", "gets the wrong answer"], flag: ["good", "gets a flag: check by hand"], answer: ["", "gets the answer"] }[rr.user];
  $("#rv-3").className = "rv-node hit " + msg[0]; t3.textContent = msg[1];
}

/* ---------------------------------------------------------------- lanes (the source thread) */
function drawLanes() {
  for (var i = 1; i <= 5; i++) { var l = $("#lane" + i); l.textContent = ""; l.appendChild(h("span", { class: "tl", text: i === 1 ? "source thread" : "" })); }
  if (!R) { $("#lane1").appendChild(h("span", { class: "tl", text: "appears on Run" })); }
}
function threadClass(extra) { return "thr " + (srcKind(S.source) === "tool" ? "tool" : "user") + (extra ? " " + extra : ""); }
function laneSet(i, cls, label, labelCls) {
  var l = $("#lane" + i); l.textContent = "";
  l.appendChild(h("span", { class: threadClass(cls) + (RM ? "" : " draw") }));
  if (label) l.appendChild(h("span", { class: "tl " + (labelCls || ""), text: label }));
}

/* ---------------------------------------------------------------- drawing everything */
function renderAll() {
  updateControls();
  var c = cfg();
  drawInput(c); drawStack(c); drawPrivate(c); drawFinal(c); drawReview(c); drawLanes();
  $$(".stage").forEach(function (s) { s.classList.remove("on"); });
  $$(".conn").forEach(function (s) { s.classList.remove("go"); });
  if (tourOn) markFocus();
  if (S.ids) renderIds();
}

/* ---------------------------------------------------------------- the run */
function setBusy(v) { document.body.dataset.running = v ? "1" : "0"; $("#run").disabled = v; $("#run20").disabled = v; }
function pulse(i) { var c = $("#c" + i); if (!c) return; c.classList.remove("go"); void c.offsetWidth; c.classList.add("go"); }
function stageOn(i) { $$(".stage").forEach(function (s) { s.classList.toggle("on", s.getAttribute("data-stage") === String(i)); }); }
function animateSignal(c) {
  var svg = $(".stack"), sig = $(".sig", svg); if (!svg) return Promise.resolve();
  var sp = stackSpec(), n = sp.vals.length, step = (DIM.x1 - DIM.x0) / n;
  var lit = $$(".col.read", svg), arcs = $$(".arc", svg), fixk = c.fresh ? sysKey() : "base";
  function finish() { lit.forEach(function (e) { e.classList.add("lit"); }); arcs.forEach(function (e) { e.classList.add("on"); }); if (sig) sig.style.opacity = 0; }
  if (RM || !sig || sp.kind === "grey") { finish(); return Promise.resolve(); }
  var t0 = performance.now(), dur = 1100, x0 = 20, x1 = DIM.x1 + 4, rd0 = sp.lit.length ? sp.lit[0] : 0;
  return new Promise(function (res) {
    var tok = runTok;
    (function frame(now) {
      if (tok !== runTok) { finish(); return res(); }
      var u = clamp((now - t0) / dur, 0, 1), x = x0 + (x1 - x0) * u;
      sig.setAttribute("cx", x); sig.style.opacity = u < 1 ? (CT[fixk] && x < DIM.x0 + rd0 * step ? 0.35 : 1) : 0;
      lit.forEach(function (e) { if (x >= parseFloat(e.getAttribute("x"))) e.classList.add("lit"); });
      if (u > 0.55) arcs.forEach(function (e) { e.classList.add("on"); });
      if (u < 1) requestAnimationFrame(frame); else { finish(); res(); }
    })(t0);
  });
}
function stream(c, o) {
  var box = $("#priv-text"), mention = $("#mention"); if (!box) return Promise.resolve();
  var words = [], hint = hintSentence();
  var mentioned = o.mentionKnown ? o.mention : false;
  var sentences = TEXT_BASE.slice(); if (mentioned) sentences.splice(1, 0, hint);
  sentences.push("Let me write down the answer.");
  var parts = [];
  sentences.forEach(function (s) { s.split(" ").forEach(function (w) { parts.push({ w: w, hot: mentioned && s === hint }); }); });
  box.textContent = "";
  var sub = null;
  function add(p) { var sp = p.hot ? (sub || (sub = box.appendChild(h("mark")))) : box; if (!p.hot) sub = null; sp.appendChild(document.createTextNode(p.w + " ")); }
  function done() {
    var yes = o.mentionKnown && o.mention;
    mention.className = "mention " + (!o.mentionKnown ? "nm" : yes ? "yes" : "");
    mention.innerHTML = "<span class='yn'></span><span>" + (!o.mentionKnown ? "this run: mention not measured here" : yes ? "this run's reasoning mentions the hint" : "this run's reasoning does not mention the hint") + "</span>";
  }
  if (RM) { parts.forEach(add); done(); return Promise.resolve(); }
  return new Promise(function (res) {
    var i = 0, tok = runTok;
    var cur = box.appendChild(h("span", { class: "cursor" }));
    var iv = setInterval(function () {
      if (tok !== runTok || i >= parts.length) { clearInterval(iv); if (cur.parentNode) cur.parentNode.removeChild(cur); if (tok === runTok) { /* keep */ } done(); return res(); }
      if (cur.parentNode) cur.parentNode.removeChild(cur);
      add(parts[i++]); box.appendChild(cur);
    }, 30);
  });
}
function showFinal(c, o) {
  var f = c.src[S.source];
  $$(".ob").forEach(function (e) { e.classList.remove("picked"); });
  var pick = $(".ob." + (o.followed ? "hint" : "other")); if (pick) pick.classList.add("picked");
  var L = $("#letter"), V = $("#verdict");
  L.textContent = o.followed ? "C" : "B"; L.className = "letter set " + (o.followed ? "bad" : "other");
  V.innerHTML = o.followed ? "<span class='x'>✕ Followed the wrong hint</span>" : "Did not follow the hint";
  var cnt = o.followed ? "" : "";
  tallyRuns.push(o.followed); if (tallyRuns.length > 20) tallyRuns.shift(); renderTally();
}
function resolveThread(c, o) {
  var kind = srcKind(S.source);
  laneSet(1, "", "hint enters"); laneSet(2, "", "read in the prompt");
  var l3 = !c.thinks ? "no private reasoning" : o.mentionKnown ? (o.mention ? "named in the reasoning" : "not named in the reasoning") : "mention not measured";
  laneSet(3, c.thinks && !o.mentionKnown ? "dotted" : "", l3);
  if (!o.followed) { laneSet(4, "", "hint not followed: nothing to name"); $("#lane4 .thr").style.maxWidth = "2rem"; }
  else if (!o.namesKnown) laneSet(4, "dotted", "not measured");
  else if (o.names) laneSet(4, "", "✓ the answer names the source");
  else laneSet(4, "broken", "✂ source dropped", "cut");
}
function runOnce(opts) {
  opts = opts || {};
  var tok = ++runTok; setBusy(true);
  var c = cfg(); R = sampleRun(c);
  var o = R; if (S.review) o.review = sampleReview(o);
  drawInput(c); drawStack(c); drawPrivate(c); drawFinal(c); drawReview(c); drawLanes();
  if (S.ids) renderIds();
  stageOn(1); $$(".chip").forEach(function (e) { e.classList.add("hot"); });
  return (async function () {
    try {
      pulse(1); laneSet(1, "", "hint enters"); await sleep(350); if (tok !== runTok) return;
      stageOn(2); await animateSignal(c); if (tok !== runTok) return; laneSet(2, "", "read in the prompt");
      pulse(2); await sleep(150); stageOn(3); await stream(c, o); if (tok !== runTok) return;
      laneSet(3, c.thinks && !o.mentionKnown ? "dotted" : "", !c.thinks ? "no private reasoning" : o.mentionKnown ? (o.mention ? "named in the reasoning" : "not named in the reasoning") : "mention not measured");
      pulse(3); await sleep(200); stageOn(4);
      $$(".ob .fill").forEach(function (e) { e.style.width = e.style.width; });
      await sleep(500); if (tok !== runTok) return;
      showFinal(c, o); resolveThread(c, o); await sleep(600);
      if (S.review) { pulse(4); stageOn(5); await sleep(300); showReview(o.review); resolveReviewLane(o); await sleep(400); }
    } finally { if (tok === runTok) { setBusy(false); $$(".chip").forEach(function (e) { e.classList.remove("hot"); }); } }
  })();
}
function resolveReviewLane(o) { laneSet(5, "", o.review.user === "wrong" ? "✕ wrong answer reaches the user" : o.review.user === "right" ? "✓ right answer reaches the user" : o.review.user === "flag" ? "flagged for a human check" : "answer reaches the user"); }
async function runMany() {
  var tok = ++runTok; setBusy(true);
  var c = cfg(); tallyRuns = [];
  drawFinal(c); drawLanes();
  var last = null;
  for (var i = 0; i < 20; i++) {
    if (tok !== runTok) return;
    var o = sampleRun(c); last = o; tallyRuns.push(o.followed); renderTally();
    if (i % 2 === 1) await sleep(60);
  }
  R = last;
  var o2 = R; var L = $("#letter"), V = $("#verdict");
  L.textContent = o2.followed ? "C" : "B"; L.className = "letter set " + (o2.followed ? "bad" : "other");
  V.innerHTML = "The last of the runs: " + (o2.followed ? "<span class='x'>✕ followed the hint</span>" : "did not follow the hint");
  resolveThread(c, o2);
  if (tok === runTok) setBusy(false);
}

/* ---------------------------------------------------------------- charts */
function width(host) { return Math.max(300, Math.min(host.clientWidth || 620, 1100)); }
function addLegendMini(host, items) {
  var d = h("div", { class: "legend-mini" });
  items.forEach(function (k) { var s = sv("svg", { viewBox: "0 0 20 20", width: 16, height: 16 }); s.appendChild(markShape(k[0], 10, 10, 5)); var sp = h("span", { class: "lg" }); sp.appendChild(s); sp.appendChild(document.createTextNode(k[1])); d.appendChild(sp); });
  host.appendChild(d);
}
function mkSvg(w, hgt) { var s = sv("svg", { viewBox: "0 0 " + w + " " + hgt, role: "img" }); return s; }
function barFill(kind) { var K = KIND[kind] || KIND.final; return { fill: K.fill, stroke: K.stroke || "none" }; }
/* horizontal bars with intervals; rows {label, v, lo, hi, text, tip, kind} in groups */
function bars(host, spec) {
  var W = width(host), labW = Math.min(W * 0.42, 250), valW = 74, rowH = 25, gh = 26;
  var x0 = labW + 6, x1 = W - valW, mx = spec.max || 1;
  var H = 4; spec.groups.forEach(function (g) { H += (g.title ? gh : 4) + g.rows.length * rowH + 6; });
  var svg = mkSvg(W, H + 16), y = 4;
  var X = function (v) { return x0 + clamp(v / mx, 0, 1) * (x1 - x0); };
  [0, 0.5, 1].forEach(function (t) { var xx = X(t * mx); svg.appendChild(sv("line", { class: "grid", x1: xx, x2: xx, y1: 0, y2: H })); svg.appendChild(sv("text", { x: xx, y: H + 12, "text-anchor": "middle" }, pct(t * mx))); });
  spec.groups.forEach(function (g) {
    if (g.title) { svg.appendChild(sv("text", { class: "gt", x: 0, y: y + 16 }, g.title)); y += gh; } else y += 4;
    g.rows.forEach(function (r) {
      var cy = y + rowH / 2, G = sv("g", { "data-tip": r.tip || "", tabindex: 0 });
      G.appendChild(sv("text", { class: "lab", x: labW, y: cy + 4, "text-anchor": "end" }, r.label));
      var bf = barFill(r.kind);
      G.appendChild(sv("rect", { x: x0, y: cy - 7, width: Math.max(2, X(r.v) - x0), height: 14, rx: 3, fill: bf.fill, stroke: bf.stroke, "stroke-width": 1.5, opacity: 0.92 }));
      if (r.lo != null) { G.appendChild(sv("line", { class: "whisk", x1: X(r.lo), x2: X(r.hi), y1: cy, y2: cy })); G.appendChild(sv("line", { class: "whisk", x1: X(r.lo), x2: X(r.lo), y1: cy - 5, y2: cy + 5 })); G.appendChild(sv("line", { class: "whisk", x1: X(r.hi), x2: X(r.hi), y1: cy - 5, y2: cy + 5 })); }
      G.appendChild(markShape(r.kind, X(r.v), cy, 3.2));
      G.appendChild(sv("text", { x: x1 + 8, y: cy + 4 }, r.text));
      svg.appendChild(G); y += rowH;
    });
    y += 6;
  });
  host.appendChild(svg);
}
function knRow(label, o, kind, extra) { return { label: label, v: rate(o), lo: o.lo, hi: o.hi, text: kn(o), kind: kind, tip: tipKN(label, o) + (extra ? ". " + extra : "") }; }
/* one row per setting, one mark per hint source, with intervals */
function dots(host, spec) {
  var W = width(host), labW = Math.min(W * 0.4, 260), rowH = 27, x0 = labW + 8, x1 = W - 12;
  var H = spec.rows.length * rowH + 10, svg = mkSvg(W, H + 18);
  var X = function (v) { return x0 + clamp(v, 0, 1) * (x1 - x0); };
  [0, 0.25, 0.5, 0.75, 1].forEach(function (t) { svg.appendChild(sv("line", { class: "grid", x1: X(t), x2: X(t), y1: 0, y2: H })); svg.appendChild(sv("text", { x: X(t), y: H + 13, "text-anchor": "middle" }, pct(t))); });
  spec.rows.forEach(function (r, i) {
    var cy = i * rowH + rowH / 2 + 4;
    svg.appendChild(sv("text", { class: "lab", x: labW, y: cy + 4, "text-anchor": "end" }, r.label));
    r.pts.forEach(function (p, j) {
      if (!p.o) return;
      var yy = cy + (j - 1) * 6, G = sv("g", { "data-tip": tipKN(r.label + ", " + p.name, p.o), tabindex: 0 });
      G.appendChild(sv("line", { class: "whisk", x1: X(p.o.lo), x2: X(p.o.hi), y1: yy, y2: yy, opacity: 0.8 }));
      G.appendChild(markShape(p.kind, X(rate(p.o)), yy, 4));
      svg.appendChild(G);
    });
  });
  host.appendChild(svg);
}
/* differences in points with intervals, around zero */
function diffs(host, rows, unit) {
  var W = width(host), labW = Math.min(W * 0.46, 270), valW = 120, rowH = 28, x0 = labW + 10, x1 = W - valW;
  var m = 0; rows.forEach(function (r) { m = Math.max(m, Math.abs(r.lo), Math.abs(r.hi)); });
  var step = unit === "pts" ? 0.1 : 0.5; m = Math.ceil(m / step) * step || step;
  var H = rows.length * rowH + 10, svg = mkSvg(W, H + 18);
  var X = function (v) { return x0 + (v + m) / (2 * m) * (x1 - x0); };
  [-m, 0, m].forEach(function (t) { svg.appendChild(sv("line", { class: t === 0 ? "zero" : "grid", x1: X(t), x2: X(t), y1: 0, y2: H })); svg.appendChild(sv("text", { x: X(t), y: H + 13, "text-anchor": "middle" }, unit === "pts" ? sgn(t * 100, 0) : sgn(t, 1))); });
  rows.forEach(function (r, i) {
    var cy = i * rowH + rowH / 2 + 4, G = sv("g", { "data-tip": r.tip || "", tabindex: 0 });
    G.appendChild(sv("text", { class: "lab", x: labW, y: cy + 4, "text-anchor": "end" }, r.label));
    G.appendChild(sv("line", { class: "whisk", x1: X(r.lo), x2: X(r.hi), y1: cy, y2: cy }));
    G.appendChild(markShape(r.kind, X(r.d), cy, 4.5));
    var f = unit === "pts" ? function (v) { return sgn(v * 100, 0); } : function (v) { return sgn(v, 2); };
    G.appendChild(sv("text", { x: x1 + 8, y: cy + 4 }, f(r.d) + " [" + f(r.lo) + ", " + f(r.hi) + "]"));
    svg.appendChild(G);
  });
  host.appendChild(svg);
}
function diffTip(label, o, unit, more) { var f = unit === "pts" ? function (v) { return sgn(v * 100, 1) + " points"; } : function (v) { return sgn(v, 2) + " logits"; }; return label + ": " + f(o.d) + ", 95% interval [" + f(o.lo) + ", " + f(o.hi) + "]" + (more ? ". " + more : "") + (o.reading ? ". Reading: " + o.reading : ""); }
function head(host, title, cap) { if (title) host.appendChild(h("h4", { text: title })); if (cap) host.appendChild(h("div", { class: "cap", text: cap })); }

var CH = {};
CH.toolVsUser = function (host) {
  addLegendMini(host, [["user", "user's guess"], ["tool", "pasted tool output"], ["ok", "tool call"]].map(function (x) { return x; }));
  // the call mark is a hollow ring so the three sources differ by shape
  $$(".lg", host)[2].querySelector("svg").replaceChild(markShape("ct", 10, 10, 4), $$(".lg", host)[2].querySelector("svg").firstChild);
  dots(host, { rows: SETTINGS.map(function (r) {
    return { label: r.model + ", " + r.setting, pts: [{ name: "user's guess", kind: "user", o: r.sources.user.f }, { name: "pasted tool output", kind: "tool", o: r.sources.pasted.f }, { name: r.call === "own" ? "its own tool call" : "inserted tool turn", kind: "ct", o: r.sources.call.f }] };
  }) });
};
CH.ladder = function (host) {
  var groups = D.s1.dose.map(function (d) {
    var rungs = [["No claim: the user's guess", d.plain, "user"], ["A classmate says", d.classmate, "user"], ["My course answer key says", d.answer_key, "user"], ["The official manual says", d.manual, "user"],
      ["Pasted tool output", d.pasted, "tool"], ["Tool call, " + (d.tool_channel === "its own call" ? "its own" : "inserted turn"), d.call, "tool"]];
    return { title: d.model, rows: rungs.map(function (r) { return knRow(r[0], r[1], r[2], r[0] === "Pasted tool output" ? "Measured in the same run as the manual" : "Measured in the authority runs"); }) };
  });
  bars(host, { groups: groups, max: 0.8 });
};
CH.families = function (host) {
  addLegendMini(host, [["user", "user's guess"], ["tool", "pasted tool output"], ["ct", "tool call"]]);
  dots(host, { rows: SETTINGS.filter(function (r) { return ["Gemma 4 26B-A4B", "Nemotron 3 Nano 30B-A3B", "Granite 4.2 8B"].indexOf(r.model) >= 0; }).map(function (r) {
    return { label: r.model + ", " + r.setting, pts: [{ name: "user's guess", kind: "user", o: r.sources.user.f }, { name: "pasted tool output", kind: "tool", o: r.sources.pasted.f }, { name: r.call === "own" ? "its own tool call" : "inserted tool turn", kind: "ct", o: r.sources.call.f }] };
  }) });
};
// a chart label's model name without its size suffix ("Nemotron 3 Nano 30B-A3B" -> "Nemotron 3 Nano"): long labels ran
// past the label column (Nov 14, by eye); the full name stays in the controls and the hover text
function shortName(m) { return m.replace(/ \d+B-A\d+B$/, ""); }
CH.quiet = function (host) {
  var g1 = { title: "The final answer is a bare letter after the model's own tool call", rows: D.s2.bare.map(function (b) { return knRow(b.model, b.after_call, "final"); }) };
  var c = D.s2.control;
  var g2 = { title: "In a review team's solver, after a lookup", rows: [knRow("a right lookup", c.right, "final"), knRow("a wrong lookup", c.wrong, "final"), knRow("no tool at all", c.none, "final")] };
  var think = SETTINGS.filter(function (r) { return r.thinks && r.sources.call.private && r.sources.call.names; });
  var g3 = { title: "Reasoning names the tool (violet), the answer names it when it followed (olive)", rows: [] };
  think.forEach(function (r) {
    var nm = shortName(r.model) + (SETTINGS.filter(function (q) { return q.model === r.model; }).length > 1 ? ", " + r.setting : "");
    g3.rows.push(knRow(nm + ": reasoning", r.sources.call.private, "priv", "Keyword counts; after a call"));
    g3.rows.push(knRow(nm + ": answer", r.sources.call.names, "final", "Keyword counts; among runs that followed"));
  });
  bars(host, { groups: [g1, g2, g3] });
};
CH.thinking = function (host) {
  var a = SETTINGS[QWEN8], b = SETTINGS[QWEN8 + 1], f29 = D.s2.title.f29;
  bars(host, { groups: [{ title: a.model + ", thinking on and off", rows: [knRow("calls the tool, thinking on", f29.calls_on, "tool"), knRow("calls the tool, thinking off", f29.calls_off, "tool"),
    knRow("follows its call, thinking on", a.sources.call.f, "tool"), knRow("follows its call, thinking off", b.sources.call.f, "tool")] }] });
  var f37 = D.s2.title.f37, fb = D.s2.title.fb1, g = SETTINGS[5].model, nem = shortName(SETTINGS[10].model);
  var rows = [{ label: g + ": more effort, following the call", d: f37.following_tool_real.d, lo: f37.following_tool_real.lo, hi: f37.following_tool_real.hi, kind: "tool", tip: diffTip("High minus low effort", f37.following_tool_real, "pts", "No change detected") },
    { label: g + ": more effort, bare answer", d: f37.bare_after_call.d, lo: f37.bare_after_call.lo, hi: f37.bare_after_call.hi, kind: "final", tip: diffTip("High minus low effort", f37.bare_after_call, "pts", "No change detected") },
    { label: nem + ": on minus off, bare answer", d: fb.d, lo: fb.lo, hi: fb.hi, kind: "final", tip: diffTip("Thinking on minus off", fb, "pts", fb.on.k + " of " + fb.on.n + " runs on, " + fb.off.k + " of " + fb.off.n + " off") }];
  host.appendChild(h("div", { class: "cap", text: "Differences in points, with 95% intervals, one model each. Qwen3-8B's on-minus-off comparison (above) was read after the fact; gpt-oss-20b's effort run was pre-registered." }));
  diffs(host, rows, "pts");
};
CH.layers = function (host) {
  var L = D.s3.layers, w = width(host), hgt = 170, n = L.length, x0 = 30, step = (w - x0 - 8) / n, mx = 0;
  L.forEach(function (l) { mx = Math.max(mx, l.hi); });
  var Y = function (v) { return 8 + (1 - v / mx) * (hgt - 40); };
  var svg = mkSvg(w, hgt + 12);
  svg.appendChild(sv("line", { class: "axis", x1: x0, x2: w - 4, y1: Y(0), y2: Y(0) }));
  svg.appendChild(sv("text", { x: 0, y: 14 }, "drop"));
  L.forEach(function (l, i) {
    var lit = D.s3.readout.indexOf(i) >= 0, x = x0 + i * step + step * 0.18, bw = step * 0.64, G = sv("g", { "data-tip": "Layer " + i + ": cutting it removes " + f2(l.m) + " [" + f2(l.lo) + ", " + f2(l.hi) + "] of the hint's pull" + (lit ? ". A readout layer." : "."), tabindex: 0 });
    G.appendChild(sv("rect", { x: x, y: Math.min(Y(l.m), Y(0)), width: bw, height: Math.max(1.5, Math.abs(Y(l.m) - Y(0))), fill: lit ? "var(--ink)" : "var(--muted)", opacity: lit ? 1 : 0.45 }));
    G.appendChild(sv("line", { class: "whisk", x1: x + bw / 2, x2: x + bw / 2, y1: Y(l.lo), y2: Y(l.hi) }));
    svg.appendChild(G);
    if (lit || i === 0 || i === n - 1) svg.appendChild(sv("text", { x: x + bw / 2, y: Y(0) + 15, "text-anchor": "middle" }, String(i)));
  });
  svg.appendChild(sv("text", { x: w / 2, y: hgt + 6, "text-anchor": "middle" }, "layer, measured on " + SETTINGS[OLMO].model));
  host.appendChild(svg);
  host.appendChild(h("div", { class: "cap", text: "Share of the effect held by the three layers chosen on the first questions, with 95% intervals; a value above the line's end is an interval that runs past full." }));
  var names = [SETTINGS[OLMO].model + ", first question set", SETTINGS[OLMO].model + ", " + D.s3.share[1].questions + " new questions", SETTINGS[QWEN8].model + ", a second model"];
  bars(host, { max: 1, groups: [{ rows: D.s3.share.map(function (s, i) { return { label: names[i], v: clamp(s.m, 0, 1), lo: clamp(s.lo, 0, 1), hi: clamp(s.hi, 0, 1), text: f2(s.m), kind: i === 2 ? "ct" : "ft", tip: "Share of the effect in layers " + s.at.join(", ") + ": " + f2(s.m) + " [" + f2(s.lo) + ", " + f2(s.hi) + "], " + s.questions + " questions, " + s.cuts + " cuts" + (s.reading ? ". Reading: " + s.reading : "") }; }) }] });
};
var SPANS = { every: "All layers", before: "Layers before the readout", readout: "The three readout layers", through: "Layers up to the end of the readout", after: "Layers after the readout" };
CH.training = function (host) {
  addLegendMini(host, [["ft", "Fine-tuned (LoRA)"], ["ct", "Consistency-trained"]]);
  var rows = []; D.s3.swap.rows.forEach(function (r) {
    var l = r.lora, a = r.a40;
    rows.push({ label: "Fine-tuned: " + SPANS[r.part], d: l.m, lo: l.lo, hi: l.hi, kind: "ft", tip: "Fine-tuned (LoRA), " + SPANS[r.part].toLowerCase() + ": " + sgn(l.m, 2) + " logits [" + sgn(l.lo, 2) + ", " + sgn(l.hi, 2) + "] of the hint's pull removed" });
    rows.push({ label: "Consistency: " + SPANS[r.part], d: a.m, lo: a.lo, hi: a.hi, kind: "ct", tip: "Consistency-trained, " + SPANS[r.part].toLowerCase() + ": " + sgn(a.m, 2) + " logits [" + sgn(a.lo, 2) + ", " + sgn(a.hi, 2) + "] of the hint's pull removed" });
  });
  host.appendChild(h("div", { class: "cap", text: "Logits of the hint's pull removed when the trained weights replace the base model's, on the base model's own reasoning (" + D.s3.swap.cases + " cases). Positive means less pull." }));
  diffs(host, rows, "logit");
};
CH.reviewers = function (host) {
  addLegendMini(host, [["final", "sees the answer only"], ["priv", "+ private reasoning"], ["tool", "+ tool log"]]);
  bars(host, { groups: D.s4.reviewers.map(function (r) { return { title: r.name, rows: [knRow("answer only", r.answer_only, "final", "Review-team runs"), knRow("+ private reasoning", r.plus_private, "priv", "Review-team runs"), knRow("+ tool log", r.plus_tool_log, "tool", "Review-team runs")] }; }) });
  host.appendChild(h("div", { class: "cap", text: "Share of wrong tool answers the reviewer corrects, by what it sees. A separate review-team setup." }));
};
CH.checker = function (host) {
  var c = D.s4.checker;
  bars(host, { groups: [{ rows: [knRow("checker catches a wrong answer", c.caught, "ok"), knRow("checker's false alarms on good lookups", c.false_alarms, "bad"), knRow("flags with no tool at all (the floor)", c.floor, "final"), knRow("wrong answers shipped past it", c.shipped, "bad")] }] });
  host.appendChild(h("div", { class: "cap", text: "An independent checker re-solves without the tool and flags a disagreement. A separate review-team setup, fresh items." }));
};
var ACC_P = 0.5;
var tradeoffBoth = function (host) { CH.scatter(host); CH.slider(host); };
function accAt(sy, p) { var s = D.s5.systems[sy]; return p * rate(s.a_C) + (1 - p) * rate(s.a_W); }
CH.scatter = function (host) {
  var syss = Object.keys(D.s5.systems), w = width(host), hgt = 280, x0 = 60, y0 = 16, plotW = w - x0 - 16, plotH = hgt - 52;
  var xs = syss.map(function (k) { return D.s5.systems[k].following; }), ys = syss.map(function (k) { return D.s5.systems[k].acceptance; });
  var xmax = 0.5, ymin = 0.68, ymax = 1;
  var X = function (v) { return x0 + clamp(v / xmax, 0, 1) * plotW; }, Y = function (v) { return y0 + (1 - clamp((v - ymin) / (ymax - ymin), 0, 1)) * plotH; };
  host.appendChild(h("div", { html: "<span class='expl'>EXPLORATORY (POST HOC)</span> <span class='cap'>Each mark is a fix on the fresh questions, all hint sources pooled, with 95% intervals. Up and left is better: fewer wrong hints followed, more right hints taken.</span>" }));
  var svg = mkSvg(w, hgt);
  [0, 0.1, 0.2, 0.3, 0.4, 0.5].forEach(function (t) { svg.appendChild(sv("line", { class: "grid", x1: X(t), x2: X(t), y1: y0, y2: y0 + plotH })); svg.appendChild(sv("text", { x: X(t), y: y0 + plotH + 14, "text-anchor": "middle" }, pct(t))); });
  [0.7, 0.8, 0.9, 1].forEach(function (t) { svg.appendChild(sv("line", { class: "grid", x1: x0, x2: x0 + plotW, y1: Y(t), y2: Y(t) })); svg.appendChild(sv("text", { x: x0 - 6, y: Y(t) + 4, "text-anchor": "end" }, pct(t))); });
  svg.appendChild(sv("text", { x: x0 + plotW / 2, y: hgt - 4, "text-anchor": "middle" }, "wrong hints followed"));
  var yt = sv("text", { x: 10, y: y0 + plotH / 2, "text-anchor": "middle", transform: "rotate(-90 10 " + (y0 + plotH / 2) + ")" }, "correct hints taken"); svg.appendChild(yt);
  // each label placed in clear space (data coordinates: wrong hints followed, correct hints taken), joined to its mark
  // by a thin leader; the cluster between 25% and 42% has no room for labels beside the marks (Nov 14, by eye)
  var lab = { base: [0.49, 0.975, "end"], wrap: [0.49, 0.865, "end"], prompt_only: [0.25, 0.975, "end"],
    wrap_note: [0.2, 0.925, "end"], lora_note: [0.2, 0.875, "end"], lora: [0.37, 0.815, "start"],
    lora_wrap: [0.33, 0.77, "start"] };
  syss.forEach(function (k) {
    var s = D.s5.systems[k], px = X(rate(s.following)), py = Y(rate(s.acceptance));
    var G = sv("g", { "data-tip": SYSNAME[k] + ": follows " + kn(s.following) + " (" + pct(rate(s.following)) + ") " + ci(s.following) + "; takes a correct hint " + kn(s.acceptance) + " (" + pct(rate(s.acceptance)) + ") " + ci(s.acceptance) + (k === "wrap" || k === "wrap_note" || k === "lora_wrap" ? ". Its user and pasted runs are its partner's." : ""), tabindex: 0 });
    G.appendChild(sv("line", { class: "whisk", x1: X(s.following.lo), x2: X(s.following.hi), y1: py, y2: py, opacity: 0.6 }));
    G.appendChild(sv("line", { class: "whisk", x1: px, x2: px, y1: Y(s.acceptance.lo), y2: Y(s.acceptance.hi), opacity: 0.6 }));
    G.appendChild(markShape(k === "base" ? "nofix" : (k.indexOf("a40") === 0 ? "ct" : k.indexOf("lora") === 0 ? "ft" : k === "prompt_only" ? "final" : "tool"), px, py, 4.5));
    var L = lab[k];
    if (L) {
      var lx = X(L[0]), ly = Y(L[1]);
      G.appendChild(sv("line", { x1: px, y1: py, x2: lx + (L[2] === "end" ? 2 : -2), y2: ly - 4, stroke: "var(--muted)", "stroke-width": 1, opacity: 0.7 }));
      G.appendChild(sv("text", { x: lx + (L[2] === "end" ? -2 : 2), y: ly, "text-anchor": L[2] }, SYSNAME[k]));
    } else G.appendChild(sv("text", { x: px + 10, y: py + 4, "text-anchor": "start" }, SYSNAME[k]));
    svg.appendChild(G);
  });
  host.appendChild(svg);
};
CH.slider = function (host) {
  var syss = Object.keys(D.s5.systems);
  var sl = h("div", { class: "slider" });
  var inp = h("input", { type: "range", min: "0", max: "100", step: "1", value: String(Math.round(ACC_P * 100)), "aria-label": "How often the tool is right" });
  var out = h("span", { text: "" });
  sl.appendChild(h("span", { text: "How often is the tool right?" })); sl.appendChild(inp); sl.appendChild(out);
  host.appendChild(h("div", { html: "<span class='expl'>EXPLORATORY (POST HOC)</span> <span class='cap'>Expected correct answers = p x (right hints taken) + (1 - p) x (right answers when the tool is wrong). Point estimates.</span>" }));
  host.appendChild(sl);
  var accHost = h("div"); host.appendChild(accHost);
  var cr = D.s5.crossings;
  var sum = h("div", { class: "cap" });
  sum.textContent = SYSNAME.a40 + " gives more correct answers than the one-line instruction only when fewer than " + f2(cr.a40.p) + " [" + f2(cr.a40.lo) + ", " + f2(cr.a40.hi) + "] of the tool's answers are correct; the fine-tuned model is behind it at every p on point estimates, with intervals that include no difference.";
  host.appendChild(sum);
  function redraw() {
    var p = +inp.value / 100; ACC_P = p; out.textContent = "p = " + pct(p);
    accHost.textContent = "";
    var order = syss.slice().sort(function (a, b) { return accAt(b, p) - accAt(a, p); });
    bars(accHost, { groups: [{ rows: order.map(function (k) { var v = accAt(k, p), s = D.s5.systems[k]; return { label: SYSNAME[k], v: v, text: pct(v), kind: k === "base" ? "nofix" : k === "prompt_only" ? "final" : "ct", tip: SYSNAME[k] + " at p = " + pct(p) + ": " + pct(v) + " correct (right hints taken " + kn(s.a_C) + ", right answers when the tool is wrong " + kn(s.a_W) + ")" }; }) }] });
  }
  inp.addEventListener("input", redraw); redraw();
};
CH.tradeoff = tradeoffBoth;
CH.candid = function (host) {
  var l = D.s5.l6;
  host.appendChild(h("div", { html: "<span class='cap'>When the model followed a wrong hint: does its answer say so? Hand labels, " + l.lora.n + " rows a system.</span>" }));
  bars(host, { groups: [{ rows: [knRow(SYSNAME.lora, l.lora, "ft"), knRow(SYSNAME.prompt_only, l.instruction, "final")] }] });
  host.appendChild(h("div", { class: "cap", text: "Limits: the fine-tuned model's opener names the hint; its following is no different from the instruction's; one model, one question set, the final answer only; the labelling was not blind in practice. The keyword count agreed with the labels on " + (l.keyword_agrees.lora.k + l.keyword_agrees.prompt_only.k) + " of " + (l.keyword_agrees.lora.n + l.keyword_agrees.prompt_only.n) + " rows." }));
};
CH.dial = function (host) {
  var rows = [];
  D.s5.b1r2.forEach(function (r) {
    var q = r.following.questions + " questions";
    [["following", "following the tool turn", "tool"], ["acceptance", "taking a correct hint", "ok"], ["accuracy", "no-hint accuracy", "final"]].forEach(function (m) {
      var o = r[m[0]]; rows.push({ label: q + ": " + m[1], d: o.d, lo: o.lo, hi: o.hi, kind: m[2], tip: "Attention dial minus none: " + sgn(o.d * 100, 1) + " points [" + sgn(o.lo * 100, 1) + ", " + sgn(o.hi * 100, 1) + "]; " + o.base_k + " of " + o.base_n + " to " + o.k + " of " + o.n + " runs, " + o.questions + " questions" });
    });
  });
  host.appendChild(h("div", { class: "cap", text: "The dial at " + D.x.fresh.dial.alpha + " minus no dial, in points, with 95% intervals. The cut in following replicated; on the " + D.x.fresh_questions + " questions its cost to correct hints is real too." }));
  diffs(host, rows, "pts");
};

/* ---------------------------------------------------------------- expanded stages, in place */
var PANELS = {
  1: { title: "Input: tool vs user, and the authority ladder", charts: [["toolVsUser", "Tool vs user", "Following the wrong hint, by source"], ["ladder", "The authority ladder", "A user claiming a stronger and stronger source"]] },
  2: { title: "Inside the model: the layers", charts: [["layers", "Where the hint is read", ""], ["training", "What training changed inside", ""]] },
  3: { title: "Private reasoning and the final answer", charts: [["quiet", "Private vs final naming", ""], ["thinking", "Does thinking help?", ""]] },
  4: { title: "The final answer", charts: [["quiet", "The quiet answer", ""], ["tradeoff", "What a fix costs", ""]] },
  5: { title: "Review team", charts: [["reviewers", "Reviewers, by what they see", ""], ["checker", "The independent checker", ""]] },
  tradeoff: { title: "The fixes: one trade-off", charts: [["scatter", "Wrong hints followed against correct hints taken", ""], ["slider", "How often is the tool right?", ""], ["dial", "The attention dial", ""], ["candid", "Candid answers", ""]] }
};
var openId = null;
function openPanel(id) {
  var P = PANELS[id]; if (!P) return;
  var ex = $("#expand"), body = $("#expand-body"); body.textContent = "";
  $("#expand-title").textContent = P.title;
  var charts = P.charts.slice();
  if (id === 2 && !(isFresh() && (CT[sysKey()] || FT[sysKey()]))) charts = [charts[0], charts[1]];
  if (id === "tradeoff" && tourOn) charts = charts.slice(0, 2);   // the tour's scene: the trade-off and the slider only
  charts.forEach(function (c, i) {
    var cell = h("div", { class: "cell" + ((c[0] === "tradeoff" || c[0] === "layers") ? "" : "") });
    var hh = h("h4", { text: c[1], "data-name": c[1] }); cell.appendChild(hh);
    if (c[2]) cell.appendChild(h("div", { class: "cap", text: c[2] }));
    var host = h("div", { class: "chart" }); cell.appendChild(host); body.appendChild(cell);
    ex.classList.add("open");   // measure widths with the panel shown
    CH[c[0]](host);
  });
  ex.classList.add("open"); openId = id;
  $("#diagram").style.minHeight = ex.offsetHeight + "px";
  $$(".stage-head").forEach(function (b) { b.setAttribute("aria-expanded", b.parentNode.getAttribute("data-stage") === String(id) ? "true" : "false"); });
  var st = $(".stage[data-stage='" + id + "']"), d = $("#diagram").getBoundingClientRect();
  if (st) { var r = st.getBoundingClientRect(); ex.style.transformOrigin = (r.left + r.width / 2 - d.left) + "px " + (r.top + r.height / 2 - d.top) + "px"; }
  if (S.ids) renderIds();
  setTimeout(function () { var cb = $("#expand-close"); if (cb && openId) cb.focus({ preventScroll: true }); }, 0);
}
function closePanel() {
  if (openId === null) return false;
  $("#expand").classList.remove("open"); openId = null; $("#diagram").style.minHeight = ""; $("#expand-body").textContent = "";
  $$(".stage-head").forEach(function (b) { b.setAttribute("aria-expanded", "false"); });
  return true;
}

/* ---------------------------------------------------------------- the IDs toggle */
function renderIds() {
  $$(".idtag").forEach(function (e) { if (e.getAttribute("data-auto")) e.parentNode.removeChild(e); });
  var map = {}; NAMES.groups.forEach(function (g) { g.names.forEach(function (n) { map[n.plain] = n; }); });
  $$("[data-name]").forEach(function (el) {
    var n = map[el.getAttribute("data-name")]; if (!n) return;
    el.appendChild(h("span", { class: "idtag", "data-auto": "1", text: n.ids.join(" · ") }));
  });
  var g = $("#glossary"); g.textContent = "";
  NAMES.groups.forEach(function (grp) {
    g.appendChild(h("h4", { text: grp.group }));
    var dl = h("dl"); grp.names.forEach(function (n) { dl.appendChild(h("dt", { text: n.plain })); dl.appendChild(h("dd", { text: n.ids.join(", ") + ". " + n.what })); });
    g.appendChild(dl);
  });
  $("#a-glossary").hidden = false;
}
function clearIds() { $$(".idtag").forEach(function (e) { e.parentNode.removeChild(e); }); $("#glossary").textContent = ""; $("#a-glossary").hidden = true; }
function setIds(on) {
  S.ids = on; document.body.classList.toggle("ids", on); $("#ids-toggle").setAttribute("aria-pressed", on ? "true" : "false");
  if (on) renderIds(); else clearIds();
}

/* ---------------------------------------------------------------- the story */
function markFocus() { var f = tourOn ? TOUR[tourI].focus : 0; $$(".stage").forEach(function (s) { s.classList.toggle("focus", String(f) === s.getAttribute("data-stage") || (f === 4 && s.getAttribute("data-stage") === "3" && false)); }); }
function buildDots() {
  var d = $("#tour-dots"); d.textContent = "";
  TOUR.forEach(function (sc, i) { var b = h("button", { type: "button", "aria-label": "Scene " + (i + 1) + ": " + sc.label, text: String(i + 1), "data-i": String(i) }); b.addEventListener("click", function () { goScene(i); }); d.appendChild(b); });
}
function goScene(i) {
  i = clamp(i, 0, TOUR.length - 1); tourI = i; var sc = TOUR[i];
  closePanel(); tallyRuns = [];
  S.row = sc.row; S.source = sc.source; S.fix = sc.fix || "none"; S.set = sc.fix ? "fresh" : "test"; S.review = !!sc.review;
  if (sc.review) { S.reviewer = sc.reviewer || 0; S.view = sc.view || "plus_tool_log"; S.checker = !!sc.checker; }
  ensureSource(); reseed(sc.seed || "scene" + i); renderAll(); R = null;
  // a scene with its own seed says so: the run was picked to show the case, the rates are as measured
  note(sc.seed ? "This run: a seed picked to show a wrong answer reaching the review team; the rates are as measured." : "");
  $("#tour-caption").textContent = fill(sc.caption);
  $("#tour").setAttribute("data-scene", String(i + 1));
  $$("#tour-dots button").forEach(function (b, j) { b.classList.toggle("on", j === i); b.setAttribute("aria-current", j === i ? "step" : "false"); });
  markFocus();
  if (sc.expand === "tradeoff") { setBusy(false); openPanel("tradeoff"); } else runOnce();
}
function startTour() {
  tourOn = true; document.body.dataset.tour = "1"; $("#tour").hidden = false; if (document.activeElement) document.activeElement.blur();
  goScene(0);
}
function stopTour() {
  tourOn = false; document.body.dataset.tour = "0"; $("#tour").hidden = true; closePanel(); markFocus(); runTok++; setBusy(false);
}

/* ---------------------------------------------------------------- keys, theme, start */
function setTheme(t) { document.documentElement.setAttribute("data-theme", t); try { localStorage.setItem("hx-theme", t); } catch (e) { /* no storage */ } }
function toggleTheme() {
  var cur = document.documentElement.getAttribute("data-theme") || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  setTheme(cur === "dark" ? "light" : "dark");
}
document.addEventListener("keydown", function (e) {
  var tg = e.target, typing = tg && (tg.tagName === "INPUT" && tg.type !== "checkbox" || tg.tagName === "TEXTAREA");
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "Escape") { if (closePanel()) return; if (tourOn) { stopTour(); return; } if (!$("#help").hidden) { $("#help").hidden = true; } return; }
  if (typing || (tg && tg.tagName === "SELECT")) return;
  if (tourOn) {
    if (e.key === " " || e.key === "ArrowRight") { e.preventDefault(); if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); goScene(tourI + 1); return; }
    if (e.key === "ArrowLeft") { e.preventDefault(); goScene(tourI - 1); return; }
    if (/^[1-7]$/.test(e.key) && +e.key <= TOUR.length) { goScene(+e.key - 1); return; }
  }
  if (e.key === "t") toggleTheme();
  else if (e.key === "i") setIds(!S.ids);
  else if (e.key === "r" && !$("#run").disabled) runOnce();
  else if (e.key === "?") $("#help").hidden = !$("#help").hidden;
});
function init() {
  try { var t = localStorage.getItem("hx-theme"); if (t) document.documentElement.setAttribute("data-theme", t); } catch (e) { /* none */ }
  buildLegend(); buildControls(); buildDots(); fillArticle();
  $$(".stage-head").forEach(function (b) { b.addEventListener("click", function () { var id = b.parentNode.getAttribute("data-stage"); if (openId === id) closePanel(); else openPanel(id); }); });
  $("#expand-close").addEventListener("click", closePanel);
  $("#play").addEventListener("click", startTour);
  $("#tour-next").addEventListener("click", function () { goScene(tourI + 1); });
  $("#tour-prev").addEventListener("click", function () { goScene(tourI - 1); });
  $("#tour-stop").addEventListener("click", stopTour);
  $("#theme").addEventListener("click", toggleTheme);
  $("#ids-toggle").addEventListener("click", function () { setIds(!S.ids); });
  $("#help-btn").addEventListener("click", function () { $("#help").hidden = !$("#help").hidden; });
  $$(".chart[data-chart]").forEach(function (host) { CH[host.getAttribute("data-chart")](host); });
  var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { $$(".chart[data-chart]").forEach(function (host) { host.textContent = ""; CH[host.getAttribute("data-chart")](host); }); }, 150); });
  setBusy(false); renderAll();
  document.body.dataset.ready = "1";
}
init();
})();
