import pandas as pd
import requests
import time
import json
from datetime import datetime

# 1. 재시도 로직이 포함된 전송 함수
def send_with_retry(url, data, max_retries=3, backoff_factor=1):
    for i in range(max_retries):
        try:
            # 실시간 시스템이므로 타임아웃은 짧게(2초) 설정
            response = requests.post(url, json=data, timeout=2) 
            if response.status_code == 200:
                return True
            else:
                print(f"  [경고] 서버 응답 오류 ({response.status_code}). {i+1}회차 재시도...")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print(f"  [오류] 서버 연결 불가. {i+1}회차 재시도...")
        
        # 실패 시 대기 시간: 1초 -> 2초 -> 4초 (지수 백오프)
        time.sleep(backoff_factor * (2 ** i))
    return False

def stream_factory_data(file_path, target_url, interval=1):
    """
    파일을 읽어 실시간으로 데이터를 쏘는 핵심 루프
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"[치명적] {file_path} 파일을 찾을 수 없습니다.")
        return

    print(f"🚀 실시간 데이터 전송 시작 (총 {len(df)}행, 주기: {interval}초)")

    for index, row in df.iterrows():
        payload = row.to_dict()
        
        # [현실화] 데이터의 시간을 현재 시간으로 갱신 (대시보드 실시간성 확보)
        payload['timestamp'] = datetime.now().strftime('%H:%M:%S')
        
        # 자동 재시도가 포함된 전송 실행
        success = send_with_retry(target_url, payload)
        
        if success:
            # print(f"✅ [{payload['timestamp']}] {index}번 로우 전송 성공")
            pass  # 출력 없이 그냥 조용히 넘어감
        else:
            print(f"❌ [{payload['timestamp']}] {index}번 로우 최종 전송 실패 (건너뜀)")
            # 필요 시 여기서 실패한 데이터만 별도 csv로 저장하는 로직을 추가할 수 있습니다.

        # 지정된 간격만큼 대기
        time.sleep(interval)

if __name__ == "__main__":
    # --- 설정 값 ---
    CONFIG = {
        "DATA_PATH": "final_2018ver.csv",
        "API_URL": "http://127.0.0.1:5000/ingest",
        "INTERVAL": 1  # 1초 간격
    }
    
    # 스크립트 실행
    try:
        stream_factory_data(
            file_path=CONFIG["DATA_PATH"],
            target_url=CONFIG["API_URL"],
            interval=CONFIG["INTERVAL"]
        )
    except KeyboardInterrupt:
        print("\n⏹ 사용자에 의해 전송이 중단되었습니다.")