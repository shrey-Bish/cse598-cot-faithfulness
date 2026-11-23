/* The scratch pad's review-team flow: solver -> reviewer -> checker -> you, each step's recorded verdict, left to right.
   PAD_REVIEW.open(host, {entry, rows, counts, unpack}); PAD_REVIEW.close(). Counts come from DATA.pad.review (frozen,
   each with its path); nothing is computed here. The pipeline's rule: agents/run_team.py (lines 31-32) and
   agents/c15.py (line 18): a checker flag escalates the item and no answer ships, otherwise the reviewer's letter is
   the final output. Run names and paths appear only in hover titles. Marks come from marks.js; own timers. */
const PAD_REVIEW = (() => {
  const SEE = { answer_only: "the answer only", plus_explanation: "+ its explanation", plus_private: "+ its private reasoning", plus_tool_log: "+ the tool’s log", plus_tool_log_redacted: "+ the tool’s log, redacted" };
  const ORDER = Object.keys(SEE);
  let root = null, ids = [], st = null;
  const later = (ms, fn) => { if (INSTANT || REDUCE) fn(); else ids.push(setTimeout(fn, ms)); };
  const cut = (s, n) => (s.length > n ? s.slice(0, n).replace(/\s+\S*$/, "") + " …" : s);
  const tt = (r) => (r ? `${r.file}, line ${r.line}${r.rec ? ". " + r.rec : ""}` : "");

  function close() {
    ids.forEach(clearTimeout); ids = [];
    if (root) root.remove();
    root = null; st = null;
  }

  function open(host, ctx) {
    close();
    const { entry, rows, counts } = ctx, W = host.clientWidth || 1000, Hh = host.clientHeight || 600;
    const solver = rows.find((r) => r.kind === "solver"), checker = rows.find((r) => r.kind === "checker");
    const revs = rows.filter((r) => r.kind === "reviewer");
    root = H("div", { class: "prv" }, host);
    if (!solver) { H("div", { class: "prv-note", style: { top: "20px" } }, root, "No recorded solver run for this question."); return; }
    const models = [...new Set(revs.map((r) => r.m))];
    const first = models.includes("Olmo 3.1 32B Instruct") ? "Olmo 3.1 32B Instruct" : models[0];
    st = { rv: first, v: null };
    const ctl = H("div", { class: "prv-ctl" }, root), stage = H("div", { class: "prv-stage" }, root);
    const set = entry.set || solver.set;

    const variantsOf = (m) => ORDER.filter((v) => revs.some((r) => r.m === m && r.variant === v));
    function choose(parent, label, opts, value, pick) {
      const row = H("div", { class: "prv-row", role: "radiogroup", "aria-label": label }, parent, `<span class="lab">${label}</span>`);
      const box = H("div", { class: "opts" }, row);
      opts.forEach((o) => {
        const b = H("button", { type: "button", class: "prv-opt", role: "radio", "aria-checked": String(o.id === value) }, box, `<span class="bub"></span>${o.label}`);
        b.addEventListener("click", () => pick(o.id));
      });
    }
    function controls() {
      ctl.innerHTML = "";
      if (!models.length) return;
      choose(ctl, "Reviewer", models.map((m) => ({ id: m, label: m })), st.rv, (m) => { st.rv = m; st.v = null; render(); });
      choose(ctl, "It sees", variantsOf(st.rv).map((v) => ({ id: v, label: SEE[v] })), st.v, (v) => { st.v = v; render(); });
    }
    function textPanel(title, text) {
      const p = H("div", { class: "prv-text", role: "dialog", "aria-label": title }, root);
      const h = H("div", { class: "h" }, p, `<span>${title}</span><button type="button" class="xlink">Close</button>`);
      h.querySelector("button").addEventListener("click", () => p.remove());
      H("pre", {}, p).textContent = text;
    }
    const readBtn = (parent, y, label, title, load) => {
      const b = H("button", { type: "button", class: "xlink", style: { top: y + "px" } }, parent, label);
      b.addEventListener("click", async () => { const X = await ctx.unpack(load.x); textPanel(title, cut(load.fmt(X), 2200)); });
    };

    function render() {
      ids.forEach(clearTimeout); ids = [];
      const keep = root.querySelector(".prv-text"); if (keep) keep.remove();
      if (!st.v || !variantsOf(st.rv).includes(st.v)) {
        const vs = variantsOf(st.rv); st.v = vs.includes("plus_tool_log") ? "plus_tool_log" : vs[0];
      }
      controls();
      stage.innerHTML = "";
      const top = ctl.offsetHeight + 14;
      Object.assign(stage.style, { top: top + "px", height: Hh - top + "px" });
      const gap = 30, cw = (W - 3 * gap) / 4, ch = 395;
      const col = (i, title, hover) => {
        const p = H("div", { class: "prv-st", title: hover || "", style: { left: i * (cw + gap) + "px", width: cw + "px", height: ch + "px" } }, stage);
        H("div", { class: "t" }, p, title);
        return p;
      };
      const line = (p, y, html) => H("div", { class: "m", style: { top: y + "px" } }, p, html);
      const right = entry.right, rv = revs.find((r) => r.m === st.rv && r.variant === st.v);
      for (let i = 0; i < 3; i++) {
        const x = (i + 1) * (cw + gap) - gap + 3;
        penStroke(stage, [[x, 28], [x + gap - 8, 28]], { delay: 900 * (i + 1) - 250, pencil: true, color: "--pencil" });
        penStroke(stage, [[x + gap - 16, 21], [x + gap - 8, 28], [x + gap - 16, 35]], { delay: 900 * (i + 1) - 80, pencil: true, color: "--pencil" });
      }

      /* 1 the solver */
      const s1 = col(0, "The solver", tt(solver));
      line(s1, 46, `<span class="mu">${solver.m}, with the tool</span>`);
      line(s1, 118, `The tool said (${solver.tool_letter})${solver.tool_letter !== right ? ", the wrong letter" : ""}.`);
      writeText(s1, { x: 14, y: 172, text: `(${solver.L})`, size: 60, delay: 100 });
      writeText(s1, { x: 100, y: 190, text: solver.L === right ? "right" : "wrong", size: 38, red: true, delay: 500, dur: 0.4 });
      line(s1, 238, solver.L === solver.tool_letter ? "It followed the tool." : "It didn’t follow the tool.");
      if (solver.x) readBtn(s1, 290, "Read its reasoning", "The solver’s recorded text", { x: solver.x, fmt: (X) => X ? [X.reasoning, X.final].filter(Boolean).join("\n\n— final answer —\n") + (X.tool ? `\n\n— tool call —\n${JSON.stringify(X.tool.call)}\n— tool reply —\n${typeof X.tool.reply === "string" ? X.tool.reply : JSON.stringify(X.tool.reply)}` : "") : "(no text recorded)" });

      /* 2 the reviewer */
      const s2 = col(1, "The reviewer", tt(rv));
      if (rv) {
        const cnt = ((set === "c15" ? counts.c15 : counts.reviewers) || []).find((r) => r.name === st.rv), o = cnt && cnt[st.v];
        const verdict = rv.corrected ? "corrected it" : rv.L === rv.solver_L ? "deferred" : rv.L ? "changed it, still wrong" : "no letter";
        line(s2, 46, `<span class="mu">${rv.m} sees ${SEE[st.v]}</span>`);
        writeText(s2, { x: 14, y: 130, text: `(${rv.L || "?"})`, size: 60, delay: 900 + 100 });
        writeText(s2, { x: 100, y: 142, text: verdict, size: 38, red: true, delay: 900 + 500, dur: 0.5, width: cw - 112 });
        if (o) {
          const c = line(s2, 214, "");
          c.title = `${cnt.run ? cnt.run + ". " : ""}${o.path}`;
          later(900 + 900, () => { c.innerHTML = `<span style="font-family:var(--hand-font);color:var(--red);font-size:40px;line-height:1">${o.k} of ${o.n}</span><br>wrong tool answers corrected`; });
        } else line(s2, 214, `<span class="mu">No frozen count for this view.</span>`);
        if (rv.x) readBtn(s2, ch - 38, "Read its verdict", "The reviewer’s recorded verdict", { x: rv.x, fmt: (X) => (X && X.final) || "(no text recorded)" });
      } else line(s2, 60, "No recorded verdict for this view.");

      /* 3 the checker */
      const s3 = col(2, "The checker", tt(checker));
      const ck = counts.checker || {};
      line(s3, 46, `<span class="mu">solves again, without the tool</span>`);
      if (checker) {
        writeText(s3, { x: 14, y: 100, text: `(${checker.L || "?"})`, size: 60, delay: 1800 + 100 });
        stamp(s3, { x: 100, y: 112, text: checker.flag === true ? "Flagged" : checker.flag === false ? "Agrees" : "No flag recorded", delay: 1800 + 600 });
      } else line(s3, 100, "No checker record for this case.");
      const cl = line(s3, 190, "");
      const fmt = (o, w) => o ? `<div title="${o.path}">${w}: <b>${o.k} of ${o.n}</b></div>` : "";
      later(1800 + 900, () => { cl.innerHTML = fmt(ck.caught, "Caught") + fmt(ck.false_alarms, "False alarms") + fmt(ck.shipped, "Shipped wrong") + `<div class="mu">on its own 100 items</div>`; });

      /* 4 you */
      const s4 = col(3, "You get", "The pipeline’s rule: a flag escalates and no answer ships; otherwise the reviewer’s letter is the final output (agents/run_team.py, lines 31-32; agents/c15.py, line 18).");
      later(2700, () => {
        if (!checker || checker.flag == null) {
          line(s4, 46, "No flag recorded, so the rule can’t say what ships.");
        } else if (checker.flag) {
          stamp(s4, { x: 14, y: 60, text: "Escalated", delay: 0 });
          line(s4, 130, "The checker flagged it: escalated, so no answer ships.");
        } else if (rv) {
          line(s4, 46, "No flag, so the reviewer’s letter ships:");
          writeText(s4, { x: 14, y: 130, text: `(${rv.L || "?"})`, size: 60, delay: 100 });
          writeText(s4, { x: 100, y: 146, text: rv.L === right ? "right" : "wrong", size: 38, red: true, delay: 500, dur: 0.4 });
        } else line(s4, 46, "No flag, but no recorded review to ship.");
        line(s4, ch - 70, `<span class="mu">Right answer: (${right}).</span>`);
      });
      H("div", { class: "prv-note", style: { top: ch + 14 + "px" } }, stage, "Each step is a recorded run. Hover a step for its file and line.");
    }
    render();
  }
  return { open, close };
})();
