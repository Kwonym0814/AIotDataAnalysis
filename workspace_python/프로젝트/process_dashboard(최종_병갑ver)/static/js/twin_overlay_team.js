// static/js/twin_overlay_team.js
// Team-style: Stage click -> right panel opens, ALWAYS shows 3 items,
// and the selected stage expands (slider/buttons), others stay collapsed.

(() => {
  const btn = document.getElementById("openTwinBtn");
  const stageLayer = document.getElementById("sfStageLayer");
  const panel = document.getElementById("sfConfigPanel");
  const closeX = document.getElementById("sfConfigClose");
  const resetAll = document.getElementById("sfResetAll");
  const bodyEl = document.getElementById("sfConfigBody");

  if (!btn || !stageLayer || !panel || !closeX || !bodyEl) return;

  // ---- TEAM-LIKE STAGES ----
  // 필요하면 window.TWIN_INLINE_STAGES로 외부 주입 가능
  const DEFAULT = [
    {
      id: "stage1",
      stageLabel: "STAGE 01",
      live: true,
      value: 1242,
      sub: "BLAST FURNACE (°C)",
      coords: { x: 24, y: 28 },
      panel: { title: "BLAST FURNACE", value: 1239, unit: "°C", accent: "cyan" }
    },
    {
      id: "stage2",
      stageLabel: "STAGE 02",
      live: true,
      value: 452,
      sub: "OXYGEN SUPPLY (NM³/H)",
      coords: { x: 54, y: 47 },
      panel: {
        title: "OXYGEN SUPPLY",
        value: 460,
        unit: "Nm³ / h",
        accent: "blue",
        slider: { label: "SAFETY THRESHOLD", min: 0, max: 1000, step: 1, value: 465, unit: "NM³/H" }
      }
    },
    {
      id: "stage3",
      stageLabel: "STAGE 03",
      live: true,
      value: 8.7,
      sub: "ROLLING MILL (M/S)",
      coords: { x: 73, y: 62 },
      panel: { title: "ROLLING MILL", value: 8.4, unit: "m/s", accent: "emerald" }
    }
  ];

  const fmt = (v) =>
    typeof v === "number"
      ? (Number.isInteger(v) ? v.toLocaleString() : String(v))
      : String(v);

  const getStages = () => {
    const ext = window.TWIN_INLINE_STAGES;
    if (Array.isArray(ext) && ext.length) return ext;
    return DEFAULT;
  };

  let activeId = getStages()[0]?.id ?? "stage1";

  const openPanel = () => panel.classList.add("is-open");
  const closePanel = () => panel.classList.remove("is-open");
  const togglePanel = () => panel.classList.toggle("is-open");

  btn.addEventListener("click", togglePanel);
  closeX.addEventListener("click", closePanel);

  if (resetAll) {
    resetAll.addEventListener("click", () => {
      delete window.TWIN_INLINE_STAGES;
      activeId = getStages()[0]?.id ?? "stage1";
      renderStages();
      renderPanel();
      closePanel();
    });
  }

  function renderStages() {
    const stages = getStages();
    stageLayer.innerHTML = "";

    for (const s of stages) {
      const card = document.createElement("div");
      card.className = "sf-stage-card sf-glass";
      card.style.left = `${s.coords.x}%`;
      card.style.top = `${s.coords.y}%`;

      card.innerHTML = `
        <div class="sf-stage-card__top">
          <div class="sf-stage-pill">${s.stageLabel}</div>
          <div class="sf-live"><span class="sf-live-dot"></span>LIVE</div>
        </div>
        <div class="sf-stage-card__body">
          <div class="sf-stage-val">${fmt(s.value)}</div>
          <div class="sf-stage-sub">${s.sub}</div>
        </div>
      `;

      card.addEventListener("click", () => {
        activeId = s.id;
        openPanel();
        renderPanel(); // ✅ 패널은 "항상 3개" + active만 확장
      });

      stageLayer.appendChild(card);
    }
  }

  function renderPanel() {
    const stages = getStages();

    const itemsHtml = stages
      .map((s) => {
        const isActive = s.id === activeId;
        const p = s.panel ?? {};
        const slider = p.slider;

        return `
          <div class="sf-acc-item ${isActive ? "is-active" : ""}" data-stage="${s.id}">
            <button class="sf-acc-head" type="button">
              <div class="sf-acc-left">
                <div class="sf-acc-title">${p.title ?? s.sub ?? "STAGE"}</div>
              </div>
              <div class="sf-acc-right">
                <div class="sf-acc-val">${fmt(p.value ?? s.value)}<span class="sf-acc-unit">${p.unit ?? ""}</span></div>
              </div>
            </button>

            <div class="sf-acc-body">
              ${
                slider
                  ? `
                <div class="sf-acc-row">
                  <div class="sf-acc-label">${slider.label}</div>
                  <div class="sf-acc-mini" id="sfMiniVal">${fmt(slider.value)}<span class="sf-acc-unit">${slider.unit}</span></div>
                </div>
                <input class="sf-range" id="sfRange"
                  type="range" min="${slider.min}" max="${slider.max}" step="${slider.step ?? 1}" value="${slider.value}">
                <div class="sf-actions">
                  <button class="sf-btn" data-act="reset">RESET VALUE</button>
                  <button class="sf-btn danger" data-act="remove">REMOVE</button>
                </div>
              `
                  : `
                <div class="sf-actions">
                  <button class="sf-btn" data-act="reset">RESET VALUE</button>
                  <button class="sf-btn danger" data-act="remove">REMOVE</button>
                </div>
              `
              }
            </div>
          </div>
        `;
      })
      .join("");

    bodyEl.innerHTML = `
      <div class="sf-panel__title">
        <div>
          <h3>SYSTEM CONFIG</h3>
          <button class="sf-panel__reset" type="button" id="sfResetAllPanels">RESET ALL PANELS</button>
        </div>
      </div>
      <div class="sf-acc">${itemsHtml}</div>
    `;

    // ✅ 헤더 reset 연결
    const resetAllPanels = document.getElementById("sfResetAllPanels");
    if (resetAllPanels) {
      resetAllPanels.addEventListener("click", () => {
        delete window.TWIN_INLINE_STAGES;
        activeId = getStages()[0]?.id ?? "stage1";
        renderStages();
        renderPanel();
      });
    }

    // ✅ 헤더 클릭: active 전환 + 부드럽게 확장
    bodyEl.querySelectorAll(".sf-acc-item .sf-acc-head").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const item = e.currentTarget.closest(".sf-acc-item");
        if (!item) return;
        activeId = item.dataset.stage;
        renderPanel();
      });
    });

    // ✅ slider & actions (active에만 존재)
    const range = document.getElementById("sfRange");
    const mini = document.getElementById("sfMiniVal");

    if (range && mini) {
      range.addEventListener("input", () => {
        const v = Number(range.value);
        const stage = getStages().find((x) => x.id === activeId);
        if (stage?.panel?.slider) {
          stage.panel.slider.value = v;
          // 외부 주입 사용하는 경우를 대비해서 보관
          window.TWIN_INLINE_STAGES = getStages().map((x) => ({ ...x }));
          mini.innerHTML = `${fmt(v)}<span class="sf-acc-unit">${stage.panel.slider.unit}</span>`;
        }
      });
    }

    bodyEl.querySelectorAll('[data-act="reset"]').forEach((b) => {
      b.addEventListener("click", () => renderPanel());
    });

    bodyEl.querySelectorAll('[data-act="remove"]').forEach((b) => {
      b.addEventListener("click", () => {
        const next = getStages().filter((x) => x.id !== activeId);
        window.TWIN_INLINE_STAGES = next;
        activeId = next[0]?.id ?? "";
        renderStages();
        renderPanel();
      });
    });
  }

  renderStages();
  renderPanel();
})();

