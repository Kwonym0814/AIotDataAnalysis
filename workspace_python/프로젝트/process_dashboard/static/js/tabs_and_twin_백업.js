/**
 * 통합 모니터링 시스템 메인 스크립트
 * 1. 테마 전환 (Dark/Light)
 * 2. 탭 전환 (Energy/Process/CO2)
 * 3. 공정 흐름(Digital Twin) 인터랙션 및 아코디언 제어
 */

(function() {
    // [1] 전역 설정 및 상태 관리
    const STAGE_CONFIG = {
        'stage-1': { order: 1, name: 'Blast Furnace', base: 1240, range: 10, unit: '°C', threshold: 1246, color: 'cyan' },
        'stage-2': { order: 2, name: 'Oxygen Supply', base: 450, range: 20, unit: 'Nm³/h', threshold: 465, color: 'indigo' },
        'stage-3': { order: 3, name: 'Rolling Mill', base: 8.5, range: 0.5, unit: 'm/s', threshold: 8.9, color: 'emerald' }
    };

    let activeStages = new Set();
    const twinStage = document.getElementById('twinStage');
    const sidebar = document.getElementById('twinSidebar');
    const accordionContainer = document.getElementById('accordionContainer');

    // [2] 테마 전환 로직 (tabs_and_twin_2 이식)
    const initTheme = () => {
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

        const saved = localStorage.getItem("theme") || "dark";
        setTheme(saved);

        btn.addEventListener("click", () => {
            const cur = root.getAttribute("data-theme") === "light" ? "dark" : "light";
            setTheme(cur);
        });
    };

    // [3] 탭 전환 로직 (SPA 방식)
    const initTabs = () => {
        const tabBtns = document.querySelectorAll(".tab-btn");
        const views = document.querySelectorAll("[data-view]");

        function activate(tabName) {
            tabBtns.forEach(b => b.dataset.active = (b.dataset.tab === tabName ? "true" : "false"));
            views.forEach(v => v.classList.toggle("active", v.dataset.view === tabName));
        }

        tabBtns.forEach(btn => {
            btn.addEventListener("click", () => activate(btn.dataset.tab));
        });
    };

    // [4] 공정 제어 로직 (tabs_and_twin_1 기반 통합)
    window.toggleControl = function(id) {
        if (!id || !STAGE_CONFIG[id]) return;

        // 사이드바 열기 및 스타일 강제 적용
        if (twinStage && sidebar) {
            twinStage.classList.add('sidebar-open');
            sidebar.style.width = '400px';
            sidebar.style.visibility = 'visible';
        }

        renderAccordion(id);

        const targetItem = document.getElementById(`item-${id}`);
        if (targetItem) {
            document.querySelectorAll('.accordion-item').forEach(el => el.classList.remove('active'));
            targetItem.classList.add('active');
            targetItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    };

    function renderAccordion(id) {
        if (activeStages.has(id) || !accordionContainer) return;
        
        activeStages.add(id);
        const conf = STAGE_CONFIG[id];
        const item = document.createElement('div');
        item.id = `item-${id}`;
        item.dataset.order = conf.order;
        item.className = `accordion-item border border-slate-800 rounded-xl p-4 bg-slate-900/30 mb-4 active active-${conf.color}`;
        
        item.innerHTML = `
            <div class="flex justify-between items-center cursor-pointer" onclick="this.parentElement.classList.toggle('active')">
                <div class="text-xs font-black text-slate-400 uppercase tracking-tighter">${conf.name}</div>
                <span class="text-${conf.color}-400 font-mono text-sm font-bold" id="side-val-${id}">${conf.base}${conf.unit}</span>
            </div>
            <div class="accordion-content pt-4 space-y-4">
                <div class="flex justify-between text-[10px] text-slate-500 uppercase">
                    <span>Safety Threshold</span>
                    <span class="text-amber-500" id="threshold-val-${id}">${conf.threshold}${conf.unit}</span>
                </div>
                <div class="flex gap-2">
                    <button onclick="requestAnalysis('${id}')" class="flex-1 py-2 text-[9px] bg-cyan-500/10 text-cyan-400 rounded border border-cyan-500/20 hover:bg-cyan-500/20 font-bold">RUN ANALYTICS</button>
                    <button onclick="removeItem('${id}')" class="flex-1 py-2 text-[9px] bg-red-500/5 text-red-500/40 rounded border border-red-500/10 hover:bg-red-500/20 font-bold">REMOVE</button>
                </div>
            </div>`;

        const existing = Array.from(accordionContainer.children);
        const next = existing.find(el => parseInt(el.dataset.order) > conf.order);
        if (next) accordionContainer.insertBefore(item, next);
        else accordionContainer.appendChild(item);
    }

    window.removeItem = function(id) {
        document.getElementById(`item-${id}`)?.remove();
        activeStages.delete(id);
        if (activeStages.size === 0) window.closeSidebar();
    };

    window.closeSidebar = function() {
        if (twinStage && sidebar) {
            twinStage.classList.remove('sidebar-open');
            sidebar.style.width = '0px';
            sidebar.style.visibility = 'hidden';
        }
    };

    window.requestAnalysis = async function(id) {
        const val = STAGE_CONFIG[id].base;
        try {
            const res = await fetch('/api/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ module: STAGE_CONFIG[id].name, value: val })
            });
            const data = await res.json();
            console.log(`${id} 분석 결과:`, data.status);
            // 알람 패널 연동 로직 추가 가능
        } catch (e) {
            console.error("분석 요청 실패:", e);
        }
    };

    // [5] 초기화 실행
    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        initTabs();
        console.log("System Initialized");
    });
	
	// [차트 테마 관리 함수]
    function getChartTheme(theme) {
        const isLight = theme === "light";
        return {
            textColor: isLight ? "#0f172a" : "#ffffff",
            gridColor: isLight ? "rgba(0, 0, 0, 0.1)" : "rgba(255, 255, 255, 0.1)",
            chartColor: isLight ? "#0ea5e9" : "#00e5ff" // 라이트: 사이언 / 다크: 형광 사이언
        };
    }

    // [테마 변경 감지 및 차트 업데이트]
    window.addEventListener("themechange", (e) => {
        const newTheme = e.detail.theme;
        const colors = getChartTheme(newTheme);

        // 페이지 내 모든 Chart.js 인스턴스를 찾아 업데이트
        Chart.helpers.each(Chart.instances, function(instance) {
            const options = instance.options;

            // 축 색상 업데이트
            if (options.scales && options.scales.x) {
                options.scales.x.ticks.color = colors.textColor;
            }
            if (options.scales && options.scales.y) {
                options.scales.y.ticks.color = colors.textColor;
                options.scales.y.grid.color = colors.gridColor;
            }

            // 차트 갱신 (애니메이션과 함께 흐르듯 변경)
            instance.update();
        });
	

})();