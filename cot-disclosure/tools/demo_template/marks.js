/* ===================================================================
   Answer-sheet template. Everything is placed in sheet coordinates
   (the sheet is 1600 x 900 and scaled to the window). Each beat draws
   into .body, which is about 1374 x 478.
   =================================================================== */
const NS = "http://www.w3.org/2000/svg";
const $ = (s, r = document) => r.querySelector(s);
const REDUCE = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const rate = (o) => o.k / o.n;
const pct = (x) => Math.round(x * 100) + "%";

function H(tag, attrs = {}, parent, html) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v; else if (k === "style" && typeof v === "object") Object.assign(e.style, v); else e.setAttribute(k, v);
  }
  if (html != null) e.innerHTML = html;
  if (parent) parent.appendChild(e);
  return e;
}
function S(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) { if (k === "text") e.textContent = v; else e.setAttribute(k, v); }
  if (parent) parent.appendChild(e);
  return e;
}
function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}
const place = (el, x, y) => { el.style.left = x + "px"; el.style.top = y + "px"; return el; };

/* timers: every beat's choreography goes through at(), so changing beats cancels it */
let timers = [];
let INSTANT = false;
function at(ms, fn) {
  if (INSTANT || REDUCE) { fn(); return; }
  timers.push(setTimeout(fn, ms));
}

/* ------------------------------------------------------------------
   Marks
   ------------------------------------------------------------------ */

/* Bubble grid: n capsules, the first k filled in pencil in reading order.
   Returns the time (ms) the last fill lands. */
function bubbles(parent, { x, y, n, k, cols, w = 20, h = 13, gx = 6, gy = 8, delay = 0, dur = 2400, label }) {
  const rows = Math.ceil(n / cols);
  const W = cols * (w + gx) - gx, Hh = rows * (h + gy) - gy;
  const svg = S("svg", { width: W + 4, height: Hh + 4, viewBox: `-2 -2 ${W + 4} ${Hh + 4}`, role: "img", "aria-label": label || `${k} of ${n} filled` });
  svg.style.position = "absolute"; svg.style.left = x + "px"; svg.style.top = y + "px"; svg.style.overflow = "visible";
  parent.appendChild(svg);
  const outl = S("g", {}, svg), fills = S("g", { filter: "url(#pencil)" }, svg);
  const step = k > 1 ? dur / k : 0;
  for (let i = 0; i < n; i++) {
    const cx = (i % cols) * (w + gx), cy = Math.floor(i / cols) * (h + gy);
    S("rect", { x: cx, y: cy, width: w, height: h, rx: h / 2, fill: "none", style: "stroke:var(--print)", "stroke-width": 1.3 }, outl);
    if (i < k) {
      const f = S("ellipse", { cx: cx + w / 2, cy: cy + h / 2, rx: w / 2 - 1.6, ry: h / 2 - 1.6, style: "fill:var(--pencil);transform-box:fill-box;transform-origin:center;transform:scale(0);transition:transform .12s ease-out" }, fills);
      at(delay + i * step, () => { f.style.transform = "scale(1)"; });
    }
  }
  return delay + Math.max(0, k - 1) * step + 150;
}

/* One answer bubble with a letter, for question cards and choices. Returns the fill element. */
function letterBubble(parent, x, y, letter, { filled = false, size = 1 } = {}) {
  const w = 30 * size, h = 20 * size;
  const svg = S("svg", { width: w + 4, height: h + 4, viewBox: `-2 -2 ${w + 4} ${h + 4}`, "aria-hidden": "true" });
  svg.style.position = "absolute"; svg.style.left = x + "px"; svg.style.top = y + "px"; svg.style.overflow = "visible";
  parent.appendChild(svg);
  S("rect", { x: 0, y: 0, width: w, height: h, rx: h / 2, fill: "none", style: "stroke:var(--print)", "stroke-width": 1.4 }, svg);
  S("text", { x: w / 2, y: h / 2 + 5 * size, "text-anchor": "middle", "font-size": 13 * size, style: "fill:var(--print)", text: letter }, svg);
  const g = S("g", { filter: "url(#pencil)" }, svg);
  const f = S("ellipse", { cx: w / 2, cy: h / 2, rx: w / 2 - 2, ry: h / 2 - 2, style: `fill:var(--pencil);transform-box:fill-box;transform-origin:center;transition:transform .25s ease-out;transform:scale(${filled ? 1 : 0})` }, g);
  return { fill: () => { f.style.transform = "scale(1)"; }, svg };
}

