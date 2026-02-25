/**
 * [통합 모니터링 시스템 메인 컨트롤러]
 * 최종 수정일: 2026-02-25
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

    // [2] 실시간 데이터 스트리밍 (SSE)
    function initRealtimeStream() {
        const source = new EventSource("/stream");

        source.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === "cost") {
                updateCostChart(data);
				// [핵심] PSI 게이지 업데이트 함수 호출
				// 백엔드에서 보낸 psi_before, psi_after 데이터를 사용합니다.
				updatePSIGauge('before', data.psi_before);
				updatePSIGauge('after', data.psi_after);
				
				// [중요 - 수치 자동 업데이트!]
				// 백엔드가 보낸 'total_human_cost'를 화면에 꽂아주는 함수 호출
				updateLiveKPIs(data);
				
            } else {
                updateProcessUI(data);
                updateProcessCharts(data);
                
                // [추가 로직] 데이터가 임계치를 넘으면 HTML의 알람 함수 호출
                Object.keys(STAGE_CONFIG).forEach(id => {
                    const conf = STAGE_CONFIG[id];
                    if (conf.name === data.module && data.value > conf.threshold) {
                        // HTML 하단에 정의된 triggerAlarm 함수 호출
                        if (typeof window.triggerAlarm === 'function') {
                            window.triggerAlarm(conf.name, data.value, conf.unit);
                        }
                    }
                });
            }
        };

        source.onerror = function() {
            console.warn("SSE 연결 끊김. 브라우저가 재연결을 시도합니다.");
        };
    }
	
	/**
	 * PSI 게이지 바늘과 텍스트를 실시간으로 업데이트하는 함수
	 * @param {string} type - 'before' 또는 'after'
	 * @param {number} value - PSI 수치 (0~100)
	 */
	function updatePSIGauge(type, value) {
		if (value === undefined || value === null) return;

		const safeVal = Math.max(0, Math.min(100, parseFloat(value))); // 0~100 사이로 제한
		const displayVal = safeVal.toFixed(1);

		// 1. 바늘(Needle) 회전 제어
		// -90도(0)에서 +90도(100)까지 회전
		const needle = document.querySelector(`[data-psi-needle="${type}"]`);
			if (needle) {
			const angle = (safeVal / 100) * 180 - 90; // 0~100을 -90도 ~ +90도로 변환
			needle.setAttribute("transform", `rotate(${angle}, 110, 120)`);
		}

		// 2. 중앙 숫자 및 상단 텍스트 업데이트
		const textCenter = document.querySelector(`[data-psi-text="${type}"]`);
		const textTop = document.querySelector(`[data-psi-value="${type}"]`);
		if (textCenter) textCenter.textContent = displayVal;
		if (textTop) textTop.textContent = `${displayVal} PSI`;

		// 3. 상태 뱃지(Badge) 색상 및 문구 동적 변경
		const badge = document.querySelector(`[data-psi-badge="${type}"]`);
		if (badge) {
			updatePSIBadge(badge, safeVal);
		}
	}
	
	function updatePSIBadge(el, val) {
		el.className = "psi-badge px-2 py-0.5 rounded text-[10px] font-bold tracking-widest border";
		if (val < 35) {
			el.textContent = "STABLE";
			el.classList.add("text-emerald-400", "bg-emerald-400/10", "border-emerald-400/20");
		} else if (val < 75) {
			el.textContent = "WARNING";
			el.classList.add("text-amber-400", "bg-amber-400/10", "border-amber-400/20");
		} else {
			el.textContent = "CRITICAL";
			el.classList.add("text-red-400", "bg-red-400/10", "border-red-400/20", "animate-pulse");
		}
	}
	

    // 전기료 추이 차트(costTrend) 업데이트 (흐르는 효과)
    function updateCostChart(data) {
        const costChart = Chart.getChart("costTrend");
        if (costChart) {
            costChart.data.labels.push(data.time || new Date().toLocaleTimeString());
            if(costChart.data.datasets[0]) costChart.data.datasets[0].data.push(data.actual);
            if(costChart.data.datasets[1]) costChart.data.datasets[1].data.push(data.projected);

            if (costChart.data.labels.length > 12) {
                costChart.data.labels.shift();
                costChart.data.datasets.forEach(ds => ds.data.shift());
            }
            costChart.update('none');
        }
    }
	
	function updateLiveKPIs(data) {
		// HTML에 정의한 ID들을 찾습니다.
		const costEl = document.getElementById('realtime-accumulated-cost');
		const savingsEl = document.getElementById('realtime-potential-savings');

		if (costEl && data.total_human_cost !== undefined) {
			// 천단위 콤마 포맷팅 후 삽입
			costEl.textContent = Math.floor(data.total_human_cost).toLocaleString();
		}

		if (savingsEl && data.potential_savings !== undefined) {
			savingsEl.textContent = Math.floor(data.potential_savings).toLocaleString() + " 원";
		}
	}
	
	// [중요] onmessage 내부에서 위 함수를 호출해야 합니다.
	source.onmessage = function(event) {
		const data = JSON.parse(event.data);
		if (data.type === "cost") {
			updateCostChart(data);
			updatePSIGauge('before', data.psi_before);
			updatePSIGauge('after', data.psi_after);
			
			// 추가된 수치 업데이트 함수 호출
			updateLiveKPIs(data);
		}
	};

    // 공정 수치 텍스트 업데이트
    function updateProcessUI(data) {
        Object.keys(STAGE_CONFIG).forEach(id => {
            const conf = STAGE_CONFIG[id];
            if (conf.name === data.module) {
                const sideValEl = document.getElementById(`side-val-${id}`);
                const mainValEl = document.getElementById(`val-${id}`);
                
                if (sideValEl) sideValEl.innerText = `${data.value}${conf.unit}`;
                if (mainValEl) {
                    mainValEl.innerText = data.value;
                    mainValEl.classList.add('animate-pulse');
                    setTimeout(() => mainValEl.classList.remove('animate-pulse'), 500);
                }
            }
        });
    }

    // 공정 상세 차트들 업데이트 (흐르는 효과)
    function updateProcessCharts(data) {
        if (typeof Chart !== 'undefined' && Chart.instances) {
            Object.values(Chart.instances).forEach(instance => {
                if (instance.canvas.id === "costTrend") return;

                instance.data.labels.push(data.timestamp || new Date().toLocaleTimeString());
                instance.data.datasets.forEach(dataset => {
                    dataset.data.push(data.value);
                });

                if (instance.data.labels.length > 10) {
                    instance.data.labels.shift();
                    instance.data.datasets.forEach(dataset => {
                        dataset.data.shift(); // [수정됨] ds => ds.data.shift() 에러 수정
                    });
                }
                instance.update('none');
            });
        }
    }

    // [3] 테마 및 탭 제어 (이전과 동일, 안정화 버전)
    function getChartTheme(theme) {
        const isLight = theme === "light";
        return {
            textColor: isLight ? "#0f172a" : "#ffffff",
            gridColor: isLight ? "rgba(0, 0, 0, 0.1)" : "rgba(255, 255, 255, 0.1)"
        };
    }

    window.addEventListener("themechange", (e) => {
        const colors = getChartTheme(e.detail.theme);
        if (typeof Chart !== 'undefined' && Chart.instances) {
            Object.values(Chart.instances).forEach(instance => {
                const options = instance.options;
                if (options.scales?.x) options.scales.x.ticks.color = colors.textColor;
                if (options.scales?.y) {
                    options.scales.y.ticks.color = colors.textColor;
                    options.scales.y.grid.color = colors.gridColor;
                }
                instance.update();
            });
        }
    });

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

        setTheme(localStorage.getItem("theme") || "dark");
        btn.addEventListener("click", () => {
            const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
            setTheme(next);
        });
    };

    const initTabs = () => {
        const tabBtns = document.querySelectorAll(".tab-btn");
        const views = document.querySelectorAll("[data-view]");
        tabBtns.forEach(btn => btn.addEventListener("click", () => {
            const tabName = btn.dataset.tab;
            tabBtns.forEach(b => b.dataset.active = (b.dataset.tab === tabName ? "true" : "false"));
            views.forEach(v => v.classList.toggle("active", v.dataset.view === tabName));
        }));
    };

    // [4] 사이드바 및 아코디언 상호작용 (전역 등록 필수)
    window.toggleControl = function(id) {
        if (!id || !STAGE_CONFIG[id]) return;
        if (twinStage && sidebar) {
            twinStage.classList.add('sidebar-open');
            sidebar.style.width = '400px';
            sidebar.style.visibility = 'visible';
        }
        renderAccordion(id);
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
        if (activeStages.size === 0) {
            twinStage.classList.remove('sidebar-open');
            sidebar.style.width = '0px';
        }
    };

    // [5] DOM 로드 완료 후 실행
    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        initTabs();
        initRealtimeStream(); // [추가] 스트리밍 시작 호출
        console.log("System Master Controller Ready.");
    });

})();