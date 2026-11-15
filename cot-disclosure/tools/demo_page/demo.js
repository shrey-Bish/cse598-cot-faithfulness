(function () {
  "use strict";
  // Every number drawn here is read from the page's data block (#demo-data), where each one names its summary and
  // key (tools/build_demo.py). Nothing is fetched: the page works from file://.
  var NS = "http://www.w3.org/2000/svg";
  var DATA = JSON.parse(document.getElementById("demo-data").textContent);
  var exNode = document.getElementById("demo-examples");
  var EX = exNode ? JSON.parse(exNode.textContent) : null;
  var MINUS = "−";
  var MARGIN = 0.05;                     // B1's rule: acceptance and accuracy may move by 5 points (provenance_job.MARGIN)

  // ------------------------------------------------------------------ numbers and words
  function V(o) { return o.v; }
  function C(name) { return "var(--c-" + name + ")"; }
  function sgn(x, nd) {
    var s = Math.abs(x).toFixed(nd || 0);
    if (Number(s) === 0) return (nd ? (0).toFixed(nd) : "0");
    return (x > 0 ? "+" : MINUS) + s;
  }
  function pts(o, nd) { return sgn(V(o) * 100, nd); }
  function ptsIv(o, nd) { return pts(o.d, nd) + " [" + pts(o.lo, nd) + ", " + pts(o.hi, nd) + "]"; }
  function rate(kn) { return V(kn.k) / V(kn.n); }
  function xy(kn) { return V(kn.k) + " of " + V(kn.n); }
  function pc(x) { return String(Math.round(x * 100)); }
  function wil(kn) { return pc(rate(kn)) + "% [" + pc(V(kn.lo)) + ", " + pc(V(kn.hi)) + "]"; }
  function num2(o) { return V(o).toFixed(2); }
  function ci2(o) { return sgn(V(o.m), 2) + " [" + sgn(V(o.lo), 2) + ", " + sgn(V(o.hi), 2) + "]"; }
  function first(reading) { return String(reading).split(" (")[0]; }
  function rem() { return parseFloat(getComputedStyle(document.documentElement).fontSize) || 16; }
  var ctx2d = document.createElement("canvas").getContext("2d");
  function measure(s, px, weight) {
    ctx2d.font = (weight || 400) + " " + px + "px " + getComputedStyle(document.body).fontFamily;
    return ctx2d.measureText(String(s)).width;
  }
  function clamp(x, a, b) { return Math.max(a, Math.min(b, x)); }

  // ------------------------------------------------------------------ svg
  function S(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    if (attrs) for (var k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function T(parent, x, y, s, cls, anchor, base) {
    var t = S("text", { x: x, y: y, "class": cls || "t" }, parent);
    if (anchor) t.setAttribute("text-anchor", anchor);
    t.setAttribute("dominant-baseline", base || "middle");
    t.textContent = s;
    return t;
  }
  function mkSvg(host, label) {
    host.textContent = "";
    var w = Math.max(10, host.clientWidth), h = Math.max(10, host.clientHeight);
    var svg = S("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h, role: "img", preserveAspectRatio: "xMinYMin meet" }, host);
    svg.setAttribute("aria-label", label || "");
    return { svg: svg, w: w, h: h };
  }
  var hatchN = 0;
  function hatch(svg, color) {
    var id = "h" + (++hatchN);
    var p = S("pattern", { id: id, width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" },
      S("defs", null, svg));
    S("rect", { width: 6, height: 6, style: "fill:" + color + ";opacity:0.35" }, p);
    S("rect", { width: 3, height: 6, style: "fill:" + color }, p);
    return "url(#" + id + ")";
  }
  function shape(g, kind, x, y, r, color, hollow) {
    var e;
    if (kind === "diamond") {
      var d = r * 1.32;
      e = S("path", { d: "M" + x + "," + (y - d) + "L" + (x + d) + "," + y + "L" + x + "," + (y + d) + "L" + (x - d) + "," + y + "Z" }, g);
    } else if (kind === "square") {
      var q = r * 0.98;
      e = S("rect", { x: x - q, y: y - q, width: 2 * q, height: 2 * q, rx: 1.5 }, g);
    } else {
      e = S("circle", { cx: x, cy: y, r: r }, g);
    }
    e.setAttribute("style", hollow ? "fill:var(--bg);stroke:" + color + ";stroke-width:2.6"
                                   : "fill:" + color + ";stroke:var(--bg);stroke-width:2");
    return e;
  }
  function keySvg(kind, color, hollow) {
    var svg = S("svg", { viewBox: "0 0 30 18", "aria-hidden": "true" });
    if (kind === "bar") S("rect", { x: 3, y: 3, width: 24, height: 12, rx: 2, style: "fill:" + color }, svg);
    else if (kind === "hatch") { var f = hatch(svg, color); S("rect", { x: 3, y: 3, width: 24, height: 12, rx: 2, style: "fill:" + f }, svg); }
    else if (kind === "band") S("rect", { x: 2, y: 2, width: 26, height: 14, style: "fill:var(--band);stroke:var(--muted);stroke-dasharray:3 2" }, svg);
    else { S("line", { x1: 2, y1: 9, x2: 28, y2: 9, style: "stroke:" + color + ";stroke-width:2.5" }, svg); shape(svg, kind, 15, 9, 5, color, hollow); }
    return svg;
  }

  // ------------------------------------------------------------------ the legend keys (one color per idea)
  var LEG = {
    user: ["the user's hint", "user", "circle"], pasted: ["the tool result pasted in", "tool", "circle", true],
    call: ["the model's own tool call, or the inserted tool turn", "tool", "diamond"],
    userclaim: ["the user's claim, left to right: more authority", "user", "circle"],
    aftercall: ["the final answer after a tool call", "final", "bar"], comparison: ["comparison: the hint pasted; no tool", "base", "bar"],
    private: ["the private reasoning names the tool", "private", "bar"], final: ["the final answer names the tool", "final", "bar"],
    finalinstr: ["the final answer, with B15's one instruction", "final", "hatch"],
    readout: ["layers 15, 19, 23", "tool", "bar"], otherlayer: ["the other layers", "base", "bar"],
    lora: ["LoRA's weights", "lora", "bar"], a40: ["A40's weights", "a40", "bar"],
    answeronly: ["the answer only", "final", "circle"], pluspriv: ["+ the private reasoning", "private", "circle"],
    pluslog: ["+ the tool log", "tool", "circle"], redacted: ["+ the tool log, its letter redacted (C15)", "tool", "circle", true],
    olmo: ["Olmo 3.1 32B Instruct", "ink", "circle"], qwen: ["Qwen3 30B Instruct", "base", "circle", true],
    keywordbar: ["the keyword (bars, each system's color)", "base", "bar"],
    handlabel: ["hand labels, L6", "ink", "diamond"],
    follow: ["follows the wrong hint", "damage", "circle"], accept: ["takes the correct hint", "correct", "diamond"],
    accuracy: ["no-hint accuracy", "base", "square"], limit: ["within the rule's 5-point limit", "band", "band"]
  };
  function col(name) { return name === "ink" ? "var(--ink)" : C(name); }
  function fillLegend(ul, keys) {
    ul.textContent = "";
    keys.forEach(function (k) {
      var e = LEG[k]; if (!e) return;
      var li = document.createElement("li");
      li.appendChild(keySvg(e[2], col(e[1]), e[3]));
      li.appendChild(document.createTextNode(e[0]));
      ul.appendChild(li);
    });
  }
  var SYS = {
    base: { name: "base", c: "base", shape: "circle" }, prompt_only: { name: "the instruction", c: "inst", shape: "circle" },
    lora: { name: "LoRA", c: "lora", shape: "circle" }, lora_note: { name: "LoRA + note", c: "lora", shape: "diamond" },
    a40: { name: "A40", c: "a40", shape: "circle" }, a40_note: { name: "A40 + note", c: "a40", shape: "diamond" },
    wrap: { name: "wrapper", c: "wrap", shape: "circle", hollow: true },
    wrap_note: { name: "wrapper + note", c: "wrap", shape: "diamond", hollow: true },
    lora_wrap: { name: "LoRA + wrapper", c: "wrap", shape: "square", hollow: true }
  };

  // ------------------------------------------------------------------ the tooltip, and every mark into the numbers table
  var tipEl = document.getElementById("tip");
  var TBL = [];
  function tipLines(lines) {
    tipEl.textContent = "";
    lines.forEach(function (l) {
      var row = document.createElement("div");
      if (l.c) { var k = document.createElement("span"); k.className = "tk"; k.style.background = l.c; row.appendChild(k); }
      if (l.v) { var v = document.createElement("span"); v.className = "tv"; v.textContent = l.v + " "; row.appendChild(v); }
      var t = document.createElement("span"); t.className = "tl"; t.textContent = l.l || ""; row.appendChild(t);
      tipEl.appendChild(row);
    });
  }
  function place(x, y) {
    tipEl.hidden = false;
    var r = tipEl.getBoundingClientRect(), W = window.innerWidth, H = window.innerHeight;
    var left = x + 16, top = y + 14;
    if (left + r.width > W - 8) left = x - r.width - 16;
    if (top + r.height > H - 8) top = y - r.height - 14;
    tipEl.style.left = Math.max(8, left) + "px"; tipEl.style.top = Math.max(8, top) + "px";
  }
  function bindTip(node, lines, group, mark) {
    node.setAttribute("tabindex", "0");
    node.setAttribute("role", "img");
    node.setAttribute("aria-label", lines.map(function (l) { return (l.v ? l.v + " " : "") + (l.l || ""); }).join("; "));
    TBL.push({ group: group || "", lines: lines });
    var on = function () { tipLines(lines); if (mark) mark.classList.add("mark-on"); };
    var off = function () { tipEl.hidden = true; if (mark) mark.classList.remove("mark-on"); };
    node.addEventListener("pointerenter", function (e) { on(); place(e.clientX, e.clientY); });
    node.addEventListener("pointermove", function (e) { place(e.clientX, e.clientY); });
    node.addEventListener("pointerleave", off);
    node.addEventListener("focus", function () { on(); var r = node.getBoundingClientRect(); place(r.right, r.top); });
    node.addEventListener("blur", off);
  }
  function knTip(kn, label, color, extra) {
    var l = [{ v: xy(kn), l: wil(kn) + ", 95% Wilson", c: color }, { l: label }];
    return extra ? l.concat(extra) : l;
  }

  // ------------------------------------------------------------------ chart: rows of dots with intervals
  // o: {rows: [{head} | {label, sub, marks: [{x, lo, hi, color, shape, hollow, dy, tip}], right, rightSub, refs, band}],
  //     x: {min, max, ticks, fmt, title}, zero, bands: [[x0, x1]], rightHead, group, labelW, maxUnit}
  function dotPlot(host, o) {
    var R = rem(), m = mkSvg(host, o.group), svg = m.svg, w = m.w, h = m.h;
    var fl = 0.82 * R, fs = 0.64 * R, fv = 0.72 * R;
    var rows = o.rows.filter(function (r) { return !r.head; });
    var labelW = o.labelW != null ? o.labelW : Math.min(w * 0.42, Math.max.apply(null, rows.map(function (r) {
      return Math.max(measure(r.label, fl, 550), r.sub ? measure(r.sub, fs) : 0);
    })) + R * 0.9);
    var rightW = o.rightW != null ? o.rightW : (rows.some(function (r) { return r.right; }) ? Math.max.apply(null, rows.map(function (r) {
      return r.right ? Math.max(measure(r.right, fv), r.rightSub ? measure(r.rightSub, fs) : 0) : 0;
    }).concat([o.rightHead ? measure(o.rightHead, fs) : 0])) + R * 0.9 : R * 0.6);
    var top = (o.rightHead || o.topPad) ? R * 1.1 : R * 0.25, bottom = o.x.title ? R * 2.35 : R * 1.35;
    var x0 = labelW, x1 = Math.max(x0 + 40, w - rightW);
    var sx = function (v) { return x0 + (clamp(v, o.x.min, o.x.max) - o.x.min) / (o.x.max - o.x.min) * (x1 - x0); };
    var weights = o.rows.map(function (r) { return r.head ? 0.62 : (r.weight || 1); });
    var total = weights.reduce(function (a, b) { return a + b; }, 0);
    var minU = rows.some(function (r) { return r.sub || r.rightSub; }) ? 2.05 * R : 1.45 * R;
    var unit = Math.max(minU, Math.min((h - top - bottom) / total, R * (o.maxUnit || 3.3)));
    if (top + unit * total + bottom > h + 1) host.style.minHeight = Math.ceil(top + unit * total + bottom) + "px";
    var yEnd = top + unit * total;
    (o.bands || []).forEach(function (b) { S("rect", { x: sx(b[0]), y: top, width: sx(b[1]) - sx(b[0]), height: yEnd - top, "class": "band" }, svg); });
    o.x.ticks.forEach(function (t) {
      S("line", { x1: sx(t), x2: sx(t), y1: top, y2: yEnd, "class": "gridline" }, svg);
      T(svg, sx(t), yEnd + R * 0.55, o.x.fmt ? o.x.fmt(t) : String(t), "t t-tick", "middle");
    });
    if (o.zero != null) S("line", { x1: sx(o.zero), x2: sx(o.zero), y1: top, y2: yEnd, "class": "zero" }, svg);
    if (o.x.title) T(svg, (x0 + x1) / 2, yEnd + R * 1.6, o.x.title, "t", "middle");
    if (o.rightHead) T(svg, w, top - R * 0.55, o.rightHead, "t t-sub", "end");
    var y = top;
    o.rows.forEach(function (r, i) {
      var hh = weights[i] * unit;
      if (r.head) {
        T(svg, 0, y + hh * 0.62, r.head, "t t-head", "start");
        y += hh; return;
      }
      var cy = y + hh / 2;
      if (r.band) S("rect", { x: sx(r.band[0]), y: y + hh * 0.12, width: sx(r.band[1]) - sx(r.band[0]), height: hh * 0.76, "class": "band" }, svg);
      (r.refs || []).forEach(function (x) { S("line", { x1: sx(x), x2: sx(x), y1: y + hh * 0.1, y2: y + hh * 0.9, "class": "refline" }, svg); });
      T(svg, 0, r.sub ? cy - fs * 0.62 : cy, r.label, "t t-label", "start");
      if (r.sub) T(svg, 0, cy + fl * 0.62, r.sub, "t t-sub", "start");
      if (r.right) T(svg, w, r.rightSub ? cy - fs * 0.62 : cy, r.right, "t t-val", "end");
      if (r.rightSub) T(svg, w, cy + fv * 0.62, r.rightSub, r.rightSubCls || "t t-sub", "end");
      (r.marks || []).forEach(function (mk) {
        var my = cy + (mk.dy || 0) * hh, g = S("g", null, svg);
        if (mk.lo != null) S("line", { x1: sx(mk.lo), x2: sx(mk.hi), y1: my, y2: my, style: "stroke:" + mk.color + ";stroke-width:2.4;stroke-linecap:butt" }, g);
        var sh = shape(g, mk.shape || "circle", sx(mk.x), my, Math.max(4.5, R * 0.3), mk.color, mk.hollow);
        if (mk.label) T(g, sx(mk.hi != null ? mk.hi : mk.x) + R * 0.45, my, mk.label, "t t-val t-halo", "start");
        var hit = S("circle", { cx: sx(mk.x), cy: my, r: Math.max(12, R * 0.62), "class": "hit" }, g);
        if (mk.tip) bindTip(hit, mk.tip, o.group, sh);
      });
      y += hh;
    });
    return { sx: sx, top: top, yEnd: yEnd };
  }

  // ------------------------------------------------------------------ chart: horizontal bars, grouped, 0-100%
  // o: {rows: [{label, sub, bars: [{kn, color, fill, name, tip}]}], group, foot}
  function hBars(host, o) {
    var R = rem(), m = mkSvg(host, o.group), svg = m.svg, w = m.w, h = m.h;
    var fl = 0.82 * R, fs = 0.64 * R, fv = 0.72 * R;
    var labelW = o.labelW != null ? o.labelW : Math.min(w * 0.4, Math.max.apply(null, o.rows.map(function (r) {
      return Math.max(measure(r.label, fl, 550), r.sub ? measure(r.sub, fs) : 0);
    })) + R * 0.9);
    var valW = Math.max.apply(null, o.rows.map(function (r) { return Math.max.apply(null, r.bars.map(function (b) { return measure(b.text || xy(b.kn), fv); })); })) + R * 0.7;
    var top = R * 0.2, bottom = (o.foot ? R * 1.5 : 0) + R * 1.35;
    var x0 = labelW, x1 = Math.max(x0 + 40, w - valW);
    var sx = function (v) { return x0 + clamp(v, 0, 1) * (x1 - x0); };
    var nb = o.rows.reduce(function (a, r) { return a + r.bars.length; }, 0);
    var gapG = R * 0.75, avail = h - top - bottom - gapG * (o.rows.length - 1);
    var bt = clamp(avail / nb * 0.78, 6, R * 1.2), step = Math.min(avail / nb, bt / 0.78);
    var yEnd = top + step * nb + gapG * (o.rows.length - 1);
    [0, 0.25, 0.5, 0.75, 1].forEach(function (t) {
      S("line", { x1: sx(t), x2: sx(t), y1: top, y2: yEnd, "class": t === 0 ? "axisline" : "gridline" }, svg);
      T(svg, sx(t), yEnd + R * 0.55, Math.round(t * 100) + "%", "t t-tick", "middle");
    });
    var y = top;
    o.rows.forEach(function (r) {
      var gh = step * r.bars.length, cy = y + gh / 2;
      T(svg, 0, r.sub ? cy - fs * 0.62 : cy, r.label, "t t-label", "start");
      if (r.sub) T(svg, 0, cy + fl * 0.62, r.sub, "t t-sub", "start");
      r.bars.forEach(function (b, j) {
        var by = y + j * step + (step - bt) / 2, v = rate(b.kn), g = S("g", null, svg);
        var fillv = b.fill === "hatch" ? hatch(svg, b.color) : b.color;
        var bw = Math.max(sx(v) - x0, v > 0 ? 2 : 0);
        var bar = S("path", { d: barPath(x0, by, bw, bt, 4), style: "fill:" + fillv }, g);
        if (v === 0) S("line", { x1: x0, x2: x0, y1: by, y2: by + bt, style: "stroke:" + b.color + ";stroke-width:3" }, g);
        S("line", { x1: sx(V(b.kn.lo)), x2: sx(V(b.kn.hi)), y1: by + bt / 2, y2: by + bt / 2, style: "stroke:var(--ink);stroke-width:1.4" }, g);
        T(g, Math.max(sx(V(b.kn.hi)), sx(v)) + R * 0.4, by + bt / 2, b.text || xy(b.kn), "t t-val", "start");
        var hit = S("rect", { x: x0, y: y + j * step, width: Math.max(sx(V(b.kn.hi)), sx(v)) - x0 + valW * 0.6, height: step, "class": "hit" }, g);
        bindTip(hit, b.tip || knTip(b.kn, r.label + ": " + b.name, b.color), o.group, bar);
      });
      y += gh + gapG;
    });
    if (o.foot) T(svg, 0, yEnd + R * 1.75, o.foot, "t t-ink", "start");
  }
  function barPath(x, y, w, h, r) {           // rounded at the data end (right), square at the baseline
    r = Math.min(r, w, h / 2);
    if (w <= 0) return "";
    return "M" + x + "," + y + "H" + (x + w - r) + "Q" + (x + w) + "," + y + " " + (x + w) + "," + (y + r) +
      "V" + (y + h - r) + "Q" + (x + w) + "," + (y + h) + " " + (x + w - r) + "," + (y + h) + "H" + x + "Z";
  }
  function vBarPath(x, y0, w, y1, r) {        // vertical: rounded at the data end, square at the zero line
    var up = y1 < y0, hgt = Math.abs(y1 - y0);
    r = Math.min(r, w / 2, hgt);
    if (hgt < 0.5) return "M" + x + "," + y0 + "H" + (x + w);
    if (up) return "M" + x + "," + y0 + "V" + (y1 + r) + "Q" + x + "," + y1 + " " + (x + r) + "," + y1 + "H" + (x + w - r) +
      "Q" + (x + w) + "," + y1 + " " + (x + w) + "," + (y1 + r) + "V" + y0 + "Z";
    return "M" + x + "," + y0 + "V" + (y1 - r) + "Q" + x + "," + y1 + " " + (x + r) + "," + y1 + "H" + (x + w - r) +
      "Q" + (x + w) + "," + y1 + " " + (x + w) + "," + (y1 - r) + "V" + y0 + "Z";
  }

  // ------------------------------------------------------------------ chart: vertical bars (categories x series), with whiskers
  // o: {cats: [{label, sub, tick}], series: [{name, color}], vals: [[{m, lo, hi} per series] per cat], y: {min, max, ticks,
  //     fmt, title}, colorOf(ci, si), labelOf(ci, si), group, divider}
  function vBars(host, o) {
    var R = rem(), m = mkSvg(host, o.group), svg = m.svg, w = m.w, h = m.h;
    var left = R * 3.2, right = R * 0.6, top = R * 1.0, bottom = R * (o.cats.some(function (c) { return c.sub; }) ? 2.6 : 1.8);
    var x0 = left, x1 = w - right, y0 = top, y1 = h - bottom;
    var sy = function (v) { return y1 - (clamp(v, o.y.min, o.y.max) - o.y.min) / (o.y.max - o.y.min) * (y1 - y0); };
    o.y.ticks.forEach(function (t) {
      S("line", { x1: x0, x2: x1, y1: sy(t), y2: sy(t), "class": t === 0 ? "zero" : "gridline" }, svg);
      T(svg, x0 - R * 0.35, sy(t), o.y.fmt ? o.y.fmt(t) : String(t), "t t-tick", "end");
    });
    if (o.y.title) { var tt = T(svg, 0, 0, o.y.title, "t t-sub", "middle"); tt.setAttribute("transform", "translate(" + (R * 0.55) + "," + ((y0 + y1) / 2) + ") rotate(-90)"); }
    var nc = o.cats.length, ns = o.series.length, band = (x1 - x0) / nc;
    var bw = Math.min(R * 1.25, band * 0.8 / ns), gap = 2;
    if (o.divider != null) S("line", { x1: x0 + band * o.divider, x2: x0 + band * o.divider, y1: y0 - R * 0.6, y2: y1 + R * 0.4, "class": "gridline" }, svg);
    o.cats.forEach(function (c, ci) {
      var cx = x0 + band * (ci + 0.5);
      if (c.tick !== false) T(svg, cx, y1 + R * 0.6, c.label, "t t-tick", "middle");
      if (c.sub) T(svg, cx, y1 + R * 1.45, c.sub, "t t-sub", "middle");
      o.series.forEach(function (s, si) {
        var v = o.vals[ci][si]; if (!v) return;
        var bx = cx - (ns * bw + (ns - 1) * gap) / 2 + si * (bw + gap), g = S("g", null, svg);
        var color = o.colorOf ? o.colorOf(ci, si) : s.color;
        var bar = S("path", { d: vBarPath(bx, sy(0), bw, sy(V(v.m)), 3), style: "fill:" + color }, g);
        S("line", { x1: bx + bw / 2, x2: bx + bw / 2, y1: sy(V(v.lo)), y2: sy(V(v.hi)), style: "stroke:var(--ink);stroke-width:1.3" }, g);
        var lab = o.labelOf ? o.labelOf(ci, si) : null;
        if (lab) {
          var up = V(v.m) >= 0;
          var lx = ns === 2 ? (si ? bx + bw * 0.15 : bx + bw * 0.85) : bx + bw / 2, la = ns === 2 ? (si ? "start" : "end") : "middle";
          T(g, lx, up ? sy(V(v.hi)) - R * 0.45 : sy(V(v.lo)) + R * 0.5, lab, "t t-val t-halo", la);
        }
        var hit = S("rect", { x: bx - 2, y: Math.min(sy(V(v.hi)), sy(0)) - 4, width: bw + 4, height: Math.abs(sy(V(v.lo)) - sy(V(v.hi))) + Math.abs(sy(V(v.m)) - sy(0)) + 8, "class": "hit" }, g);
        bindTip(hit, o.tipOf(ci, si), o.group, bar);
      });
    });
    return { sy: sy, x0: x0, x1: x1, band: band };
  }

  // ------------------------------------------------------------------ section 0
  function s0() {
    var ideas = [["the tool, its hint", "tool", "circle"], ["the user's hint", "user", "circle"],
      ["the private reasoning", "private", "bar"], ["the final answer", "final", "bar"],
      ["follows a wrong hint", "damage", "circle"], ["takes the correct hint, accuracy", "correct", "diamond"],
      ["comparison, base", "base", "bar"]];
    var ul = document.getElementById("key-ideas"); ul.textContent = "";
    ideas.forEach(function (k) { var li = document.createElement("li"); li.appendChild(keySvg(k[2], C(k[1]))); li.appendChild(document.createTextNode(k[0])); ul.appendChild(li); });
    var us = document.getElementById("key-systems"); us.textContent = "";
    var lab = document.createElement("li"); lab.textContent = "E2's systems:"; lab.style.color = "var(--muted)"; us.appendChild(lab);
    ["prompt_only", "lora", "lora_note", "a40", "a40_note", "wrap", "lora_wrap"].forEach(function (s) {
      var e = SYS[s], li = document.createElement("li"); li.appendChild(keySvg(e.shape, C(e.c), e.hollow)); li.appendChild(document.createTextNode(e.name)); us.appendChild(li);
    });
  }

  // ------------------------------------------------------------------ section 1: tools vs users
  function s1() {
    var d = DATA.s1;
    var heads = { voyager: "Voyager · temperature 0.6", sol: "Sol, our vLLM · Qwen3-8B 0.6 · gpt-oss-20b 1.0, §13", b20: "B20 on Sol · temperature 1.0" };
    var rows = [], last = null;
    d.gate2.forEach(function (r) {
      if (r.group !== last) { rows.push({ head: heads[r.group] }); last = r.group; }
      var name = r.model + ", " + r.setting;
      var g2 = [{ v: ptsIv(r.d_pasted), l: "pasted minus user (points), " + r.d_pasted.reading },
                { v: ptsIv(r.d_tool), l: r.channel + " minus user (points), " + r.d_tool.reading }];
      rows.push({
        label: r.model, sub: r.setting + " · " + r.finding + (r.channel === "inserted tool turn" ? " · inserted turn" : ""),
        right: pts(r.d_pasted.d) + " · " + pts(r.d_tool.d),
        marks: [
          { x: rate(r.user) * 100, lo: V(r.user.lo) * 100, hi: V(r.user.hi) * 100, color: C("user"), dy: -0.2,
            tip: knTip(r.user, name + ": the user's hint", C("user")) },
          { x: rate(r.pasted) * 100, lo: V(r.pasted.lo) * 100, hi: V(r.pasted.hi) * 100, color: C("tool"), hollow: true, dy: 0,
            tip: knTip(r.pasted, name + ": the tool result pasted in", C("tool"), [g2[0]]) },
          { x: rate(r.tool) * 100, lo: V(r.tool.lo) * 100, hi: V(r.tool.hi) * 100, color: C("tool"), shape: "diamond", dy: 0.2,
            tip: knTip(r.tool, name + ": " + r.channel, C("tool"), [g2[1]]) }]
      });
    });
    dotPlot(document.getElementById("c-gate2"), {
      rows: rows, group: "Following: the user's hint and the tool's (Gate 2)", rightHead: "tool − user (points): pasted · call",
      x: { min: 0, max: 100, ticks: [0, 25, 50, 75, 100], fmt: function (t) { return t + "%"; }, title: "follows the wrong letter (% of answered runs)" }
    });
    dose(document.getElementById("c-dose"), d.dose);
    var r2 = [], byKey = {};
    d.r2.forEach(function (r) { var k = r.model + "|" + r.setting; if (!byKey[k]) { byKey[k] = []; r2.push(byKey[k]); } byKey[k].push(r); });
    var formShort = function (f) { return f === "pasted block" ? "pasted" : f === "inserted tool turn" ? "inserted" : "own call"; };
    r2 = r2.map(function (pair) {
      var a = pair[0], b = pair[1];
      var mk = function (r, dy) {
        return { x: V(r.d) * 100, lo: V(r.lo) * 100, hi: V(r.hi) * 100, color: C("tool"), shape: r.pasted ? "circle" : "diamond", hollow: r.pasted, dy: dy,
          tip: [{ v: ptsIv(r), l: "points, " + r.reading, c: C("tool") }, { l: r.model + ", " + r.setting + ": " + r.form + " minus the user's answer-key claim" },
                { v: xy(r.tool) + " vs " + xy(r.claim), l: "following: tool vs claim" }] };
      };
      return { label: a.model.split(" ")[0] + ", " + a.setting, sub: formShort(a.form) + " ○ · " + formShort(b.form) + " ◆",
        right: formShort(a.form) + " " + pts(a.d) + ": " + a.reading, rightSub: formShort(b.form) + " " + pts(b.d) + ": " + b.reading, rightSubCls: "t t-val",
        marks: [mk(a, -0.17), mk(b, 0.17)] };
    });
    dotPlot(document.getElementById("c-r2"), {
      rows: r2, group: "B20: the tool's form minus the user's claim (FB1, R2)", zero: 0, maxUnit: 2.6,
      x: { min: -45, max: 90, ticks: [-40, -20, 0, 20, 40, 60, 80], fmt: function (t) { return sgn(t, 0); }, title: "following: tool minus the claim (points)" }
    });
  }
  function dose(host, rows) {
    var R = rem(), m = mkSvg(host, "The authority dose"), svg = m.svg, w = m.w, h = m.h;
    var group = "The authority dose (F40, B16, B24)";
    var gapF = R * 1.2, left = R * 2.4, top = R * 1.5, bottom = R * 5.0;
    var fw = (w - left - gapF * (rows.length - 1)) / rows.length;
    var sy = function (v) { return top + (1 - v) * (h - top - bottom); };
    [0, 0.25, 0.5, 0.75, 1].forEach(function (t) {
      S("line", { x1: left, x2: w, y1: sy(t), y2: sy(t), "class": t === 0 ? "axisline" : "gridline" }, svg);
      T(svg, left - R * 0.35, sy(t), Math.round(t * 100) + "%", "t t-tick", "end");
    });
    var levels = [["plain", "Track B's hint"], ["classmate", "a classmate"], ["answer_key", "my answer key"], ["manual", "official manual"]];
    var rot = function (x, s_) { var t = T(svg, 0, 0, s_, "t t-sub", "end"); t.setAttribute("transform", "translate(" + (x + 3) + "," + (h - bottom + R * 0.55) + ") rotate(-38)"); };
    rows.forEach(function (r, i) {
      var fx = left + i * (fw + gapF), xs = function (j) { return fx + fw * (j + 0.5) / 7; };
      T(svg, fx, R * 0.55, r.model, "t t-label", "start");
      var pts_ = levels.map(function (l, j) { return [xs(j), sy(rate(r[l[0]]))]; });
      S("polyline", { points: pts_.map(function (p) { return p.join(","); }).join(" "), style: "fill:none;stroke:" + C("user") + ";stroke-width:2;stroke-linejoin:round" }, svg);
      levels.forEach(function (l, j) {
        var kn = r[l[0]], g = S("g", null, svg);
        S("line", { x1: xs(j), x2: xs(j), y1: sy(V(kn.lo)), y2: sy(V(kn.hi)), style: "stroke:" + C("user") + ";stroke-width:2;opacity:0.55" }, g);
        var sh = shape(g, "circle", xs(j), sy(rate(kn)), Math.max(4.5, R * 0.28), C("user"));
        rot(xs(j), l[1]);
        var lab = l[0] === "plain" ? "Track B's hedged user hint (Oct 27–28)" : l[0] === "answer_key" ? "“My course answer key says…” (B16, Oct 31)" :
          l[0] === "classmate" ? "“A classmate of mine says…” (B24)" : "“The official solution manual says…” (B24)";
        var extra = l[0] === "manual" ? [{ v: ptsIv(r.manual_minus_classmate), l: "manual − classmate: " + r.manual_minus_classmate.reading },
                                         { v: ptsIv(r.manual_minus_key), l: "manual − answer key: " + r.manual_minus_key.reading }] : null;
        bindTip(S("circle", { cx: xs(j), cy: sy(rate(kn)), r: 13, "class": "hit" }, g), knTip(kn, r.model + ": " + lab, C("user"), extra), group, sh);
      });
      S("line", { x1: xs(4.5) - fw / 28, x2: xs(4.5) - fw / 28, y1: top, y2: h - bottom, "class": "gridline" }, svg);
      [["pasted", 5, "circle", true, "pasted", "pasted_minus_manual"], ["call", 6, "diamond", false, r.tool_channel === "its own call" ? "own call" : "inserted", "call_minus_manual"]].forEach(function (t) {
        var kn = r[t[0]], x = xs(t[1]) - fw / 14, g = S("g", null, svg);
        S("line", { x1: x, x2: x, y1: sy(V(kn.lo)), y2: sy(V(kn.hi)), style: "stroke:" + C("tool") + ";stroke-width:2;opacity:0.55" }, g);
        var sh = shape(g, t[2], x, sy(rate(kn)), Math.max(4.5, R * 0.28), C("tool"), t[3]);
        rot(x, "tool, " + t[4]);
        bindTip(S("circle", { cx: x, cy: sy(rate(kn)), r: 13, "class": "hit" }, g),
          knTip(kn, r.model + ": the tool, " + t[4] + " (B19, Nov 1)", C("tool"), [{ v: ptsIv(r[t[5]]), l: "tool − manual: " + r[t[5]].reading }]), group, sh);
      });
      T(svg, fx, h - R * 0.45, "manual − classmate " + ptsIv(r.manual_minus_classmate), "t t-val", "start");
    });
  }

  // ------------------------------------------------------------------ section 2: the bare final answer, the title question
  function s2() {
    var d = DATA.s2;
    var rows = d.bare.map(function (b) {
      return { label: b.model, sub: b.finding, bars: [
        { kn: b.after_call, color: C("final"), name: "the final answer after its own call", text: "after its call: " + xy(b.after_call) },
        { kn: b.pasted, color: C("base"), name: "the same hint pasted", text: "pasted: " + xy(b.pasted) }] };
    });
    rows.push({ label: "C4: the call forced", sub: "Qwen3 30B Thinking · F15's control", bars: [
      { kn: d.control.right, color: C("final"), name: "after a right lookup", text: "right lookup: " + xy(d.control.right) },
      { kn: d.control.wrong, color: C("final"), name: "after a wrong lookup", text: "wrong lookup: " + xy(d.control.wrong) },
      { kn: d.control.none, color: C("base"), name: "no tool", text: "no tool: " + xy(d.control.none) }] });
    hBars(document.getElementById("c-bare"), { rows: rows, group: "The bare final answer (F15, F16, F29)" });
    var n = d.names, b = n.b15;
    hBars(document.getElementById("c-names"), {
      group: "Who names the tool (F15, F25)",
      rows: [
        { label: "Qwen3 30B Thinking", sub: "after its call · F15", bars: [
          { kn: n.thinking_private, color: C("private"), name: "the private reasoning names the tool", text: "private: " + xy(n.thinking_private) },
          { kn: n.thinking_final, color: C("final"), name: "the final answer names it (followed runs)", text: "final: " + xy(n.thinking_final) }] },
        { label: "+ one instruction", sub: "B15 · F25", bars: [
          { kn: b.thinking.names.with, color: C("final"), fill: "hatch", name: "the final answer names the tool, with the instruction",
            text: "final: " + xy(b.thinking.names.with), tip: knTip(b.thinking.names.with, "Qwen3 30B Thinking, with the instruction: the final answer names the tool after a call", C("final"),
              [{ v: ptsIv(b.thinking.names), l: "with minus without (points): " + b.thinking.names.reading },
               { v: ptsIv(b.thinking.following), l: "following the wrong letter, with minus without: " + b.thinking.following.reading }]) }] },
        { label: "Qwen3 30B Instruct", sub: "no private reasoning · F16, F25", bars: [
          { kn: b.instruct.names.without, color: C("final"), name: "the final answer names the tool after a call", text: "final: " + xy(b.instruct.names.without) },
          { kn: b.instruct.names.with, color: C("final"), fill: "hatch", name: "with the instruction", text: "with it: " + xy(b.instruct.names.with),
            tip: knTip(b.instruct.names.with, "Qwen3 30B Instruct, with the instruction: the final answer names the tool after a call", C("final"),
              [{ v: ptsIv(b.instruct.names), l: "with minus without (points): " + b.instruct.names.reading },
               { v: ptsIv(b.instruct.following), l: "following the wrong letter, with minus without: " + b.instruct.following.reading }]) }] }],
      foot: "Following the tool's wrong letter, with the instruction minus without: " + ptsIv(b.thinking.following) + " and " + ptsIv(b.instruct.following) + ", " + b.thinking.following.reading + " (F25)."
    });
    var t = d.title;
    hBars(document.getElementById("c-t29"), {
      group: "The title question: Qwen3-8B, thinking on (F29)", labelW: rem() * 6.2,
      rows: [{ label: "names the tool", sub: "after a call", bars: [
        { kn: t.f29.private, color: C("private"), name: "the private reasoning names the tool, after its call", text: "private: " + xy(t.f29.private) },
        { kn: t.f29.final, color: C("final"), name: "the final answer names the tool (followed runs)", text: "final: " + xy(t.f29.final) }] }],
      foot: "Calls the tool: " + xy(t.f29.calls_on) + " (thinking off " + xy(t.f29.calls_off) + ")"
    });
    var f = t.f37;
    dotPlot(document.getElementById("c-t37"), {
      group: "The title question: gpt-oss-20b, effort high − low (F37)", zero: 0, labelW: rem() * 6.2, maxUnit: 2.4,
      rows: [
        { label: "follows", sub: "the real call", right: f.following_tool_real.reading, rightSub: ptsIv(f.following_tool_real),
          marks: [{ x: V(f.following_tool_real.d) * 100, lo: V(f.following_tool_real.lo) * 100, hi: V(f.following_tool_real.hi) * 100, color: C("damage"),
            tip: [{ v: ptsIv(f.following_tool_real), l: "high − low, points: " + f.following_tool_real.reading, c: C("damage") },
                  { v: xy(f.following_tool_real.low) + " → " + xy(f.following_tool_real.high), l: "low → high effort, following on the real call" }] }] },
        { label: "bare", sub: "after a call", right: f.bare_after_call.reading, rightSub: ptsIv(f.bare_after_call),
          marks: [{ x: V(f.bare_after_call.d) * 100, lo: V(f.bare_after_call.lo) * 100, hi: V(f.bare_after_call.hi) * 100, color: C("final"),
            tip: [{ v: ptsIv(f.bare_after_call), l: "high − low, points: " + f.bare_after_call.reading, c: C("final") },
                  { v: xy(f.bare_after_call.low) + " → " + xy(f.bare_after_call.high), l: "low → high effort, bare final answer after a call" }] }] }],
      x: { min: -20, max: 20, ticks: [-20, -10, 0, 10, 20], fmt: function (x) { return sgn(x, 0); }, title: "high − low effort (points)" }
    });
    var fb = t.fb1;
    hBars(document.getElementById("c-tfb1"), {
      group: "The title question: Nemotron 3 Nano, the inserted tool turn (FB1)", labelW: rem() * 6.2,
      rows: [{ label: "bare final", sub: "after the tool turn", bars: [
        { kn: fb.off, color: C("final"), name: "thinking off", text: "off: " + xy(fb.off) },
        { kn: fb.on, color: C("final"), name: "thinking on", text: "on: " + xy(fb.on),
          tip: knTip(fb.on, "thinking on: bare after the inserted tool turn", C("final"), [{ v: ptsIv(fb), l: "on − off (points): " + fb.reading }]) }] }],
      foot: "on − off " + ptsIv(fb) + ": " + fb.reading
    });
  }

  // ------------------------------------------------------------------ section 3: inside the model
  function s3() {
    var d = DATA.s3;
    var readout = d.readout.map(V), full = d.full.map(V);
    var lo = Math.min.apply(null, d.layers.map(function (l) { return V(l.lo); })), hi = Math.max.apply(null, d.layers.map(function (l) { return V(l.hi); }));
    var ymin = Math.floor(Math.min(lo, 0) * 10) / 10, ymax = Math.ceil(hi * 10) / 10 + 0.05;
    var ticks = []; for (var t = ymin; t <= ymax + 1e-9; t += 0.1) ticks.push(Math.round(t * 10) / 10);
    vBars(document.getElementById("c-layers"), {
      group: "Olmo 3 7B Think, Test 2: the drop by layer (F11)",
      cats: d.layers.map(function (l, i) { return { label: String(i), tick: full.indexOf(i) >= 0 }; }),
      series: [{ name: "share" }], vals: d.layers.map(function (l) { return [l]; }),
      colorOf: function (ci) { return readout.indexOf(ci) >= 0 ? C("tool") : C("base"); },
      labelOf: function (ci) { return readout.indexOf(ci) >= 0 ? ci + ": " + num2(d.layers[ci].m) : null; },
      tipOf: function (ci) { var l = d.layers[ci]; return [{ v: num2(l.m) + " [" + num2(l.lo) + ", " + num2(l.hi) + "]", l: "share of the drop, 95% bootstrap over questions", c: readout.indexOf(ci) >= 0 ? C("tool") : C("base") },
        { l: "layer " + ci + (full.indexOf(ci) >= 0 ? " (full attention)" : " (slides over 4,096 tokens)") }]; },
      y: { min: ymin, max: ymax, ticks: ticks, fmt: function (x) { return x.toFixed(1); }, title: "share of the drop" }
    });
    var share = d.share.map(function (s) {
      return { label: s.what, sub: "layers " + s.at.map(V).join(", ") + " · " + V(s.questions) + " questions · " + s.finding,
        right: num2(s.m) + " [" + num2(s.lo) + ", " + num2(s.hi) + "]", rightSub: s.reading ? "the rule (lower bound above " + V(s.threshold) + "): " + s.reading : "",
        refs: s.threshold ? [V(s.threshold)] : [],
        marks: [{ x: V(s.m), lo: V(s.lo), hi: V(s.hi), color: C("tool"),
          tip: [{ v: num2(s.m) + " [" + num2(s.lo) + ", " + num2(s.hi) + "]", l: "share of the drop at layers " + s.at.map(V).join(", "), c: C("tool") },
                { l: s.what + ": " + V(s.questions) + " questions, " + V(s.cuts) + " cuts; 95% bootstrap clustered by question" }] }] };
    });
    dotPlot(document.getElementById("c-share"), {
      rows: share, group: "Share of the drop at three layers (F11, F26, F36)", maxUnit: 2.6,
      x: { min: 0, max: 1.1, ticks: [0, 0.25, 0.5, 0.75, 1], fmt: function (x) { return x.toFixed(2); }, title: "share of the hint's drop at the takeover (dashed: Qwen3-8B's rule)" }
    });
    var hd = d.heads;
    document.getElementById("n-heads").textContent = "F12's three heads separate followed from resisted runs on set A: " +
      sgn(V(hd.d), 3) + " [" + sgn(V(hd.lo), 3) + ", " + sgn(V(hd.hi), 3) + "], " + V(hd.questions) + " questions (" + hd.reading + "; F32). Lines: 95% bootstrap clustered by question.";
    var sw = d.swap, parts = { every: "every layer", before: "0–14", readout: "15, 19, 23", through: "0–23", after: "24–31" };
    var all = []; sw.rows.forEach(function (r) { all.push(V(r.lora.lo), V(r.lora.hi), V(r.a40.lo), V(r.a40.hi)); });
    var smin = Math.floor(Math.min.apply(null, all) * 2) / 2 - 0.25, smax = Math.ceil(Math.max.apply(null, all) * 2) / 2 + 0.25;
    var st = []; for (var u = Math.ceil(smin * 2) / 2; u <= smax + 1e-9; u += 0.5) st.push(Math.round(u * 10) / 10);
    vBars(document.getElementById("c-swaps"), {
      group: "What the trained weights remove of base's hint effect (F39, F42)", divider: 1,
      cats: sw.rows.map(function (r) { return { label: parts[r.part], sub: r.part === "every" ? "the fix itself" : "a layer swap" }; }),
      series: [{ name: "LoRA", color: C("lora") }, { name: "A40", color: C("a40") }],
      vals: sw.rows.map(function (r) { return [r.lora, r.a40]; }),
      labelOf: function (ci, si) { var r = sw.rows[ci], v = si ? r.a40 : r.lora; return sgn(V(v.m), 2); },
      tipOf: function (ci, si) {
        var r = sw.rows[ci], v = si ? r.a40 : r.lora, who = si ? "A40" : "LoRA";
        return [{ v: ci2(v), l: "logits removed of base's hint effect (R), 95% bootstrap clustered by question", c: C(si ? "a40" : "lora") },
                { l: r.part === "every" ? who + "'s weights, every layer: " + first(si ? sw.a40_reading : sw.lora_reading) : "base with " + who + "'s weights on layers " + parts[r.part] + " only: reported, " + (si ? "no decision" : "not read") }];
      },
      y: { min: smin, max: smax, ticks: st, fmt: function (x) { return sgn(x, 1); }, title: "removes of base's hint effect (logits)" }
    });
    document.getElementById("n-swaps").textContent = "On base's own reasoning (" + V(sw.cases) + " cases, " + V(sw.questions) + " questions): LoRA's weights " +
      ci2(sw.rows[0].lora) + ", “" + first(sw.lora_reading) + "” (F39); A40's " + ci2(sw.rows[0].a40) + ", “" + sw.a40_reading + ", " + sw.a40_where + "” (F42); A40 minus LoRA " +
      ci2(sw.a40_minus_lora) + ". The swaps are reported, not read. 95% bootstrap clustered by question.";
  }

  // ------------------------------------------------------------------ section 4: between agents
  function s4() {
    var d = DATA.s4, rows = [];
    var view = function (kn, label, color, hollow, dy, who) {
      return { x: rate(kn) * 100, lo: V(kn.lo) * 100, hi: V(kn.hi) * 100, color: color, hollow: hollow, dy: dy, tip: knTip(kn, who + ": " + label, color) };
    };
    var famHead = { Olmo: "The Olmo family · C4's 73 cases", other: "Qwen3, Granite, Mistral · C4's 73 cases" }, last = null;
    d.reviewers.forEach(function (r) {
      var fam = r.family === "Olmo" ? "Olmo" : "other";
      if (fam !== last) { rows.push({ head: famHead[fam] }); last = fam; }
      rows.push({ label: r.name, sub: r.run + " · " + r.finding, right: pts(r.log_minus_answer.d), marks: [
        view(r.answer_only, "the answer only", C("final"), false, -0.21, r.name),
        view(r.plus_private, "+ the private reasoning", C("private"), false, 0, r.name),
        view(r.plus_tool_log, "+ the tool log", C("tool"), false, 0.21, r.name)] });
    });
    rows.push({ head: "C15 · 53 fresh items" });
    d.c15.forEach(function (r) {
      rows.push({ label: r.name, sub: "C15 · F24 · " + r.log_minus_answer.reading, right: pts(r.log_minus_answer.d), marks: [
        view(r.answer_only, "the answer only", C("final"), false, -0.21, r.name),
        view(r.plus_tool_log_redacted, "+ the tool log, its letter redacted", C("tool"), true, 0, r.name),
        view(r.plus_tool_log, "+ the tool log", C("tool"), false, 0.21, r.name)] });
    });
    dotPlot(document.getElementById("c-rev"), {
      rows: rows, group: "The reviewer alone corrects a wrong solver answer (F18, F22, F24, F30)", rightHead: "+ tool log − answer only (points)",
      x: { min: 0, max: 100, ticks: [0, 25, 50, 75, 100], fmt: function (t) { return t + "%"; }, title: "corrects the wrong solver answer" }
    });
    var ck = d.checker, tiles = document.getElementById("c-checker"); tiles.textContent = "";
    [[ck.caught, "wrong tool answers caught (bad lookups)"], [ck.false_alarms, "false alarms on good lookups"], [ck.floor, "the no-tool floor: the re-ask disagrees with no lookup"]].forEach(function (t) {
      var div = document.createElement("div"); div.className = "tile";
      var v = document.createElement("span"); v.className = "tile-v"; v.textContent = xy(t[0]);
      var l = document.createElement("span"); l.className = "tile-l"; l.textContent = t[1];
      var s = document.createElement("span"); s.className = "tile-s"; s.textContent = wil(t[0]) + ", 95% Wilson";
      div.appendChild(v); div.appendChild(l); div.appendChild(s); tiles.appendChild(div);
      TBL.push({ group: "The checker (C15, F24)", lines: [{ v: xy(t[0]), l: t[1] + "; " + wil(t[0]) }] });
    });
    var cues = [], seen = {};
    d.cues.forEach(function (c) { var k = c.experiment + c.what; if (!seen[k]) { seen[k] = []; cues.push(seen[k]); } seen[k].push(c); });
    dotPlot(document.getElementById("c-cues"), {
      group: "What the deferring reviewer responds to (C16–C18)", zero: 0, bands: [[-20, 20]], maxUnit: 2.3,
      rows: cues.map(function (pair) {
        var o = pair[0];
        return { label: o.experiment + " · " + o.finding, sub: o.what, right: pair[0].reading, rightSub: ptsIv(pair[0]),
          marks: pair.map(function (c, j) {
            return { x: V(c.d) * 100, lo: V(c.lo) * 100, hi: V(c.hi) * 100, color: j ? C("base") : "var(--ink)", hollow: !!j, dy: j ? 0.17 : -0.17,
              tip: [{ v: ptsIv(c), l: "points, paired by item: " + c.reading, c: j ? C("base") : "var(--ink)" },
                    { l: c.reviewer + ", " + c.experiment + ": " + c.what }, { v: V(c.a_k) + " vs " + V(c.b_k) + " of " + V(c.n), l: V(c.items) + " items" }] };
          }) };
      }),
      x: { min: -45, max: 75, ticks: [-40, -20, 0, 20, 40, 60], fmt: function (t) { return sgn(t, 0); }, title: "corrects a wrong answer: difference (points); right: Olmo's reading" }
    });
    var lb = d.labels;
    var lrows = [{ label: "“[unverified tool output]”", sub: "A39 · F44 · inserted turn", right: lb.wrapper.reading, rightSub: ptsIv(lb.wrapper),
      marks: [{ x: V(lb.wrapper.d) * 100, lo: V(lb.wrapper.lo) * 100, hi: V(lb.wrapper.hi) * 100, color: C("wrap"),
        tip: [{ v: ptsIv(lb.wrapper), l: "wrong hints followed, wrapper minus base (points): " + lb.wrapper.reading, c: C("wrap") }] }] }];
    lb.tag.forEach(function (t, j) {
      lrows.push({ label: "the pipeline's tag", sub: "C20 · FC3 · " + t.reviewer.replace(" Instruct", ""), right: t.reading, rightSub: ptsIv(t),
        marks: [{ x: V(t.d) * 100, lo: V(t.lo) * 100, hi: V(t.hi) * 100, color: j ? C("base") : "var(--ink)", hollow: !!j,
          tip: [{ v: ptsIv(t), l: "catches, tag minus blind (points): " + t.reading }, { v: V(t.a_k) + " vs " + V(t.b_k) + " of " + V(t.n), l: t.reviewer }] }] });
    });
    dotPlot(document.getElementById("c-labels"), {
      rows: lrows, group: "Provenance labels alone (F44, FC3)", zero: 0, maxUnit: 2.1,
      x: { min: -25, max: 30, ticks: [-20, -10, 0, 10, 20, 30], fmt: function (t) { return sgn(t, 0); } }
    });
  }

  // ------------------------------------------------------------------ section 5: the fixes
  var tradeView = "pooled";
  function s5() {
    var d = DATA.s5;
    trade(document.getElementById("c-trade"), d);
    acc(document.getElementById("c-acc"), d);
    l6(document.getElementById("c-l6"), d);
    b1r2(document.getElementById("c-b1r2"), d.b1r2);
  }
  function trade(host, d) {
    var R = rem(), m = mkSvg(host, "The trade-off on E2"), svg = m.svg, w = m.w, h = m.h;
    var group = "The trade-off on E2 (exploratory, post hoc)";
    var fk = tradeView === "pooled" ? "following" : "following_ins", ak = tradeView === "pooled" ? "acceptance" : "acceptance_ins";
    var names = Object.keys(d.systems);
    var xs = [], ys = [];
    names.forEach(function (s) { var e = d.systems[s]; xs.push(V(e[ak].lo), V(e[ak].hi)); ys.push(V(e[fk].lo), V(e[fk].hi)); });
    var xmin = Math.floor(Math.min.apply(null, xs) * 20) / 20, xmax = Math.min(1, Math.ceil(Math.max.apply(null, xs) * 20) / 20 + 0.02);
    var ymin = Math.max(0, Math.floor(Math.min.apply(null, ys) * 20) / 20 - 0.02), ymax = Math.ceil(Math.max.apply(null, ys) * 20) / 20;
    var left = R * 3.2, right = R * 0.8, top = R * 0.5, bottom = R * 2.4;
    var sx = function (v) { return left + (v - xmin) / (xmax - xmin) * (w - left - right); };
    var sy = function (v) { return top + (ymax - v) / (ymax - ymin) * (h - top - bottom); };
    for (var t = Math.ceil(xmin * 20) / 20; t <= xmax + 1e-9; t += 0.05) {
      S("line", { x1: sx(t), x2: sx(t), y1: top, y2: h - bottom, "class": "gridline" }, svg);
      T(svg, sx(t), h - bottom + R * 0.6, Math.round(t * 100) + "%", "t t-tick", "middle");
    }
    for (var u = Math.ceil(ymin * 20) / 20; u <= ymax + 1e-9; u += 0.05) {
      S("line", { x1: left, x2: w - right, y1: sy(u), y2: sy(u), "class": "gridline" }, svg);
      T(svg, left - R * 0.35, sy(u), Math.round(u * 100) + "%", "t t-tick", "end");
    }
    T(svg, (left + w - right) / 2, h - R * 0.55, "takes the correct hint (correct-hint acceptance) →", "t", "middle");
    var yt = T(svg, 0, 0, "follows the wrong hint ↓ better", "t", "middle"); yt.setAttribute("transform", "translate(" + (R * 0.55) + "," + ((top + h - bottom) / 2) + ") rotate(-90)");
    var placed = [], pts_ = [];
    names.forEach(function (s) {
      var e = d.systems[s], st = SYS[s], c = C(st.c), x = sx(rate(e[ak])), y = sy(rate(e[fk])), g = S("g", null, svg);
      S("line", { x1: sx(V(e[ak].lo)), x2: sx(V(e[ak].hi)), y1: y, y2: y, style: "stroke:" + c + ";stroke-width:1.6;opacity:0.6" }, g);
      S("line", { x1: x, x2: x, y1: sy(V(e[fk].lo)), y2: sy(V(e[fk].hi)), style: "stroke:" + c + ";stroke-width:1.6;opacity:0.6" }, g);
      var sh = shape(g, st.shape, x, y, Math.max(5, R * 0.34), c, st.hollow);
      pts_.push({ x: x, y: y, s: s });
      var tip = [{ v: xy(e[fk]), l: "wrong hints followed, " + wil(e[fk]), c: c }, { v: xy(e[ak]), l: "correct hints taken, " + wil(e[ak]), c: c },
                 { l: st.name + (tradeView === "pooled" ? ", pooled over the channels" : ", the inserted tool turn") + (e.diluted && tradeView === "pooled" ? " (diluted by design)" : "") }];
      bindTip(S("circle", { cx: x, cy: y, r: Math.max(13, R * 0.7), "class": "hit" }, g), tip, group + ", " + tradeView, sh);
    });
    // direct labels: the offset that collides least with labels and points
    var fs = 0.72 * R;
    pts_.forEach(function (p) {
      var label = SYS[p.s].name, lw = measure(label, fs), best = null;
      [[1, 0], [1, -1], [1, 1], [-1, 0], [-1, -1], [-1, 1], [0, -1], [0, 1]].forEach(function (o, rank) {
        var dx = o[0] * (R * 0.75), dy = o[1] * (R * 0.85);
        var bx = o[0] > 0 ? p.x + dx : o[0] < 0 ? p.x + dx - lw : p.x - lw / 2, by = p.y + dy - fs / 2;
        var box = { x0: bx - 2, x1: bx + lw + 2, y0: by - 1, y1: by + fs + 1 };
        var score = rank * 0.3;
        if (box.x0 < left || box.x1 > w - right || box.y0 < top || box.y1 > h - bottom) score += 1000;
        placed.forEach(function (q) { if (!(box.x1 < q.x0 || box.x0 > q.x1 || box.y1 < q.y0 || box.y0 > q.y1)) score += 200; });
        pts_.forEach(function (q) { if (q.x > box.x0 - 6 && q.x < box.x1 + 6 && q.y > box.y0 - 6 && q.y < box.y1 + 6) score += 60; });
        if (!best || score < best.score) best = { score: score, box: box, ax: o[0] > 0 ? "start" : o[0] < 0 ? "end" : "middle", tx: o[0] > 0 ? p.x + dx : o[0] < 0 ? p.x + dx : p.x, ty: p.y + dy };
      });
      placed.push(best.box);
      T(svg, best.tx, best.ty, label, "t t-val t-halo", best.ax);
    });
    var note = document.getElementById("n-trade");
    note.textContent = "E2: 120 questions, each run once; answered runs. " + (tradeView === "pooled" ?
      "Pooled: wrong hints over the user, pasted and inserted channels; correct hints over pasted and inserted. Hollow: the wrapper systems, diluted by design here (their runs without a tool message are their partner's)." :
      "The inserted tool turn only, where the wrapper acts.") + " Lines: 95% Wilson. Not pre-registered; replaces no verdict.";
  }
  function acc(host, d) {
    var R = rem(), m = mkSvg(host, "Acc(p)"), svg = m.svg, w = m.w, h = m.h;
    var group = "Acc(p) on the tool channels (exploratory, post hoc)";
    var input = document.getElementById("acc-p"), p = Number(input.value);
    document.getElementById("acc-p-out").textContent = p.toFixed(2);
    var sys = ["base", "prompt_only", "lora", "a40"];
    var line = sys.map(function (s) { var e = d.systems[s]; return { s: s, w: rate(e.a_W), c: rate(e.a_C), e: e }; });
    var lo = Math.min.apply(null, line.map(function (l) { return Math.min(l.w, l.c); })), hi = Math.max.apply(null, line.map(function (l) { return Math.max(l.w, l.c); }));
    var ymin = Math.floor(lo * 10) / 10 - 0.02, ymax = Math.min(1, Math.ceil(hi * 10) / 10 + 0.02);
    var labW = Math.max.apply(null, sys.map(function (s) { return measure(SYS[s].name + " 00.0%", 0.72 * R); })) + R;
    var left = R * 3.0, right = labW, top = R * 0.5, bottom = R * 3.2;
    var sx = function (v) { return left + v * (w - left - right); }, sy = function (v) { return top + (ymax - v) / (ymax - ymin) * (h - top - bottom); };
    var x = d.crossings.a40;
    if (x.p) {                                                   // A40's crossing with the instruction, and its interval
      S("rect", { x: sx(V(x.lo)), y: top, width: sx(V(x.hi)) - sx(V(x.lo)), height: h - bottom - top, "class": "band" }, svg);
      S("line", { x1: sx(V(x.p)), x2: sx(V(x.p)), y1: top, y2: h - bottom, style: "stroke:" + C("a40") + ";stroke-width:1.2;stroke-dasharray:5 4" }, svg);
    }
    for (var t = Math.ceil(ymin * 20) / 20; t <= ymax + 1e-9; t += 0.05) {
      S("line", { x1: left, x2: w - right, y1: sy(t), y2: sy(t), "class": "gridline" }, svg);
      T(svg, left - R * 0.35, sy(t), Math.round(t * 100) + "%", "t t-tick", "end");
    }
    [0, 0.25, 0.5, 0.75, 1].forEach(function (u) { T(svg, sx(u), h - bottom + R * 0.6, u.toFixed(2), "t t-tick", "middle"); });
    T(svg, (left + w - right) / 2, h - bottom + R * 1.55, "p: the share of the tool's answers that are right", "t", "middle");
    var yt = T(svg, 0, 0, "expected correct answers, Acc(p)", "t t-sub", "middle"); yt.setAttribute("transform", "translate(" + (R * 0.55) + "," + ((top + h - bottom) / 2) + ") rotate(-90)");
    line.forEach(function (l) {
      var c = C(SYS[l.s].c);
      S("line", { x1: sx(0), x2: sx(1), y1: sy(l.w), y2: sy(l.c), style: "stroke:" + c + ";stroke-width:2.4;stroke-linecap:round" }, svg);
      [[0, l.e.a_W, "a_W: the right letter among answered wrong-hint tool runs (p = 0)"], [1, l.e.a_C, "a_C: correct among answered correct-hint tool runs (p = 1)"]].forEach(function (end) {
        var g = S("g", null, svg), yy = sy(rate(end[1]));
        var sh = shape(g, "circle", sx(end[0]), yy, Math.max(4, R * 0.24), c);
        bindTip(S("circle", { cx: sx(end[0]), cy: yy, r: 12, "class": "hit" }, g), knTip(end[1], SYS[l.s].name + ", " + end[2], c), group, sh);
      });
    });
    S("line", { x1: sx(p), x2: sx(p), y1: top, y2: h - bottom, style: "stroke:var(--ink);stroke-width:1.3" }, svg);
    var vals = line.map(function (l) { return { l: l, v: p * l.c + (1 - p) * l.w }; }).sort(function (a, b) { return b.v - a.v; });
    // the values are at the slider's p, not at the lines' right ends: say so above them (Nov 14, the by-eye check)
    var headY = Math.max(top + R * 0.5, sy(vals[0].v) - R * 0.95);
    T(svg, w - right + R * 0.6, headY, "at p = " + p.toFixed(2) + ":", "t t-sub", "start");
    var lastY = headY;
    vals.forEach(function (o) {
      var c = C(SYS[o.l.s].c), yy = sy(o.v);
      shape(svg, SYS[o.l.s].shape, sx(p), yy, Math.max(4.5, R * 0.3), c);
      var ty = Math.max(yy, lastY + R * 0.95); lastY = ty;
      T(svg, w - right + R * 0.6, ty, SYS[o.l.s].name + " " + (o.v * 100).toFixed(1) + "%", "t t-val", "start");
      S("line", { x1: sx(1) + 3, x2: w - right + R * 0.45, y1: sy(o.l.c), y2: ty, style: "stroke:var(--grid);stroke-width:1" }, svg);
    });
    var lora = d.crossings.lora, n = document.getElementById("n-acc");
    var ahead = function (s) { return SYS[s].name; };
    n.textContent = "Acc(p) = p · a_C + (1 − p) · a_W on the two tool channels (pasted, inserted); line ends: 95% Wilson. " +
      (x.p ? "A40 gives more correct answers than the instruction only when fewer than " + num2(x.p) + " [" + num2(x.lo) + ", " + num2(x.hi) + "] of the tool's answers are correct (shaded; the order flips in " + V(x.flipped).toLocaleString("en-US") + " of 20,000 resamples). " : "") +
      ahead("lora") + " against the instruction: " + lora.status + ". Questions resampled, paired, 20,000 times (seed 0). Not pre-registered; replaces no verdict.";
  }
  function l6(host, d) {
    var R = rem(), m = mkSvg(host, "Disclosure when following"), svg = m.svg, w = m.w, h = m.h;
    var group = "When it follows a wrong hint, the final answer says so (F45; keyword exploratory)";
    var sys = ["base", "prompt_only", "lora", "a40"], hand = { prompt_only: d.l6.instruction, lora: d.l6.lora };
    var left = R * 2.6, right = R * 0.4, top = R * 1.0, bottom = R * 2.6;
    var band = (w - left - right) / sys.length, sy = function (v) { return top + (1 - v) * (h - top - bottom); };
    [0, 0.25, 0.5, 0.75, 1].forEach(function (t) {
      S("line", { x1: left, x2: w - right, y1: sy(t), y2: sy(t), "class": t === 0 ? "axisline" : "gridline" }, svg);
      T(svg, left - R * 0.35, sy(t), Math.round(t * 100) + "%", "t t-tick", "end");
    });
    sys.forEach(function (s, i) {
      var e = d.systems[s].keyword, c = C(SYS[s].c), cx = left + band * (i + 0.5), bw = Math.min(R * 1.3, band * 0.32), g = S("g", null, svg);
      var bx = hand[s] ? cx - bw - R * 0.25 : cx - bw / 2;
      var bar = S("path", { d: vBarPath(bx, sy(0), bw, sy(rate(e)), 3), style: "fill:" + c }, g);
      S("line", { x1: bx + bw / 2, x2: bx + bw / 2, y1: sy(V(e.lo)), y2: sy(V(e.hi)), style: "stroke:var(--ink);stroke-width:1.3" }, g);
      T(g, bx + bw / 2, sy(V(e.hi)) - R * 0.45, V(e.k) + "/" + V(e.n), "t t-sub t-halo", "middle");
      T(svg, cx, h - bottom + R * 0.7, SYS[s].name, "t t-label", "middle");
      bindTip(S("rect", { x: bx - 3, y: sy(V(e.hi)) - 6, width: bw + 6, height: sy(0) - sy(V(e.hi)) + 6, "class": "hit" }, g),
        knTip(e, SYS[s].name + ": the keyword, the final answer names the hint when following (exploratory, post hoc; pooled)", c), group, bar);
      if (hand[s]) {
        var k = hand[s], hx = cx + R * 0.75, g2 = S("g", null, svg);
        S("line", { x1: hx, x2: hx, y1: sy(V(k.lo)), y2: sy(V(k.hi)), style: "stroke:var(--ink);stroke-width:2.2" }, g2);
        var sh = shape(g2, "diamond", hx, sy(rate(k)), Math.max(4.5, R * 0.3), "var(--ink)");
        T(g2, hx, sy(V(k.lo)) + R * 0.7, V(k.k) + "/" + V(k.n), "t t-sub t-halo", "middle");
        bindTip(S("circle", { cx: hx, cy: sy(rate(k)), r: 13, "class": "hit" }, g2),
          knTip(k, SYS[s].name + ": hand labels (L6, Ritik's, final), the final answer discloses the followed hint", "var(--ink)"), group, sh);
      }
    });
    var l = d.l6, kw = d.keyword_vs.lora;
    document.getElementById("n-l6").textContent = "LoRA " + xy(l.lora) + " against the instruction's " + xy(l.instruction) + ": " + ptsIv(l.comparison) +
      ", “" + l.comparison.reading + "” (Ritik against J-opus, kappa " + num2(l.kappa) + "). None of LoRA's " + V(l.rejects_lora.n) + " claims to reject the hint it ends on (" +
      xy(l.rejects_lora) + "). The keyword gave the same, " + xy(d.systems.lora.keyword) + " against " + xy(d.systems.prompt_only.keyword) + " (" + ptsIv(kw) + "; exploratory, post hoc).";
    document.getElementById("n-l6-blind").textContent = "The sheet not blind in practice, with J-opus (blind to systems) agreeing on " +
      Math.round(V(l.agreement) * V(l.rows)) + " of " + V(l.rows) + " rows.";
  }
  function b1r2(host, rows) {
    host.textContent = "";
    host.style.display = "flex"; host.style.gap = "1.2rem";
    var vals = []; rows.forEach(function (r) { ["following", "acceptance", "accuracy"].forEach(function (k) { vals.push(V(r[k].lo) * 100, V(r[k].hi) * 100); }); });
    var xmin = Math.min(-10, Math.floor(Math.min.apply(null, vals) / 10) * 10 - 5), xmax = Math.max(10, Math.ceil(Math.max.apply(null, vals) / 10) * 10 + 5);
    var ticks = []; for (var t = Math.ceil(xmin / 10) * 10; t <= xmax; t += 10) ticks.push(t);
    var ms = { following: ["follows the wrong hint", "damage", "circle", "inserted tool turn"], acceptance: ["takes the correct hint", "correct", "diamond", "inserted tool turn"],
               accuracy: ["no-hint accuracy", "base", "square", "no hint"] };
    var facets = [];
    rows.forEach(function (r, i) {
      var div = document.createElement("div"); div.style.cssText = "position:relative;flex:" + (i ? "1" : "1.35") + " 1 0;min-width:0;display:flex;flex-direction:column";
      var hd = document.createElement("p"); hd.className = "note"; hd.style.color = "var(--ink)"; hd.style.fontSize = "0.74rem";
      hd.textContent = (r.study === "B1" ? "B1, the held-out 30 (primary): “" : "B1R2, E2's 120 questions (a labelled replication): “") + r.reading + "”";
      var ch = document.createElement("div"); ch.className = "chart";
      div.appendChild(hd); div.appendChild(ch); host.appendChild(div);
      facets.push([ch, r, i]);
    });
    facets.forEach(function (f) {
      var ch = f[0], r = f[1], i = f[2];
      var step = ch.clientWidth < rem() * 30 ? 20 : 10, tk = ticks.filter(function (t) { return t % step === 0; });
      dotPlot(ch, {
        group: "Attention scaling, " + r.study + " (F38)", zero: 0, labelW: i ? rem() * 0.2 : undefined, maxUnit: 2.6,
        rows: ["following", "acceptance", "accuracy"].map(function (k) {
          var e = r[k], mm = ms[k], c = C(mm[1]);
          return { label: i ? "" : mm[0], sub: i ? "" : mm[3], right: ptsIv(e, 1), rightSub: V(e.base_k) + " of " + V(e.base_n) + " → " + V(e.k) + " of " + V(e.n),
            band: k === "acceptance" ? [-MARGIN * 100, xmax] : k === "accuracy" ? [-MARGIN * 100, MARGIN * 100] : null,
            marks: [{ x: V(e.d) * 100, lo: V(e.lo) * 100, hi: V(e.hi) * 100, color: c, shape: mm[2],
              tip: [{ v: ptsIv(e, 1), l: "the span minus alpha = 1 (points), " + V(e.questions) + " questions", c: c },
                    { v: V(e.base_k) + " of " + V(e.base_n) + " → " + V(e.k) + " of " + V(e.n), l: r.study + ": " + mm[0] + ", alpha 1 → " + V(r.alpha) }] }] };
        }),
        x: { min: xmin, max: xmax, ticks: tk, fmt: function (t) { return sgn(t, 0); }, title: "span minus alpha = 1 (points)" }
      });
    });
  }

  // ------------------------------------------------------------------ section 6
  function s6() { document.getElementById("n-kappa").textContent = V(DATA.s6.kappa_l6).toFixed(3); }

  // ------------------------------------------------------------------ the examples (the local page only)
  var HINT_WORDS = /\b(tool|tools|lookup|look-up|lookup_answer_key|answer key|database|hint|provided|suggest(?:s|ed|ion)?|according to)\b/gi;
  function marked(text, letter) {
    var frag = document.createDocumentFragment(), s = String(text || "");
    var rx = new RegExp("\\(" + (letter || "#").replace(/[^A-Za-z]/g, "") + "\\)|" + HINT_WORDS.source, "gi"), i = 0, mm;
    while ((mm = rx.exec(s))) {
      if (mm.index > i) frag.appendChild(document.createTextNode(s.slice(i, mm.index)));
      var mk = document.createElement("mark"); mk.textContent = mm[0]; frag.appendChild(mk); i = mm.index + mm[0].length;
      if (mm[0].length === 0) rx.lastIndex++;
    }
    if (i < s.length) frag.appendChild(document.createTextNode(s.slice(i)));
    return frag;
  }
  function examples() {
    if (!EX) return;
    var list = document.getElementById("ex-list"); list.textContent = "";
    document.getElementById("ex-sub").textContent = EX.examples.length + " rows drawn by the seed “" + EX.seed + "”; the hint's letter and words about a source marked. " +
      (EX.missing.length ? "Missing: " + EX.missing.join("; ") : "Every source was there.");
    EX.examples.forEach(function (e) {
      var art = document.createElement("article"); art.className = "ex";
      var meta = document.createElement("p"); meta.className = "ex-meta";
      meta.textContent = e.source + " row " + e.row + " · run " + e.run_id + " · " + e.system + " · " + e.channel + " · label: " + e.label +
        (e.label_private ? " (private: " + e.label_private + ")" : "") + " · hint (" + e.hint_letter + ") · " + e.labels_are + " · " + e.illustrative;
      art.appendChild(meta);
      var cols = document.createElement("div"); cols.className = "ex-cols";
      [["private", "the private reasoning", "private"], ["final_answer", "the final answer", "final"]].forEach(function (c) {
        var div = document.createElement("div"); div.className = "ex-col";
        var h4 = document.createElement("h4"); var sw = document.createElement("span"); sw.className = "sw sw-" + c[2]; h4.appendChild(sw); h4.appendChild(document.createTextNode(c[1]));
        div.appendChild(h4);
        if (e[c[0]]) { var pre = document.createElement("pre"); pre.appendChild(marked(e[c[0]], e.hint_letter)); div.appendChild(pre); }
        else { var ab = document.createElement("p"); ab.className = "absent"; ab.textContent = e.private_status || "not in this sheet"; div.appendChild(ab); }
        cols.appendChild(div);
      });
      art.appendChild(cols); list.appendChild(art);
    });
  }

  // ------------------------------------------------------------------ the deck: sections, keys, hash, theme
  var slides = Array.prototype.slice.call(document.querySelectorAll(".slide"));
  var RENDER = { s0: s0, s1: s1, s2: s2, s3: s3, s4: s4, s5: s5, s6: s6, examples: examples };
  var TABLES = {}, cur = -1;
  var pips = document.getElementById("pips");
  slides.forEach(function (s, i) {
    var b = document.createElement("button"); b.type = "button";
    b.textContent = s.id === "examples" ? "E" : s.id.slice(1);
    b.title = s.getAttribute("data-title"); b.setAttribute("aria-label", ["Section", b.textContent, "·", s.getAttribute("data-title")].join(" "));
    b.addEventListener("click", function () { go(i); });
    pips.appendChild(b);
  });
  var ix = document.getElementById("index-list");
  slides.forEach(function (s, i) {
    var li = document.createElement("li"), b = document.createElement("button"); b.type = "button";
    var n = document.createElement("span"); n.className = "ix"; n.textContent = s.id === "examples" ? "E" : s.id.slice(1);
    var t = document.createElement("span"); t.textContent = s.getAttribute("data-title");
    b.appendChild(n); b.appendChild(t); b.addEventListener("click", function () { closeAll(); go(i); });
    li.appendChild(b); ix.appendChild(li);
  });
  document.querySelectorAll("[data-legend]").forEach(function (ul) { fillLegend(ul, ul.getAttribute("data-legend").split(",")); });

  function renderCurrent(again) {
    var s = slides[cur]; if (!s) return;
    TBL = [];
    try { RENDER[s.id] && RENDER[s.id](); }
    catch (err) { if (window.console) console.error(err); }
    TABLES[s.id] = TBL;
    if (!again) requestAnimationFrame(function () {
      var moved = Array.prototype.some.call(s.querySelectorAll(".chart > svg"), function (svg) {
        var host = svg.parentNode;
        return Math.abs(host.clientWidth - Number(svg.getAttribute("width"))) > 1 || Math.abs(host.clientHeight - Number(svg.getAttribute("height"))) > 1;
      });
      if (moved) renderCurrent(true);
    });
  }
  function go(i) {
    i = clamp(i, 0, slides.length - 1);
    var id = slides[i].id;
    if (location.hash !== "#" + id) location.hash = id; else show(i);
  }
  function show(i) {
    cur = i; tipEl.hidden = true;
    slides.forEach(function (s, j) { s.hidden = j !== i; });
    Array.prototype.forEach.call(pips.children, function (b, j) { b.setAttribute("aria-current", j === i ? "true" : "false"); });
    requestAnimationFrame(function () { renderCurrent(); });
  }
  function fromHash() {
    var id = (location.hash || "").replace(/^#/, "");
    for (var i = 0; i < slides.length; i++) if (slides[i].id === id) return i;
    return 0;
  }
  window.addEventListener("hashchange", function () { show(fromHash()); });
  var resizeT = null;
  window.addEventListener("resize", function () { clearTimeout(resizeT); resizeT = setTimeout(function () { renderCurrent(); }, 120); });

  // overlays
  var overIndex = document.getElementById("index"), overNums = document.getElementById("nums");
  function closeAll() { overIndex.hidden = true; overNums.hidden = true; }
  function toggleIndex() { var open = overIndex.hidden; closeAll(); overIndex.hidden = !open; if (open) { var b = ix.querySelectorAll("button")[cur]; if (b) b.focus(); } }
  function toggleNums() {
    var open = overNums.hidden; closeAll(); if (!open) return;
    var body = document.getElementById("nums-body"); body.textContent = "";
    document.getElementById("nums-h").textContent = "The numbers on this screen: " + slides[cur].getAttribute("data-title");
    var groups = {};
    (TABLES[slides[cur].id] || []).forEach(function (r) { (groups[r.group] = groups[r.group] || []).push(r.lines); });
    Object.keys(groups).forEach(function (g) {
      var tb = document.createElement("table"), cap = document.createElement("caption"); cap.textContent = g; tb.appendChild(cap);
      groups[g].forEach(function (lines) {
        var tr = document.createElement("tr");
        var a = document.createElement("td"); a.textContent = lines.filter(function (l) { return !l.v; }).map(function (l) { return l.l; }).join("; ");
        var b = document.createElement("td"); b.textContent = lines.filter(function (l) { return l.v; }).map(function (l) { return l.v + " " + (l.l || ""); }).join("; ");
        tr.appendChild(a); tr.appendChild(b); tb.appendChild(tr);
      });
      body.appendChild(tb);
    });
    if (!body.childNodes.length) body.textContent = "No chart on this screen.";
    overNums.hidden = false;
  }
  [overIndex, overNums].forEach(function (o) { o.addEventListener("click", function (e) { if (e.target === o) closeAll(); }); });

  // theme: the system's by default; t or the button sets one and remembers it on this browser
  function isDark() {
    var t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function toggleTheme() {
    var next = isDark() ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("cse598-demo-theme", next); } catch (e) { /* storage may be off */ }
  }
  try { var saved = localStorage.getItem("cse598-demo-theme"); if (saved === "dark" || saved === "light") document.documentElement.setAttribute("data-theme", saved); } catch (e) { /* none */ }
  function fullScreen() {
    try { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen().catch(function () {}); } catch (e) { /* not offered */ }
  }

  document.getElementById("btn-prev").addEventListener("click", function () { go(cur - 1); });
  document.getElementById("btn-next").addEventListener("click", function () { go(cur + 1); });
  document.getElementById("btn-index").addEventListener("click", toggleIndex);
  document.getElementById("btn-nums").addEventListener("click", toggleNums);
  document.getElementById("btn-theme").addEventListener("click", toggleTheme);
  document.getElementById("trade-pooled").addEventListener("click", function () { setTrade("pooled"); });
  document.getElementById("trade-ins").addEventListener("click", function () { setTrade("inserted"); });
  function setTrade(v) {
    tradeView = v;
    document.getElementById("trade-pooled").setAttribute("aria-pressed", v === "pooled" ? "true" : "false");
    document.getElementById("trade-ins").setAttribute("aria-pressed", v === "pooled" ? "false" : "true");
    renderCurrent();
  }
  document.getElementById("acc-p").addEventListener("input", function () { acc(document.getElementById("c-acc"), DATA.s5); });

  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var k = e.key, inRange = e.target && e.target.type === "range";
    if (k === "Escape") { closeAll(); return; }
    if (inRange && (k === "ArrowLeft" || k === "ArrowRight" || k === "Home" || k === "End" || k === "PageUp" || k === "PageDown")) return;
    if (k === "ArrowRight" || k === "PageDown") { e.preventDefault(); go(cur + 1); }
    else if (k === "ArrowLeft" || k === "PageUp") { e.preventDefault(); go(cur - 1); }
    else if (k === "Home") { e.preventDefault(); go(0); }
    else if (k === "End") { e.preventDefault(); go(slides.length - 1); }
    else if (/^[0-6]$/.test(k)) { var j = slides.findIndex(function (s) { return s.id === "s" + k; }); if (j >= 0) { closeAll(); go(j); } }
    else if (k === "e" && EX) { var x = slides.findIndex(function (s) { return s.id === "examples"; }); if (x >= 0) go(x); }
    else if (k === "i") toggleIndex();
    else if (k === "n") toggleNums();
    else if (k === "t") toggleTheme();
    else if (k === "f") fullScreen();
  });
  show(fromHash());
})();
