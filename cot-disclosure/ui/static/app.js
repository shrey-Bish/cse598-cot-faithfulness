// Wrong-hint demo: four short scenes + an optional live call. Data comes from /api/demo,
// which the server builds from saved replies; nothing here invents text or numbers.
const $ = (id) => document.getElementById(id);
const scenes = [...document.querySelectorAll(".scene")];
const PLAY_MS = [9000, 14000, 10000, 12000];   // ~45 s; the live scene is never auto-played
let D = null, cur = 0, timers = [], playing = false, playTimer = null;

const esc = (s) => (s || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const later = (ms, fn) => timers.push(setTimeout(fn, ms));
const clearTimers = () => { timers.forEach(clearTimeout); timers = []; };
const fmt = (n) => n.toLocaleString("en-US");

function chip(letter, cls, delay, box) {
  const c = document.createElement("div");
  c.className = "chip " + cls;
  c.textContent = letter ?? "–";
  box.appendChild(c);
  later(delay, () => c.classList.add("show"));
}

function tail(text, n) {
  const t = (text || "").trim();
  if (t.length <= n) return t;
  const cut = t.slice(t.length - n);
  return "…" + cut.slice(cut.indexOf(" ") + 1);
}

// type text into an element quickly (about 1.6 s whatever the length)
function typeInto(el, text, delay, ms = 1600) {
  el.textContent = "";
  later(delay, () => {
    const steps = 40, per = Math.ceil(text.length / steps);
    let i = 0;
    const tick = () => {
      i += per;
      el.textContent = text.slice(0, i);
      el.scrollTop = el.scrollHeight;
      if (i < text.length) timers.push(setTimeout(tick, ms / steps));
    };
    tick();
  });
}

// "searching N characters for the hint" counter, then the keyword-check result
function scan(el, text, hits, delay, where) {
  const n = (text || "").length;
  el.innerHTML = "";
  later(delay, () => {
    const t0 = performance.now();
    const step = () => {
      const f = Math.min(1, (performance.now() - t0) / 1300);
      el.innerHTML = `Searching ${fmt(Math.round(n * f))} characters for the hint…`;
      if (f < 1) return timers.push(setTimeout(step, 40));
      el.innerHTML = hits.length === 0
        ? `Keyword check: <b>no mention of the hint</b> in ${fmt(n)} characters of ${where}.`
        : `Keyword check: ${hits.length} match(es) in ${fmt(n)} characters.`;
    };
    step();
  });
}

function letterChips(card, prefix, delay) {
  const nh = $(prefix + "-nohint"), hb = $(prefix + "-hinted");
  nh.innerHTML = ""; hb.innerHTML = "";
  card.no_hint.forEach((r, i) => chip(r.letter, r.letter === card.correct ? "right" : "wrong", delay + i * 250, nh));
  const cap = document.createElement("div");
  cap.className = "chip-cap";
  cap.textContent = card.no_hint.some((r) => r.letter === card.hint) ? "" : `${card.no_hint.length} runs, never (${card.hint})`;
  nh.parentElement.querySelector(".chip-cap")?.remove();
  nh.parentElement.appendChild(cap);
  const cls = card.answer === card.hint ? "hint" : card.answer === card.correct ? "right" : "wrong";
  chip(card.answer, cls, delay + 1100, hb);
}

// ---------------------------------------------------------------- scenes
const enter = {
  question() {
    const q = D.question;
    $("q-meta").textContent = `MMLU-Pro exam question · ${q.category} · item ${q.id}`;
    $("q-text").textContent = q.text;
    $("q-options").innerHTML = q.options.map((o) =>
      `<li class="${o.letter === q.correct ? "correct" : ""} ${o.letter === q.hint_letter ? "hinted" : ""}">` +
      `<span class="l">(${o.letter})</span>${esc(o.text)}</li>`).join("");
    $("q-correct").textContent = `(${q.correct})`;
    $("q-hint").textContent = `(${q.hint_letter})`;
    const bubble = $("hint-bubble");
    bubble.classList.remove("show");
    later(1200, () => bubble.classList.add("show"));
    typeInto($("hint-text"), "“" + q.hint_text + "”", 1500, 1400);
    later(3200, () => document.querySelector(".options li.hinted")?.classList.add("show"));
  },
  fell() { showCard("fell", D.fell, true); },
  held() { showCard("held", D.held, false); },
  numbers() {
    const F = D.findings;
    document.querySelectorAll("[data-k]").forEach((el) => { el.style.width = "0"; });
    document.querySelectorAll("[data-c]").forEach((el) => {
      const f = F[el.dataset.c];
      const unit = el.dataset.c.startsWith("review") ? "reviews" : ["tool", "user"].includes(el.dataset.c) ? "questions" : "runs";
      el.innerHTML = `${f.k} of ${f.n} ${unit} <span class="pct">(${Math.round((100 * f.k) / f.n)}%)</span>`;
    });
    later(300, () => document.querySelectorAll("[data-k]").forEach((el) => {
      const f = F[el.dataset.k];
      el.style.width = `${(100 * f.k) / f.n}%`;
    }));
    $("numbers-prov").textContent = "Computed when the page loaded from " + F.sources.join(", ") + ".";
  },
  live() { renderFresh(); },
};

function showCard(prefix, card, isFail) {
  $(prefix + "-model").textContent = card.model_name;
  letterChips(card, prefix, 300);
  const priv = $(prefix + "-private"), fin = $(prefix + "-final"), v = $(prefix + "-verdict");
  v.classList.remove("show");
  typeInto(priv, tail(card.private, isFail ? 650 : 520), 1700);
  if (isFail) {
    scan($("fell-scan"), card.private, card.private_hits, 1700, "private reasoning");
    typeInto(fin, card.final.trim(), 3600, 400);
    scan($("fell-scan-final"), card.final, card.final_hits, 3700, "the final answer");
    v.textContent = `It switched to the hint’s wrong answer (${card.hint}) and never said the hint was the reason.`;
  } else {
    typeInto(fin, tail(card.final, 260), 3000, 700);
    v.textContent = card.answer === card.correct
      ? `It did not follow the hint and kept the correct answer (${card.correct}).`
      : `It did not follow the hint (${card.hint}).`;
  }
  later(isFail ? 5400 : 4200, () => v.classList.add("show"));
  if (isFail) {
    const s = D.fresh_summary, again = $("fell-again");
    again.classList.remove("show");
    again.innerHTML = s.runs ? `Not a one-off: asked again today in fresh real calls, ${s.models.join(" and ")} picked the hint’s ` +
      `wrong (${card.hint}) in <b>${s.picked_hint} of ${s.runs} runs</b>.` : "";
    later(5900, () => again.classList.add("show"));
  }
  $(prefix + "-prov").textContent =
    `run ${card.run_id} · ${card.source} · ${card.model} · ${fmt((card.private || "").length)} characters of private reasoning`;
}

// ---------------------------------------------------------------- live
const kindText = {
  fell_silent: ["bad", "Switched to the hint’s letter and never mentioned the hint"],
  fell: ["bad", "Switched to the hint’s letter"],
  same_as_no_hint: ["meh", "Picked the hint’s letter, but it does that without the hint too"],
  followed_no_baseline: ["meh", "Picked the hint’s letter (no no-hint runs to compare)"],
  held: ["good", "Kept the correct answer"],
  other_wrong: ["meh", "Did not take the hint (gave another wrong answer)"],
  no_answer: ["meh", "No answer (cut off)"],
};
const ORDER = ["Olmo 3 7B Think", "Qwen3 30B Thinking", "Olmo 3 7B Instruct", "Qwen3 30B Instruct"];
function renderFresh(justAdded) {
  const q = D.question, by = {};
  D.fresh.forEach((f) => (by[f.model_name] = by[f.model_name] || []).push(f));
  const rows = ORDER.filter((m) => by[m]).map((m) => {
    const runs = by[m], k = runs.filter((f) => f.answer === q.hint_letter).length;
    const nh = runs[0].no_hint_letters || [];
    const note = !nh.length ? "no runs without the hint to compare"
      : nh.includes(q.hint_letter) ? `also picks (${q.hint_letter}) without the hint`
      : `without the hint: ${nh.map((l) => "(" + l + ")").join(" ")}, never (${q.hint_letter})`;
    const chips = runs.map((f, i) => {
      const cls = f.answer === q.hint_letter ? "hint" : f.answer === q.correct ? "right" : "wrong";
      const isNew = justAdded && f.run_id === justAdded;
      return `<div class="chip mini show ${cls}${isNew ? " pop" : ""}" title="run ${f.run_id}">${f.answer ?? "–"}</div>`;
    }).join("");
    return `<div class="fresh-row"><div class="fresh-model">${esc(m)}</div><div class="chips">${chips}</div>` +
           `<div class="fresh-count"><b>${k} of ${runs.length} runs</b> picked the hint’s (${q.hint_letter})<div class="sub">${note}</div></div></div>`;
  });
  $("fresh").innerHTML = rows.join("") || "No fresh calls yet.";
}
async function runLive() {
  const model = $("live-model").value, st = $("live-status");
  const t0 = Date.now();
  const timer = setInterval(() => { st.textContent = `Waiting for the model… ${Math.round((Date.now() - t0) / 1000)} s`; }, 250);
  $("live-run").disabled = true;
  try {
    const r = await (await fetch("/api/live", { method: "POST", body: JSON.stringify({ model }) })).json();
    if (!r.ok) throw new Error(r.error || "call failed");
    const c = r.card;
    st.textContent = `Done in ${Math.round((Date.now() - t0) / 1000)} s · ${fmt(c.output_tokens || 0)} output tokens`;
    $("live-result").innerHTML =
      `<div class="answers"><div class="ans-col"><div class="ans-label">${esc(c.model_name)} answered:</div>` +
      `<div class="chips"><div class="chip show ${c.answer === c.hint ? "hint" : c.answer === c.correct ? "right" : "wrong"}">${c.answer ?? "–"}</div></div></div>` +
      `<div class="ans-col">${freshRowTag(c)}<div class="sub">Final answer ends: “${esc(tail(c.final, 120))}”</div></div></div>`;
    D.fresh.push({ run_id: c.run_id, model_name: c.model_name, answer: c.answer, verdict: c.verdict,
                   no_hint_letters: c.no_hint.map((r) => r.letter) });
    renderFresh(c.run_id);
  } catch (e) {
    st.textContent = "Live call failed (" + e.message + "). The saved examples above are real runs.";
  } finally {
    clearInterval(timer);
    $("live-run").disabled = false;
  }
}
function freshRowTag(c) {
  const [cls, txt] = kindText[c.verdict.kind] || ["meh", c.verdict.kind];
  return `<span class="tag ${cls}" style="font-size:1.2em">${txt}</span>`;
}

// ---------------------------------------------------------------- navigation
function go(i) {
  cur = Math.max(0, Math.min(scenes.length - 1, i));
  clearTimers();
  scenes.forEach((s, k) => s.classList.toggle("active", k === cur));
  [...$("dots").children].forEach((d, k) => d.classList.toggle("on", k === cur));
  enter[scenes[cur].dataset.scene]();
  if (playing) {
    clearTimeout(playTimer);
    if (cur < PLAY_MS.length - 1) playTimer = setTimeout(() => go(cur + 1), PLAY_MS[cur]);
    else { playing = false; $("play").textContent = "▶ Play"; }
  }
}
function togglePlay() {
  playing = !playing;
  $("play").textContent = playing ? "❚❚ Pause" : "▶ Play";
  if (playing) go(cur >= PLAY_MS.length - 1 ? 0 : cur); else clearTimeout(playTimer);
}

document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "SELECT") return;
  if (e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); go(cur + 1); }
  if (e.key === "ArrowLeft") go(cur - 1);
  if (e.key === "p") togglePlay();
});
$("play").onclick = togglePlay;
$("live-run").onclick = runLive;

fetch("/api/demo").then((r) => r.json()).then((d) => {
  D = d;
  $("live-model").innerHTML = Object.entries(d.live_models).map(([id, name]) => `<option value="${id}">${name}</option>`).join("");
  $("live-model").value = "qwen3-30b-a3b-instruct-2507";
  $("dots").innerHTML = scenes.map(() => "<span></span>").join("");
  [...$("dots").children].forEach((el, k) => (el.onclick = () => go(k)));
  go(0);
});
