"""
EXP-03: YOLOv11s 해상도 실험 (imgsz=832) 학습 스크립트
실행: conda activate proj2 && python train_exp03.py

EXP-02(YOLOv11s, imgsz=640, batch=16)에서 imgsz=832, batch=8로 변경
소형 결함(paint_drip, dust, gap_fault) 탐지 개선 목표
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

# ── 설정 ──
YAML_PATH = str(SCRIPT_DIR / 'dataset.yaml')
PROJECT   = 'runs/exp03'
NAME      = 'yolov11s_exp03'
LOG_FILE  = SCRIPT_DIR / f'{NAME}_log.txt'

# ── 로그 함수 (콘솔 + 파일 동시 출력) ──
def log(msg):
    line = f'[{datetime.now().strftime("%H:%M:%S")}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def main():
    log('=' * 50)
    log('EXP-03: YOLOv11s 해상도 실험 (imgsz=832) 시작')
    log('=' * 50)

    # ── GPU 확인 ──
    import torch
    if torch.cuda.is_available():
        log(f'GPU: {torch.cuda.get_device_name(0)}')
        log(f'VRAM: {round(torch.cuda.get_device_properties(0).total_mem / 1e9, 1) if hasattr(torch.cuda.get_device_properties(0), "total_mem") else round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)} GB')
    else:
        log('GPU 미인식 — CPU로 학습됩니다')

    # ── 학습 ──
    log(f'model: yolo11s.pt')
    log(f'data:  {YAML_PATH}')
    log(f'epochs=300, imgsz=832, batch=8, seed=42, patience=50')
    log(f'변경점: imgsz 640→832, batch 16→8 (VRAM 8GB 제약)')
    log('학습 시작')
    start = time.time()

    model = YOLO('yolo11s.pt')
    results = model.train(
        data=YAML_PATH,
        epochs=300,       # 동일
        imgsz=832,        # ← 변경: 640 → 832
        batch=8,          # ← 변경: 16 → 8 (VRAM 대응)
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
        val = best_model.val(data=YAML_PATH, verbose=True)

        log('=== EXP-03 평가 결과 ===')
        log(f'  mAP@0.5:      {val.box.map50:.4f}')
        log(f'  mAP@0.5:0.95: {val.box.map:.4f}')
        log(f'  Precision:     {val.box.mp:.4f}')
        log(f'  Recall:        {val.box.mr:.4f}')

        # ── 클래스별 결과 ──
        log('')
        log('=== EXP-03 클래스별 성능 ===')
        names = val.names
        log(f'  {"클래스":<15} {"P":>8} {"R":>8} {"mAP50":>8} {"mAP50-95":>10}')
        log(f'  {"─"*51}')
        for i, cname in names.items():
            p  = val.box.p[i]
            r  = val.box.r[i]
            a50 = val.box.ap50[i]
            a   = val.box.ap[i]
            log(f'  {cname:<15} {p:>8.4f} {r:>8.4f} {a50:>8.4f} {a:>10.4f}')

        # ── 3개 실험 전체 비교 ──
        log('')
        log('=== EXP-01 vs EXP-02 vs EXP-03 비교 ===')
        exp01 = {'mAP50': 0.9950, 'mAP50_95': 0.9522, 'P': 0.9904, 'R': 0.9929}
        exp02 = {'mAP50': 0.9950, 'mAP50_95': 0.9569, 'P': 0.9916, 'R': 0.9984}
        exp03 = {'mAP50': val.box.map50, 'mAP50_95': val.box.map, 'P': val.box.mp, 'R': val.box.mr}

        log(f'  {"지표":<16} {"EXP-01(v8s/640)":>16} {"EXP-02(v11s/640)":>17} {"EXP-03(v11s/832)":>17}')
        log(f'  {"─"*68}')
        for key, label in [('mAP50', 'mAP@0.5'), ('mAP50_95', 'mAP@0.5:0.95'), ('P', 'Precision'), ('R', 'Recall')]:
            log(f'  {label:<16} {exp01[key]:>16.4f} {exp02[key]:>17.4f} {exp03[key]:>17.4f}')

        # ── 핵심 클래스 비교 (소형 결함) ──
        log('')
        log('=== 핵심 개선 대상 클래스 비교 ===')
        exp02_cls = {'paint_drip': 0.931, 'dust': 0.955, 'gap_fault': 0.871}
        log(f'  {"클래스":<15} {"EXP-02":>8} {"EXP-03":>8} {"차이":>8} {"판정":>6}')
        log(f'  {"─"*47}')
        for cname, exp02_val in exp02_cls.items():
            idx = [k for k, v in names.items() if v == cname][0]
            exp03_val = val.box.ap[idx]
            diff = exp03_val - exp02_val
            sign = '+' if diff >= 0 else ''
            verdict = '개선' if diff > 0.005 else ('동일' if abs(diff) <= 0.005 else '하락')
            log(f'  {cname:<15} {exp02_val:>8.4f} {exp03_val:>8.4f} {sign}{diff:>7.4f} {verdict:>6}')

        # ── 최종 판정 ──
        log('')
        best_exp = 'EXP-03' if exp03['mAP50_95'] > exp02['mAP50_95'] else 'EXP-02'
        log(f'최종 판정: {best_exp} 채택 (mAP@0.5:0.95 기준)')
        if best_exp == 'EXP-03':
            log(f'  → 해상도 향상 효과 확인 (EXP-02 {exp02["mAP50_95"]:.4f} → EXP-03 {exp03["mAP50_95"]:.4f})')
        else:
            log(f'  → 해상도 향상 효과 없음 (EXP-02 {exp02["mAP50_95"]:.4f} ≥ EXP-03 {exp03["mAP50_95"]:.4f})')
    else:
        log('best.pt 없음 — 검증 스킵')

    log(f'총 소요 시간: {elapsed/60:.1f}분')
    log('완료')


if __name__ == '__main__':
    main()
