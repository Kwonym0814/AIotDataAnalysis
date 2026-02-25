// static/js/cost_trend.js
const raw = window.COST_TREND_DATA || [];
const labels = raw.map(d => d.time);
const actual = raw.map(d => d.actual);
const projected = raw.map(d => d.projected ?? null);

const canvas = document.getElementById("costTrend");
const ctx = canvas.getContext("2d");

let showProjection = false;

// ✅ 다크테마용 그라데이션(에어리어)
const grad = ctx.createLinearGradient(0, 0, 0, canvas.height || 300);
grad.addColorStop(0, "rgba(0, 229, 255, 0.30)"); // 상단 진하게
grad.addColorStop(1, "rgba(0, 229, 255, 0.02)"); // 하단 거의 투명

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

        // ✅ 테마 색감
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

        // ✅ 보조색(탭 그라데이션과 자연스럽게)
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
    maintainAspectRatio: false, // ✅ div 높이 그대로 따라가게

    plugins: {
      legend: {
        labels: { color: "rgba(229,231,235,0.75)" }
      },
      tooltip: {
        backgroundColor: "rgba(0,0,0,0.85)",
        padding: 12,
        label: (ctx) => {
          if (ctx.raw === null || ctx.raw === undefined) return null; // 표시 안 함
          return `${ctx.dataset.label}: ${Number(ctx.raw).toLocaleString()}원`;
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
        grace: "10%",   // ✅ 상단 여유
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

// ✅ 안전한 이벤트 바인딩(버튼이 나중에 렌더되어도 동작)
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("toggleProjection");
  if (!btn) return;

  btn.addEventListener("click", () => {
    showProjection = !showProjection;
    chart.data.datasets[1].hidden = !showProjection;
    chart.update();
  });
});

