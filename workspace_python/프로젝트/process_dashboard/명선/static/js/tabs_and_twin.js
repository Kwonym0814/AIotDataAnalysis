// [1] 사이드바 및 아코디언 상태 관리
let activeStages = new Set();
const twinStage = document.getElementById('twinStage');
const sidebar = document.getElementById('twinSidebar');
const accordionContainer = document.getElementById('accordionContainer');

/**
 * 공정 카드나 SVG 영역 클릭 시 호출되는 메인 함수
 */
function toggleControl(id) {
    if (!id || !STAGE_CONFIG[id]) return;

    // 1. 사이드바 열기 (Transition 효과 포함)
    if (!twinStage.classList.contains('sidebar-open')) {
        sidebar.style.width = '400px';
        twinStage.classList.add('sidebar-open');
    }

    // 2. 아코디언 패널 생성 및 렌더링
    renderAccordion(id);

    // 3. 방금 클릭한 항목으로 스크롤 및 활성화 시각화
    const targetItem = document.getElementById(`item-${id}`);
    if (targetItem) {
        // 모든 아이템의 active 제거 후 현재 아이템만 활성화
        document.querySelectorAll('.accordion-item').forEach(el => el.classList.remove('active'));
        targetItem.classList.add('active');
        targetItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * 오른쪽 사이드바에 분석용 아코디언 아이템 추가
 */
function renderAccordion(id) {
    if (activeStages.has(id)) return; // 이미 있으면 추가 안 함
    
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
            <input type="range" min="${conf.base - 50}" max="${conf.base + 50}" value="${conf.threshold}"
                   class="w-full h-1 bg-slate-800 rounded-lg appearance-none accent-${conf.color}-500"
                   oninput="updateThreshold('${id}', this.value)">
            <div class="flex gap-2">
                <button onclick="requestAnalysis('${id}')" class="flex-1 py-2 text-[9px] bg-cyan-500/10 text-cyan-400 rounded border border-cyan-500/20 hover:bg-cyan-500/20 font-bold">RUN ANALYTICS</button>
                <button onclick="removeItem('${id}')" class="flex-1 py-2 text-[9px] bg-red-500/5 text-red-500/40 rounded border border-red-500/10 hover:bg-red-500/20 hover:text-red-400 font-bold">REMOVE</button>
            </div>
            <div id="chart-area-${id}" class="h-32 mt-2 hidden">
                 <canvas id="canvas-${id}"></canvas>
            </div>
        </div>`;

    // 순서에 맞게 배치
    const existing = Array.from(accordionContainer.children);
    const next = existing.find(el => parseInt(el.dataset.order) > conf.order);
    if (next) accordionContainer.insertBefore(item, next);
    else accordionContainer.appendChild(item);
}

/**
 * Flask API와 통신하여 실시간 분석 결과 가져오기
 */
async function requestAnalysis(id) {
    const val = STAGE_CONFIG[id].base; // 현재 실시간 값 보냄
    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ module: STAGE_CONFIG[id].name, value: val })
        });
        const data = await res.json();
        
        // 결과 알람창 표시 (테스트용)
        console.log(`${id} 분석 결과:`, data.status);
        
        // 차트 영역 표시 및 데이터 렌더링 로직 추가 가능
        document.getElementById(`chart-area-${id}`).classList.remove('hidden');
    } catch (e) {
        console.error("분석 요청 실패:", e);
    }
}

/**
 * 사이드바 닫기 함수
 */
function closeSidebar() {
    twinStage.classList.remove('sidebar-open');
    sidebar.style.width = '0px';
}