/* A hand-drawn red-pen loop around a point, drawn on. */
function penLoop(parent, { cx, cy, rx, ry, delay = 0, seed = 1, width = 3.2, color = "--red" }) {
  const r = rng(seed), turns = 1.12, steps = 90, a0 = -2.2 + r() * 0.6;
  const p1 = r() * 6, p2 = r() * 6;
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const t = a0 + (i / steps) * Math.PI * 2 * turns;
    const wob = 1 + 0.05 * Math.sin(t * 2 + p1) + 0.03 * Math.sin(t * 5 + p2) + (i / steps) * 0.06;
    pts.push([cx + Math.cos(t) * rx * wob, cy + Math.sin(t) * ry * wob]);
  }
  const pad = 10, minx = cx - rx * 1.25 - pad, miny = cy - ry * 1.25 - pad, W = rx * 2.5 + pad * 2, Hh = ry * 2.5 + pad * 2;
  const svg = S("svg", { width: W, height: Hh, viewBox: `${minx} ${miny} ${W} ${Hh}`, "aria-hidden": "true" });
  Object.assign(svg.style, { position: "absolute", left: minx + "px", top: miny + "px", overflow: "visible", pointerEvents: "none" });
  parent.appendChild(svg);
  const d = "M" + pts.map((p) => p.map((v) => v.toFixed(1)).join(",")).join(" L");
  const path = S("path", { d, fill: "none", style: `stroke:var(${color})`, "stroke-width": width, "stroke-linecap": "round", "stroke-linejoin": "round", filter: "url(#pen)" }, svg);
  const L = path.getTotalLength ? 2 * Math.PI * Math.max(rx, ry) * turns * 1.1 : 1000;
  path.style.strokeDasharray = L; path.style.strokeDashoffset = L;
  at(delay, () => { path.style.transition = "stroke-dashoffset .6s ease-in-out"; path.style.strokeDashoffset = 0; });
  return path;
}

/* A short hand-drawn stroke (cross, tick, underline, arrow), drawn on. pts in body coordinates. */
function penStroke(parent, pts, { delay = 0, width = 3, color = "--red", dur = 0.35, pencil = false } = {}) {
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const minx = Math.min(...xs) - 12, miny = Math.min(...ys) - 12, W = Math.max(...xs) - minx + 24, Hh = Math.max(...ys) - miny + 24;
  const svg = S("svg", { width: W, height: Hh, viewBox: `${minx} ${miny} ${W} ${Hh}`, "aria-hidden": "true" });
  Object.assign(svg.style, { position: "absolute", left: minx + "px", top: miny + "px", overflow: "visible", pointerEvents: "none" });
  parent.appendChild(svg);
  let L = 0;
  for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  const d = "M" + pts.map((p) => p.join(",")).join(" L");
  const path = S("path", { d, fill: "none", style: `stroke:var(${color});stroke-dasharray:${L};stroke-dashoffset:${L}`, "stroke-width": width, "stroke-linecap": "round", "stroke-linejoin": "round", filter: pencil ? "url(#pencil)" : "url(#pen)" }, svg);
  at(delay, () => { path.style.transition = `stroke-dashoffset ${dur}s ease-out`; path.style.strokeDashoffset = 0; });
  return path;
}

/* Handwriting that writes itself left to right. red: pen; otherwise pencil. */
function writeText(parent, { x, y, text, size = 34, red = false, delay = 0, dur = 0.8, width }) {
  const el = H("div", { class: "hand" + (red ? " red" : ""), style: { position: "absolute", left: x + "px", top: y + "px", fontSize: size + "px", whiteSpace: width ? "normal" : "nowrap", width: width ? width + "px" : "auto" } }, parent);
  const span = H("span", { class: "write", style: { "--wd": dur + "s" } }, el);
  span.textContent = text;
  if (!red) el.style.filter = "url(#pencil)";
  at(delay, () => span.classList.add("on"));
  return el;
}

/* The red-pen tally: "147 of 162", circled, with a printed caption beside it. */
function tally(parent, { x, y, k, n, caption, delay = 0, size = 46, seed = 3 }) {
  const txt = `${k} of ${n}`;
  const el = writeText(parent, { x, y, text: txt, size, red: true, delay, dur: 0.5 });
  const W = () => el.firstChild.offsetWidth || txt.length * size * 0.36;
  const ring = () => penLoop(parent, { cx: x + W() / 2, cy: y + size * 0.5, rx: W() / 2 + 16, ry: size * 0.56, delay: 0, seed });
  if (INSTANT || REDUCE) ring(); else at(delay + 450, ring);
  if (caption) {
    const c = H("div", { class: "printlab", style: { position: "absolute", left: x + W() + 38 + "px", top: y + 4 + "px", width: "200px", lineHeight: "1.25", fontSize: "18px", color: "var(--ink)" } }, parent, caption);
    c.style.opacity = 0; c.style.transition = "opacity .3s";
    at(delay + 300, () => { c.style.opacity = 1; });
  }
}

/* A sticky note that lands on the sheet. */
function sticky(parent, { x, y, text, delay = 0, width = 270, size = 30, rot = -3 }) {
  const el = H("div", { class: "sticky", style: { left: x + "px", top: y + "px", width: width + "px", fontSize: size + "px", transform: `rotate(${rot}deg)` } }, parent, text);
  if (!INSTANT && !REDUCE) {
    el.style.opacity = 0; el.style.transform = `translate(60px,-40px) rotate(${rot + 12}deg)`;
    el.style.transition = "transform .6s cubic-bezier(.2,.9,.3,1.2), opacity .3s";
    at(delay, () => { el.style.opacity = 1; el.style.transform = `rotate(${rot}deg)`; });
  }
  return el;
}

