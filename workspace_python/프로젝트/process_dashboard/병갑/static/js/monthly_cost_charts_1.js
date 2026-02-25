// static/js/monthly_cost_charts_1.js
// ✅ 월별 전기료 추이: 캡슐 바 + 상단 축약 라벨 + 상단 링
// ✅ (단위: ...)는 캔버스 아래 DOM으로 고정(리사이즈해도 안 튐)
// ✅ 라이트/다크 테마 전환 시 축/그리드/툴팁/단위 색 자동 동기화

(() => {
  // -----------------------------
  // 0) Data (없으면 더미)
  // -----------------------------
  const forecast = window.MONTHLY_FORECAST || { before: 18500000, after: 15200000 };

  const monthLabels =
    Array.isArray(window.MONTH_LABELS) && window.MONTH_LABELS.length === 12
      ? window.MONTH_LABELS
      : ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"];

  const monthlyCosts =
    Array.isArray(window.MONTHLY_COSTS) && window.MONTHLY_COSTS.length === 12
      ? window.MONTHLY_COSTS
      : [12000000,13500000,14200000,15000000,16800000,17500000,18200000,19000000,17600000,16200000,15500000,17000000];

  const highlightIndex = Number.isInteger(window.HIGHLIGHT_MONTH_INDEX) ? window.HIGHLIGHT_MONTH_INDEX : 3;

  // -----------------------------
  // 1) Theme helpers
  // -----------------------------
  function isLightTheme() {
    return document.documentElement.getAttribute("data-theme") === "light";
  }

  function axisText() {
    return isLightTheme() ? "rgba(15,23,42,0.78)" : "rgba(235,245,255,0.72)";
  }

  function axisGrid() {
    return isLightTheme() ? "rgba(15,23,42,0.10)" : "rgba(255,255,255,0.08)";
  }

  function tooltipNow() {
    const light = isLightTheme();
    return {
      backgroundColor: light ? "rgba(255,255,255,0.96)" : "rgba(10,12,18,0.96)",
      borderColor: light ? "rgba(15,23,42,0.12)" : "rgba(255,255,255,0.12)",
      borderWidth: 1,
      padding: 12,
      titleColor: light ? "rgba(15,23,42,0.92)" : "rgba(235,245,255,0.90)",
      bodyColor: light ? "rgba(15,23,42,0.92)" : "rgba(235,245,255,0.90)",
      displayColors: false
    };
  }

  function unitTextColor() {
    return isLightTheme() ? "rgba(15,23,42,0.55)" : "rgba(235,245,255,0.55)";
  }

  function fmtWon(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return String(v);
    return n.toLocaleString("ko-KR");
  }

  function formatCompactWon(n) {
    const v = Number(n);
    if (!Number.isFinite(v)) return String(n);
    const abs = Math.abs(v);
    if (abs >= 1e9) return (v / 1e9).toFixed(1).replace(/\.0$/, "") + "B";
    return (v / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
  }

  function getUnitCaption(maxVal) {
    const abs = Math.abs(Number(maxVal));
    if (!Number.isFinite(abs)) return "(단위: 원)";
    if (abs >= 1e9) return "(단위: B원 = 1,000,000,000원)";
    return "(단위: M원 = 1,000,000원)";
  }

  const maxMonthly = Math.max(...monthlyCosts.map(v => Number(v) || 0));
  const unitCaption = getUnitCaption(maxMonthly);

  // -----------------------------
  // 2) Plugin: 상단 라벨 + 링
  // -----------------------------
  const CapsuleTopLabelPlugin = {
    id: "capsuleTopLabelPlugin",
    afterDatasetsDraw(chart, args, pluginOptions) {
      const { ctx } = chart;
      const meta = chart.getDatasetMeta(0);
      if (!meta || !meta.data) return;

      const data = chart.data.datasets[0].data;
      const fontSize = pluginOptions?.fontSize ?? 12;
      const ringR = pluginOptions?.ringRadius ?? 6;
      const ringStrokeW = pluginOptions?.ringStrokeWidth ?? 2;

      ctx.save();
      ctx.font = `800 ${fontSize}px system-ui, -apple-system, Segoe UI, Roboto, Arial`;
      ctx.textAlign = "center";
      ctx.textBaseline = "bottom";

      meta.data.forEach((bar, i) => {
        const x = bar.x;
        const yTop = bar.y;
        const value = data[i];
        const txt = formatCompactWon(value);

        const safeGap = ringR + ringStrokeW + 10;
        const desiredY = yTop - safeGap;
        const yLabel = Math.max(desiredY, chart.chartArea.top + 12);

        // 외곽선(배경 상관없이 또렷하게)
        ctx.lineWidth = 3;
        ctx.strokeStyle = "rgba(0,0,0,0.55)";
        ctx.strokeText(txt, x, yLabel);

        ctx.fillStyle = "#ffffff";
        ctx.fillText(txt, x, yLabel);

        // 링(흰색)
        ctx.beginPath();
        ctx.arc(x, yTop, ringR, 0, Math.PI * 2);
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();
      });

      ctx.restore();
    }
  };

  // -----------------------------
  // 3) (단위: ...) DOM 캡션을 캔버스 아래 고정
  // -----------------------------
  function ensureUnitCaptionUnderCanvas(canvas, text) {
    const parent = canvas?.parentElement;
    if (!parent) return;

    parent.classList.add("parent-flex-fix");

    // 부모를 세로 플렉스로: (캔버스 위 / 캡션 아래)
    const ps = getComputedStyle(parent);
    if (ps.display !== "flex") {
      parent.style.display = "flex";
      parent.style.flexDirection = "column";
      parent.style.minHeight = "0";
    }
    canvas.style.flex = "1 1 auto";
    canvas.style.minHeight = "0";

    let el = parent.querySelector(".unit-caption");
    if (!el) {
      el = document.createElement("div");
      el.className = "unit-caption";
      parent.appendChild(el);

      Object.assign(el.style, {
        marginTop: "14px",      // ✅ 월 라벨 아래로 더 띄움
        paddingBottom: "6px",
        textAlign: "center",
        fontSize: "12px",
        fontWeight: "700",
        lineHeight: "1",
        userSelect: "none",
        pointerEvents: "none",
        opacity: "0.78",
      });
    }

    el.style.color = unitTextColor();
    el.textContent = text;
  }

  // -----------------------------
  // 4) Chart instances
  // -----------------------------
  let forecastChart = null;
  let monthlyTrendChart = null;

  // 4-A) 이번 달 예측 전기료 (가로 바)
  const fCanvas = document.getElementById("monthlyForecastBar");
  if (fCanvas) {
    const fctx = fCanvas.getContext("2d");

    forecastChart = new Chart(fctx, {
      type: "bar",
      data: {
        labels: ["최적화 전", "최적화 후"],
        datasets: [{
          data: [forecast.before, forecast.after],
          borderRadius: 12,
          backgroundColor: [
            "rgba(148,163,184,0.88)", // 전: slate
            "rgba(0,160,255,0.95)"    // 후: blue
          ],
          borderColor: [
            "rgba(15,23,42,0.18)",
            "rgba(0,180,255,0.20)"
          ],
          borderWidth: 1
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: Object.assign({}, tooltipNow(), {
            callbacks: {
              label: (ctx) => `${ctx.label}: ${fmtWon(ctx.raw)}원`
            }
          })
        },
        scales: {
          x: {
            ticks: { color: axisText(), callback: (v) => fmtWon(v), font: { weight: "700" } },
            grid: { color: axisGrid() }
          },
          y: {
            ticks: { color: axisText(), font: { weight: "800" } },
            grid: { display: false }
          }
        }
      }
    });
  }

  // 4-B) 월별 전기료 추이 (캡슐 바)
  const mCanvas = document.getElementById("monthlyCostTrend");
  if (mCanvas) {
    const mctx = mCanvas.getContext("2d");
    ensureUnitCaptionUnderCanvas(mCanvas, unitCaption);

    const barColors = monthlyCosts.map((_, i) =>
      i === highlightIndex ? "rgba(120,230,120,0.92)" : "rgba(0,160,255,0.92)"
    );

    monthlyTrendChart = new Chart(mctx, {
      type: "bar",
      data: {
        labels: monthLabels,
        datasets: [{
          data: monthlyCosts,
          borderRadius: { topLeft: 10, topRight: 10, bottomLeft: 0, bottomRight: 0 },
          borderSkipped: "bottom",
          borderWidth: 0,
          backgroundColor: barColors,
          hoverBackgroundColor: barColors,

          // ✅ 고정 두께 제거 → 리사이즈 최적화
          maxBarThickness: 52,
          categoryPercentage: 0.9,
          barPercentage: 0.95
        }]
      },
      plugins: [CapsuleTopLabelPlugin],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        layout: { padding: { top: 6, bottom: 6 } },
        plugins: {
          legend: { display: false },
          tooltip: Object.assign({}, tooltipNow(), {
            callbacks: {
              title: (items) => items?.[0]?.label ?? "",
              label: (ctx) => `${fmtWon(ctx.raw)}원`
            }
          }),
          capsuleTopLabelPlugin: { fontSize: 12, ringRadius: 6, ringStrokeWidth: 2 }
        },
        scales: {
          x: {
            ticks: {
              color: axisText(),
              font: { weight: "800" },
              callback: function (value, index) {
                if (index === highlightIndex) return "이번달";
                return this.getLabelForValue(value);
              }
            },
            grid: { display: false }
          },
          y: {
            display: false,
            suggestedMax: maxMonthly * 1.06,
            grace: "10%"
          }
        }
      }
    });
  }

  // -----------------------------
  // 5) Theme apply + auto sync
  // -----------------------------
  function applyThemeToCharts() {
    // Forecast
    if (forecastChart) {
      const t = tooltipNow();
      forecastChart.options.scales.x.ticks.color = axisText();
      forecastChart.options.scales.x.grid.color = axisGrid();
      forecastChart.options.scales.y.ticks.color = axisText();

      forecastChart.options.plugins.tooltip.backgroundColor = t.backgroundColor;
      forecastChart.options.plugins.tooltip.borderColor = t.borderColor;
      forecastChart.options.plugins.tooltip.titleColor = t.titleColor;
      forecastChart.options.plugins.tooltip.bodyColor = t.bodyColor;

      forecastChart.update();
    }

    // Monthly trend
    if (monthlyTrendChart) {
      const t = tooltipNow();
      monthlyTrendChart.options.scales.x.ticks.color = axisText();

      monthlyTrendChart.options.plugins.tooltip.backgroundColor = t.backgroundColor;
      monthlyTrendChart.options.plugins.tooltip.borderColor = t.borderColor;
      monthlyTrendChart.options.plugins.tooltip.titleColor = t.titleColor;
      monthlyTrendChart.options.plugins.tooltip.bodyColor = t.bodyColor;

      monthlyTrendChart.update();
    }

    // Unit caption recolor
    const mc = document.getElementById("monthlyCostTrend");
    if (mc) ensureUnitCaptionUnderCanvas(mc, unitCaption);
  }

  // themechange 이벤트가 있으면 그걸로, 없어도 MutationObserver로 따라감
  window.addEventListener("themechange", applyThemeToCharts);
  window.addEventListener("resize", applyThemeToCharts);

  const mo = new MutationObserver((mutList) => {
    for (const m of mutList) {
      if (m.type === "attributes" && m.attributeName === "data-theme") {
        applyThemeToCharts();
      }
    }
  });
  mo.observe(document.documentElement, { attributes: true });

  // 최초 1회
  applyThemeToCharts();
})();