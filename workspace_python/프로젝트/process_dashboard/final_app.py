# final_app.py
from flask import Flask, render_template, request, jsonify, Response
import random
import time
import json
import queue
import logging

app = Flask(__name__)

# [로그 끄기] Werkzeug(플라스크 기본 서버)의 접속 로그를 ERROR 레벨로 낮춤
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)



# 데이터를 임시 저장할 큐 (최대 100개)
# [수정] 큐 이름을 하나로 통일하여 관리
stream_queue = queue.Queue(maxsize=100)
recent_cost_history = []

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
    raw_row = request.json
    if not raw_row:
        return jsonify({"error": "No data"}), 400

    # [스마트 분류 1] 전기료 데이터인지 판단 (Human_Energy_Cost 키가 있는지 확인)
    if 'Human_Energy_Cost' in raw_row:
        try:
            human_cost = float(raw_row.get("Human_Energy_Cost") or 0)
            ai_cost = float(raw_row.get("AI_Energy_Cost") or human_cost)

            # [수정] 프론트로 넘길 데이터에 PSI 값 2개 추가
            processed_data = {
                "type": "cost",
                "time": raw_row.get("timestamp", time.strftime("%H:%M:%S")),
                "actual": human_cost,
                "projected": ai_cost,
                "psi_before": float(raw_row.get("PSI") or 0),  # 최적화 이전 PSI
                "psi_after": float(raw_row.get("AI_PSI") or 0)  # 최적화 이후 PSI
            }

            recent_cost_history.append(processed_data)
            if len(recent_cost_history) > 20:
                recent_cost_history.pop(0)

            stream_queue.put(processed_data, timeout=0.1)
            return jsonify({"status": "success", "dataType": "cost"}), 200

        except queue.Full:
            pass
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid value"}), 400

        return jsonify({"status": "ignored"}), 200

    # [스마트 분류 2] 추후 공정 데이터가 들어올 경우를 대비한 분기
    elif 'module' in raw_row:
        processed_data = {
            "type": "process",
            "module": raw_row.get("module"),
            "value": raw_row.get("value"),
            "unit": raw_row.get("unit", ""),
            "timestamp": raw_row.get("timestamp", time.strftime("%H:%M:%S"))
        }
        try:
            stream_queue.put(processed_data, timeout=0.1)
        except queue.Full:
            pass

        return jsonify({"status": "success", "dataType": "process"}), 200

    # 분류할 수 없는 다른 데이터가 들어온 경우
    return jsonify({"status": "ignored", "reason": "Unknown data structure"}), 200

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
    if recent_cost_history:
        cost_trend_data = recent_cost_history[-10:]  # 최근 10개
    else:
    # 데이터가 하나도 없을 때만 예시 데이터 출력
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