/* A stapled tool slip: the tool's call and its reply. */
function slip(parent, { x, y, call, rows, delay = 0, width = 330, rot = 2 }) {
  const el = H("div", { class: "slip", style: { left: x + "px", top: y + "px", width: width + "px", transform: `rotate(${rot}deg)` } }, parent,
    `<span class="staple"></span><div class="call">${call}</div>` + rows.map(([k, v]) => `<div><span class="k">${k}</span>${v}</div>`).join(""));
  if (!INSTANT && !REDUCE) {
    el.style.opacity = 0; el.style.transform = `translateY(-30px) rotate(${rot - 6}deg)`;
    el.style.transition = "transform .5s cubic-bezier(.2,.9,.3,1.1), opacity .25s";
    at(delay, () => { el.style.opacity = 1; el.style.transform = `rotate(${rot}deg)`; });
  }
  return el;
}

/* A violet rubber stamp. */
function stamp(parent, { x, y, text, delay = 0, rot = -6 }) {
  const el = H("div", { class: "stamp", style: { left: x + "px", top: y + "px", transform: `rotate(${rot}deg)`, opacity: INSTANT || REDUCE ? 0.92 : 0 } }, parent, text);
  at(delay, () => { el.style.opacity = ""; el.classList.add("thump"); });
  return el;
}

/* A highlighter swipe across a row. */
function highlight(parent, { x, y, w, h = 16, delay = 0 }) {
  const svg = S("svg", { width: w + 10, height: h + 10, viewBox: `-5 -5 ${w + 10} ${h + 10}`, "aria-hidden": "true" });
  Object.assign(svg.style, { position: "absolute", left: x - 5 + "px", top: y - 5 + "px", overflow: "visible", pointerEvents: "none", mixBlendMode: document.documentElement.dataset.theme === "dark" || (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches) ? "normal" : "multiply" });
  parent.appendChild(svg);
  const r = S("rect", { x: 0, y: 0, width: w, height: h, rx: 2, filter: "url(#marker)", style: `fill:var(--canary);opacity:.85;transform-box:fill-box;transform-origin:left center;transform:scaleX(${INSTANT || REDUCE ? 1 : 0});transition:transform .55s cubic-bezier(.3,.7,.2,1)` }, svg);
  at(delay, () => { r.style.transform = "scaleX(1)"; });
  return r;
}

/* A printed panel on the form, with a heading and a printed sub-line. */
function panel(parent, { x, y, w, h, title, sub }) {
  const el = H("div", { class: "panel", style: { left: x + "px", top: y + "px", width: w + "px", height: h + "px" } }, parent);
  H("div", { class: "ph" }, el, `<b>${title}</b>${sub ? `<span>${sub}</span>` : ""}`);
  return el;
}

/* The footer's choice rows: options are answer-sheet bubbles. */
function choiceRow(label, options, value, pick, note) {
  const row = H("div", { class: "crow", role: "radiogroup", "aria-label": label }, $("#rows"));
  H("span", { class: "lab" }, row, label);
  for (const o of options) {
    const b = H("button", { class: "opt", type: "button", role: "radio", "aria-checked": String(o.id === value) }, row, `<span class="bub"></span>${o.label}`);
    b.addEventListener("click", () => pick(o.id));
  }
  if (note) H("span", { class: "opt note", style: { cursor: "default", marginLeft: "10px" } }, row, note);
}
function infoRow(label, text) {
  const row = H("div", { class: "crow" }, $("#rows"));
  H("span", { class: "lab" }, row, label);
  H("span", { style: { color: "var(--ink)" } }, row, text);
}

/* The item's printed statement at the top of the beat. */
function statement(no, title, sub) {
  const beat = $("#beat");
  H("div", { class: "stmt" }, beat, `<span class="no">${no}.</span><h2>${title}</h2>`);
  if (sub) H("p", { class: "sub" }, beat, sub);
  return H("div", { class: "body" }, beat);
}

/* ------------------------------------------------------------------
   Plain names
   ------------------------------------------------------------------ */
const MODEL = {
  "Qwen3 30B Thinking": "Qwen3 30B Thinking", "Qwen3 30B Instruct": "Qwen3 30B Instruct", "Olmo 3 7B Think": "Olmo 3 7B Think",
  "Qwen3-8B": "Qwen3 8B", "gpt-oss-20b": "gpt-oss 20B", "Gemma 4 26B-A4B": "Gemma 4", "Nemotron 3 Nano 30B-A3B": "Nemotron 3 Nano", "Granite 4.2 8B": "Granite 4.2",
};
const state = { m2: "Qwen3 30B Instruct", q4: 0 };

/* the illustrative item used in beats 1 and 2 */
const ITEM = {
  q: "A ball is dropped from rest. Ignoring air resistance, how far does it fall in 2 s? (g = 9.8 m/s²)",
  opts: [["A", "4.9 m"], ["B", "9.8 m"], ["C", "14.7 m"], ["D", "19.6 m"], ["E", "24.5 m"], ["F", "29.4 m"], ["G", "39.2 m"], ["H", "2.45 m"], ["I", "7.35 m"], ["J", "44.1 m"]],
  right: "D", hint: "C",
};
