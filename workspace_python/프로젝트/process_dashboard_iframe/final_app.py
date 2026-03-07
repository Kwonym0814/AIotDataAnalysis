# final_app.py
from flask import Flask, render_template, request, jsonify, Response
import random
import time
import json
import queue
import logging
import pandas as pd
import requests

app = Flask(__name__)

# [로그 끄기] Werkzeug(플라스크 기본 서버)의 접속 로그를 ERROR 레벨로 낮춤
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


# 데이터를 임시 저장할 큐 (최대 100개)
# [수정] 큐 이름을 하나로 통일하여 관리
stream_queue = queue.Queue(maxsize=100)
recent_cost_history = []

# [누적 변수] 서버가 켜져 있는 동안 수치를 계속 합산함
total_human_cost = 0.0
total_ai_cost = 0.0
current_month = None  # 현재 월 추적
monthly_human_data = [] # 과거 기록 저장용
monthly_ai_data = []

# 3. 데이터 로드 함수 (서버 기동 시 1회 실행)
def load_csv_to_globals():
    global monthly_human_data, monthly_ai_data
    try:
        df = pd.read_csv("final_2026ver.csv")
        df['date'] = pd.to_datetime(df['date'])
        df['Month'] = df['date'].dt.month

        # 월별 합계 계산
        m_fate = df.groupby('Month').sum(numeric_only=True)

        # 기본요금 포함 최종 데이터 리스트화
        human_list = (m_fate['Human_Energy_Cost'] + m_fate['Current_Unit_Price']).astype(int).tolist()
        ai_list = (m_fate['AI_Energy_Cost'] + m_fate['Current_Unit_Price']).astype(int).tolist()

        # [주의] 데이터가 12개월치가 다 없을 경우를 대비해 부족한 달은 0으로 채움
        monthly_human_data = (human_list + [0] * 12)[:12]
        monthly_ai_data = (ai_list + [0] * 12)[:12]

        print("✅ CSV 데이터 임포트 완료 (기본요금 반영됨)")
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        # 실패 시 기본 샘플 데이터
        monthly_human_data = [0] * 12
        monthly_ai_data = [0] * 12


# 서버 시작 전 실행
load_csv_to_globals()


SERVICE_KEY = "8f60b786617639fe6fd980f7708756a806a7f6a67fd149377d329a8ee028877d"
BASE_URL = "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/getCertifiedEmissionReductionPriceInfo"


def event_stream():
    """ 큐에 쌓인 최적화 결과를 하나씩 꺼내 SSE 형식으로 전송 """
    while True:
        # 큐에 데이터가 들어올 때까지 대기
        data = stream_queue.get()
        yield f"data: {json.dumps(data)}\n\n"


@app.route('/stream')
def stream():
    """ 브라우저가 구독하는 실시간 데이터 스트림 주소 """
    return Response(event_stream(), mimetype='text/event-stream')


@app.route('/ingest', methods=['POST'])
def ingest_data():
    global total_human_cost, total_ai_cost, current_month
    
    import datetime
    
    raw_row = request.json
    if not raw_row:
        return jsonify({"error": "No data"}), 400
    
    # 현재 월 확인 및 월 변경 시 누적값 초기화
    today = datetime.date.today()
    if current_month is None:
        current_month = today.month
    elif current_month != today.month:
        # 월이 변경됨 → 누적값 초기화
        total_human_cost = 0.0
        total_ai_cost = 0.0
        current_month = today.month

    try:
        # 통합 전송할 데이터 꾸러미 생성
        merged_data = {
            "type": "all_in_one",
            "time": raw_row.get("timestamp", time.strftime("%H:%M:%S")),
            "cost": {},
            "processes": []
        }

        # [1] 전기료 데이터 처리
        if 'Human_Energy_Cost' in raw_row:
            human_cost = float(raw_row.get("Human_Energy_Cost") or 0)
            ai_cost = float(raw_row.get("AI_Energy_Cost") or human_cost)
            total_human_cost += human_cost
            total_ai_cost += ai_cost

            merged_data["cost"] = {
                "actual": human_cost,
                "projected": ai_cost,
                "psi_before": float(raw_row.get("PSI") or 0),
                "psi_after": float(raw_row.get("AI_PSI") or 0),
                "total_human_cost": total_human_cost,
                "total_ai_cost": total_ai_cost
            }

            # (차트용 히스토리는 기존 포맷 유지)
            recent_cost_history.append({"time": merged_data["time"], **merged_data["cost"]})
            if len(recent_cost_history) > 20:
                recent_cost_history.pop(0)

        # [2] 🚀 공정 데이터 처리
        if 'Motor_Operating_Rate' in raw_row:
            motor_rate = float(raw_row['Motor_Operating_Rate'])

            iron_ore_value = 50 + (motor_rate * 0.6) + random.uniform(-5.0, 5.0)
            temp_value = 1600 - (motor_rate * 0.5) + random.uniform(-8.0, 8.0)

            # 리스트에 3개의 공정 데이터 한 번에 담기
            merged_data["processes"].extend([
                {"module": "Motor Rate", "value": round(motor_rate, 1), "unit": "%"},
                {"module": "Iron Ore Feed", "value": round(iron_ore_value, 1), "unit": "ton/h"},
                {"module": "Furnace Temp", "value": round(temp_value, 0), "unit": "°C"}
            ])

        # 🚀 큐에 묶음 데이터 딱 한 번만 적재
        if merged_data["cost"] or merged_data["processes"]:
            stream_queue.put(merged_data, timeout=0.1)

        return jsonify({"status": "success"}), 200

    except queue.Full:
        pass
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid value format"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# (선택) 천단위 콤마 필터
@app.template_filter("fmt")
def fmt(v):
    try:
        return f"{int(v):,}"
    except Exception:
        return v



