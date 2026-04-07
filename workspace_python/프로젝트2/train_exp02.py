"""
EXP-02: YOLOv11s 비교 실험 학습 스크립트
실행: conda activate proj2 && python train_exp02.py

EXP-01(YOLOv8s)과 동일 조건, 모델만 yolo11s.pt로 변경
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'   # OpenMP 중복 로드 충돌 방지
import time
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO

# ── 스크립트 위치 기준으로 작업 디렉토리 고정 ──
SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)

# ── 설정 (EXP-01과 동일 조건, 모델/프로젝트만 변경) ──
YAML_PATH = str(SCRIPT_DIR / 'dataset.yaml')
PROJECT   = 'runs/compare'
NAME      = 'yolov11s_exp02'
LOG_FILE  = SCRIPT_DIR / f'{NAME}_log.txt'

# ── 로그 함수 (콘솔 + 파일 동시 출력) ──
def log(msg):
    line = f'[{datetime.now().strftime("%H:%M:%S")}] {msg}'
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def main():
    log('=' * 50)
    log('EXP-02: YOLOv11s 비교 실험 시작')
    log('=' * 50)

    # ── GPU 확인 ──
    import torch
    if torch.cuda.is_available():
        log(f'GPU: {torch.cuda.get_device_name(0)}')
        log(f'VRAM: {round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)} GB')
    else:
        log('GPU 미인식 — CPU로 학습됩니다')

    # ── 학습 (EXP-01과 동일 하이퍼파라미터) ──
    log(f'model: yolo11s.pt')
    log(f'data:  {YAML_PATH}')
    log(f'epochs=300, imgsz=640, batch=16, seed=42, patience=50')
    log('학습 시작')
    start = time.time()

    model = YOLO('yolo11s.pt')   # ← EXP-01: yolov8s.pt → EXP-02: yolo11s.pt
    results = model.train(
        data=YAML_PATH,
        epochs=300,       # 동일
        imgsz=640,        # 동일
        batch=16,         # 동일
        seed=42,          # 동일 — 재현성
        patience=50,      # 동일
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

        log('=== EXP-02 평가 결과 ===')
        log(f'  mAP@0.5:      {val.box.map50:.4f}')
        log(f'  mAP@0.5:0.95: {val.box.map:.4f}')
        log(f'  Precision:     {val.box.mp:.4f}')
        log(f'  Recall:        {val.box.mr:.4f}')

        # ── EXP-01 비교 ──
        log('')
        log('=== EXP-01 vs EXP-02 비교 ===')
        exp01 = {'mAP50': 0.9950, 'mAP50_95': 0.9522, 'P': 0.9904, 'R': 0.9929}
        exp02 = {'mAP50': val.box.map50, 'mAP50_95': val.box.map, 'P': val.box.mp, 'R': val.box.mr}

        log(f'  {"지표":<16} {"EXP-01(v8s)":>12} {"EXP-02(v11s)":>12} {"차이":>10}')
        log(f'  {"─"*52}')
        for key, label in [('mAP50', 'mAP@0.5'), ('mAP50_95', 'mAP@0.5:0.95'), ('P', 'Precision'), ('R', 'Recall')]:
            diff = exp02[key] - exp01[key]
            sign = '+' if diff >= 0 else ''
            log(f'  {label:<16} {exp01[key]:>12.4f} {exp02[key]:>12.4f} {sign}{diff:>9.4f}')

        winner = 'YOLOv11s' if exp02['mAP50_95'] > exp01['mAP50_95'] else 'YOLOv8s'
        log(f'\n  판정: {winner} 우세 (mAP@0.5:0.95 기준)')
        log(f'  → EXP-03은 {winner} 기반으로 진행 권장')
    else:
        log('best.pt 없음 — 검증 스킵')

    log(f'소요 시간: {elapsed/60:.1f}분')
    log('완료')


if __name__ == '__main__':
    main()
