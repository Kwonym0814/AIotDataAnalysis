// static/js/cost_trend.js
const raw = window.COST_TREND_DATA || [];

// =============================
// Last point pulse (TV ripple)
// =============================
let costTrendRafId = null;

// 전역 상태(플러그인이 이 값만 보고 판단)
window.__SHOW_PROJECTION__ = window.__SHOW_PROJECTION__ ?? false;

const CostTrendLastPointPulse = {
  id: "costTrendLastPointPulse",
  afterDatasetsDraw(chart, args, pluginOptions) {
    const { ctx } = chart;

    // ✅ 요구 동작:
    // - 점선 OFF: 실선(0)만 펄스
    // - 점선 ON : 실선(0) + 점선(1) 둘 다 펄스
    const wantProjection = (window.__SHOW_PROJECTION__ === true);
    const targetIdxs = wantProjection ? [0, 1] : [0];

    targetIdxs.forEach((datasetIndex) => {
      const meta = chart.getDatasetMeta(datasetIndex);
      if (!meta || !meta.data || meta.data.length === 0) return;

      const ds = chart.data.datasets[datasetIndex] || {};
      const baseColor =
        (typeof ds.borderColor === "string" ? ds.borderColor : null) ||
        (pluginOptions?.color ?? "#00e5ff");

      function toRgba(color, a) {
        if (!color) return `rgba(0,229,255,${a})`;
        const hex = color.replace("#", "");
        if (hex.length === 6) {
          const r = parseInt(hex.slice(0, 2), 16);
          const g = parseInt(hex.slice(2, 4), 16);
          const b = parseInt(hex.slice(4, 6), 16);
          return `rgba(${r},${g},${b},${a})`;
        }
        return (color.startsWith("rgb") ? color.replace(/[\d.]+\)$/g, `${a})`) : `rgba(0,229,255,${a})`);
      }

      const minR = pluginOptions?.minRadius ?? 3;
      const maxR = pluginOptions?.maxRadius ?? 16;
      const speed = pluginOptions?.speed ?? 1200;

      // 링 컬러는 데이터셋 색을 자동 추종
      const ringBaseA = wantProjection ? 0.32 : 0.35; // 느낌만 약간 조절
      const ringColorBase = pluginOptions?.ringColor ?? toRgba(baseColor, ringBaseA);

      const dataArr = ds.data ?? [];
      let lastIdx = dataArr.length - 1;
      while (lastIdx >= 0 && (dataArr[lastIdx] == null || Number.isNaN(Number(dataArr[lastIdx])))) lastIdx--;
      if (lastIdx < 0) return;

      const pt = meta.data[lastIdx];
      if (!pt) return;

      const x = pt.x;
      const y = pt.y;

      const tt = (Date.now() % speed) / speed;
      const ease = tt * (2 - tt);     // easeOutQuad
      const r = minR + (maxR - minR) * ease;
      const alpha = 1 - tt;

      ctx.save();

      // 1) 중심 점
      ctx.beginPath();
      ctx.fillStyle = baseColor;
      ctx.arc(x, y, minR + 2, 0, Math.PI * 2);
      ctx.fill();

      // 2) 리플 링
      ctx.beginPath();
      ctx.strokeStyle = ringColorBase.replace(/[\d.]+\)$/g, `${(0.35 * alpha).toFixed(3)})`);
      ctx.lineWidth = 2;
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.stroke();

      // 3) 글로우
      ctx.beginPath();
      ctx.fillStyle = toRgba(baseColor, (0.10 * alpha).toFixed(3));
      ctx.arc(x, y, r * 0.65, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    });
  }
};

const labels = raw.map(d => d.time);
const actual = raw.map(d => d.actual);
const projected = raw.map(d => d.projected ?? null);