@app.get("/")
def home():

    # [수정 1] 전역 변수 참조 명시 (읽기 전용이지만 명시하는 것이 안전)
    global total_human_cost, total_ai_cost, recent_cost_history

    # [수정] 전월 비용 기준값 (상수로 관리하거나 DB에서 가져와야 함)
    previous_month_cost = 15159144 # 전체 전기료 월평균

    # [계산 1] 전월 대비 증감률 실시간 계산
    # 공식: ((현재값 - 이전값) / 이전값) * 100
    if previous_month_cost > 0:
        change_pct = ((total_human_cost - previous_month_cost) / previous_month_cost) * 100
    else:
        change_pct = 0.0

    # [계산 2] 증가 여부 판단
    is_inc = (total_human_cost > previous_month_cost)

    # 시간대별 전기료 추이 데이터 결정
    if recent_cost_history:
        display_trend_data = recent_cost_history[-10:]
    else:
        display_trend_data = [
            {"time": "09:00", "actual": 28500, "projected": 28500},
            {"time": "10:00", "actual": 32000, "projected": 30500},
            {"time": "11:00", "actual": 35000, "projected": 31800},
            {"time": "12:00", "actual": 38500, "projected": 33200},
            {"time": "13:00", "actual": 42000, "projected": 34500},
            {"time": "14:00", "actual": 35000, "projected": 30100},
            {"time": "15:00", "actual": 33000, "projected": 28800},
            {"time": "16:00", "actual": 37000, "projected": 31500},
        ]

    return render_template(
        "index.html",
        current_cost=total_human_cost,
        previous_cost=previous_month_cost,
        potential_savings=total_human_cost - total_ai_cost,
        unit="원",
        is_increase=is_inc,
        change_percentage=round(abs(change_pct), 1),
        cost_trend_data=display_trend_data,
        processes=[],
        monthly_human_data = monthly_human_data,
        monthly_ai_data = monthly_ai_data
    )


@app.post("/api/simulate_report")
def api_simulate_report():
    """
    현재 설정된 5대 파라미터를 모두 받아 종합 리포트 데이터를 생성
    """
    params = request.get_json(silent=True) or {}

    # 1. 파라미터 추출 (기본값 세팅)
    iron_ore = float(params.get('stage-1', 100))  # Iron Ore Feed
    temp = float(params.get('stage-2', 1550))  # Furnace Temp
    motor = float(params.get('stage-3', 85))  # Motor Rate
    cap = float(params.get('stage-4', 90))  # Capacitor Rate
    carbon = float(params.get('stage-5', 0.18))  # Carbon Content

    # 2. 가상 물리 수식 (Baseline vs Simulated)
    # 기존(Baseline): 1200 kWh, 60 PSI 가정
    sim_usage = 1200 + (iron_ore - 100) * 2.5 + (temp - 1500) * 1.5

    # PSI 로직: 온도가 낮거나(점도 상승), 역률 관리가 안 될 때 스트레스 증가
    temp_stress = max(0, (1550 - temp) * 0.4)
    pf_stress = max(0, motor - cap) * 0.5
    sim_psi = (motor * 0.5) + temp_stress + pf_stress
    sim_psi = max(0, min(100, sim_psi))

    # CO2 절감량 가상 산출 (기존 대비 절감된 전력량 * 배출계수)
    kwh_saved = max(0, 1200 - sim_usage)
    co2_saved = kwh_saved * 0.466

    # 3. 리포트 인사이트 자동 생성
    insights = []
    if sim_psi > 80:
        insights.append("- ⚠️ **위험**: 공정 스트레스(PSI)가 높습니다. 온도 상향 또는 모터 부하 분산이 필요합니다.")
    elif kwh_saved > 0:
        insights.append(f"- ✅ **효율**: AI 제어를 통해 시간당 {kwh_saved:.1f} kWh의 에너지를 절감 중입니다.")
    if temp < 1500:
        insights.append("- ⚠️ **품질 경고**: 로(Furnace) 온도가 너무 낮아 탄소 성분 제어(0.18%)에 실패할 확률이 높습니다.")

    return jsonify({
        "status": "success",
        "parameters": params,
        "results": {
            "usage_kwh": round(sim_usage, 1),
            "psi": round(sim_psi, 1),
            "co2_saved_kg": round(co2_saved, 1)
        },
        "insights": insights
    })



