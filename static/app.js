/* =====================================================================
   Dashboard logic for the "Activity in English" ML comparison app.
   Reads precomputed results from /api/results and renders the UI with
   Plotly interactive charts. The "Re-train models" button triggers a
   background re-run via POST /api/train and polls /api/train/status.
===================================================================== */

const $ = (id) => document.getElementById(id);

const PLOT_TEMPLATE = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#1e293b", family: "Segoe UI, sans-serif" },
  margin: { t: 20, r: 16, b: 40, l: 44 },
};

const COLORES = {
  KNN: "#17becf",
  SVC: "#ff7f0e",
  GradientBoosting: "#2ca02c",
  GaussianNB: "#d62728",
};

let DATA = null;

/* ------------------- safe Plotly access ------------------- */

function showPlotlyNote() {
  const n = $("plotly-note");
  if (n) n.classList.remove("d-none");
}

function sfPlot(target, data, layout, config) {
  if (typeof window.Plotly === "undefined") {
    showPlotlyNote();
    return;
  }
  try {
    window.Plotly.newPlot(target, data, layout, config);
  } catch (e) {
    console.warn("Plotly error on #" + target, e);
  }
}

/* ----------------------------- load ----------------------------- */

async function cargarDatos() {
  const res = await fetch("/api/results");
  DATA = await res.json();
  renderTodo();
}

function cacheBus(t) {
  return t + "?v=" + encodeURIComponent((DATA.generated_at || "0").replace(/\D/g, ""));
}

function renderTodo() {
  if (!DATA) return;
  renderMeta();
  renderDataset();
  renderModelCards();
  renderTable();
  renderCharts();
  renderConfusiones();
  renderImagenes();
  renderVeredicto();
}

function renderMeta() {
  const g = DATA.generated_at || "-";
  $("generated-at").textContent = "Results generated: " + g + "  ·  full experiment duration: " +
    (DATA.runtime_seconds ?? "-") + " s (local machine)";
  if (DATA.mode === "quick") {
    $("generated-at").textContent += "  ·  ⚠️ these are the results of a last quick re-training (reduced grid)";
  }
  $("badge-updated").textContent = "⏱ results: " + g.split(" ")[0];
}

/* ----------------------------- dataset --------------------------- */

function renderDataset() {
  const d = DATA.dataset || {};
  const clases = d.classes || { empty: 0, occupied: 0 };
  const total = (clases.empty + clases.occupied) || 1;
  $("dataset-note").textContent =
    d.instances + " instances · " + d.features + " numeric predictors · " +
    d.columns.join(", ") + " · class imbalance ~" + (d.imbalance * 100).toFixed(0) +
    "% empty vs ~" + (100 - (d.imbalance * 100)).toFixed(0) + "% occupied.";

  sfPlot("chart-dataset", [{
    x: ["Empty (0)", "Occupied (1)"],
    y: [clases.empty, clases.occupied],
    type: "bar",
    marker: { color: ["#1f77b4", "#d62728"] },
    text: [clases.empty, clases.occupied],
    textposition: "auto",
  }], Object.assign({}, PLOT_TEMPLATE, {
    xaxis: { title: "" }, yaxis: { title: "Instances" },
  }), { responsive: true, displayModeBar: false });
}

/* --------------------------- model cards ------------------------- */

