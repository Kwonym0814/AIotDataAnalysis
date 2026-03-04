// static/js/psi_gauge_1.js
(() => {
  // 180° 게이지: 0→-90°, 100→+90°
  const START_DEG = -90;
  const SWEEP_DEG = 180;

  // 애니메이션 시간
  const DURATION_MS = 450;

  const state = {
    before: { cur: null, raf: null },
    after: { cur: null, raf: null },
  };

  function clamp100(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return 0;
    return Math.max(0, Math.min(100, n));
  }

  function levelMeta(v100) {
    if (v100 >= 85) return { label: "위험" };
    if (v100 >= 70) return { label: "경고" };
    if (v100 >= 40) return { label: "주의" };
    return { label: "안정" };
  }

  function vToAngle(v) {
    return START_DEG + (v / 100) * SWEEP_DEG;
  }

  function hexToRgba(hex, a) {
    const h = String(hex).replace("#", "").trim();
    const r = parseInt(h.substring(0, 2), 16);
    const g = parseInt(h.substring(2, 4), 16);
    const b = parseInt(h.substring(4, 6), 16);
    return `rgba(${r},${g},${b},${a})`;
  }

  function apply(which, v) {
    const needle = document.querySelector(`[data-psi-needle="${which}"]`);
    const text = document.querySelector(`[data-psi-text="${which}"]`);
    const badge = document.querySelector(`[data-psi-badge="${which}"]`);

    // 새 구조 훅
    const topv = document.querySelector(`[data-psi-value="${which}"]`);
    const block = document.querySelector(`[data-psi-block="${which}"]`);

    if (!needle || !text || !badge) return;

    const needlePath = needle.querySelector("path");

    const color =
      v >= 85 ? "#ef4444" :
      v >= 70 ? "#fb923c" :
      v >= 40 ? "#facc15" :
                "#22c55e";

    if (needlePath) needlePath.setAttribute("fill", color);

    const angle = vToAngle(v);
    needle.setAttribute("transform", `rotate(${angle} 110 120)`);

    const iv = Math.round(v);
    text.textContent = String(iv);

    const meta = levelMeta(v);
    badge.textContent = meta.label;

    // 우측 상단 수치
    if (topv) topv.textContent = `${iv} PSI`;

    // 뱃지 배경 틴트
    badge.style.backgroundColor = hexToRgba(color, 0.14);
    badge.style.borderColor = hexToRgba(color, 0.28);
    badge.style.color = meta.label === "주의" ? "rgba(15,23,42,0.85)" : color;

    // 블록 배경 틴트
    if (block) {
      block.style.boxShadow = `0 0 0 1px ${hexToRgba(color, 0.12)} inset`;
      block.style.backgroundImage =
        `linear-gradient(180deg, ${hexToRgba(color, 0.10)}, rgba(0,0,0,0) 60%)`;
    }
  }

  function animateTo(which, targetV) {
    const st = state[which];
    if (!st) return;

    const to = clamp100(targetV);

    // 첫 값은 즉시 반영
    if (st.cur === null) {
      st.cur = to;
      apply(which, to);
      return;
    }

    // 기존 애니메이션 취소
    if (st.raf) cancelAnimationFrame(st.raf);

    const from = st.cur;
    const start = performance.now();

    const step = (now) => {
      const p = Math.min(1, (now - start) / DURATION_MS);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic

      const v = from + (to - from) * eased;
      st.cur = v;
      apply(which, v);

      if (p < 1) st.raf = requestAnimationFrame(step);
      else st.raf = null;
    };

    st.raf = requestAnimationFrame(step);
  }

  // 외부에서 실시간 값 주입
  window.setPSI = (which, v) => {
    if (which !== "before" && which !== "after") return;
    animateTo(which, v);
  };

  // 초기 테스트 값 (DOM 타이밍 안전)
  function initPSI() {
    window.setPSI("before", 72);
    window.setPSI("after", 28);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPSI);
  } else {
    initPSI();
  }
})();

