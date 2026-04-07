# EXP-03 — YOLOv11s 해상도 실험 (최종 실험)
> GitHub Copilot 전달용 | 자동차 도장 표면 결함 탐지 프로젝트

---

## 1. 실험 목적

EXP-02(YOLOv11s, imgsz=640)에서 확인된 **소형 결함 탐지 약점**을 해상도 향상으로 개선할 수 있는지 검증한다.

**개선 대상 클래스 (EXP-02 기준)**

| 클래스 | EXP-02 mAP@0.5:0.95 | 문제 원인 |
|---|---|---|
| gap_fault | 0.871 | bbox가 선형으로 길어 IoU 손실 |
| paint_drip | 0.931 | bbox 평균 면적 0.0029 — 매우 작음 |
| dust | 0.955 | bbox 작고 흐릿함 |

> imgsz 640 → 832로 높이면 동일 결함이 더 많은 픽셀로 표현되어 특징 추출 개선 기대

---

## 2. 환경

| 항목 | 내용 |
|---|---|
| OS | Windows 11 |
| Python | 3.10.20 (conda: proj2) |
| GPU | NVIDIA RTX 3070 8GB |
| 프레임워크 | Ultralytics (v8.4.34) |
| PyTorch | 2.5.1+cu121 |
| 예상 VRAM | ~6~7GB (EXP-02 3.96GB에서 증가) |

```python
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # OMP Error #15 방지 — 필수
```

---

## 3. 학습 설정 — EXP-03

| 파라미터 | EXP-02 | EXP-03 | 변경 여부 |
|---|---|---|---|
| model | yolo11s.pt | yolo11s.pt | 동일 |
| imgsz | 640 | **832** | ← 변경 |
| batch | 16 | **8** | ← VRAM 대응 변경 |
| epochs | 300 | 300 | 동일 |
| seed | 42 | 42 | 동일 |
| patience | 50 | 50 | 동일 |
| project | runs/compare | runs/exp03 | |
| name | yolov11s_exp02 | yolov11s_exp03 | |

```python
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from ultralytics import YOLO

model = YOLO('yolo11s.pt')

results = model.train(
    data='data.yaml',
    epochs=300,
    imgsz=832,
    batch=8,
    seed=42,
    patience=50,
    project='runs/exp03',
    name='yolov11s_exp03',
    exist_ok=True,
)
```

---

## 4. 평가 코드

```python
from ultralytics import YOLO

best_model = YOLO('runs/exp03/yolov11s_exp03/weights/best.pt')
val_results = best_model.val(data='data.yaml')

print('=== EXP-03 평가 결과 ===')
print(f'mAP@0.5:      {val_results.box.map50:.4f}')
print(f'mAP@0.5:0.95: {val_results.box.map:.4f}')
print(f'Precision:    {val_results.box.mp:.4f}')
print(f'Recall:       {val_results.box.mr:.4f}')
```

---

## 5. 전체 실험 비교표 (EXP-03 완료 후 채울 것)

| 지표 | EXP-01 (v8s 640) | EXP-02 (v11s 640) | EXP-03 (v11s 832) |
|---|---|---|---|
| mAP@0.5 | 0.9950 | 0.9950 | |
| mAP@0.5:0.95 | 0.9522 | 0.9569 | |
| Precision | 0.9904 | 0.9916 | |
| Recall | 0.9929 | 0.9984 | |
| 학습 시간 | 77.3분 | 52.8분 | |
| VRAM | 3.92GB | 3.96GB | |

**핵심 비교 클래스**

| 클래스 | EXP-02 | EXP-03 | 개선 여부 |
|---|---|---|---|
| gap_fault | 0.871 | | |
| paint_drip | 0.931 | | |
| dust | 0.955 | | |

---

## 6. 판정 기준

| 결과 | 결론 |
|---|---|
| mAP@0.5:0.95 > 0.9569 | 해상도 향상 효과 있음 → EXP-03 최종 모델 채택 |
| mAP@0.5:0.95 ≤ 0.9569 | 효과 없음 → EXP-02 최종 모델 채택 |

---

## 7. 전체 실험 진행 현황

| 실험 | 모델 | 상태 | mAP@0.5:0.95 |
|---|---|---|---|
| EXP-01 | YOLOv8s / imgsz=640 | ✅ 완료 | 0.9522 |
| EXP-02 | YOLOv11s / imgsz=640 | ✅ 완료 | 0.9569 |
| EXP-03 | YOLOv11s / imgsz=832 | 🔄 진행 (최종) | - |

---

## 8. EXP-03 완료 후 다음 단계

```
[완료 예정] EXP-03 학습 및 평가
      ↓
최종 모델 선정 (EXP-02 또는 EXP-03)
      ↓
YOLO 추론 결과 → master_defect_type JOIN → 재작업 비용 산출
      ↓
정형 데이터 트랙 (LightGBM) 진행
```