function renderModelCards() {
  const cont = $("model-cards");
  cont.innerHTML = "";
  const modelos = [...DATA.models].sort((a, b) => b.f1 - a.f1);
  const ganador = modelos[0].name;
  $("winner-badge").textContent = "🏆 Winner: " + ganador;

  modelos.forEach((m, i) => {
    const gan = m.name === ganador;
    const params = Object.entries(m.params || {}).map(([k, v]) =>
      `<code>${k}=${v}</code>`).join("&nbsp;· ");
    const card = document.createElement("div");
    card.className = "col-md-6 col-xl-3";
    card.innerHTML = `
      <div class="card modal-card h-100 ${gan ? "" : "opacity-75"}">
        ${gan ? '<div class="winner-ribbon">🏆 BEST</div>' : ""}
        <div class="card-body d-flex flex-column">
          <h5 class="card-title d-flex justify-content-between align-items-center">
            <span>${m.name}</span>
            <svg width="20" height="20" viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="${COLORES[m.name] || "#888"}" /></svg>
          </h5>
          <p class="display-6 fw-bold mb-1" style="color:${COLORES[m.name] || "#1e293b"}">${m.f1.toFixed(4)}</p>
          <p class="text-muted small mb-2">macro F1-Score · 5-fold CV</p>
          <table class="table table-sm table-borderless mb-2 small">
            <tr><td>Accuracy</td><td class="text-end">${m.accuracy.toFixed(4)}</td></tr>
            <tr><td>Precision</td><td class="text-end">${m.precision.toFixed(4)}</td></tr>
            <tr><td>Recall</td><td class="text-end">${m.recall.toFixed(4)}</td></tr>
            <tr><td>Time</td><td class="text-end">${m.time_s.toFixed(2)} s</td></tr>
          </table>
          <p class="mt-auto small text-muted mb-0"><strong>Best params:</strong><br>${params}</p>
        </div>
      </div>`;
    cont.appendChild(card);
  });
}

/* ---------------------------- results table ---------------------- */

function renderTable() {
  const rows = [...DATA.models].sort((a, b) => b.f1 - a.f1);
  const ganador = rows[0].name;
  const tb = $("results-table").querySelector("tbody");
  tb.innerHTML = "";
  rows.forEach((m) => {
    const tr = document.createElement("tr");
    if (m.name === ganador) tr.style.boxShadow = "inset 3px 0 0 #ffc107";
    const params = Object.entries(m.params || {}).map(([k, v]) => `${k}=${v}`).join(", ");
    tr.innerHTML = `
      <td class="fw-bold">${m.name} ${m.name === ganador ? '<span class="badge text-bg-warning">🏆</span>' : ""}</td>
      <td class="text-success fw-bold">${m.f1.toFixed(4)}</td>
      <td>${m.accuracy.toFixed(4)}</td>
      <td>${m.precision.toFixed(4)}</td>
      <td>${m.recall.toFixed(4)}</td>
      <td>${m.time_s.toFixed(2)}</td>
      <td class="small text-muted"><code>${params}</code></td>`;
    tb.appendChild(tr);
  });
}

/* ------------------------------- charts --------------------------- */

function graf(modelos) {
  const orden = [...modelos].sort((a, b) => b.f1 - a.f1);
  return { x: orden.map(m => m.name), y: orden.map(m => m.f1),
           color: orden.map(m => COLORES[m.name] || "#888") };
}

