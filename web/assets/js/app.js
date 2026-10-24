/* ============================================================
   Powerball Predictor - browser app
   Replaces the Flask REST layer: the same engine, run client-side.
   ============================================================ */

(function () {
  "use strict";

  const E = window.PowerballEngine;
  const DATA_URL = "data/powerball_history.csv";

  let draws = [];
  let analysis = null;
  let chart = null;
  let chartMode = "white";

  const $ = (id) => document.getElementById(id);

  /* ---------- helpers ---------- */

  function ball(n, cls) {
    return '<span class="ball ' + cls + '">' + n + "</span>";
  }

  function el(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  const STRATEGY_NOTES = {
    frequency:
      "<strong>Frequency strategy:</strong> weights each number by how often it has been drawn. " +
      "The most frequently drawn numbers get the highest chance of appearing.",
    balanced:
      "<strong>Balanced strategy:</strong> weights every number by a softened frequency (exponent 1.2), " +
      "so hot numbers are favoured but a long tail of less-drawn numbers stays in the running.",
    random:
      "<strong>Random strategy:</strong> no historical weighting at all — every valid combination is " +
      "equally likely. Included as the honest baseline to compare the other strategies against.",
    due:
      "<strong>Due strategy:</strong> inverts the frequency weighting (exponent −1.5), favouring the " +
      "numbers that have gone the longest without appearing."
  };

  /* ---------- rendering ---------- */

  function renderOverview(a) {
    $("statTotal").textContent = a.total_draws;
    $("statAvgWhite").textContent = a.avg_white;
    $("statAvgPb").textContent = a.avg_powerball;
    $("statFreqPb").textContent = a.most_common_pb != null ? a.most_common_pb : "—";
    $("statRange").textContent = a.span;
  }

  function renderNumbers(a) {
    $("hotWhite").innerHTML = a.hot_white
      .slice(0, 10)
      .map((p) => ball(p[0], "ball-white"))
      .join("");
    $("coldWhite").innerHTML = a.cold_white
      .slice(0, 10)
      .map((p) => ball(p[0], "ball-white"))
      .join("");
    $("hotPb").innerHTML = a.hot_pb
      .slice(0, 5)
      .map((p) => ball(p[0], "ball-red"))
      .join("");
  }

  function renderHistory(list) {
    const recent = list.slice(-20).reverse();
    $("historyBody").innerHTML = recent
      .map((d) => {
        const whites = [d.number1, d.number2, d.number3, d.number4, d.number5]
          .sort((x, y) => x - y)
          .map((n) => ball(n, "ball-white"))
          .join("");
        return (
          "<tr><td>" + d.date + "</td>" +
          '<td><div class="balls-inline">' + whites + "</div></td>" +
          '<td><div class="balls-inline">' + ball(d.powerball, "ball-red") +
          '<span style="color:#9b87c7;font-size:.85em;">×' + d.multiplier + "</span></div></td></tr>"
        );
      })
      .join("");
  }

  function renderChart(a) {
    const canvas = $("freqChart");
    if (!canvas) return;

    const isWhite = chartMode === "white";
    const labels = isWhite
      ? Array.from({ length: E.WHITE_MAX - E.WHITE_MIN + 1 }, (_, i) => String(i + E.WHITE_MIN))
      : Array.from({ length: E.POWERBALL_MAX - E.POWERBALL_MIN + 1 }, (_, i) => String(i + E.POWERBALL_MIN));
    const values = isWhite ? a.white_freq_list : a.pb_freq_list;

    if (chart) chart.destroy();

    chart = new Chart(canvas, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: isWhite ? "White Ball Frequency" : "Powerball Frequency",
          data: values,
          backgroundColor: isWhite
            ? "rgba(192, 132, 252, .65)"
            : "rgba(244, 114, 182, .65)",
          borderColor: isWhite ? "#c084fc" : "#f472b6",
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#b89cf0" } },
          title: {
            display: true,
            text: isWhite ? "White Ball Frequency (1–69)" : "Powerball Frequency (1–26)",
            color: "#b89cf0",
            font: { size: 14 }
          }
        },
        scales: {
          x: { ticks: { color: "#9b87c7", maxRotation: 60, minRotation: 0, autoSkip: true, maxTicksLimit: 20 }, grid: { color: "rgba(160,120,255,.07)" } },
          y: { ticks: { color: "#9b87c7" }, grid: { color: "rgba(160,120,255,.07)" } }
        }
      }
    });
  }

  /* ---------- prediction ---------- */

  // The UI's four labels map onto the engine's three weighted strategies
  // plus pure random.
  function engineStrategy(ui) {
    if (ui === "random") return "random";
    if (ui === "due") return "cold";
    if (ui === "frequency") return "hot";
    return "balanced"; // "balanced"
  }

  function generate() {
    const uiStrategy = $("strategy").value;
    const count = parseInt($("num_predictions").value, 10) || 3;
    const out = $("predictionOutput");

    $("strategyNote").innerHTML = STRATEGY_NOTES[uiStrategy] || "";

    out.innerHTML = '<span class="spinner"></span> <span style="color:#9b87c7;">Generating…</span>';

    // Yield a frame so the spinner paints before the (synchronous) generation
    setTimeout(function () {
      const preds = E.generatePrediction(draws, engineStrategy(uiStrategy), count);
      out.innerHTML = "";

      preds.forEach(function (p) {
        const row = document.createElement("div");
        row.style.width = "100%";
        row.style.display = "flex";
        row.style.flexWrap = "wrap";
        row.style.gap = "6px";
        row.style.alignItems = "center";
        row.style.paddingBottom = "10px";
        row.style.marginBottom = "10px";
        row.style.borderBottom = "1px solid rgba(160,120,255,.1)";

        p.white.forEach(function (n) { row.appendChild(el(ball(n, "ball-white"))); });
        const pb = el(ball(p.powerball, "ball-red"));
        pb.classList.add("label-pb");
        row.appendChild(pb);

        out.appendChild(row);
      });
    }, 30);
  }

  /* ---------- boot ---------- */

  function bind() {
    $("btnGenerate").addEventListener("click", generate);
    $("strategy").addEventListener("change", function () {
      $("strategyNote").innerHTML = STRATEGY_NOTES[$("strategy").value] || "";
    });

    $("btnWhiteFreq").addEventListener("click", function () {
      chartMode = "white";
      $("btnWhiteFreq").classList.add("active");
      $("btnPowerFreq").classList.remove("active");
      if (analysis) renderChart(analysis);
    });
    $("btnPowerFreq").addEventListener("click", function () {
      chartMode = "power";
      $("btnPowerFreq").classList.add("active");
      $("btnWhiteFreq").classList.remove("active");
      if (analysis) renderChart(analysis);
    });
  }

  async function init() {
    bind();
    $("strategyNote").innerHTML = STRATEGY_NOTES[$("strategy").value] || "";

    try {
      draws = await E.loadDraws(DATA_URL);
    } catch (err) {
      $("historyBody").innerHTML =
        '<tr class="loading-row"><td colspan="3" style="color:#fca5a5;">Could not load draw history: ' +
        escHtml(String(err.message || err)) + "</td></tr>";
      return;
    }

    analysis = E.analyzeDraws(draws);
    renderOverview(analysis);
    renderNumbers(analysis);
    renderHistory(draws);
    renderChart(analysis);
  }

  function escHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
