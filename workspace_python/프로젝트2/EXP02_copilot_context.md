# EXP-02 — YOLOv11s 비교 실험 컨텍스트
> GitHub Copilot 전달용 | 자동차 도장 표면 결함 탐지 프로젝트

---

## 1. 실험 목표

EXP-01 (YOLOv8s) 베이스라인과 **동일 조건**으로 YOLOv11s를 학습하여 아키텍처 성능을 비교한다.

- 비교 핵심 지표: `mAP@0.5:0.95`
- EXP-01 기준값: mAP@0.5 = **0.9950**, mAP@0.5:0.95 = **0.9522**

---

## 2. 환경

| 항목 | 내용 |
|---|---|
| OS | Windows 11 |
| Python | 3.10.20 (conda: proj2) |
| GPU | NVIDIA RTX 3070 8GB (학습 중 VRAM 사용 ~3.92GB) |
| 프레임워크 | Ultralytics (v8.4.34) |
| PyTorch | 2.5.1+cu121 |

**주의사항 (EXP-01에서 발생한 문제)**
```python
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # OMP Error #15 방지 — 반드시 학습 전 설정
```

---

## 3. 데이터셋

```
track_a_yolo_dataset (1)/
└── track_a_images/
    ├── images/
    │   ├── train/    800장
    │   └── val/      200장
    ├── labels/
    │   ├── train/    800개 (YOLO 형식)
    │   └── val/      200개
    └── data.yaml
```

### data.yaml (확정, 수정 불필요)

```yaml
path: C:/IT/workspace_python/프로젝트2/현대오토에버/track_a_yolo_dataset (1)/track_a_images
train: images/train
val: images/val
nc: 8
names:
  0: scratch
  1: dent
  2: paint_bubble
  3: paint_drip
  4: dust
  5: orange_peel
  6: crack
  7: gap_fault
```

---

## 4. 학습 설정 — EXP-02

**EXP-01과 반드시 동일하게 유지해야 할 파라미터**

| 파라미터 | 값 | 비고 |
|---|---|---|
| model | `yolo11s.pt` | ← EXP-01의 yolov8s.pt에서 변경 |
| data | `data.yaml` | 동일 |
| epochs | 300 | 동일 |
| imgsz | 640 | 동일 |
| batch | 16 | 동일 |
| seed | **42** | 동일 — 재현성 필수 |
| patience | 50 | 동일 |
| project | `runs/compare` | ← EXP-01과 다른 폴더 |
| name | `yolov11s_exp02` | |

```python
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from ultralytics import YOLO

model = YOLO('yolo11s.pt')  # 최초 실행 시 자동 다운로드

results = model.train(
    data='data.yaml',
    epochs=300,
    imgsz=640,
    batch=16,
    seed=42,
    patience=50,
    project='runs/compare',
    name='yolov11s_exp02',
    exist_ok=True,
)
```

---

## 5. 평가 코드

```python
from ultralytics import YOLO

best_model = YOLO('runs/compare/yolov11s_exp02/weights/best.pt')
val_results = best_model.val(data='data.yaml')

print('=== EXP-02 평가 결과 ===')
print(f'mAP@0.5:      {val_results.box.map50:.4f}')
print(f'mAP@0.5:0.95: {val_results.box.map:.4f}')
print(f'Precision:    {val_results.box.mp:.4f}')
print(f'Recall:       {val_results.box.mr:.4f}')
```

---

## 6. EXP-01 vs EXP-02 비교표 작성

학습 완료 후 아래 표를 채운다.

| 지표 | EXP-01 (YOLOv8s) | EXP-02 (YOLOv11s) | 차이 |
|---|---|---|---|
| mAP@0.5 | 0.9950 | | |
| mAP@0.5:0.95 | 0.9522 | | |
| Precision | 0.9904 | | |
| Recall | 0.9929 | | |
| 학습 시간 | 77.3분 | | |
| VRAM | ~3.92GB | | |

**판정 기준**
- mAP@0.5:0.95 > 0.9522 → YOLOv11s 우세 → EXP-03은 YOLOv11s로 진행
- mAP@0.5:0.95 ≤ 0.9522 → YOLOv8s 유지 → EXP-03은 YOLOv8s로 진행

---

## 7. 클래스별 성능 비교 (EXP-01 기준값)

| 클래스 | EXP-01 mAP@0.5 | EXP-01 mAP@0.5:0.95 | EXP-02 mAP@0.5 | EXP-02 mAP@0.5:0.95 |
|---|---|---|---|---|
| scratch | 0.995 | 0.988 | | |
| dent | 0.995 | 0.995 | | |
| paint_bubble | 0.995 | 0.981 | | |
| paint_drip | 0.995 | 0.940 | | |
| dust | 0.995 | 0.939 | | |
| orange_peel | 0.995 | 0.954 | | |
| crack | 0.995 | 0.957 | | |
| gap_fault | 0.995 | 0.865 | | |

**주목할 클래스**: `gap_fault` (EXP-01에서 mAP@0.5:0.95 = 0.865로 가장 낮음)
→ EXP-02에서 개선 여부가 핵심 비교 포인트

---

## 8. 산출물 확인 목록

학습 완료 후 아래 파일 확인

```
runs/compare/yolov11s_exp02/
├── weights/
│   ├── best.pt       ← 평가에 사용
│   └── last.pt
├── results.csv       ← epoch별 loss, mAP 추이
├── confusion_matrix.png
├── val_batch0_pred.jpg
└── args.yaml         ← 학습 파라미터 기록 확인용
```

---

## 9. 전체 실험 진행 현황

| 실험 | 모델 | 상태 | mAP@0.5:0.95 |
|---|---|---|---|
| EXP-01 | YOLOv8s | ✅ 완료 | 0.9522 |
| EXP-02 | YOLOv11s | 🔄 진행 중 | - |
| EXP-03 | 최적 모델, imgsz=832 | 예정 | - |