function renderCharts() {
  const modelos = DATA.models;
  const g = graf(modelos);

  sfPlot("chart-f1", [{
    x: g.x, y: g.y, type: "bar", marker: { color: g.color },
    text: g.y.map(v => v.toFixed(4)), textposition: "auto",
  }], Object.assign({}, PLOT_TEMPLATE, {
    yaxis: { title: "Macro F1-Score", range: [0.90, 1.005] },
    showlegend: false,
  }), { responsive: true, displayModeBar: false });

  const ordT = ["GaussianNB", "KNN", "GradientBoosting", "SVC"];
  const t = { x: ordT, y: ordT.map(n => (modelos.find(m => m.name === n) || { time_s: 0 }).time_s),
              color: ordT.map(n => COLORES[n] || "#888") };
  sfPlot("chart-time", [{
    x: t.x, y: t.y, type: "bar", marker: { color: t.color },
    text: t.y.map(v => v.toFixed(2) + " s"), textposition: "auto",
  }], Object.assign({}, PLOT_TEMPLATE, {
    yaxis: { title: "Time (s)" }, showlegend: false,
  }), { responsive: true, displayModeBar: false });

  sfPlot("chart-f1time", [{
    x: modelos.map(m => m.time_s), y: modelos.map(m => m.f1), mode: "markers+text",
    type: "scatter", text: modelos.map(m => m.name), textposition: "top right",
    marker: { size: 18, color: modelos.map(m => COLORES[m.name] || "#888") },
  }], Object.assign({}, PLOT_TEMPLATE, {
    xaxis: { title: "Time (s)" }, yaxis: { title: "Macro F1-Score", range: [0.90, 1.005] },
    showlegend: false,
  }), { responsive: true, displayModeBar: false });

  sfPlot("chart-kernels", [{
    x: DATA.kernels.map(k => k.kernel), y: DATA.kernels.map(k => k.f1), type: "bar",
    marker: { color: ["#ff7f0e", "#2ca02c", "#d62728"] },
    text: DATA.kernels.map(k => k.f1.toFixed(4)), textposition: "auto",
  }], Object.assign({}, PLOT_TEMPLATE, {
    yaxis: { title: "Best macro F1", range: [0.85, 1.005] }, showlegend: false,
  }), { responsive: true, displayModeBar: false });

  sfPlot("chart-metrics", [{
    x: DATA.metricas.map(m => m.metric), y: DATA.metricas.map(m => m.f1), type: "bar",
    marker: { color: ["#17becf", "#9467bd"] },
    text: DATA.metricas.map(m => m.f1.toFixed(4)), textposition: "auto",
  }], Object.assign({}, PLOT_TEMPLATE, {
    yaxis: { title: "Best macro F1", range: [0.85, 1.005] }, showlegend: false,
  }), { responsive: true, displayModeBar: false });
}

/* ----------------------- confusion matrices ----------------------- */

function renderConfusiones() {
  const grid = $("confusion-grid");
  grid.innerHTML = "";
  const modelos = [...DATA.models].sort((a, b) => b.f1 - a.f1);
  const etiq = ["Empty", "Occupied"];
  modelos.forEach(m => {
    const cm = m.confusion || [[0, 0], [0, 0]];
    const col = document.createElement("div");
    col.className = "col-md-6 col-xl-3";
    col.innerHTML = `<div class="card h-100"><div class="card-body">
        <h6 class="chart-title text-center">${m.name} <span class="text-muted small">(F1 ${m.f1.toFixed(4)})</span></h6>
        <div class="cm-${m.name.replace(/[^a-zA-Z]/g, "")}"></div>
        <p class="text-muted small mb-0 mt-2 text-center">FP = ${cm[0][1]} · FN = ${cm[1][0]}</p>
      </div></div>`;
    grid.appendChild(col);
    sfPlot(col.querySelector(".cm-" + m.name.replace(/[^a-zA-Z]/g, "")), [{
      z: cm, x: etiq, y: etiq, type: "heatmap",
      colorscale: "Blues", showscale: false, zmin: 0, zmax: Math.max(...cm.flat(), 1),
      text: cm, texttemplate: "%{text}", textfont: { color: "white" },
      xgap: 2, ygap: 2,
    }], Object.assign({}, PLOT_TEMPLATE, {
      margin: { t: 10, r: 8, b: 34, l: 44 },
      xaxis: { title: "Predicted", dtick: 1 },
      yaxis: { title: "Actual", dtick: 1 },
      height: 280,
    }), { responsive: true, displayModeBar: false });
  });
}

/* ----------------------------- images ----------------------------- */

