// static/js/cost_trend.js
const raw = window.COST_TREND_DATA || [];
const labels = raw.map(d => d.time);
const actual = raw.map(d => d.actual);
const projected = raw.map(d => d.projected ?? null);

const canvas = document.getElementById("costTrend");
if (!canvas) throw new Error("#costTrend canvas not found");
const ctx = canvas.getContext("2d");

let showProjection = false;

// -----------------------------
// Theme helpers
// -----------------------------
function isLightTheme() {
  return document.documentElement.getAttribute("data-theme") === "light";
}

function themeColors() {
  const light = isLightTheme();
  return {
    text: light ? "rgba(15,23,42,0.88)" : "rgba(235,245,255,0.85)",
    muted: light ? "rgba(15,23,42,0.65)" : "rgba(156,163,175,0.85)",
    grid: light ? "rgba(15,23,42,0.10)" : "rgba(255,255,255,0.06)",
    tooltipBg: light ? "rgba(255,255,255,0.96)" : "rgba(0,0,0,0.85)",
    tooltipText: light ? "rgba(15,23,42,0.92)" : "rgba(235,245,255,0.90)",
    tooltipBorder: light ? "rgba(15,23,42,0.12)" : "rgba(255,255,255,0.12)"
  };
}

// -----------------------------
// Area gradient
// -----------------------------
function makeAreaGradient(ctx, canvas) {
  const light = isLightTheme();
  const grad = ctx.createLinearGradient(0, 0, 0, canvas.height || 300);

  if (light) {
    // ✅ 라이트에서 면이 "확실히" 보이게
    grad.addColorStop(0, "rgba(0, 180, 255, 0.22)");
    grad.addColorStop(1, "rgba(0, 180, 255, 0.04)");
  } else {
    grad.addColorStop(0, "rgba(0, 229, 255, 0.30)");
    grad.addColorStop(1, "rgba(0, 229, 255, 0.02)");
  }

  return grad;
}

let grad = makeAreaGradient(ctx, canvas);

// -----------------------------
// Chart
// -----------------------------
const chart = new Chart(ctx, {
  type: "line",
  data: {
    labels,
    datasets: [
      {
        label: "실제 전기료",
        data: actual,
        fill: true,
        tension: 0.35,
        borderColor: "#00e5ff",
        backgroundColor: grad,
        pointBackgroundColor: "#00e5ff",
        pointBorderColor: "rgba(0,0,0,0.0)",
        pointRadius: 3,
        pointHoverRadius: 5,
        borderWidth: 2,
      },
      {
        label: "절감 후 예상",
        data: projected,
        fill: false,
        tension: 0.35,
        hidden: true,
        borderColor: "#a78bfa",
        pointBackgroundColor: "#a78bfa",
        borderWidth: 2,
        borderDash: [6, 6],
        pointRadius: 2,
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          // ✅ 초기값(테마 적용 함수에서 다시 덮어씀)
          color: "rgba(229,231,235,0.75)",
          font: { weight: "700" }
        }
      },
      tooltip: {
        backgroundColor: "rgba(0,0,0,0.85)",
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          label: (ctx) => {
            if (ctx.raw === null || ctx.raw === undefined) return "";
            return `${ctx.dataset.label}: ${Number(ctx.raw).toLocaleString()}원`;
          }
        }
      }
    },
    interaction: { intersect: false, mode: "index" },
    scales: {
      x: {
        ticks: { color: "rgba(156,163,175,0.8)" },
        grid: { color: "rgba(255,255,255,0.06)" }
      },
      y: {
        grace: "10%",
        ticks: {
          color: "rgba(156,163,175,0.8)",
          callback: (v) => Number(v).toLocaleString()
        },
        title: { display: true, text: "전기료(원)", color: "rgba(156,163,175,0.85)" },
        grid: { color: "rgba(255,255,255,0.06)" }
      }
    }
  }
});

// -----------------------------
// ✅ Theme apply (없던 함수 "추가")
// -----------------------------
function applyThemeToCostTrend() {
  const c = themeColors();

  // 그라데이션 재생성(테마별)
  grad = makeAreaGradient(ctx, canvas);
  chart.data.datasets[0].backgroundColor = grad;

  // legend
  chart.options.plugins.legend.labels.color = c.text;

  // tooltip
  chart.options.plugins.tooltip.backgroundColor = c.tooltipBg;
  chart.options.plugins.tooltip.borderColor = c.tooltipBorder;
  chart.options.plugins.tooltip.titleColor = c.tooltipText;
  chart.options.plugins.tooltip.bodyColor = c.tooltipText;

  // ticks + grid
  chart.options.scales.x.ticks.color = c.muted;
  chart.options.scales.y.ticks.color = c.muted;
  chart.options.scales.y.title.color = c.muted;

  chart.options.scales.x.grid.color = c.grid;
  chart.options.scales.y.grid.color = c.grid;

  chart.update();
}

// 최초 1회 적용 + 테마 전환 반영
applyThemeToCostTrend();
window.addEventListener("themechange", applyThemeToCostTrend);
window.addEventListener("resize", applyThemeToCostTrend);

// -----------------------------
// Projection toggle button
// -----------------------------
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("toggleProjection");
  if (!btn) return;

  btn.addEventListener("click", () => {
    showProjection = !showProjection;
    chart.data.datasets[1].hidden = !showProjection;
    chart.update();
  });
});