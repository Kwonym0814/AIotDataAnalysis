"""
EXP-01: YOLOv8s 베이스라인 학습 스크립트
실행: conda activate proj2 && python train_exp01.py
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'   # OpenMP 중복 로드 충돌 방지
import sys
import time
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO

# ── 스크립트 위치 기준으로 작업 디렉토리 고정 ──
SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)

# ── 설정 ──
YAML_PATH = str(SCRIPT_DIR / 'dataset.yaml')
PROJECT   = 'runs/baseline'
NAME      = 'yolov8s_exp01'
LOG_FILE  = SCRIPT_DIR / f'{NAME}_log.txt'

# ── 로그 함수 (콘솔 + 파일 동시 출력) ──
def log(msg):
    line = f'[{datetime.now().strftime("%H:%M:%S")}] {msg}'
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def main():
    # ── GPU 확인 ──
    import torch
    if torch.cuda.is_available():
        log(f'GPU: {torch.cuda.get_device_name(0)}')
        log(f'VRAM: {round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)} GB')
    else:
        log('GPU 미인식 — CPU로 학습됩니다')

    # ── 학습 ──
    log(f'data: {YAML_PATH}')
    log('학습 시작')
    start = time.time()

    model = YOLO('yolov8s.pt')
    results = model.train(
        data=YAML_PATH,
        epochs=300,
        imgsz=640,
        batch=16,       # VRAM 부족 시 8로 변경
        seed=42,
        patience=50,
        project=PROJECT,
        name=NAME,
        exist_ok=True,
    )

    elapsed = time.time() - start
    log(f'학습 완료 — 소요 시간: {elapsed/60:.1f}분')
    log(f'결과 저장: {results.save_dir}')

    # ── 검증 ──
    best_pt = Path(results.save_dir) / 'weights' / 'best.pt'
    if best_pt.exists():
        log('검증(val) 시작')
        best_model = YOLO(str(best_pt))
        val = best_model.val(data=YAML_PATH)

        log('=== EXP-01 평가 결과 ===')
        log(f'  mAP@0.5:      {val.box.map50:.4f}')
        log(f'  mAP@0.5:0.95: {val.box.map:.4f}')
        log(f'  Precision:     {val.box.mp:.4f}')
        log(f'  Recall:        {val.box.mr:.4f}')
    else:
        log('best.pt 없음 — 검증 스킵')

    log('완료')


if __name__ == '__main__':
    main()
