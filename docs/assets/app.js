/* --------------------------------------------------------------------------
   The Electrode Budget — front-end
   No build step, no chart library. Everything is drawn as SVG from the JSON
   bundle written by scripts/build_site.py.
   -------------------------------------------------------------------------- */
(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  // Useful for printing and for static screenshots: ?static=1 reveals every
  // section without waiting for the scroll observer.
  if (new URLSearchParams(window.location.search).get("static") === "1") {
    document.documentElement.classList.add("no-reveal");
  }

  const state = {
    taskId: "mi_leftright_22ch",
    protocol: "within_session",
    pipeline: "riemann_tslr",
    view: "score",
    metric: "accuracy",
    selectedSubset: null,
    detailTaskId: "mi_leftright_22ch",
    sleepView: "night",
  };

  let DATA = null;
  let SIGNALS = null;

  const STRATEGY_COLORS = {
    region: "var(--region)",
    distributed: "var(--distributed)",
    random: "var(--random)",
    wearable: "var(--wearable)",
    full: "var(--full)",
  };
  const ROLE_COLORS = {
    accent: "var(--accent)",
    accent2: "var(--accent-2)",
    muted: "var(--ink-3)",
    violet: "var(--violet)",
    coral: "var(--coral)",
    amber: "var(--amber)",
    indigo: "var(--indigo)",
    slate: "var(--slate)",
  };
  const TASK_ROLES = {
    mi_leftright_22ch: "accent",
    p300_8ch: "amber",
    ssvep_8ch: "violet",
    motor_execution_ear_vs_scalp: "coral",
    sleep_staging_local: "indigo",
    cvep_local: "slate",
  };

  const fmt = (v, d = 3) =>
    v === null || v === undefined || Number.isNaN(Number(v))
      ? "—"
      : Number(v).toFixed(d);
  const fmtSigned = (v, d = 3) =>
    v === null || v === undefined || Number.isNaN(Number(v))
      ? "—"
      : `${Number(v) >= 0 ? "+" : "−"}${Math.abs(Number(v)).toFixed(d)}`;
  const pct = (v, d = 1) => (v == null ? "—" : `${Number(v).toFixed(d)}%`);
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const escapeHTML = (s) =>
    String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

  // ------------------------------------------------------------------ boot
  document.addEventListener("DOMContentLoaded", init);

  async function init() {
    initTheme();
    initHeader();
    observeReveals();

    try {
      const [benchRes, sigRes] = await Promise.all([
        fetch("data/benchmark.json", { cache: "no-store" }),
        fetch("data/signals.json", { cache: "no-store" }),
      ]);
      if (!benchRes.ok) throw new Error(`benchmark.json: ${benchRes.status}`);
      DATA = await benchRes.json();
      SIGNALS = sigRes.ok ? await sigRes.json() : { signals: {}, errors: {} };
    } catch (err) {
      showLoadError(err);
      return;
    }

    $("#generated-date").textContent = DATA.generated || "—";
    state.taskId = DATA.tasks[0].id;
    state.detailTaskId = DATA.tasks[0].id;
    state.protocol = DATA.tasks[0].defaultProtocol;
    state.pipeline = DATA.tasks[0].defaultPipeline;
    applyQueryState();

    renderHero();
    renderTaskGrid();
    renderTaskTabs();
    renderTaskDetail(state.detailTaskId);
    renderExplorerControls();
    renderExplorer();
    renderFindings();
    renderCrossTask();
    renderControls();
    renderQuality();
    observeReveals();
  }

  function applyQueryState() {
    const p = new URLSearchParams(window.location.search);
    const wanted = p.get("task");
    if (wanted && getTask(wanted)) {
      state.taskId = wanted;
      state.detailTaskId = wanted;
    }
    const task = getTask(state.taskId);
    const protocol = p.get("protocol");
    const pipeline = p.get("pipeline");
    if (protocol && task.protocols.includes(protocol)) state.protocol = protocol;
    else state.protocol = task.defaultProtocol;
    if (pipeline && task.pipelines.includes(pipeline)) state.pipeline = pipeline;
    else state.pipeline = task.defaultPipeline;
    state.view = p.get("view") === "delta" ? "delta" : "score";
    state.metric =
      p.get("metric") === "itr" && task.id === "ssvep_8ch"
        ? "itr"
        : "accuracy";
    const detail = p.get("detail");
    if (detail && getTask(detail)) state.detailTaskId = detail;
  }

  function syncUrl() {
    if (new URLSearchParams(window.location.search).get("static") === "1") return;
    const p = new URLSearchParams();
    const current = new URLSearchParams(window.location.search);
    if (current.get("theme")) p.set("theme", current.get("theme"));
    p.set("task", state.taskId);
    p.set("protocol", state.protocol);
    p.set("pipeline", state.pipeline);
    p.set("view", state.view);
    if (state.taskId === "ssvep_8ch") p.set("metric", state.metric);
    const hash = window.location.hash || "";
    history.replaceState(null, "", `${window.location.pathname}?${p}${hash}`);
  }

  function showLoadError(err) {
    const box = document.createElement("div");
    box.className = "load-error";
    box.innerHTML = `
      <strong>Could not load the benchmark data.</strong>
      <p>${escapeHTML(err.message || String(err))}</p>
      <p>If you opened this file directly, run a local server instead:</p>
      <pre class="code-block">python -m http.server 8000 --directory docs</pre>`;
    $("#task-grid").replaceWith(box);
    console.error(err);
  }

  // ------------------------------------------------------------------ theme
  function initTheme() {
    const params = new URLSearchParams(window.location.search);
    const saved = localStorage.getItem("eegbench-theme");
    const prefersDark =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.dataset.theme =
      params.get("theme") || saved || (prefersDark ? "dark" : "light");
    const btn = $("#theme-toggle");
    btn.addEventListener("click", () => {
      const next =
        document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      localStorage.setItem("eegbench-theme", next);
      if (DATA) {
        renderHero();
        renderTaskGrid();
        renderTaskDetail(state.detailTaskId);
        renderExplorer();
        renderFindings();
        renderCrossTask();
        renderControls();
      }
    });
  }

  function initHeader() {
    const header = $("#site-header");
    const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  function observeReveals() {
    const nodes = $$(".reveal:not(.is-visible)");
    if (!("IntersectionObserver" in window)) {
      nodes.forEach((n) => n.classList.add("is-visible"));
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            obs.unobserve(entry.target);
          }
        }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
    );
    nodes.forEach((n) => obs.observe(n));
  }

  // ---------------------------------------------------------------- helpers
  const getTask = (id) => DATA.tasks.find((t) => t.id === id);
  const taskRows = (id) => DATA.rows.filter((r) => r.track === id);

  function rowsFor(id, protocol, pipeline) {
    return DATA.rows.filter(
      (r) =>
        r.track === id &&
        r.protocol === protocol &&
        r.pipeline === pipeline
    );
  }

  function rowFor(id, protocol, pipeline, subset) {
    return (
      DATA.rows.find(
        (r) =>
          r.track === id &&
          r.protocol === protocol &&
          r.pipeline === pipeline &&
          r.subset === subset &&
          !r.isRandom
      ) || null
    );
  }

  function referenceRow(rows) {
    return rows.find((r) => r.isFull) || rows.find((r) => r.subset === "scalp_6_k6") || null;
  }

  function taskChannels(id) {
    const set = new Set();
    taskRows(id).forEach((r) => (r.channels || []).forEach((c) => set.add(c)));
    return Array.from(set);
  }

  function bestReduced(rows) {
    const cand = rows.filter(
      (r) =>
        !r.isFull &&
        !r.isRandom &&
        r.k <= 8 &&
        ["region", "distributed", "wearable"].includes(r.strategy)
    );
    if (!cand.length) return referenceRow(rows);
    return cand.reduce((a, b) => (Number(a.score) >= Number(b.score) ? a : b));
  }

  function channelSet(rows) {
    const set = new Set();
    rows.forEach((r) => (r.channels || []).forEach((c) => set.add(c)));
    return set;
  }

  function itrFromScore(task, score) {
    if (!task.nClasses || !task.trialSeconds || score == null) return null;
    const n = Number(task.nClasses);
    const p = clamp(Number(score), 1e-6, 1 - 1e-6);
    const bits =
      Math.log2(n) +
      p * Math.log2(p) +
      (1 - p) * Math.log2((1 - p) / Math.max(n - 1, 1));
    return Math.max(bits, 0) * (60 / Number(task.trialSeconds));
  }

  function niceStep(span, count) {
    const raw = span / Math.max(count, 1);
    const mag = Math.pow(10, Math.floor(Math.log10(raw || 1)));
    const norm = (raw || 1) / mag;
    const step = norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10;
    return step * mag;
  }

  function niceTicks(min, max, count = 5) {
    if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
      return [min];
    }
    const step = niceStep(max - min, count - 1);
    const start = Math.ceil(min / step) * step;
    const out = [];
    for (let v = start; v <= max + step * 0.25; v += step) out.push(v);
    return out.length ? out : [min, max];
  }

  function groupBy(arr, key) {
    const map = new Map();
    arr.forEach((item) => {
      const k = item[key];
      if (!map.has(k)) map.set(k, []);
      map.get(k).push(item);
    });
    return map;
  }

  function subsetNameFromLabel(label) {
    return label
      .replace(" region", "")
      .toLowerCase()
      .replaceAll(" ", "-");
  }

  // --------------------------------------------------------------- head SVG
  function headSVG(channels, opts = {}) {
    const pos = DATA.positions || {};
    const cx = 160;
    const cy = 170;
    const R = 118;
    const primary = new Set(opts.primary || []);
    const secondary = new Set(opts.secondary || []);
    const secondaryColor = opts.secondaryColor || "var(--violet)";
    const all = (channels || []).filter((c) => pos[c]);
    const showLabels = opts.labels !== false && primary.size <= 12;
    const dense = all.length > 55;

    const toXY = (name) => {
      const [x, y] = pos[name];
      return [cx + x * R, cy - y * R];
    };

    const muted = [];
    const sec = [];
    const prim = [];
    all.forEach((c) => {
      if (primary.has(c)) prim.push(c);
      else if (secondary.has(c)) sec.push(c);
      else muted.push(c);
    });

    const dot = (name, cls, r) => {
      const [x, y] = toXY(name);
      const title = `<title>${escapeHTML(name)}</title>`;
      const style =
        cls === "secondary" ? ` style="--dot-secondary:${secondaryColor}"` : "";
      return `<circle class="head-dot ${cls}" cx="${x.toFixed(1)}" cy="${y.toFixed(
        1
      )}" r="${r}"${style}>${title}</circle>`;
    };

    const dots = [
      ...muted.map((c) => dot(c, "muted", dense ? 1.9 : 2.6)),
      ...sec.map((c) => dot(c, "secondary", dense ? 4.2 : 5)),
      ...prim.map((c) => dot(c, "primary", dense ? 4.2 : 5.4)),
    ].join("");

    const labels = showLabels
      ? prim
          .map((c) => {
            const [x, y] = toXY(c);
            return `<text class="head-label" x="${(x + 7).toFixed(1)}" y="${(
              y + 3
            ).toFixed(1)}">${escapeHTML(c)}</text>`;
          })
          .join("")
      : "";

    return `
      <svg viewBox="0 0 320 340" role="img" aria-label="${escapeHTML(
        opts.aria || "Top-down electrode map"
      )}">
        <path class="head-outline" d="M160 34c-55 0-96 38-96 87v42c0 56 43 101 96 101s96-45 96-101v-42c0-49-41-87-96-87Z"/>
        <path class="head-nose" d="M160 34 146 17h28l-14 17Z"/>
        <path class="head-ear" d="M62 142c-13 3-18 18-16 33 2 15 10 27 19 29 4-17 4-42-3-62Z"/>
        <path class="head-ear" d="M258 142c13 3 18 18 16 33-2 15-10 27-19 29-4-17-4-42 3-62Z"/>
        <circle class="head-ring" cx="160" cy="170" r="82"/>
        <circle class="head-ring" cx="160" cy="170" r="56"/>
        ${dots}
        ${labels}
      </svg>`;
  }

  function renderHero() {
    const task = getTask("motor_execution_ear_vs_scalp");
    if (!task) return;
    const channels = taskChannels(task.id);
    const rows = taskRows(task.id);
    const sens = rows.find((r) => r.subset === "region-sensorimotor_k8");
    const ear = rows.find((r) => r.subset === "wu2020_inear_k8");
    $("#hero-head").innerHTML = headSVG(channels, {
      primary: sens ? sens.channels : [],
      secondary: ear ? ear.channels : [],
      labels: true,
      aria: "Top-down map of a 115-channel scalp cap with eight sensorimotor and eight in-ear electrodes highlighted",
    });

    // Two mini heads in the explainer: count vs placement.
    const mi = taskRows("mi_leftright_22ch");
    const miSens = mi.find((r) => r.subset === "region-sensorimotor_k8");
    const miDist = mi.find((r) => r.subset === "distributed_k4");
    $("#mini-count").innerHTML = headSVG(taskChannels("mi_leftright_22ch"), {
      primary: miSens ? miSens.channels : [],
      secondary: miDist ? miDist.channels : [],
      secondaryColor: "var(--distributed)",
      labels: false,
      aria: "Motor imagery head map with 8 sensorimotor electrodes and 4 spread electrodes",
    });
    $("#mini-placement").innerHTML = headSVG(channels, {
      primary: sens ? sens.channels : [],
      secondary: ear ? ear.channels : [],
      labels: false,
      aria: "Motor execution head map with 8 scalp and 8 in-ear electrodes",
    });
  }

  // ----------------------------------------------------------- illustrations
  function illustrationSVG(type) {
    const a = (d, cls = "art-line") =>
      `<path class="${cls}" d="${d}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
    if (type === "mi") {
      const hand = (x) => `
        <circle cx="${x}" cy="86" r="9" class="art-soft art-line"/>
        ${[0, 1, 2, 3]
          .map(
            (i) =>
              `<path class="art-line" d="M${x - 6 + i * 4} 78v-8" stroke-linecap="round"/>`
          )
          .join("")}
        <path class="art-line" d="M${x + 8} 90c9 0 12-5 12-9" stroke-linecap="round"/>`;
      return `<svg viewBox="0 0 320 120" aria-hidden="true">
        <path class="art-head" d="M160 22c-22 0-35 16-35 35v15c0 23 16 38 35 38s35-15 35-38V57c0-19-13-35-35-35Z"/>
        <path class="art-head" d="M160 22 151 9h18l-9 13Z"/>
        <circle cx="146" cy="48" r="3.5" class="art-fill"/>
        <circle cx="174" cy="48" r="3.5" class="art-fill"/>
        <path class="art-accent art-dash" d="M67 84C88 75 112 68 137 61"/>
        <path class="art-accent art-dash" d="M253 84C232 75 208 68 183 61"/>
        <path class="art-accent-fill" d="m137 61-8-1 5 7 3-6Z"/>
        <path class="art-accent-fill" d="m183 61 8-1-5 7-3-6Z"/>
        ${hand(48)}
        ${hand(272)}
        <text x="48" y="112" text-anchor="middle" class="art-text">left hand</text>
        <text x="272" y="112" text-anchor="middle" class="art-text">right hand</text>
        <text x="160" y="112" text-anchor="middle" class="art-text">imagine</text>
      </svg>`;
    }
    if (type === "p300") {
      const cells = [];
      for (let r = 0; r < 3; r += 1) {
        for (let c = 0; c < 3; c += 1) {
          const x = 18 + c * 30;
          const y = 18 + r * 30;
          const on = r === 1 && c === 2;
          cells.push(
            `<rect x="${x}" y="${y}" width="24" height="24" rx="5" class="${
              on ? "art-accent-fill-soft" : "art-soft art-line"
            }" ${on ? 'stroke="var(--accent)"' : ""}/>`
          );
        }
      }
      return `<svg viewBox="0 0 320 120" aria-hidden="true">
        ${cells.join("")}
        <text x="72" y="112" text-anchor="middle" class="art-text">speller grid</text>
        <path class="art-line art-dash" d="M122 60h34"/>
        <path class="art-line" d="M162 85h128"/>
        <path class="art-accent" d="M162 85c18 0 18-16 34-16s16 20 32 20 16-16 30-16 16 8 34 8" stroke-width="2"/>
        <path class="art-text-fill" d="M228 58h34v3h-34z" opacity=".16"/>
        <text x="245" y="54" text-anchor="middle" class="art-text">P300</text>
        <text x="245" y="106" text-anchor="middle" class="art-text">time →</text>
      </svg>`;
    }
    if (type === "ssvep") {
      const tiles = [9.25, 11.25, 13.75, 14.75]
        .map((freq, i) => {
          const x = 66 + i * 58;
          const on = i === 2;
          const wave = [];
          for (let j = 0; j <= 30; j += 1) {
            const xx = x + 8 + j;
            const yy = 52 + Math.sin((j / 30) * Math.PI * (2 + (i + 1) * 0.7)) * 10;
            wave.push(`${j === 0 ? "M" : "L"}${xx.toFixed(1)} ${yy.toFixed(1)}`);
          }
          return `<g>
            <rect x="${x}" y="30" width="48" height="48" rx="8" class="${
            on ? "art-accent-fill-soft" : "art-soft art-line"
          }" ${on ? 'stroke="var(--accent)"' : ""}/>
            <path class="${on ? "art-accent" : "art-line"}" d="${wave.join(" ")}"/>
            <text x="${x + 24}" y="92" text-anchor="middle" class="art-text">${freq}</text>
          </g>`;
        })
        .join("");
      return `<svg viewBox="0 0 320 120" aria-hidden="true">
        <path class="art-line" d="M18 54c9-14 27-14 36 0-9 14-27 14-36 0Z"/>
        <circle cx="36" cy="54" r="6" class="art-fill"/>
        <path class="art-accent art-dash" d="M58 54h84"/>
        ${tiles}
        <text x="36" y="86" text-anchor="middle" class="art-text">look</text>
      </svg>`;
    }
    if (type === "motor") {
      return `<svg viewBox="0 0 320 120" aria-hidden="true">
        <path class="art-head" d="M98 22c-22 0-35 16-35 35v15c0 23 16 38 35 38s35-15 35-38V57c0-19-13-35-35-35Z"/>
        <path class="art-head" d="M98 22 89 9h18l-9 13Z"/>
        <path class="art-ear" d="M62 50c-8 2-11 11-10 20 1 9 6 16 12 17 3-10 3-25-2-37Z"/>
        <path class="art-ear" d="M134 50c8 2 11 11 10 20-1 9-6 16-12 17-3-10-3-25 2-37Z"/>
        <circle cx="86" cy="48" r="3.5" class="art-fill"/>
        <circle cx="110" cy="48" r="3.5" class="art-fill"/>
        <circle cx="62" cy="70" r="3.2" class="art-violet-fill"/>
        <circle cx="134" cy="70" r="3.2" class="art-violet-fill"/>
        <path class="art-accent art-dash" d="M152 60h42"/>
        <path class="art-accent-fill" d="m194 60-8-4v8l8-4Z"/>
        <circle cx="224" cy="58" r="13" class="art-soft art-line"/>
        <path class="art-line" d="M216 50v-9M222 49v-11M229 50v-9M234 54c6 2 6 9 0 12" stroke-linecap="round"/>
        <text x="224" y="92" text-anchor="middle" class="art-text">clench</text>
        <text x="62" y="112" text-anchor="middle" class="art-text">in-ear</text>
        <text x="98" y="112" text-anchor="middle" class="art-text">scalp</text>
        <text x="276" y="58" text-anchor="middle" class="art-text">L / R</text>
      </svg>`;
    }
    if (type === "sleep") {
      return `<svg viewBox="0 0 320 120" aria-hidden="true">
        <path class="art-amber-fill" d="M34 20a24 24 0 1 0 24 34 20 20 0 0 1-24-34Z"/>
        <circle cx="80" cy="26" r="1.5" class="art-fill"/>
        <circle cx="96" cy="16" r="1.2" class="art-fill"/>
        <circle cx="66" cy="12" r="1" class="art-fill"/>
        <rect x="42" y="76" width="104" height="26" rx="12" class="art-soft art-line"/>
        <circle cx="108" cy="68" r="20" class="art-soft art-line"/>
        <path class="art-line" d="M99 66c4 3 8 3 12 0" stroke-linecap="round"/>
        <path class="art-text-fill" d="M134 42h9l-9 11h9M148 30h7l-7 9h7" fill="none" stroke="var(--ink-3)" stroke-width="1.5" stroke-linejoin="round"/>
        <path class="art-accent" d="M182 104h18v-12h18v-7h18v-16h18v8h18v-12h18v22h18" stroke-width="2"/>
        <text x="182" y="116" class="art-text">night →</text>
      </svg>`;
    }
    if (type === "cvep") {
      const bits = [0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1];
      const blocks = bits
        .map(
          (b, i) =>
            `<rect x="${18 + i * 14}" y="18" width="10" height="10" rx="2" class="${
              b ? "art-violet-fill-soft" : "art-soft art-line"
            }"/>`
        )
        .join("");
      return `<svg viewBox="0 0 320 120" aria-hidden="true">
        ${blocks}
        <text x="18" y="44" class="art-text">stimulus code</text>
        <path class="art-line" d="M18 92h284"/>
        <path class="art-violet" d="M18 92c10 0 10-9 20-9s10 16 20 16 10-22 20-22 10 18 20 18 10-24 20-24 10 20 20 20 10-14 20-14 10 12 20 12 10-18 20-18 10 10 20 10 10-6 20-6 10 4 20 4" stroke-width="2"/>
        <text x="160" y="112" text-anchor="middle" class="art-text">EEG response</text>
      </svg>`;
    }
    return "";
  }

  // --------------------------------------------------------------- sparkline
  function sparklineSVG(sig) {
    if (!sig) return "";
    const w = 96;
    const h = 30;
    const pad = 2;
    const pathFor = (values, min, max) => {
      if (!values || values.length < 2) return "";
      const span = max - min || 1;
      return values
        .map((v, i) => {
          const x = pad + (i / (values.length - 1)) * (w - pad * 2);
          const y = h - pad - ((v - min) / span) * (h - pad * 2);
          return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
        })
        .join(" ");
    };
    if (sig.type === "trace" || sig.type === "erp" || sig.type === "spectrum") {
      const values = sig.type === "spectrum" ? sig.power : sig.series[0].values;
      const min = Math.min(...values);
      const max = Math.max(...values);
      return `<svg class="task-spark" viewBox="0 0 ${w} ${h}" aria-hidden="true"><path d="${pathFor(
        values,
        min,
        max
      )}" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>`;
    }
    if (sig.type === "hypnogram") {
      const values = sig.stages;
      const min = 1;
      const max = 5;
      const stepPath = values
        .map((v, i) => {
          const x0 = pad + (i / (values.length - 1)) * (w - pad * 2);
          const y = h - pad - ((v - min) / (max - min)) * (h - pad * 2);
          return `${i === 0 ? "M" : "L"}${x0.toFixed(1)} ${y.toFixed(1)}`;
        })
        .join(" ");
      return `<svg class="task-spark" viewBox="0 0 ${w} ${h}" aria-hidden="true"><path d="${stepPath}" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>`;
    }
    if (sig.type === "bars") {
      const max = Math.max(...sig.items.map((i) => i.value));
      const min = Math.min(...sig.items.map((i) => i.value));
      return `<svg class="task-spark" viewBox="0 0 ${w} ${h}" aria-hidden="true">${sig.items
        .slice(0, 6)
        .map((item, i) => {
          const bw = (w - pad * 2) / 8;
          const bh = Math.max(2, ((item.value - min + 0.02) / (max - min + 0.02)) * (h - pad * 2));
          return `<rect x="${pad + i * (bw + 2)}" y="${h - pad - bh}" width="${bw}" height="${bh}" rx="1.5" fill="currentColor" opacity="${item.group === "ear" ? 0.35 : 0.8}"/>`;
        })
        .join("")}</svg>`;
    }
    if (sig.type === "trace_code") {
      const values = sig.series[0].values;
      const min = Math.min(...values);
      const max = Math.max(...values);
      return `<svg class="task-spark" viewBox="0 0 ${w} ${h}" aria-hidden="true"><path d="${pathFor(
        values,
        min,
        max
      )}" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>`;
    }
    return "";
  }

  // --------------------------------------------------------------- task grid
  function renderTaskGrid() {
    if (!DATA) return;
    const grid = $("#task-grid");
    grid.innerHTML = DATA.tasks
      .map((task) => {
        const sig = SIGNALS.signals[task.signalKey];
        const status = task.status === "exploratory"
          ? '<span class="task-chip exploratory">exploratory</span>'
          : `<span class="task-chip">${escapeHTML(task.kicker)}</span>`;
        return `<button class="task-card ${
          task.id === state.detailTaskId ? "is-active" : ""
        }" data-task-id="${task.id}" type="button">
          <div class="task-card-top">
            <span class="task-index">${String(task.order).padStart(2, "0")}</span>
            ${status}
          </div>
          <div class="task-art">${illustrationSVG(task.illustration)}</div>
          <h3>${escapeHTML(task.name)}</h3>
          <p class="task-result">${escapeHTML(task.headline)}</p>
          <div class="task-card-foot">
            <span>${escapeHTML(task.nLabel)} · ${escapeHTML(task.datasetName)}</span>
            ${sparklineSVG(sig)}
          </div>
        </button>`;
      })
      .join("");

    $$(".task-card", grid).forEach((card) => {
      card.addEventListener("click", () => {
        const id = card.dataset.taskId;
        state.detailTaskId = id;
        setExplorerTask(id);
        renderTaskGrid();
        renderTaskTabs();
        renderTaskDetail(id);
        renderExplorer();
        const detail = $("#task-detail");
        if (detail) detail.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  function renderTaskTabs() {
    if (!DATA) return;
    $("#task-tabs").innerHTML = DATA.tasks
      .map(
        (task) => `<button class="task-tab ${
          task.id === state.detailTaskId ? "is-active" : ""
        }" type="button" role="tab" aria-selected="${
          task.id === state.detailTaskId
        }" data-task-id="${task.id}">
          <span class="task-tab-dot"></span>${escapeHTML(task.short)}
        </button>`
      )
      .join("");
    $$(".task-tab", $("#task-tabs")).forEach((btn) => {
      btn.addEventListener("click", () => {
        state.detailTaskId = btn.dataset.taskId;
        renderTaskTabs();
        renderTaskDetail(state.detailTaskId);
        renderTaskGrid();
      });
    });
  }

  // ------------------------------------------------------------- task detail
  function renderTaskDetail(id) {
    if (!DATA) return;
    const task = getTask(id);
    const panel = $("#task-panel");
    if (!task) return;
    const sig = SIGNALS.signals[task.signalKey];
    const stats = task.stats || {};
    const resultStats = [];

    if (stats.reference != null) {
      resultStats.push(`<div class="result-stat"><span>${escapeHTML(
        stats.referenceLabel || "Reference"
      )}</span><strong>${fmt(stats.reference)}</strong><span>${escapeHTML(
        task.metricLabel
      )} · ${stats.referenceK} ch</span></div>`);
    }
    if (stats.best != null) {
      resultStats.push(`<div class="result-stat"><span>${escapeHTML(
        stats.bestLabel
      )}</span><strong>${fmt(stats.best)}</strong><span>${stats.bestK} ch</span></div>`);
      resultStats.push(
        `<div class="result-stat result-delta ${
          stats.delta < 0 ? "negative" : "positive"
        }"><span>Δ vs ${escapeHTML(stats.referenceLabel || "reference")}</span><strong>${fmtSigned(
          stats.delta
        )}</strong><span>${escapeHTML(task.metricLabel)}</span></div>`
      );
    } else {
      resultStats.push(
        `<div class="result-stat"><span>Reduced montage</span><strong>not tested</strong><span>only the full cap exists</span></div>`
      );
    }
    if (task.id === "ssvep_8ch" && stats.referenceItr != null) {
      resultStats.push(
        `<div class="result-stat"><span>Information rate</span><strong>${fmt(
          stats.bestItr,
          1
        )}</strong><span>${fmt(stats.referenceItr, 1)} bits/min at full cap</span></div>`
      );
    }

    const facts = [
      ["Dataset", task.datasetName],
      ["Participants", task.subjects],
      ["Signal", `${task.channels} · ${task.sfreq}`],
      ["Trials / windows", Number(task.examples).toLocaleString("en-US")],
      ["Metric", `${task.metricLabel} · chance ${fmt(task.chance, 3)}`],
      ["Default decoder", task.pipelines
        .map((p) => (p === task.defaultPipeline ? pipelineLabel(p) : null))
        .filter(Boolean)
        .join(", ")],
    ];

    const usingSleepWindow =
      task.signalKey === "sleep" && sig?.trace && state.sleepView === "window";
    const signalTitle = usingSleepWindow
      ? "30 s of stage N3"
      : sig?.title || task.signalTitle;
    const signalCaption = usingSleepWindow
      ? "One 30-second window from the same night, shown as voltage over time. The model turns each window into band-power features before scoring it."
      : sig?.note || task.signalCaption;
    const signalSource = sig?.source || `${task.datasetName}, representative recording`;

    const hasSleepWindow = task.signalKey === "sleep" && sig?.trace;
    const toggle =
      hasSleepWindow
        ? `<div class="signal-toggle" id="sleep-toggle" role="group" aria-label="Sleep view">
            <button type="button" data-sleep="night" class="${
              state.sleepView === "night" ? "is-active" : ""
            }">Night</button>
            <button type="button" data-sleep="window" class="${
              state.sleepView === "window" ? "is-active" : ""
            }">30 s window</button>
          </div>`
        : "";

    panel.innerHTML = `
      <div class="task-narrative">
        <p class="task-kicker">${escapeHTML(task.kicker)}</p>
        <h3>${escapeHTML(task.name)}</h3>
        <p>${escapeHTML(task.person)}</p>
        <p><strong>What the decoder sees.</strong> ${escapeHTML(task.computer)}</p>
        <p class="why"><strong>Why it is here.</strong> ${escapeHTML(task.why)}</p>
        <div class="task-facts">
          ${facts
            .map(
              ([k, v]) =>
                `<div class="task-fact"><span>${escapeHTML(k)}</span><strong>${escapeHTML(
                  v
                )}</strong></div>`
            )
            .join("")}
        </div>
        <div class="task-result-strip">${resultStats.join(
          '<span class="result-arrow">→</span>'
        )}</div>
      </div>
      <div class="task-signal">
        <div class="task-signal-head">
          <h4>${escapeHTML(signalTitle)}</h4>
          ${toggle}
        </div>
        <div class="signal-chart" id="task-signal-chart"></div>
        <p class="scroll-hint">Scroll sideways for the full chart →</p>
        <p class="signal-caption">${escapeHTML(signalCaption || "")}</p>
        <p class="signal-source">${escapeHTML(signalSource || "")}</p>
      </div>`;

    const chartEl = $("#task-signal-chart");
    if (!sig) {
      chartEl.innerHTML = `<p class="signal-caption">Signal illustration not generated. Run <code>scripts/build_site_signals.py</code> with the raw datasets available.</p>`;
    } else {
      const current =
        state.sleepView === "window" && sig.trace
          ? {
              ...sig.trace,
              title: "30 s of stage N3",
              note:
                "One 30-second window from the same night, shown as voltage over time. The model turns each window into band-power features before scoring it.",
              source: sig.source,
            }
          : sig;
      renderSignalChart(chartEl, current, task);
    }

    const toggleEl = $("#sleep-toggle");
    if (toggleEl) {
      $$("button", toggleEl).forEach((btn) => {
        btn.addEventListener("click", () => {
          state.sleepView = btn.dataset.sleep;
          renderTaskDetail(id);
        });
      });
    }
  }

  function pipelineLabel(key) {
    const row = DATA.rows.find((r) => r.pipeline === key);
    return row ? row.pipelineLabel : key;
  }

  // -------------------------------------------------------------- signal plots
  function renderSignalChart(container, sig, task) {
    container.innerHTML = "";
    if (!sig) return;
    if (sig.type === "bars") {
      mountBarChart(container, {
        items: sig.items,
        chance: sig.chance,
        xLabel: sig.unit,
        yLabel: "",
        groupColors: {
          scalp: "var(--accent)",
          ear: "var(--violet)",
        },
        height: 290,
      });
      return;
    }
    if (sig.type === "hypnogram") {
      mountXYChart(container, {
        series: [
          {
            name: "Stage",
            x: sig.hours,
            y: sig.stages,
            role: "indigo",
            step: true,
          },
        ],
        xLabel: sig.xLabel,
        yLabel: "",
        yTicks: [1, 2, 3, 4, 5],
        yTickLabels: sig.stageLabels,
        yDomain: [0.5, 5.5],
        invertY: true,
        step: true,
        height: 300,
        stageBands: true,
        tooltipX: (x) => `${Number(x).toFixed(1)} h`,
        tooltipY: (y) => sig.stageLabels[Math.round(y)] || `stage ${y}`,
        legend: false,
      });
      return;
    }
    if (sig.type === "trace_code") {
      mountXYChart(container, {
        series: sig.series.map((s) => ({
          name: s.name,
          x: s.t,
          y: s.values,
          role: s.role,
        })),
        xLabel: sig.xLabel,
        yLabel: sig.unit,
        height: 240,
        zeroLine: true,
        legend: true,
      });
      const strip = codeStripSVG(sig);
      if (strip) container.insertAdjacentHTML("beforeend", strip);
      return;
    }
    if (sig.type === "spectrum") {
      mountXYChart(container, {
        series: [
          { name: "Power", x: sig.freq, y: sig.power, role: "violet" },
        ],
        xLabel: sig.xLabel,
        yLabel: sig.unit,
        height: 300,
        highlightX: sig.highlightFreqs || [],
        zeroLine: false,
        legend: false,
      });
      return;
    }
    // trace / erp: series share the x array
    const series = sig.series.map((s) => ({
      name: s.name,
      x: s.t,
      y: s.values,
      role: s.role,
    }));
    mountXYChart(container, {
      series,
      xLabel: sig.xLabel,
      yLabel: sig.unit,
      height: 300,
      zeroLine: true,
      highlight: sig.highlight,
      legend: true,
    });
  }

  function codeStripSVG(sig) {
    if (!sig.code) return "";
    const width = 760;
    const height = 54;
    const m = { l: 58, r: 22, t: 4, b: 16 };
    const xs = sig.code.t;
    const xMin = xs[0];
    const xMax = xs[xs.length - 1];
    const x = (v) =>
      m.l + ((v - xMin) / (xMax - xMin || 1)) * (width - m.l - m.r);
    const vals = sig.code.values;
    const rects = vals
      .map((v, i) => {
        if (i === 0) return "";
        const x0 = x(xs[i - 1]);
        const x1 = x(xs[i]);
        return `<rect x="${x0.toFixed(1)}" y="${m.t + 12}" width="${Math.max(
          x1 - x0,
          0.8
        ).toFixed(1)}" height="16" class="${v ? "on" : ""}"/>`;
      })
      .join("");
    return `<svg viewBox="0 0 ${width} ${height}" class="chart-svg code-strip" role="img" aria-label="Stimulus code for one c-VEP trial">
      <text x="${m.l}" y="10" class="axis-label">stimulus code</text>
      ${rects}
    </svg>`;
  }

  // --------------------------------------------------------- generic XY chart
  function mountXYChart(container, opts) {
    const width = 760;
    const height = opts.height || 300;
    const m = { l: 58, r: 22, t: 20, b: 42 };
    const plotW = width - m.l - m.r;
    const plotH = height - m.t - m.b;
    const series = opts.series
      .map((s) => ({
        ...s,
        x: s.x.map(Number),
        y: s.y.map(Number),
      }))
      .filter((s) => s.x.length && s.y.length);

    const allX = series.flatMap((s) => s.x);
    const allY = series.flatMap((s) => s.y);
    let xMin = opts.xDomain ? opts.xDomain[0] : Math.min(...allX);
    let xMax = opts.xDomain ? opts.xDomain[1] : Math.max(...allX);
    let yMin = opts.yDomain ? opts.yDomain[0] : Math.min(...allY);
    let yMax = opts.yDomain ? opts.yDomain[1] : Math.max(...allY);
    if (opts.yDomain) {
      [yMin, yMax] = opts.yDomain;
    } else {
      const pad = (yMax - yMin || 1) * 0.12;
      yMin -= pad;
      yMax += pad;
    }
    if (opts.xDomain) [xMin, xMax] = opts.xDomain;
    const xScale = opts.xScale === "log" ? (v) => Math.log2(v) : (v) => v;
    const xsMin = xScale(xMin);
    const xsMax = xScale(xMax);
    const x = (v) => m.l + ((xScale(v) - xsMin) / (xsMax - xsMin || 1)) * plotW;
    const y = (v) => {
      const t = (v - yMin) / (yMax - yMin || 1);
      return opts.invertY ? m.t + t * plotH : m.t + (1 - t) * plotH;
    };

    const xTicks = opts.xTicks || niceTicks(xMin, xMax, 6);
    const yTicks = opts.yTicks || niceTicks(yMin, yMax, 5);
    const fmtX = opts.xTickFormat || ((v) => (Math.abs(v) >= 10 ? v.toFixed(0) : v.toFixed(1)));
    const fmtY = opts.yTickFormat || ((v) => (Math.abs(v) >= 10 ? v.toFixed(0) : v.toFixed(2)));

    const gridX = xTicks
      .map(
        (v) =>
          `<line class="grid-line" x1="${x(v).toFixed(1)}" y1="${m.t}" x2="${x(
            v
          ).toFixed(1)}" y2="${m.t + plotH}"/>`
      )
      .join("");
    const gridY = yTicks
      .map(
        (v) =>
          `<line class="grid-line" x1="${m.l}" y1="${y(v).toFixed(1)}" x2="${
            m.l + plotW
          }" y2="${y(v).toFixed(1)}"/>`
      )
      .join("");
    const xLabels = xTicks
      .map(
        (v) =>
          `<text x="${x(v).toFixed(1)}" y="${m.t + plotH + 16}" text-anchor="middle">${escapeHTML(
            fmtX(v)
          )}</text>`
      )
      .join("");
    const yLabels = yTicks
      .map((v) => {
        const label =
          opts.yTickLabels && opts.yTickLabels[v] != null
            ? opts.yTickLabels[v]
            : fmtY(v);
        return `<text x="${m.l - 9}" y="${(y(v) + 3.5).toFixed(
          1
        )}" text-anchor="end">${escapeHTML(String(label))}</text>`;
      })
      .join("");

    const highlight =
      opts.highlight && opts.highlight.length === 2
        ? `<rect class="highlight-band" x="${x(opts.highlight[0]).toFixed(
            1
          )}" y="${m.t}" width="${(
            x(opts.highlight[1]) - x(opts.highlight[0])
          ).toFixed(1)}" height="${plotH}"/>`
        : "";
    const highlightX = (opts.highlightX || [])
      .map(
        (v) =>
          `<line class="zero-line" x1="${x(v).toFixed(1)}" y1="${m.t}" x2="${x(
            v
          ).toFixed(1)}" y2="${m.t + plotH}" stroke-dasharray="3 4" opacity=".6"/>`
      )
      .join("");
    const stageBands =
      opts.stageBands && opts.yTickLabels
        ? yTicks
            .map(
              (v, i) =>
                `<rect x="${m.l}" y="${y(v + 0.5).toFixed(1)}" width="${plotW}" height="${Math.abs(
                  y(v - 0.5) - y(v + 0.5)
                ).toFixed(1)}" fill="${
                  i % 2 ? "var(--bg-elev)" : "var(--bg-soft)"
                }" opacity=".45"/>`
            )
            .join("")
        : "";
    const zeroLine =
      opts.zeroLine && yMin < 0 && yMax > 0
        ? `<line class="zero-line" x1="${m.l}" y1="${y(0).toFixed(1)}" x2="${
            m.l + plotW
          }" y2="${y(0).toFixed(1)}"/>`
        : "";
    const refLine =
      opts.referenceY != null
        ? `<line class="reference-line" x1="${m.l}" y1="${y(
            opts.referenceY
          ).toFixed(1)}" x2="${m.l + plotW}" y2="${y(
            opts.referenceY
          ).toFixed(1)}"/>
           <text class="ref-label" x="${m.l + plotW - 2}" y="${(
            y(opts.referenceY) - 6
          ).toFixed(1)}" text-anchor="end">${escapeHTML(
            opts.referenceLabel || "full cap"
          )}</text>`
        : "";

    const paths = series
      .map((s) => {
        const color = ROLE_COLORS[s.role] || "var(--accent)";
        let d = "";
        for (let i = 0; i < s.x.length; i += 1) {
          const px = x(s.x[i]);
          const py = y(s.y[i]);
          if (i === 0) {
            d += `M${px.toFixed(1)} ${py.toFixed(1)}`;
          } else if (opts.step || s.step) {
            d += ` L${px.toFixed(1)} ${y(s.y[i - 1]).toFixed(1)} L${px.toFixed(
              1
            )} ${py.toFixed(1)}`;
          } else {
            d += ` L${px.toFixed(1)} ${py.toFixed(1)}`;
          }
        }
        const points = opts.showPoints
          ? s.x
              .map(
                (px, i) =>
                  `<circle cx="${x(px).toFixed(1)}" cy="${y(s.y[i]).toFixed(
                    1
                  )}" r="3.2" fill="${color}" opacity=".9"/>`
              )
              .join("")
          : "";
        return `<path class="series-line" d="${d}" stroke="${color}"/>${points}`;
      })
      .join("");

    const svg = `<svg viewBox="0 0 ${width} ${height}" class="chart-svg" role="img" aria-label="${escapeHTML(
      opts.aria || "Line chart"
    )}">
      ${stageBands}
      ${gridY}
      ${gridX}
      ${highlight}
      ${highlightX}
      ${zeroLine}
      ${refLine}
      <line class="axis-line" x1="${m.l}" y1="${m.t + plotH}" x2="${
      m.l + plotW
    }" y2="${m.t + plotH}"/>
      <line class="axis-line" x1="${m.l}" y1="${m.t}" x2="${m.l}" y2="${
      m.t + plotH
    }"/>
      ${yLabels}
      ${xLabels}
      <text class="axis-label" x="${m.l + plotW / 2}" y="${height - 5}" text-anchor="middle">${escapeHTML(
      opts.xLabel || ""
    )}</text>
      <text class="axis-label" x="13" y="${m.t + plotH / 2}" text-anchor="middle" transform="rotate(-90 13 ${
      m.t + plotH / 2
    })">${escapeHTML(opts.yLabel || "")}</text>
      ${paths}
      <g class="crosshair-group" style="display:none">
        <line class="crosshair" x1="0" y1="${m.t}" x2="0" y2="${m.t + plotH}"/>
        ${series
          .map(
            (s) =>
              `<circle r="4" fill="${ROLE_COLORS[s.role] || "var(--accent)"}" class="crosshair-dot"/>`
          )
          .join("")}
      </g>
      <rect class="overlay" x="${m.l}" y="${m.t}" width="${plotW}" height="${plotH}" fill="transparent"/>
    </svg>`;
    container.innerHTML = svg;

    if (opts.legend) {
      container.insertAdjacentHTML(
        "beforeend",
        `<div class="chart-legend">${series
          .map(
            (s) =>
              `<span class="legend-item"><span class="legend-dot" style="--dot:${
                ROLE_COLORS[s.role] || "var(--accent)"
              }"></span>${escapeHTML(s.name)}</span>`
          )
          .join("")}</div>`
      );
    }

    attachCrosshair(container, {
      width,
      height,
      m,
      plotW,
      plotH,
      x,
      y,
      series,
      xMin,
      xMax,
      xLabel: opts.xLabel,
      tooltipX: opts.tooltipX,
      tooltipY: opts.tooltipY,
    });
  }

  function attachCrosshair(container, info) {
    const svg = $("svg", container);
    if (!svg) return;
    const group = $(".crosshair-group", svg);
    const overlay = $(".overlay", svg);
    if (!group || !overlay) return;
    const tooltip = ensureTooltip(container);
    const { width, height, m, plotW, plotH, x, y, series } = info;

    let hideTimer = null;
    const hide = () => {
      group.style.display = "none";
      tooltip.classList.remove("is-visible");
    };
    overlay.addEventListener("pointerleave", () => {
      hideTimer = setTimeout(hide, 60);
    });
    overlay.addEventListener("pointerenter", () => clearTimeout(hideTimer));
    overlay.addEventListener("pointermove", (ev) => {
      const rect = svg.getBoundingClientRect();
      const sx = ((ev.clientX - rect.left) / rect.width) * width;
      if (sx < m.l || sx > m.l + plotW) {
        hide();
        return;
      }
      // The first series sets the shared x cursor. For series with their own
      // x values, each dot is placed at its nearest sample.
      const primary = series[0];
      let idx = 0;
      let best = Infinity;
      primary.x.forEach((v, i) => {
        const d = Math.abs(x(v) - sx);
        if (d < best) {
          best = d;
          idx = i;
        }
      });
      const cursorX = x(primary.x[idx]);
      const line = $("line", group);
      line.setAttribute("x1", cursorX);
      line.setAttribute("x2", cursorX);
      const dots = $$(".crosshair-dot", group);
      group.style.display = "";
      const rows = [];
      series.forEach((s, si) => {
        let j = 0;
        let bd = Infinity;
        s.x.forEach((v, i) => {
          const d = Math.abs(x(v) - cursorX);
          if (d < bd) {
            bd = d;
            j = i;
          }
        });
        const dot = dots[si];
        if (dot) {
          dot.setAttribute("cx", x(s.x[j]));
          dot.setAttribute("cy", y(s.y[j]));
        }
        rows.push({
          name: s.name,
          color: ROLE_COLORS[s.role] || "var(--accent)",
          value: info.tooltipY ? info.tooltipY(s.y[j]) : fmt(s.y[j], 2),
        });
      });
      const xText = info.tooltipX
        ? info.tooltipX(primary.x[idx])
        : fmt(primary.x[idx], Math.abs(primary.x[idx]) >= 10 ? 0 : 2);
      showTooltip(container, tooltip, xText, rows, ev);
    });
  }

  // --------------------------------------------------------------- bar chart
  function mountBarChart(container, opts) {
    const width = 760;
    const height = opts.height || 300;
    const m = { l: 86, r: 48, t: 22, b: 40 };
    const plotW = width - m.l - m.r;
    const plotH = height - m.t - m.b;
    const items = opts.items || [];
    const values = items.map((i) => Number(i.value));
    const chance = Number(opts.chance ?? 0.5);
    const lo = Math.min(...values, chance);
    const hi = Math.max(...values, chance);
    const pad = (hi - lo || 1) * 0.18;
    const xMin = opts.xDomain ? opts.xDomain[0] : lo - pad;
    const xMax = opts.xDomain ? opts.xDomain[1] : hi + pad;
    const x = (v) => m.l + ((v - xMin) / (xMax - xMin || 1)) * plotW;
    const rowH = plotH / Math.max(items.length, 1);
    const barH = Math.min(22, rowH * 0.46);
    const ticks = niceTicks(xMin, xMax, 5);

    const grid = ticks
      .map(
        (v) =>
          `<line class="grid-line" x1="${x(v).toFixed(1)}" y1="${m.t}" x2="${x(
            v
          ).toFixed(1)}" y2="${m.t + plotH}"/>`
      )
      .join("");
    const tickLabels = ticks
      .map(
        (v) =>
          `<text x="${x(v).toFixed(1)}" y="${m.t + plotH + 16}" text-anchor="middle">${fmt(
            v,
            2
          )}</text>`
      )
      .join("");
    const chanceLine = `<line class="chance-line" x1="${x(chance).toFixed(
      1
    )}" y1="${m.t}" x2="${x(chance).toFixed(1)}" y2="${m.t + plotH}"/>
      <text class="chance-label" x="${(x(chance) + 4).toFixed(1)}" y="${
      m.t - 6
    }">chance</text>`;

    const bars = items
      .map((item, i) => {
        const cy = m.t + rowH * i + rowH / 2;
        const yTop = cy - barH / 2;
        const color =
          (opts.groupColors && opts.groupColors[item.group]) || "var(--accent)";
        const v = Number(item.value);
        const x0 = x(Math.min(v, chance));
        const x1 = x(Math.max(v, chance));
        const barX = v >= chance ? x(chance) : x(v);
        const barW = Math.abs(x(v) - x(chance));
        const err =
          item.sd != null
            ? `<line class="error-bar" x1="${x(v - item.sd).toFixed(
                1
              )}" y1="${cy}" x2="${x(v + item.sd).toFixed(1)}" y2="${cy}" stroke="${color}"/>`
            : "";
        return `<g>
          <text x="${m.l - 10}" y="${cy + 3.5}" text-anchor="end">${escapeHTML(
          item.label
        )}</text>
          <rect x="${barX.toFixed(1)}" y="${yTop.toFixed(1)}" width="${Math.max(
          barW,
          1
        ).toFixed(1)}" height="${barH}" rx="4" fill="${color}" opacity=".82"/>
          ${err}
          <text x="${(x(v) + 7).toFixed(1)}" y="${cy + 3.5}" fill="var(--ink-2)" font-size="10">${fmt(
          v,
          3
        )}</text>
          <rect class="bar-hit" data-label="${escapeHTML(item.label)}" data-value="${v}" data-sd="${
          item.sd ?? ""
        }" x="${m.l}" y="${cy - rowH / 2}" width="${plotW}" height="${rowH}" fill="transparent"/>
        </g>`;
      })
      .join("");

    container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" class="chart-svg" role="img" aria-label="${escapeHTML(
      opts.aria || "Bar chart"
    )}">
      ${grid}
      ${tickLabels}
      <line class="axis-line" x1="${m.l}" y1="${m.t + plotH}" x2="${
      m.l + plotW
    }" y2="${m.t + plotH}"/>
      ${chanceLine}
      ${bars}
      <text class="axis-label" x="${m.l + plotW / 2}" y="${height - 4}" text-anchor="middle">${escapeHTML(
      opts.xLabel || ""
    )}</text>
    </svg>`;

    const tooltip = ensureTooltip(container);
    $$(".bar-hit", container).forEach((hit) => {
      hit.addEventListener("pointermove", (ev) => {
        const rows = [
          {
            name: "score",
            color: "var(--accent)",
            value: fmt(Number(hit.dataset.value), 3),
          },
        ];
        if (hit.dataset.sd) {
          rows.push({
            name: "sd",
            color: "var(--ink-3)",
            value: fmt(Number(hit.dataset.sd), 3),
          });
        }
        showTooltip(container, tooltip, hit.dataset.label, rows, ev);
      });
      hit.addEventListener("pointerleave", () => tooltip.classList.remove("is-visible"));
    });
  }

  // ---------------------------------------------------------------- tooltip
  function ensureTooltip(container) {
    let tip = $(".chart-tooltip", container);
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "chart-tooltip";
      container.appendChild(tip);
    }
    return tip;
  }

  function showTooltip(container, tip, title, rows, ev) {
    tip.innerHTML = `<strong>${escapeHTML(title)}</strong>${rows
      .map(
        (r) =>
          `<div class="tt-row"><span class="tt-dot" style="--tt:${
            r.color || "var(--accent)"
          }"></span><span>${escapeHTML(r.name)}:</span> <b>${escapeHTML(
            String(r.value)
          )}</b></div>`
      )
      .join("")}`;
    const rect = container.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    const y = ev.clientY - rect.top;
    tip.classList.add("is-visible");
    const tw = tip.offsetWidth;
    const th = tip.offsetHeight;
    let left = x + 14;
    let top = y + 14;
    if (left + tw > rect.width - 4) left = x - tw - 14;
    if (top + th > rect.height - 4) top = y - th - 14;
    tip.style.left = `${Math.max(4, left)}px`;
    tip.style.top = `${Math.max(4, top)}px`;
  }

  // --------------------------------------------------------------- explorer
  function setExplorerTask(id) {
    const task = getTask(id);
    state.taskId = id;
    state.protocol = task.defaultProtocol;
    state.pipeline = task.defaultPipeline;
    state.view = "score";
    state.metric = "accuracy";
    state.selectedSubset = null;
    syncUrl();
    renderExplorerControls();
  }

  function renderExplorerControls() {
    if (!DATA) return;
    const task = getTask(state.taskId);
    $("#task-chips").innerHTML = DATA.tasks
      .map(
        (t) => `<button class="task-chip-btn ${
          t.id === state.taskId ? "is-active" : ""
        }" type="button" role="tab" aria-selected="${
          t.id === state.taskId
        }" data-task-id="${t.id}">
          <span class="dot"></span>${escapeHTML(t.short)}
        </button>`
      )
      .join("");
    $$(".task-chip-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.taskId;
        setExplorerTask(id);
        state.detailTaskId = id;
        renderTaskGrid();
        renderTaskTabs();
        renderTaskDetail(id);
        renderExplorer();
      });
    });

    const protocolSel = $("#protocol-select");
    protocolSel.innerHTML = task.protocols
      .map(
        (p) =>
          `<option value="${p}" ${
            p === state.protocol ? "selected" : ""
          }>${escapeHTML(protocolLabel(p))}</option>`
      )
      .join("");
    protocolSel.disabled = task.protocols.length < 2;
    protocolSel.onchange = () => {
      state.protocol = protocolSel.value;
      state.selectedSubset = null;
      syncUrl();
      renderExplorer();
    };

    const pipelineSel = $("#pipeline-select");
    pipelineSel.innerHTML = task.pipelines
      .map(
        (p) =>
          `<option value="${p}" ${
            p === state.pipeline ? "selected" : ""
          }>${escapeHTML(pipelineLabel(p))}</option>`
      )
      .join("");
    pipelineSel.disabled = task.pipelines.length < 2;
    pipelineSel.onchange = () => {
      state.pipeline = pipelineSel.value;
      state.selectedSubset = null;
      syncUrl();
      renderExplorer();
    };

    const itrControl = $("#itr-control");
    itrControl.hidden = task.id !== "ssvep_8ch";
    if (task.id !== "ssvep_8ch") state.metric = "accuracy";
    $$("#metric-toggle button").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.metric === state.metric);
    });
    $$("#metric-toggle button").forEach((btn) => {
      btn.onclick = () => {
        state.metric = btn.dataset.metric;
        if (state.metric === "itr") state.view = "score";
        syncUrl();
        renderExplorerControls();
        renderExplorer();
      };
    });

    const deltaLabel =
      task.id === "sleep_staging_local" ? "Δ vs scalp" : "Δ vs full cap";
    $$("#view-toggle button").forEach((btn) => {
      if (btn.dataset.view === "delta") btn.textContent = deltaLabel;
      btn.classList.toggle("is-active", btn.dataset.view === state.view);
      btn.disabled = state.metric === "itr";
      btn.onclick = () => {
        if (state.metric === "itr") return;
        state.view = btn.dataset.view;
        syncUrl();
        renderExplorerControls();
        renderExplorer();
      };
    });
  }

  function protocolLabel(key) {
    return (
      DATA.rows.find((r) => r.protocol === key)?.protocolLabel ||
      key.replaceAll("_", " ")
    );
  }

  function metricValue(task, row) {
    if (state.metric === "itr") return row.itr;
    if (state.view === "delta") return row.delta;
    return row.score;
  }

  function referenceValue(task, ref) {
    if (state.metric === "itr") return task.stats?.referenceItr ?? null;
    if (state.view === "delta") return 0;
    return ref ? ref.score : task.stats?.reference ?? null;
  }

  function chanceValue(task, ref) {
    if (state.metric === "itr") return 0;
    if (state.view === "delta") return task.chance - (ref ? ref.score : 0);
    return task.chance;
  }

  function renderExplorer() {
    if (!DATA) return;
    const task = getTask(state.taskId);
    const rows = rowsFor(task.id, state.protocol, state.pipeline);
    if (!rows.length) return;
    const ref = referenceRow(rows);
    const refScore = ref ? ref.score : task.stats.reference;
    const refValue = referenceValue(task, ref);
    const chance = chanceValue(task, ref);
    const nonRandom = rows.filter((r) => !r.isRandom);
    const randoms = rows.filter((r) => r.isRandom);

    // Default selection: the best reduced montage, not the full cap.
    if (!state.selectedSubset) {
      const best = bestReduced(rows);
      state.selectedSubset = best ? best.subset : ref?.subset;
    }
    let selected =
      nonRandom.find((r) => r.subset === state.selectedSubset) || null;
    if (!selected) {
      const randomPick = randoms.find((r) => r.subset === state.selectedSubset);
      selected = randomPick || bestReduced(rows) || ref;
    }

    const chartEl = $("#montage-chart");
    const values = [];
    nonRandom.forEach((r) => {
      const v = metricValue(task, r);
      if (Number.isFinite(v)) values.push(v);
    });
    randoms.forEach((r) => {
      const v = metricValue(task, r);
      if (Number.isFinite(v)) values.push(v);
    });
    if (Number.isFinite(refValue)) values.push(refValue);
    if (state.view === "delta") values.push(0);

    // If chance is far below the data, showing it would compress the entire
    // interesting range into the top quarter of the plot. Keep the y-axis
    // readable and state chance explicitly below the axis instead.
    let showChance = Number.isFinite(chance) && state.view === "score";
    if (showChance && values.length) {
      const lo = Math.min(...values);
      const hi = Math.max(...values);
      const span = hi - lo || 0.1;
      if (chance < lo - 0.12 * span || chance > hi + 0.12 * span) {
        showChance = false;
      } else {
        values.push(chance);
      }
    }

    const ks = Array.from(
      new Set([...nonRandom.map((r) => r.k), ...randoms.map((r) => r.k), ref?.k])
    )
      .filter((k) => Number.isFinite(k))
      .sort((a, b) => a - b);

    // If there is only one channel count, a dot plot has nothing to show.
    if (ks.length < 2) {
      renderExplorerSingle(chartEl, task, rows, ref, selected);
    } else {
      renderMontageChart(chartEl, {
        task,
        rows,
        nonRandom,
        randoms,
        ref,
        selected,
        ks,
        values,
        refValue,
        chance,
        showChance,
        refScore,
      });
    }

    renderExplorerMap(task, selected, rows);
    renderMontageList(task, nonRandom, randoms, selected, ref);
    renderCallout(task, rows, ref, refScore);
    updateExplorerHeader(task, ref, refScore);
  }

  function renderExplorerSingle(container, task, rows, ref, selected) {
    const row = ref || rows[0];
    const value = metricValue(task, row);
    const chance = chanceValue(task, ref);
    const pctFill = clamp(
      ((value - chance) / ((ref ? ref.score : value) - chance || 1)) * 100,
      0,
      100
    );
    container.innerHTML = `<div class="single-montage">
      <p class="single-kicker">Only the full cap was tested</p>
      <div class="single-score">${fmt(value)} <span>${escapeHTML(
      task.metricLabel
    )}</span></div>
      <div class="single-track"><i style="width:${pctFill}%"></i></div>
      <p class="single-note">Chance is ${fmt(task.chance, 3)}. A reduced-montage
        comparison for this task is not available yet, so this dot is a lower bound,
        not a wearable result.</p>
    </div>`;
    $("#chart-legend").innerHTML = `<span class="legend-item"><span class="legend-dot" style="--dot:var(--full)"></span>Full cap</span>`;
  }

  function renderMontageChart(container, ctx) {
    const { task, rows, nonRandom, randoms, ref, selected, ks, values, refValue, chance, showChance } = ctx;
    const width = 820;
    const height = 430;
    const m = { l: 62, r: 28, t: 26, b: 52 };
    const plotW = width - m.l - m.r;
    const plotH = height - m.t - m.b;
    const minK = Math.min(...ks);
    const maxK = Math.max(...ks);
    const logMin = Math.log2(minK);
    const logMax = Math.log2(maxK);
    const x = (k) =>
      m.l + ((Math.log2(k) - logMin) / (logMax - logMin || 1)) * plotW;
    const xLeft = minK === maxK ? m.l + plotW / 2 : m.l;

    let yMin = Math.min(...values);
    let yMax = Math.max(...values);
    const span = yMax - yMin || 0.1;
    yMin -= span * 0.10;
    yMax += span * 0.10;
    if (state.view === "delta") {
      yMin = Math.min(yMin, -0.02);
      yMax = Math.max(yMax, 0.02);
    }
    const y = (v) =>
      m.t + (1 - (v - yMin) / (yMax - yMin || 1)) * plotH;

    const yTicks = niceTicks(yMin, yMax, 5);
    const xTicks = ks;
    const fmtY =
      state.metric === "itr"
        ? (v) => v.toFixed(1)
        : (v) => v.toFixed(2);
    const fmtX = (v) => String(v);

    const gridY = yTicks
      .map(
        (v) =>
          `<line class="grid-line" x1="${m.l}" y1="${y(v).toFixed(1)}" x2="${
            m.l + plotW
          }" y2="${y(v).toFixed(1)}"/>`
      )
      .join("");
    const gridX = xTicks
      .map(
        (k) =>
          `<line class="grid-line" x1="${x(k).toFixed(1)}" y1="${m.t}" x2="${x(
            k
          ).toFixed(1)}" y2="${m.t + plotH}" opacity=".55"/>`
      )
      .join("");
    const xLabels = xTicks
      .map(
        (k) =>
          `<text x="${x(k).toFixed(1)}" y="${m.t + plotH + 18}" text-anchor="middle">${fmtX(
            k
          )}</text>`
      )
      .join("");
    const yLabels = yTicks
      .map(
        (v) =>
          `<text x="${m.l - 10}" y="${(y(v) + 3.5).toFixed(1)}" text-anchor="end">${fmtY(
            v
          )}</text>`
      )
      .join("");

    const refLine =
      Number.isFinite(refValue)
        ? `<line class="reference-line" x1="${m.l}" y1="${y(
            refValue
          ).toFixed(1)}" x2="${m.l + plotW}" y2="${y(refValue).toFixed(1)}"/>
           <text class="ref-label" x="${m.l + plotW - 2}" y="${(
            y(refValue) - 6
          ).toFixed(1)}" text-anchor="end">${escapeHTML(
            (ref ? ref.subsetLabel : task.stats.referenceLabel) +
              " · " +
              fmt(refValue, 2)
          )}</text>`
        : "";
    const chanceLine =
      showChance && Number.isFinite(chance)
        ? `<line class="chance-line" x1="${m.l}" y1="${y(
            chance
          ).toFixed(1)}" x2="${m.l + plotW}" y2="${y(chance).toFixed(1)}"/>
           <text class="chance-label" x="${m.l + 2}" y="${(
            y(chance) - 5
          ).toFixed(1)}">chance</text>`
        : "";
    const chanceNote =
      !showChance && Number.isFinite(chance) && state.view === "score"
        ? `<text class="chance-label" x="${m.l + 2}" y="${
            m.t + plotH - 5
          }">chance ${fmt(chance, 2)} ${
            chance > yMax ? "above ↑" : "below ↓"
          }</text>`
        : "";

    // Random seeds: a small light band with a mean diamond. These are controls,
    // not candidate montages, so they stay visually quieter than the real ones.
    const randomMarkup = [];
    const randomByK = groupBy(randoms, "k");
    const offsetsFor = (n, spread = 34) => {
      if (n <= 1) return [0];
      const step = Math.min(spread / (n - 1), 20);
      return Array.from({ length: n }, (_, i) => (i - (n - 1) / 2) * step);
    };
    randomByK.forEach((group, k) => {
      const vals = group
        .map((r) => metricValue(task, r))
        .filter((v) => Number.isFinite(v));
      if (!vals.length) return;
      const cx = x(k) + (nonRandom.some((r) => r.k === k) ? 16 : 0);
      const vmin = Math.min(...vals);
      const vmax = Math.max(...vals);
      const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
      randomMarkup.push(
        `<line class="random-band" x1="${cx}" y1="${y(vmax).toFixed(
          1
        )}" x2="${cx}" y2="${y(vmin).toFixed(1)}" stroke="var(--random)"/>`
      );
      const seedOffsets = offsetsFor(vals.length, 26);
      group.forEach((seed, i) => {
        const v = metricValue(task, seed);
        if (!Number.isFinite(v)) return;
        const sx = cx + seedOffsets[i];
        const sy = y(v);
        const ring =
          selected && selected.subset === seed.subset
            ? `<circle class="selected-ring" cx="${sx}" cy="${sy}" r="7"/>`
            : "";
        randomMarkup.push(
          `<circle class="random-seed" cx="${sx.toFixed(1)}" cy="${sy.toFixed(
            1
          )}" r="2.7" fill="var(--random)"/>`
        );
        randomMarkup.push(
          `<circle class="random-seed-hit" data-subset="${seed.subset}" cx="${sx.toFixed(
            1
          )}" cy="${sy.toFixed(1)}" r="8" fill="transparent"/>${ring}`
        );
      });
      randomMarkup.push(
        `<path d="M${cx} ${(y(mean) - 4.6).toFixed(1)} l4.6 4.6 -4.6 4.6 -4.6 -4.6Z" fill="var(--random)" opacity=".8"/>`
      );
    });

    // Non-random montages. Multiple conditions at one k are jittered so that
    // overlapping points remain clickable.
    const byK = groupBy(nonRandom, "k");
    const points = [];
    byK.forEach((group, k) => {
      const hasRandom = randomByK.has(k);
      const sorted = [...group].sort((a, b) => {
        const order = { region: 0, distributed: 1, wearable: 2, full: 3 };
        return (order[a.strategy] ?? 4) - (order[b.strategy] ?? 4);
      });
      const offsets = offsetsFor(sorted.length, 54);
      const shift = hasRandom ? -14 : 0;
      sorted.forEach((row, i) => {
        const value = metricValue(task, row);
        if (!Number.isFinite(value)) return;
        const cx = x(k) + offsets[i] + shift;
        const cy = y(value);
        const color = STRATEGY_COLORS[row.strategy] || "var(--accent)";
        const isSel = selected && row.subset === selected.subset;
        const sem = row.sem;
        const err =
          Number.isFinite(sem) && sem > 0
            ? `<line class="error-bar" x1="${cx}" y1="${y(value - sem).toFixed(
                1
              )}" x2="${cx}" y2="${y(value + sem).toFixed(
                1
              )}" stroke="${color}"/>`
            : "";
        let shape = "";
        if (row.isFull) {
          shape = `<path class="point full-point" data-subset="${row.subset}" d="M${cx} ${(
            cy - 7
          ).toFixed(1)} l2 4.8 5.1.4-3.9 3.3 1.2 5-4.4-2.8-4.4 2.8 1.2-5-3.9-3.3 5.1-.4Z" fill="${color}"/>`;
        } else if (row.strategy === "wearable") {
          shape = `<rect class="point" data-subset="${row.subset}" x="${(
            cx - 4.6
          ).toFixed(1)}" y="${(cy - 4.6).toFixed(
            1
          )}" width="9.2" height="9.2" rx="2" fill="${color}"/>`;
        } else {
          shape = `<circle class="point" data-subset="${row.subset}" cx="${cx.toFixed(
            1
          )}" cy="${cy.toFixed(1)}" r="${row.isFull ? 6.5 : 5.2}" fill="${color}"/>`;
        }
        const ring = isSel
          ? `<circle class="selected-ring" cx="${cx}" cy="${cy}" r="10"/>`
          : "";
        points.push(
          `${err}${shape}${ring}<rect class="point-hit" data-subset="${
            row.subset
          }" x="${(cx - 9).toFixed(1)}" y="${(cy - 9).toFixed(
            1
          )}" width="18" height="18" fill="transparent"/>`
        );
      });
    });

    container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" class="chart-svg" role="img" aria-label="Montage score by number of electrodes">
      ${gridY}
      ${gridX}
      ${refLine}
      ${chanceLine}
      ${chanceNote}
      <line class="axis-line" x1="${m.l}" y1="${m.t + plotH}" x2="${
      m.l + plotW
    }" y2="${m.t + plotH}"/>
      <line class="axis-line" x1="${m.l}" y1="${m.t}" x2="${m.l}" y2="${
      m.t + plotH
    }"/>
      ${yLabels}
      ${xLabels}
      <text class="axis-label" x="${m.l + plotW / 2}" y="${
      height - 8
    }" text-anchor="middle">number of electrodes</text>
      <text class="axis-label" x="14" y="${m.t + plotH / 2}" text-anchor="middle" transform="rotate(-90 14 ${
      m.t + plotH / 2
    })">${escapeHTML(chartYLabel(task))}</text>
      ${randomMarkup.join("")}
      ${points.join("")}
    </svg>`;

    // Point interactions.
    const tooltip = ensureTooltip(container);
    const findRow = (subset) => rows.find((r) => r.subset === subset);
    const valueName =
      state.metric === "itr" ? "bits/min" : state.view === "delta" ? "Δ" : "score";
    $$(".point,.point-hit,.random-seed-hit", container).forEach((node) => {
      const subset = node.dataset.subset;
      const row = findRow(subset);
      if (!row) return;
      node.addEventListener("pointerenter", (ev) => {
        const v = metricValue(task, row);
        const rowsTip = [
          { name: valueName, color: STRATEGY_COLORS[row.strategy], value: fmt(v, 3) },
          { name: "score", color: "var(--ink-3)", value: fmt(row.score, 3) },
          {
            name: "Δ",
            color: "var(--ink-3)",
            value: fmtSigned(row.delta, 3),
          },
          {
            name: "n",
            color: "var(--ink-3)",
            value: String(row.n ?? "—"),
          },
        ];
        if (row.fidelity === "proxy") {
          rowsTip.push({ name: "fidelity", color: "var(--amber)", value: "proxy geometry" });
        }
        showTooltip(
          container,
          tooltip,
          `${row.subsetLabel} · ${row.k} ch · ${fmt(v, 3)}`,
          rowsTip,
          ev
        );
      });
      node.addEventListener("pointerleave", () =>
        tooltip.classList.remove("is-visible")
      );
      node.addEventListener("click", () => {
        state.selectedSubset = subset;
        renderExplorer();
      });
    });

    // Legend. Only show strategies that exist in this task.
    const legend = [
      ["Region", "var(--region)"],
      ["Max spread", "var(--distributed)"],
      ["Random (seeds)", "var(--random)"],
    ];
    if (nonRandom.some((r) => r.strategy === "wearable")) {
      legend.push(["Wearable", "var(--wearable)"]);
    }
    legend.push(["Full cap", "var(--full)"]);
    $("#chart-legend").innerHTML = legend
      .map(
        ([label, color]) =>
          `<span class="legend-item"><span class="legend-dot" style="--dot:${color}"></span>${label}</span>`
      )
      .join("");
  }

  function chartYLabel(task) {
    if (state.metric === "itr") return "bits per minute";
    if (state.view === "delta") {
      return task.id === "sleep_staging_local"
        ? "Δ κ vs scalp 6 ch"
        : `Δ ${task.metricLabel} vs full cap`;
    }
    return task.metricLabel;
  }

  function updateExplorerHeader(task, ref, refScore) {
    const protocol = protocolLabel(state.protocol);
    $("#chart-title").textContent = `${task.short} · ${protocol}`;
    const metric =
      state.metric === "itr" ? "Information transfer rate" : task.metricLabel;
    const pipeline = pipelineLabel(state.pipeline);
    $("#chart-subtitle").textContent = `${pipeline} · ${metric}${
      state.view === "delta" ? " · delta view" : ""
    }`;
    let note = "";
    if (task.id === "sleep_staging_local") {
      note = "No full-density cap exists. The reference is the matched 6-channel scalp montage.";
    } else if (task.id === "cvep_local") {
      note = "Only the full 28-channel cap was tested; treat it as a lower bound.";
    } else if (ref) {
      if (state.metric === "itr") {
        note = `Full cap: ${ref.k} channels · ${fmt(
          task.stats.referenceItr,
          1
        )} bits/min.`;
      } else {
        note = `Full cap: ${ref.k} channels · ${fmt(ref.score, 3)} ${task.metricLabel}.`;
      }
    }
    $("#chart-note").textContent = note;
  }

  function renderExplorerMap(task, selected, rows) {
    const all = taskChannels(task.id);
    const primary = selected ? selected.channels : [];
    $("#montage-head").innerHTML = headSVG(all, {
      primary,
      labels: primary.length <= 12,
      aria: `Electrode map for ${selected ? selected.subsetLabel : "the full cap"}`,
    });
    $("#map-count").textContent = selected ? `${selected.k} electrodes` : "";
    const detail = $("#montage-detail");
    if (!selected) {
      detail.innerHTML = "<p>Select a point to see the electrode set.</p>";
      return;
    }
    const isRandom = selected.isRandom;
    const fidelity =
      selected.fidelity === "proxy"
        ? '<span class="pill warn">proxy geometry — not a device claim</span>'
        : selected.fidelity
        ? `<span class="pill">${escapeHTML(selected.fidelity)}</span>`
        : "";
    const channelText =
      selected.channels.length > 22
        ? `${selected.channels.slice(0, 22).join(" · ")} · …`
        : selected.channels.join(" · ");
    detail.innerHTML = `
      <div class="md-score"><strong>${fmt(selected.score, 3)}</strong><span>${
      task.metricLabel
    } · n=${selected.n ?? "—"}</span></div>
      <p>${escapeHTML(selected.subsetLabel)} · ${escapeHTML(
      selected.strategyLabel
    )} · ${selected.k} electrodes${isRandom ? " · one random seed" : ""}</p>
      <div class="md-meta">
        ${fidelity}
        <span class="pill">Δ ${fmtSigned(selected.delta, 3)}</span>
        <span class="pill">${escapeHTML(selected.protocolLabel)}</span>
      </div>
      <div class="md-channels">${escapeHTML(channelText)}</div>`;
  }

  function renderMontageList(task, nonRandom, randoms, selected, ref) {
    const items = [];
    nonRandom.forEach((row) => {
      items.push({
        kind: "single",
        row,
        sortK: row.k,
        sortScore: row.score,
      });
    });
    const randomByK = groupBy(randoms, "k");
    randomByK.forEach((group, k) => {
      const mean = group.reduce((a, r) => a + r.score, 0) / group.length;
      const min = Math.min(...group.map((r) => r.score));
      const max = Math.max(...group.map((r) => r.score));
      items.push({
        kind: "random",
        k,
        mean,
        min,
        max,
        seeds: group,
        sortK: k,
        sortScore: mean,
      });
    });
    items.sort((a, b) => {
      if (a.sortK !== b.sortK) return a.sortK - b.sortK;
      if (a.kind === "random" && b.kind !== "random") return 1;
      if (b.kind === "random" && a.kind !== "random") return -1;
      return b.sortScore - a.sortScore;
    });

    const maxScore = Math.max(
      ...items.map((i) => (i.kind === "single" ? i.row.score : i.mean)),
      0.001
    );
    const minScore = Math.min(
      ...items.map((i) => (i.kind === "single" ? i.row.score : i.mean)),
      0
    );
    const span = maxScore - minScore || 1;

    $("#montage-list").innerHTML = items
      .map((item) => {
        if (item.kind === "random") {
          const isSel = !!selected?.isRandom && selected.k === item.k;
          const width = clamp(((item.mean - minScore) / span) * 100, 2, 100);
          return `<button class="montage-row ${
            isSel ? "is-selected" : ""
          }" type="button" data-subset="${item.seeds[0].subset}">
            <div>
              <div class="montage-row-top">
                <strong>Random subset · ${item.k} ch</strong>
                <span>${fmt(item.mean, 3)}</span>
              </div>
              <div class="montage-track"><i style="width:${width}%;--bar:var(--random)"></i></div>
            </div>
            <span class="delta">${fmt(item.min, 3)}–${fmt(item.max, 3)}</span>
          </button>`;
        }
        const row = item.row;
        const isSel = selected && selected.subset === row.subset;
        const width = clamp(((row.score - minScore) / span) * 100, 2, 100);
        return `<button class="montage-row ${
          isSel ? "is-selected" : ""
        }" type="button" data-subset="${row.subset}">
          <div>
            <div class="montage-row-top">
              <strong>${escapeHTML(row.subsetLabel)} · ${row.k} ch</strong>
              <span>${fmt(row.score, 3)}</span>
            </div>
            <div class="montage-track"><i style="width:${width}%;--bar:${
              STRATEGY_COLORS[row.strategy] || "var(--accent)"
            }"></i></div>
          </div>
          <span class="delta ${row.delta < 0 ? "neg" : ""}">${fmtSigned(
            row.delta,
            3
          )}</span>
        </button>`;
      })
      .join("");

    $$(".montage-row").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.selectedSubset = btn.dataset.subset;
        renderExplorer();
      });
    });
  }

  function renderCallout(task, rows, ref, refScore) {
    const comparison = DATA.comparisons.find((c) => c.track === task.id);
    const callout = $("#matched-callout");
    let html = "";
    if (comparison) {
      html = `<p class="callout-eyebrow">${escapeHTML(comparison.title)}</p>
        <div class="callout-number"><strong>${fmtSigned(
          comparison.delta,
          3
        )}</strong><span>${escapeHTML(comparison.metricLabel)}</span></div>
        <h3>${escapeHTML(comparison.left)} ${fmt(
        comparison.leftScore
      )} vs ${escapeHTML(comparison.right)} ${fmt(comparison.rightScore)}</h3>
        <p>${escapeHTML(comparison.note)}</p>`;
    } else if (task.id === "mi_leftright_22ch") {
      const sens = rows.find((r) => r.subset === "region-sensorimotor_k4");
      const dist = rows.find((r) => r.subset === "distributed_k4");
      const delta = sens && dist ? sens.score - dist.score : null;
      html = `<p class="callout-eyebrow">At four electrodes</p>
        <div class="callout-number"><strong>${fmtSigned(
          delta,
          3
        )}</strong><span>ROC-AUC</span></div>
        <h3>Sensorimotor beats max spread</h3>
        <p>${fmt(sens?.score)} vs ${fmt(
        dist?.score
      )} at the same channel count. Spreading electrodes to maximise coverage is the
        wrong objective for a focal source.</p>`;
    } else if (task.id === "p300_8ch") {
      const stats = task.stats;
      html = `<p class="callout-eyebrow">Half the cap</p>
        <div class="callout-number"><strong>${pct(
          stats.retainedPct
        )}</strong><span>of full-cap AUC</span></div>
        <h3>Four electrodes, ${fmt(stats.best)} AUC</h3>
        <p>The cap is only eight electrodes, so the reduced condition is four.
          The loss is ${fmt(Math.abs(stats.delta))} AUC — within the range where a
          headband-sized P300 montage is plausible.</p>`;
    } else if (task.id === "ssvep_8ch") {
      const stats = task.stats;
      html = `<p class="callout-eyebrow">Four occipital electrodes</p>
        <div class="callout-number"><strong>${pct(
          stats.retainedPct
        )}</strong><span>of full-cap accuracy</span></div>
        <h3>${fmt(stats.bestItr, 1)} bits/min vs ${fmt(
        stats.referenceItr,
        1
      )}</h3>
        <p>Ranking by accuracy alone misses the point: SSVEP is judged by
          information transfer rate, and the reduced montage keeps almost all of it.</p>`;
    } else if (task.id === "cvep_local") {
      const full = rows.find((r) => r.isFull);
      html = `<p class="callout-eyebrow">Exploratory track</p>
        <div class="callout-number"><strong>${fmt(full?.score)}</strong><span>accuracy vs ${fmt(
        task.chance,
        3
      )} chance</span></div>
        <h3>Above chance, but decoder-limited</h3>
        <p>This is the full 28-channel cap, decoded with a generic covariance
          pipeline. Template matching against the known codes is the standard
          method; 0.400 is a lower bound, not a montage result.</p>`;
    } else {
      html = `<p class="callout-eyebrow">Reading the chart</p><h3>Compare at matched k</h3>
        <p>A difference between a 4-electrode region and an 8-electrode subset is
          a difference in count, not placement. The benchmark fixes k before it
          compares strategies.</p>`;
    }
    callout.innerHTML = html;
  }

  // -------------------------------------------------------------- findings
  function miniBars(rows, opts = {}) {
    const max = opts.max ?? Math.max(...rows.map((r) => r.value));
    const min = opts.min ?? Math.min(...rows.map((r) => r.value));
    const span = max - min || 1;
    return `<div class="mini-bars">${rows
      .map(
        (r) => `<div class="mini-bar">
          <span>${escapeHTML(r.label)}</span>
          <span class="mini-bar-track"><i style="width:${clamp(
            ((r.value - min) / span) * 100,
            3,
            100
          )}%;--bar:${r.color || "var(--accent)"}"></i></span>
          <b>${fmt(r.value, 3)}</b>
        </div>`
      )
      .join("")}</div>${
      opts.note ? `<p class="finding-note">${escapeHTML(opts.note)}</p>` : ""
    }`;
  }

  function renderFindings() {
    const mi = rowsFor("mi_leftright_22ch", "within_session", "riemann_tslr");
    const sens4 = mi.find((r) => r.subset === "region-sensorimotor_k4");
    const dist4 = mi.find((r) => r.subset === "distributed_k4");
    const rand4 = mi.filter((r) => r.isRandom && r.k === 4);
    const randMean = rand4.reduce((a, r) => a + r.score, 0) / (rand4.length || 1);
    $("#finding-placement").innerHTML = miniBars(
      [
        { label: "sensorimotor", value: sens4.score, color: "var(--region)" },
        { label: "max spread", value: dist4.score, color: "var(--distributed)" },
        { label: "random mean", value: randMean, color: "var(--random)" },
      ],
      {
        min: 0.6,
        max: 0.78,
        note: "Motor imagery, k=4, within-session, Riemannian TSLR.",
      }
    );

    const p300full = DATA.rows.find(
      (r) =>
        r.track === "p300_8ch" &&
        r.pipeline === "xdawn_tslr" &&
        r.isFull
    );
    const p300generic = DATA.rows.find(
      (r) =>
        r.track === "p300_8ch" &&
        r.pipeline === "logvar_lda" &&
        r.isFull
    );
    const ssvep = DATA.rows.find(
      (r) => r.track === "ssvep_8ch" && r.isFull
    );
    $("#finding-decoder").innerHTML = miniBars(
      [
        { label: "P300 generic", value: p300generic.score, color: "var(--random)" },
        { label: "P300 xDAWN", value: p300full.score, color: "var(--amber)" },
        { label: "SSVEP generic", value: 0.133, color: "var(--random)" },
        { label: "SSVEP CCA", value: ssvep.score, color: "var(--violet)" },
      ],
      {
        min: 0,
        max: 1,
        note: "Generic band-power vs the paradigm’s standard decoder. The SSVEP generic value is from the earlier decoder run reported in the README.",
      }
    );

    const motorComp = DATA.comparisons.find(
      (c) => c.track === "motor_execution_ear_vs_scalp"
    );
    const sleepComp = DATA.comparisons.find(
      (c) => c.track === "sleep_staging_local"
    );
    $("#finding-tasks").innerHTML = miniBars(
      [
        {
          label: "motor scalp",
          value: motorComp.leftScore,
          color: "var(--coral)",
        },
        {
          label: "motor in-ear",
          value: motorComp.rightScore,
          color: "var(--wearable)",
        },
        {
          label: "sleep scalp",
          value: sleepComp.leftScore,
          color: "var(--indigo)",
        },
        {
          label: "sleep ear",
          value: sleepComp.rightScore,
          color: "var(--violet)",
        },
      ],
      {
        min: 0.4,
        max: 0.8,
        note: "Different metrics (AUC vs κ) and chance levels; compare within each pair, not across rows.",
      }
    );
  }

  function renderCrossTask() {
    const ids = [
      "mi_leftright_22ch",
      "p300_8ch",
      "ssvep_8ch",
      "motor_execution_ear_vs_scalp",
    ];
    const series = ids
      .map((id) => {
        const task = getTask(id);
        const rows = rowsFor(id, task.defaultProtocol, task.defaultPipeline);
        const ref = referenceRow(rows);
        if (!ref) return null;
        const reduced = rows.filter(
          (r) =>
            !r.isFull &&
            !r.isRandom &&
            ["region", "distributed"].includes(r.strategy) &&
            r.k <= 16
        );
        const byK = groupBy(reduced, "k");
        const pts = [];
        byK.forEach((group, k) => {
          const best = group.reduce((a, b) => (a.score > b.score ? a : b));
          pts.push({ x: k, y: (100 * best.score) / ref.score });
        });
        pts.sort((a, b) => a.x - b.x);
        pts.push({ x: ref.k, y: 100 });
        return {
          name: task.short,
          role: TASK_ROLES[id] || "accent",
          x: pts.map((p) => p.x),
          y: pts.map((p) => p.y),
        };
      })
      .filter(Boolean);

    mountXYChart($("#cross-task-chart"), {
      series,
      xLabel: "number of electrodes",
      yLabel: "% of full-cap score",
      xDomain: [4, 120],
      yDomain: [80, 102],
      xScale: "log",
      xTicks: [4, 8, 16, 32, 64, 115],
      yTicks: [80, 85, 90, 95, 100],
      xTickFormat: (v) => String(v),
      yTickFormat: (v) => `${v}%`,
      tooltipX: (v) => `${Number(v).toFixed(0)} electrodes`,
      tooltipY: (v) => `${Number(v).toFixed(1)}%`,
      referenceY: 100,
      referenceLabel: "full cap",
      height: 320,
      showPoints: true,
      legend: false,
      aria: "Percentage of full-cap accuracy recovered as electrodes are added",
    });
    $("#cross-task-legend").innerHTML = series
      .map(
        (s) =>
          `<span class="legend-item"><span class="legend-dot" style="--dot:${
            ROLE_COLORS[s.role]
          }"></span>${escapeHTML(s.name)}</span>`
      )
      .join("");
  }

  // ------------------------------------------------------------- controls
  function renderControls() {
    const rows = DATA.controls || [];
    const order = {
      mi_leftright_22ch: 1,
      p300_8ch: 2,
      ssvep_8ch: 3,
      motor_execution_ear_vs_scalp: 4,
      sleep_staging_local: 5,
    };
    rows.sort((a, b) => (order[a.track] || 99) - (order[b.track] || 99));
    const labels = {
      mi_leftright_22ch: "Motor imagery",
      p300_8ch: "P300",
      ssvep_8ch: "SSVEP",
      motor_execution_ear_vs_scalp: "Motor execution",
      sleep_staging_local: "Sleep staging",
    };
    const width = 760;
    const height = 300;
    const m = { l: 112, r: 36, t: 22, b: 42 };
    const plotW = width - m.l - m.r;
    const plotH = height - m.t - m.b;
    const x = (v) => m.l + v * plotW;
    const rowH = plotH / Math.max(rows.length, 1);
    const ticks = [0, 0.25, 0.5, 0.75, 1];
    const grid = ticks
      .map(
        (v) =>
          `<line class="grid-line" x1="${x(v)}" y1="${m.t}" x2="${x(
            v
          )}" y2="${m.t + plotH}"/>
           <text x="${x(v)}" y="${m.t + plotH + 16}" text-anchor="middle">${v.toFixed(
            2
          )}</text>`
      )
      .join("");
    const rowMarkup = rows
      .map((r, i) => {
        const cy = m.t + rowH * i + rowH / 2;
        const label = labels[r.track] || r.track;
        const chanceX = x(r.chance);
        return `<g>
          <text x="${m.l - 12}" y="${cy + 3.5}" text-anchor="end">${escapeHTML(
          label
        )}</text>
          <line x1="${x(r.perm)}" y1="${cy}" x2="${x(r.real)}" y2="${cy}" stroke="var(--line-strong)" stroke-width="3" stroke-linecap="round"/>
          <circle cx="${x(r.perm)}" cy="${cy}" r="4.5" fill="var(--ink-3)" opacity=".7"/>
          <circle cx="${x(r.real)}" cy="${cy}" r="6" fill="var(--accent)"/>
          <path d="M${chanceX} ${cy - 8} l4.5 7h-9Z" fill="var(--chance)" opacity=".85"/>
          <rect class="bar-hit" data-track="${escapeHTML(label)}" data-real="${r.real}" data-perm="${
          r.perm
        }" data-chance="${r.chance}" data-metric="${escapeHTML(
          r.metric
        )}" x="${m.l}" y="${cy - rowH / 2}" width="${plotW}" height="${rowH}" fill="transparent"/>
        </g>`;
      })
      .join("");

    $("#control-chart").innerHTML = `<svg viewBox="0 0 ${width} ${height}" class="chart-svg" role="img" aria-label="Permutation controls: real versus shuffled-label scores">
      ${grid}
      <line class="axis-line" x1="${m.l}" y1="${m.t + plotH}" x2="${
      m.l + plotW
    }" y2="${m.t + plotH}"/>
      ${rowMarkup}
      <text class="axis-label" x="${m.l + plotW / 2}" y="${
      height - 4
    }" text-anchor="middle">score (chance marker per row)</text>
    </svg>`;

    $("#control-legend").innerHTML = `
      <span class="legend-item"><span class="legend-dot" style="--dot:var(--accent)"></span>real labels</span>
      <span class="legend-item"><span class="legend-dot" style="--dot:var(--ink-3)"></span>permuted labels</span>
      <span class="legend-item"><span class="legend-dot" style="--dot:var(--chance)"></span>chance</span>`;

    const tooltip = ensureTooltip($("#control-chart"));
    $$(".bar-hit", $("#control-chart")).forEach((hit) => {
      hit.addEventListener("pointermove", (ev) => {
        showTooltip(
          $("#control-chart"),
          tooltip,
          hit.dataset.track,
          [
            { name: "real", color: "var(--accent)", value: fmt(Number(hit.dataset.real), 3) },
            { name: "permuted", color: "var(--ink-3)", value: fmt(Number(hit.dataset.perm), 3) },
            { name: "chance", color: "var(--chance)", value: fmt(Number(hit.dataset.chance), 3) },
            { name: "metric", color: "var(--ink-3)", value: hit.dataset.metric },
          ],
          ev
        );
      });
      hit.addEventListener("pointerleave", () =>
        tooltip.classList.remove("is-visible")
      );
    });
  }

  function renderQuality() {
    const rows = DATA.quality || [];
    if (!rows.length) {
      $("#quality-table").innerHTML = "<p class='finding-note'>Not computed.</p>";
      return;
    }
    $("#quality-table").innerHTML = `<table class="quality-table">
      <thead><tr><th>subset</th><th>k</th><th>reject</th><th>line noise</th><th>rank</th><th>|corr|</th></tr></thead>
      <tbody>${rows
        .map(
          (r) => `<tr>
          <td>${escapeHTML(prettySubset(r.subset))}</td>
          <td>${r.k}</td>
          <td>${(Number(r.reject_rate) * 100).toFixed(1)}%</td>
          <td>${fmt(r.line_noise_ratio, 2)}</td>
          <td>${fmt(r.effective_rank, 2)}</td>
          <td>${fmt(r.mean_abs_corr, 2)}</td>
        </tr>`
        )
        .join("")}</tbody>
    </table>`;
  }

  function prettySubset(s) {
    if (!s) return "—";
    if (s.startsWith("region-")) return s.replace("region-", "").replaceAll("_", " ");
    if (s.startsWith("random-")) return "random";
    if (s.startsWith("distributed")) return "max spread";
    if (s.startsWith("full")) return "full cap";
    return s.replaceAll("_", " ");
  }
})();
