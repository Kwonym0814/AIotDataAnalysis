# control.py
from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

# (선택) 천단위 콤마 필터
@app.template_filter("fmt")
def fmt(v):
    try:
        return f"{int(v):,}"
    except Exception:
        return v

@app.get("/")
def home():
    # === 예시 데이터(나중에 네 데이터/모델 결과로 교체) ===
    current_cost = 35640
    previous_cost = 32500
    potential_savings = 804000
    unit = "원"

    cost_change = current_cost - previous_cost
    change_percentage = (cost_change / previous_cost * 100) if previous_cost else 0.0
    is_increase = cost_change > 0

    # 시간대별 전기료 추이(에어리어 차트용)
    cost_trend_data = [
        {"time": "09:00", "actual": 28500, "projected": 28500},
        {"time": "10:00", "actual": 32000, "projected": 30500},
        {"time": "11:00", "actual": 35000, "projected": 31800},
        {"time": "12:00", "actual": 38500, "projected": 33200},
        {"time": "13:00", "actual": 42000, "projected": 34500},
        {"time": "14:00", "actual": 35000, "projected": 30100},
        {"time": "15:00", "actual": 33000, "projected": 28800},
        {"time": "16:00", "actual": 37000, "projected": 31500},
    ]

    processes = [
        {"processName": "원자재 입고", "powerConsumption": 45.2, "maxPower": 60, "cost": 5424, "efficiency": 85, "status": "normal"},
        {"processName": "전처리 공정", "powerConsumption": 88.5, "maxPower": 100, "cost": 10620, "efficiency": 72, "status": "warning"},
        {"processName": "조립 라인", "powerConsumption": 125.8, "maxPower": 130, "cost": 15096, "efficiency": 65, "status": "critical"},
        {"processName": "품질 검사", "powerConsumption": 32.5, "maxPower": 50, "cost": 3900, "efficiency": 88, "status": "normal"},
    ]

    return render_template(
        "index.html",
        current_cost=current_cost,
        previous_cost=previous_cost,
        potential_savings=potential_savings,
        unit=unit,
        is_increase=is_increase,
        change_percentage=change_percentage,
        cost_trend_data=cost_trend_data,
        processes=processes,
    )

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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
