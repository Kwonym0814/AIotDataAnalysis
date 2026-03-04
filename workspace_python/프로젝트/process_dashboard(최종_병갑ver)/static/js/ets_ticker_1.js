(() => {
  const track = document.getElementById("etsTickerTrack");
  if (!track) return;

  // ✅ 하드코딩 데이터 (원하면 여기만 계속 바꾸면 됨)
  // 참고: EUA(유럽) 최근 시세는 TradingEconomics에 공개 지표가 있음. :contentReference[oaicite:0]{index=0}
  // RGGI 경매 clearing price는 공식 경매 결과 페이지가 있음. :contentReference[oaicite:1]{index=1}
  const items = [
    { sym: "KAU25", price: 13250, chgPct: +6.9, cur: "KRW" },     // 너 API 패널과 톤 맞추기(임시)
    { sym: "EUA",   price: 72.8,  chgPct: -1.2, cur: "EUR" },     // :contentReference[oaicite:2]{index=2}
    { sym: "UKA",   price: 41.8,  chgPct: +0.4, cur: "GBP" },     // (표시용) :contentReference[oaicite:3]{index=3}
    { sym: "CCA",   price: 42.0,  chgPct: +0.1, cur: "USD" },     // (표시용) :contentReference[oaicite:4]{index=4}
    { sym: "RGGI",  price: 25.75, chgPct: +0.3, cur: "USD" },     // :contentReference[oaicite:5]{index=5}
    { sym: "NZU",   price: 55.0,  chgPct: -0.2, cur: "NZD" },     // 표시용
  ];

  const fmt = (n) => {
    const v = Number(n);
    if (!Number.isFinite(v)) return "-";
    return v >= 100 ? v.toLocaleString() : v.toFixed(2);
  };

  function pillHTML(it) {
    const up = Number(it.chgPct) >= 0;
    return `
      <span class="ets-pill">
        <span class="ets-sym">${it.sym}</span>
        <span class="ets-price">${fmt(it.price)} <span style="opacity:.65">${it.cur}</span></span>
        <span class="ets-chg ${up ? "ets-up" : "ets-dn"}">
          ${up ? "▲" : "▼"} ${Math.abs(Number(it.chgPct)).toFixed(1)}%
        </span>
      </span>
    `;
  }

  // ✅ 무한 스크롤을 위해 2번 붙여서 길이 2배 만들기
  function render() {
    track.innerHTML = "";
    const html = items.map(pillHTML).join("");
    track.insertAdjacentHTML("beforeend", html + html);
  }

  render();
})();