function renderImagenes() {
  const fig = DATA.figures || {};
  $("img-f1bars").src = cacheBus(fig.f1_bars || "");
  $("img-timebars").src = cacheBus(fig.time_bars || "");
  $("img-f1time").src = cacheBus(fig.f1_time || "");
  $("img-kernels").src = cacheBus(fig.kernels || "");
  $("img-metrics").src = cacheBus(fig.metrics || "");
  $("img-boundaries").src = cacheBus(fig.boundaries || "");
  $("img-correlation").src = cacheBus(fig.correlation || "");
  const v = DATA.pca_variance || [];
  $("pca-note").textContent = v.length
    ? "Variance explained by 2 PCA components: " + v.map(x => (x * 100).toFixed(1) + "%").join(" + ") +
      " = " + (v.reduce((a, b) => a + b, 0) * 100).toFixed(1) + "%"
    : "";
}

/* ----------------------------- verdict ---------------------------- */

function renderVeredicto() {
  const v = DATA.verdict || {};
  const c = $("verdict-container");
  const bloque = (t, x) => `
    <div class="card verdict-answer mb-3"><div class="card-body">
      <h5>${t}</h5><p>${x || ""}</p>
    </div></div>`;
  c.innerHTML =
    bloque("1 · Which model achieved the best balance between accuracy and generalization?",
           v.q1) +
    bloque("2 · Did the most complex model justify its computational cost?", v.q2) +
    bloque("3 · How did the decision boundaries behave in relation to the dimensionality of the dataset?",
           v.q3) +
    `<div class="card text-bg-warning"><div class="card-body"><h5 class="mb-1">Final conclusion</h5>
     <p class="mb-0">${v.conclusion || ""}</p></div></div>`;
}

/* -------------------------- retraining ---------------------------- */

async function reentrenar() {
  const btn = $("btn-train");
  if (btn.disabled) return;
  btn.disabled = true;
  mostrarProgreso(true, "Starting…", 0);
  setStatus("training", "⏳ Training in background…");

  const res = await fetch("/api/train", { method: "POST" });
  if (res.status === 202) {
    pollEstado();
  } else {
    const j = await res.json().catch(() => ({}));
    if (j.status === "training_already_running") {
      setStatus("training", "⏳ Already training…");
      pollEstado();
    } else {
      setStatus("error", "⚠️ Could not start training");
      btn.disabled = false;
      mostrarProgreso(false);
    }
  }
}

function mostrarProgreso(visible, mensaje, pct) {
  const wrap = $("train-progress-wrap");
  if (!wrap) return;
  wrap.classList.toggle("d-none", !visible);
  if (visible) {
    $("train-message").textContent = mensaje || "";
    $("train-percent").textContent = Math.round((pct || 0) * 100) + "%";
    $("train-bar").style.width = Math.round((pct || 0) * 100) + "%";
  }
}

async function pollEstado() {
  const btn = $("btn-train");
  const r = await fetch("/api/train/status");
  const j = await r.json();

  if (j.status === "training") {
    setStatus("training", "⏳ Training in background… (" +
      ((j.started || "").split(" ")[1] || "running") + ")");
    mostrarProgreso(true, j.message || "Working…", j.percent || 0);
    setTimeout(pollEstado, 1500);
    return;
  }

  if (j.status === "done") {
    setStatus("done", "✅ Training finished · updating dashboard…");
    mostrarProgreso(true, "Training finished — updating the dashboard…", 1);
    await cargarDatos();
    setStatus("done", "✅ Training finished " + (j.finished || ""));
    mostrarProgreso(true, "Training finished — dashboard updated ✓", 1);
    setTimeout(() => mostrarProgreso(false), 4000);
  } else if (j.status === "error") {
    setStatus("error", "⚠️ Error: " + (j.error || "unknown"));
    mostrarProgreso(false);
  } else {
    setStatus("idle", "Ready");
    mostrarProgreso(false);
  }
  btn.disabled = false;
}

function setStatus(kind, texto) {
  const pill = $("status-pill");
  pill.className = "badge rounded-pill " + kind;
  pill.textContent = texto;
}

/* ------------------------------ init ------------------------------ */

cargarDatos().catch(() => {
  setStatus("error", "⚠️ Could not load results");
});