# ✅ 팀원 app.py의 API를 app1.py에 결합 (포트/앱 분리 없이 동일 서버에서 처리)
@app.post("/api/analyze")
def api_analyze():
    data = request.get_json(silent=True) or {}
    module_name = (data.get("module") or "").strip()
    try:
        user_value = float(data.get("value", 0))
    except Exception:
        user_value = 0.0

    trend_data = [round(user_value * (1 + random.uniform(-0.05, 0.05)), 1) for _ in range(7)]

    status = "정상 작동 중"
    if module_name == "제선" and user_value > 1500:
        status = "고온 경고! 냉각 필요"
    elif module_name == "압연" and user_value < 5:
        status = "두께 부족! 공정 재확인"

    return jsonify({
        "module": module_name,
        "status": status,
        "trend": trend_data,
        "labels": ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
    })


@app.get("/api/kau25-monthly")
def api_kau25_monthly():
    import requests
    from datetime import datetime

    start_ym = "202502"
    end_ym = "202602"

    # 13개월(2025/02 ~ 2026/02) 리스트 생성
    def month_range(yyyymm_start, yyyymm_end):
        ys, ms = int(yyyymm_start[:4]), int(yyyymm_start[4:])
        ye, me = int(yyyymm_end[:4]), int(yyyymm_end[4:])
        out = []
        y, m = ys, ms
        while (y < ye) or (y == ye and m <= me):
            out.append(f"{y:04d}{m:02d}")
            m += 1
            if m == 13:
                y += 1
                m = 1
        return out

    months_full = month_range(start_ym, end_ym)

    # 공공데이터 응답 구조에서 items 안전 파싱
    def extract_items(data):
        items = (
            data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
        )
        if isinstance(items, dict):
            return [items]
        if isinstance(items, list):
            return items
        return []

    # 키 후보(스펙 차이 방어)
    date_keys = ["basDt", "trdDd", "date"]
    close_keys = ["clpr", "close", "clsPrc"]
    name_keys = ["itmsNm", "itemName", "prodNm"]

    def pick(d, keys):
        for k in keys:
            v = d.get(k)
            if v not in (None, ""):
                return v
        return None

    # 월별 마지막 거래일(yyyymmdd) 종가 저장
    monthly_best = {}  # ym -> (yyyymmdd, close)

    # ✅ 페이지네이션: 여러 페이지를 돌며 전부 수집
    page = 1
    max_pages = 20  # 1년치면 보통 이 안에 들어옴 (여유)
    while page <= max_pages:
        params = {
            "serviceKey": SERVICE_KEY,
            "pageNo": page,
            "numOfRows": 1000,
            "resultType": "json",
        }

        r = requests.get(BASE_URL, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        items = extract_items(data)
        if not items:
            break  # 더 이상 데이터 없음

        for it in items:
            nm = pick(it, name_keys)
            # 이름 필드가 내려오면 KAU25 필터
            if nm and "KAU25" not in str(nm):
                continue

            raw_dt = pick(it, date_keys)
            raw_close = pick(it, close_keys)
            if raw_dt is None or raw_close is None:
                continue

            sdt = str(raw_dt).replace("-", "").replace(".", "").replace("/", "").strip()
            if len(sdt) >= 8:
                sdt = sdt[:8]  # YYYYMMDD
            else:
                continue

            ym = sdt[:6]
            if ym < start_ym or ym > end_ym:
                continue

            try:
                close_v = float(str(raw_close).replace(",", ""))
            except:
                continue

            prev = monthly_best.get(ym)
            # 같은 월이면 더 큰 날짜가 “월봉 마지막 거래일”로 간주
            if (prev is None) or (sdt > prev[0]):
                monthly_best[ym] = (sdt, close_v)

        page += 1

    # ✅ 13개월 축 강제: 없는 달은 None
    labels = [f"{m[:4]}/{m[4:]}" for m in months_full]
    closes = []
    for m in months_full:
        if m in monthly_best:
            closes.append(monthly_best[m][1])
        else:
            closes.append(None)

    return jsonify({"labels": labels, "closes": closes})






if __name__ == "__main__":
    app.run(debug=True, port=5001)
