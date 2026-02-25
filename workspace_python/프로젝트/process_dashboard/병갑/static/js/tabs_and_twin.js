// static/js/tabs_and_twin.js
(() => {
(() => {
  const tabBtns = Array.from(document.querySelectorAll(".tab-btn"));
  const views = Array.from(document.querySelectorAll("[data-view]"));

  function setActive(tabName) {
    // buttons
    tabBtns.forEach(btn => {
      const on = btn.dataset.tab === tabName;
      btn.dataset.active = on ? "true" : "false";
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });

    // views
    views.forEach(v => {
      const on = v.dataset.view === tabName;
      v.classList.toggle("active", on);
    });
  }

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const tabName = btn.dataset.tab;
      if (!tabName) return;
      setActive(tabName);
    });
  });

  // 최초 1회: data-active="true"인 버튼 기준으로 초기화
  const init = tabBtns.find(b => b.dataset.active === "true")?.dataset.tab || "energy";
  setActive(init);
})();



  // ---------- Tabs (피그마처럼 화면 전환) ----------
  const tabBtns = document.querySelectorAll(".tab-btn");
  const views = document.querySelectorAll("[data-view]");

  function activate(tabName){
    tabBtns.forEach(b => b.dataset.active = (b.dataset.tab === tabName ? "true" : "false"));
    views.forEach(v => v.classList.toggle("active", v.dataset.view === tabName));
  }

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => activate(btn.dataset.tab));
  });

  // ---------- Twin (공정흐름 섹션) ----------
  const stage = document.getElementById("twinStage");
  const sidebar = document.getElementById("twinSidebar");
  const closePanelBtn = document.getElementById("closePanelBtn");

  const titleEl = document.getElementById("twinTitle");
  const moduleTagEl = document.getElementById("twinModuleTag");
  const inputEl = document.getElementById("twinInput");
  const runBtn = document.getElementById("runAnalyzeBtn");

  const resultWrap = document.getElementById("twinResult");
  const statusEl = document.getElementById("twinStatusText");

  let selectedModule = null;
  let twinChart = null;

  function openPanel(moduleName){
    selectedModule = moduleName;
    titleEl.textContent = `${moduleName} 공정 리포트`;
    moduleTagEl.textContent = moduleName;

    sidebar.classList.add("active");
    stage.classList.add("panel-open");

    sidebar.classList.remove("expanded");
    resultWrap.style.display = "none";
    statusEl.textContent = "상태: -";
    inputEl.value = "";

    setTimeout(() => inputEl.focus(), 250);
  }

  function closePanel(){
    sidebar.classList.remove("active", "expanded");
    stage.classList.remove("panel-open");
    resultWrap.style.display = "none";
    selectedModule = null;
  }

  async function requestAnalysis(){
    const val = inputEl.value;
    if (!selectedModule || val === "" || val === null) return;

    sidebar.classList.add("expanded");
    resultWrap.style.display = "block";

    let resJson;
    try{
      const res = await fetch("/api/analyze", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ module: selectedModule, value: val })
      });
      resJson = await res.json();
    }catch(e){
      statusEl.textContent = "상태: API 호출 실패";
      return;
    }

    statusEl.textContent = `상태: ${resJson.status || "-"}`;
    drawTwinChart(resJson.labels || [], resJson.trend || []);
  }

function isLightTheme() {
  return document.documentElement.getAttribute("data-theme") === "light";
}

function getTwinThemeColors() {
  const light = isLightTheme();
  return {
    tick: light ? "rgba(15,23,42,0.65)" : "rgba(156,163,175,0.80)",
    grid: light ? "rgba(15,23,42,0.10)" : "rgba(255,255,255,0.06)",
    tooltipBg: light ? "rgba(255,255,255,0.96)" : "rgba(0,0,0,0.85)",
    tooltipText: light ? "rgba(15,23,42,0.92)" : "rgba(235,245,255,0.90)",
    tooltipBorder: light ? "rgba(15,23,42,0.12)" : "rgba(255,255,255,0.12)"
  };
}
function drawTwinChart(labels, trend) {
  const canvas = document.getElementById("twinChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (twinChart) twinChart.destroy();

  const theme = getTwinThemeColors();

  twinChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: trend,
        borderColor: "#00e5ff",
        pointBackgroundColor: "#00e5ff",
        backgroundColor: "rgba(0,229,255,0.06)",
        borderWidth: 2,
        tension: 0.4,
        pointRadius: 3,
        fill: true,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: theme.tooltipBg,
          borderColor: theme.tooltipBorder,
          borderWidth: 1,
          titleColor: theme.tooltipText,
          bodyColor: theme.tooltipText,
          displayColors: false,
          padding: 10
        }
      },
      scales: {
        x: {
          ticks: { color: theme.tick },
          grid: { display: false }
        },
        y: {
          ticks: { color: theme.tick },
          grid: { color: theme.grid }
        }
      }
    }
  });
}

window.addEventListener("themechange", () => {
  if (!twinChart) return;
  const theme = getTwinThemeColors();

  twinChart.options.scales.x.ticks.color = theme.tick;
  twinChart.options.scales.y.ticks.color = theme.tick;
  twinChart.options.scales.y.grid.color  = theme.grid;

  if (twinChart.options.plugins?.tooltip) {
    twinChart.options.plugins.tooltip.backgroundColor = theme.tooltipBg;
    twinChart.options.plugins.tooltip.borderColor = theme.tooltipBorder;
    twinChart.options.plugins.tooltip.titleColor = theme.tooltipText;
    twinChart.options.plugins.tooltip.bodyColor = theme.tooltipText;
  }

  twinChart.update();
});




  // 이벤트
  closePanelBtn?.addEventListener("click", closePanel);
  runBtn?.addEventListener("click", requestAnalysis);
  inputEl?.addEventListener("keydown", (e) => { if (e.key === "Enter") requestAnalysis(); });

  document.querySelectorAll(".clickable-area").forEach(el => {
    el.addEventListener("click", () => {
      // 공정 흐름 탭으로 자동 이동 (피그마 UX에 더 가까움)
      activate("process");
      openPanel(el.getAttribute("data-module"));
    });
  });
})();

// ==============================
// Theme Toggle (Dark <-> Light)
// ==============================
(() => {
  const root = document.documentElement;
  const btn = document.getElementById("themeToggle");
  const icon = document.getElementById("themeIcon");
  if (!btn) return;

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    if (icon) icon.textContent = (theme === "light") ? "☀️" : "🌙";

    // 차트들이 테마 변경을 감지할 수 있게 이벤트 발사
    window.dispatchEvent(new CustomEvent("themechange", { detail: { theme } }));
  }

  window.dispatchEvent(new Event("themechange"));

  // 초기 테마: 저장값 우선, 없으면 다크
  const saved = localStorage.getItem("theme");
  setTheme(saved === "light" ? "light" : "dark");

  btn.addEventListener("click", () => {
    const cur = root.getAttribute("data-theme") || "dark";
    setTheme(cur === "light" ? "dark" : "light");
  });
})();
