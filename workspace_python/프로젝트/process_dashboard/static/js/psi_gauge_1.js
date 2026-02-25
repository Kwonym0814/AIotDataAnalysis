// static/js/psi_gauge_1.js
(() => {
  /**
   * PSI: 0 ~ 100 (percent-like)
   * Gauge sweep: 160 degrees (fan style)
   * - 0  => START(-80deg)  : left side
   * - 100=> END(+80deg)    : right side
   *
   * SVG needle pivot: rotate(angle 110 120)
   */

  const START_DEG = -80;
  const SWEEP_DEG = 160;

  // 0~100 기준 뱃지 룰(원하면 나중에 경계만 바꾸면 됨)
  // 안정: 0~39 / 주의: 40~69 / 경고: 70~84 / 위험: 85~100
  function levelMeta(v100) {
    if (v100 >= 85) return { label: "위험" };
    if (v100 >= 70) return { label: "경고" };
    if (v100 >= 40) return { label: "주의" };
    return { label: "안정" };
  }

  function clamp100(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return 0;
    return Math.max(0, Math.min(100, n));
  }

  /**
   * @param {"before"|"after"} which
   * @param {number} value100 0~100
   */
  function setGauge(which, value100) {
    const needle = document.querySelector(`[data-psi-needle="${which}"]`);
    const text = document.querySelector(`[data-psi-text="${which}"]`);
    const badge = document.querySelector(`[data-psi-badge="${which}"]`);
    if (!needle || !text || !badge) return;

    const v = clamp100(value100);

    // ✅ 0~100 → 160도 부채꼴 각도 변환
    const angle = START_DEG + (v / 100) * SWEEP_DEG;

    // ✅ SVG는 attribute transform이 가장 안정적
    needle.setAttribute("transform", `rotate(${angle} 110 120)`);

    // ✅ 숫자도 0~100으로 표기(정수)
    text.textContent = String(Math.round(v));

    // ✅ 뱃지도 0~100 기준으로
    const m = levelMeta(v);
    badge.textContent = m.label;
  }

  // 초기 샘플(레이아웃 확인용)
  document.addEventListener("DOMContentLoaded", () => {
    setGauge("before", 72);
    setGauge("after", 28);
  });

  // 외부에서 값 주입할 수 있도록
  window.setPSI = setGauge;
})();
