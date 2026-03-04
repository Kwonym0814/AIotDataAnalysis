
// static/js/tabs_and_twin.js
// ✅ 베이스용: 탭 전환 + 테마 토글만 담당
// (공정 Twin 로직은 twin_overlay.js로 분리)

(() => {
  const tabBtns = Array.from(document.querySelectorAll(".tab-btn"));
  const views = Array.from(document.querySelectorAll("[data-view]"));

  function setActive(tabName) {
    tabBtns.forEach(btn => {
      const on = btn.dataset.tab === tabName;
      btn.dataset.active = on ? "true" : "false";
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });

    views.forEach(v => {
      v.classList.toggle("active", v.dataset.view === tabName);
    });
  }

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const tabName = btn.dataset.tab;
      if (!tabName) return;
      setActive(tabName);
    });
  });

  const init = tabBtns.find(b => b.dataset.active === "true")?.dataset.tab || "energy";
  setActive(init);
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
    window.dispatchEvent(new CustomEvent("themechange", { detail: { theme } }));
  }

  const saved = localStorage.getItem("theme");
  setTheme(saved === "light" ? "light" : "dark");

  btn.addEventListener("click", () => {
    const cur = root.getAttribute("data-theme") || "dark";
    setTheme(cur === "light" ? "dark" : "light");
  });
})();
