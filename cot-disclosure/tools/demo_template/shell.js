/* ------------------------------------------------------------------
   The shell: three parts on one sheet (how we did it, run it, what we
   found), the timing marks, the keys, the theme and the scaling.
   Every part is a list of pages {title, run}; show(i) draws page i of
   the current part into #beat and #rows. No autoplay.
   ------------------------------------------------------------------ */
const PARTS = [
  { id: "map", tab: "How we did it", unit: "Step", pages: typeof MAP_STEPS !== "undefined" ? MAP_STEPS : [], home: true, onKey: typeof MAP_ONKEY !== "undefined" ? MAP_ONKEY : null },
  { id: "bench", tab: "Run it", unit: "Test", pages: typeof BENCH_TESTS !== "undefined" ? BENCH_TESTS : [], onKey: typeof BENCH_ONKEY !== "undefined" ? BENCH_ONKEY : null, leave: typeof BENCH_LEAVE !== "undefined" ? BENCH_LEAVE : null },
  { id: "found", tab: "What we found", unit: "Item", pages: BEATS },
];
/* the local build adds the scratch pad as part 1 (and the default screen); the tracked build has none */
if (typeof PAD_PAGES !== "undefined" && PAD_PAGES) PARTS.unshift({ id: "pad", tab: "Scratch pad", unit: "Scratch pad", pages: PAD_PAGES, pad: true, onKey: PAD_ONKEY, leave: PAD_LEAVE });
const partById = (id) => PARTS.find((p) => p.id === id);
/* each result sheet's test on the bench and its method on the map (page indexes) */
const LINKS = [
  { test: 0, step: 1 }, { test: 0, step: 2 }, { test: 1, step: 2 }, { test: 2, step: 3 }, { test: 2, step: 3 },
  { test: 5, step: 6 }, { test: 4, step: 10 }, { test: 3, step: 9 }, { test: 3, step: 7 }, { test: null, step: 11 },
];
let part = -1, cur = 0;
const timing = $("#timing");
const P = () => PARTS[part];

function buildTabs() {
  const nav = $("#parts");
  PARTS.forEach((p, j) => {
    const b = H("button", { type: "button", class: "ptab", "aria-current": "false", title: `${j + 1}. ${p.tab}` }, nav, `<span class="bub"></span>${p.tab}`);
    b.addEventListener("click", () => go(p.id));
  });
}
function buildTiming() {
  timing.innerHTML = "";
  const n = P().pages.length, gap = Math.min(52, Math.floor(600 / Math.max(1, n - 1)) - 9);
  timing.style.gap = gap + "px";
  P().pages.forEach((pg, i) => {
    const t = H("button", { type: "button", "aria-label": `${P().unit} ${i + (P().home ? 0 : 1)}: ${pg.title}`, title: pg.title }, timing);
    t.addEventListener("click", () => show(i));
  });
}
function go(id, i = 0) {
  const j = PARTS.findIndex((p) => p.id === id);
  if (j < 0) return;
  if (j !== part) { if (part >= 0 && P().leave) P().leave(); part = j; buildTiming(); }
  [...$("#parts").children].forEach((b, k) => b.setAttribute("aria-current", k === part ? "page" : "false"));
  if (location.hash !== "#" + id) history.replaceState(null, "", "#" + id);
  show(i);
}
function show(i, { instant = false } = {}) {
  const pages = P().pages;
  cur = Math.max(0, Math.min(pages.length - 1, i));
  timers.forEach(clearTimeout); timers = [];
  INSTANT = instant;
  $("#beat").innerHTML = ""; $("#rows").innerHTML = ""; $("#xlinks").innerHTML = "";
  $("#beat").dataset.part = P().id;
  const home = P().home && cur === 0;
  $("#sheet").dataset.part = P().id; if (PARTS.length > 3) $("#sheet").dataset.pad = "1";
  $("#keyhint").textContent = PARTS.length > 3 ? `1–${PARTS.length} part \u00a0 ${P().pad ? "Enter replay \u00a0 N next run \u00a0 Esc finish" : "← → step \u00a0 R replay"} \u00a0 T theme` : "1–3 part \u00a0 ← → step \u00a0 R replay \u00a0 T theme";
  $("#unit").textContent = P().pad ? "Part" : home ? "The map" : P().unit;
  $("#itemno").textContent = P().pad ? "1" : home ? "–" : cur + (P().home ? 0 : 1);
  $("#ofn").textContent = P().pad ? "" : `of ${pages.length - (P().home ? 1 : 0)}`;
  [...timing.children].forEach((b, j) => { b.setAttribute("aria-current", j === cur ? "step" : "false"); b.classList.toggle("done", j < cur); });
  if (pages[cur]) pages[cur].run();
  if (P().id === "found" && LINKS[cur]) {
    const L = LINKS[cur], x = $("#xlinks");
    if (L.test != null && partById("bench").pages[L.test]) H("button", { type: "button", class: "xlink" }, x, "Run this test →").addEventListener("click", () => go("bench", L.test));
    if (partById("map").pages[L.step]) H("button", { type: "button", class: "xlink" }, x, "How we did this →").addEventListener("click", () => go("map", L.step));
  }
  INSTANT = false;
}
function fit() {
  const s = Math.min(window.innerWidth / 1640, window.innerHeight / 940);
  $("#sheet").style.transform = `translate(-50%, -50%) scale(${s})`;
}
window.addEventListener("resize", fit); fit();
(function theme() {
  const root = document.documentElement, btn = $("#themeBtn");
  const dark = () => (root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches);
  const sync = () => { btn.textContent = dark() ? "Paper" : "Carbon copy"; };
  btn.addEventListener("click", () => { root.dataset.theme = dark() ? "light" : "dark"; sync(); show(cur, { instant: true }); });
  sync();
})();
document.addEventListener("keydown", (e) => {
  const tag = (document.activeElement && document.activeElement.tagName) || "";
  if (/INPUT|TEXTAREA|SELECT/.test(tag) || e.metaKey || e.ctrlKey || e.altKey) return;
  if (P().onKey && P().onKey(e)) { e.preventDefault(); return; }
  const k = e.key;
  if (!e.shiftKey && /^Digit[1-9]$/.test(e.code) && PARTS[+e.code.slice(5) - 1]) { e.preventDefault(); go(PARTS[+e.code.slice(5) - 1].id); }
  else if (k === "ArrowRight" || k === "PageDown") { e.preventDefault(); show(cur + 1); }
  else if (k === "ArrowLeft" || k === "PageUp") { e.preventDefault(); show(cur - 1); }
  else if (k === "Escape" && P().home && cur !== 0) { e.preventDefault(); show(0); }
  else if (k === "r" || k === "R") show(cur);
  else if (k === "t" || k === "T") $("#themeBtn").click();
  else if (k === "Home") show(0);
});
window.addEventListener("hashchange", () => { const id = location.hash.slice(1); if (PARTS.some((p) => p.id === id) && id !== P().id) go(id); });
buildTabs();
{
  const id = location.hash.slice(1);
  go(PARTS.some((p) => p.id === id) ? id : PARTS[0].pad ? "pad" : "map");
}