const canvas = document.getElementById("costTrend");
if (!canvas) {
  console.warn("[cost_trend] #costTrend canvas not found");
} else {
  const ctx = canvas.getContext("2d");

  // 초기: 점선 OFF
  let showProjection = false;
  window.__SHOW_PROJECTION__ = showProjection;

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
          fill: "start",
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
          hidden: true, // ✅ 초기엔 숨김(요구사항)
          borderColor: "#a78bfa",
          pointBackgroundColor: "#a78bfa",
          borderWidth: 2,
          borderDash: [6, 6],
          pointRadius: 2,
          pointHoverRadius: 4,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
          duration: 450,
          easing: "easeOutQuart",
        },
        animations: {
          x: { duration: 450, easing: "easeOutQuart" },
          y: { duration: 450, easing: "easeOutQuart" },
        },
      plugins: {
        legend: {
          labels: {
            color: "rgba(229,231,235,0.75)",
            font: { weight: "700" }
          },
          // ✅ legend에서 "절감 후 예상" 클릭해도 우리의 showProjection 상태가 같이 바뀌게
          onClick: (e, legendItem, legend) => {
            const idx = legendItem?.datasetIndex ?? -1;

            // 1번(절감 후 예상)만 우리 로직으로 제어
            if (idx === 1) {
              showProjection = !showProjection;
              window.__SHOW_PROJECTION__ = showProjection;
              chart.data.datasets[1].hidden = !showProjection;
              chart.update("none");
              requestAnimationFrame(() => chart && chart.update("none"));
              return;
            }

            // 나머지는 Chart.js 기본 동작
            const defaultOnClick = Chart.defaults.plugins.legend.onClick;
            if (typeof defaultOnClick === "function") {
              defaultOnClick(e, legendItem, legend);
            }
          }
        },
        tooltip: {
          backgroundColor: "rgba(0,0,0,0.85)",
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          callbacks: {
            label: (ctx2) => {
              if (ctx2.raw === null || ctx2.raw === undefined) return "";
              return `${ctx2.dataset.label}: ${Number(ctx2.raw).toLocaleString()}원`;
            }
          }
        },
        // 플러그인 옵션(원하면 여기 값만 조정)
        costTrendLastPointPulse: {
          minRadius: 3,
          maxRadius: 16,
          speed: 1200
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
    },
    plugins: [CostTrendLastPointPulse],
  });

  // -----------------------------
  // Theme apply
  // -----------------------------
  function applyThemeToCostTrend() {
    const c = themeColors();

    grad = makeAreaGradient(ctx, canvas);
    chart.data.datasets[0].backgroundColor = grad;

    // legend
    chart.options.plugins.legend.labels.color = c.text;

    // tooltip
    chart.options.plugins.tooltip.backgroundColor = c.tooltipBg;
    chart.options.plugins.tooltip.borderColor = c.tooltipBorder;
    chart.options.plugins.tooltip.borderWidth = 1;
    chart.options.plugins.tooltip.titleColor = c.tooltipText;
    chart.options.plugins.tooltip.bodyColor = c.tooltipText;

    // ticks + grid
    chart.options.scales.x.ticks.color = c.muted;
    chart.options.scales.y.ticks.color = c.muted;
    chart.options.scales.y.title.color = c.muted;

    chart.options.scales.x.grid.color = c.grid;
    chart.options.scales.y.grid.color = c.grid;

    chart.update("none");
  }

  applyThemeToCostTrend();
  window.addEventListener("themechange", applyThemeToCostTrend);
  window.addEventListener("resize", applyThemeToCostTrend);

  // ✅ 펄스 애니메이션 루프 (플러그인 훅 호출용)
  if (costTrendRafId) cancelAnimationFrame(costTrendRafId);

  const costTrendTick = () => {
    if (!chart) return;
    chart.draw(); // ✅ 리플 오버레이만 부드럽게 (라인/축 재계산 없음)
    costTrendRafId = requestAnimationFrame(costTrendTick);
  };

  costTrendRafId = requestAnimationFrame(costTrendTick);

    // -----------------------------
    // Projection toggle button
    // -----------------------------
    document.addEventListener("DOMContentLoaded", () => {
      const btn = document.getElementById("toggleProjection");
      if (!btn) return;

      btn.addEventListener("click", () => {
        showProjection = !showProjection;
        window.__SHOW_PROJECTION__ = showProjection;
        chart.data.datasets[1].hidden = !showProjection;

        chart.update(); // ✅ 토글은 부드럽게
      });
    });

    // (선택) 외부에서 전체 데이터 갈아끼울 때 훅
    window.updateCostTrendData = (newRows) => {
      try {
        const rows = newRows || [];
        chart.data.labels = rows.map(d => d.time);
        chart.data.datasets[0].data = rows.map(d => d.actual);
        chart.data.datasets[1].data = rows.map(d => d.projected ?? null);

        chart.update("none"); // ✅ 전체 교체는 즉시 반영(원하면 chart.update()로 바꿔도 됨)
      } catch (e) {
        console.warn("[cost_trend] updateCostTrendData failed", e);
      }
    };

    // ✅ append: “밑에서 끌어올림”만 제거 + 토글 부드러움 유지
    window.appendCostTrendPoint = (pt) => {
      try {
        if (!pt) return;

        chart.data.labels.push(pt.time);
        chart.data.datasets[0].data.push(pt.actual);
        chart.data.datasets[1].data.push(pt.projected ?? null);

        const MAX_POINTS = 60;
        if (chart.data.labels.length > MAX_POINTS) {
          chart.data.labels.shift();
          chart.data.datasets[0].data.shift();
          chart.data.datasets[1].data.shift();
        }

        const prevYDuration = chart.options.animations?.y?.duration;
        chart.options.animations.y.duration = 0;

        chart.update(); // ✅ update("none") 아님

        chart.options.animations.y.duration = prevYDuration ?? 450;
      } catch (e) {
        console.warn("[cost_trend] appendCostTrendPoint failed", e);
      }
    };


// ================================
// 🔥 하드코딩 실시간 X축 증가 테스트
// ================================
(function testRealtimeAppend() {
  let idx = 0;

  setInterval(() => {
    const lastActual =
      chart.data.datasets[0].data[chart.data.datasets[0].data.length - 1] || 35000;

    const nextVal = Math.round(
      lastActual + (Math.random() - 0.5) * 800
    );

    const timeLabel = `T${idx++}`;

    window.appendCostTrendPoint({
      time: timeLabel,
      actual: nextVal,
      projected: nextVal * 0.88
    });

  }, 1000);
})();



}