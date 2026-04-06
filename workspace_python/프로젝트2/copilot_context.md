# YOLO 분석 프로젝트 컨텍스트
> 이 문서를 GitHub Copilot에게 전달하여 코드 작성 및 분석을 진행한다.

---

## 1. 프로젝트 목표

자동차 도장 표면 이미지에서 결함의 **위치(Bounding Box)** 와 **유형(클래스)** 을 자동 탐지하는 YOLOv8 모델 개발.

---

## 2. 환경

| 항목 | 내용 |
|---|---|
| OS | Windows 11 (WSL2) |
| Python | 3.10 (conda 환경명: proj2) |
| GPU | NVIDIA RTX 3070 8GB |
| 프레임워크 | Ultralytics YOLOv8 |
| 에디터 | VSCode + Jupyter |

---

## 3. 디렉토리 구조

```
track_a_yolo_dataset (1)/
└── track_a_images/
    ├── images/
    │   ├── train/        800장 (.jpg)
    │   └── val/          200장 (.jpg)
    ├── labels/
    │   ├── train/        800개 (.txt, YOLO 형식)
    │   └── val/          200개 (.txt, YOLO 형식)
    └── data.yaml
```

---

## 4. data.yaml (확정)

```yaml
path: C:/IT/workspace_python/프로젝트2/현대오토에버/track_a_yolo_dataset (1)/track_a_images
train: images/train
val: images/val
nc: 8
names:
  0: scratch       # 스크래치    — 83개 (24.6%)
  1: dent          # 덴트        — 74개 (21.9%)
  2: paint_bubble  # 도장기포    — 48개 (14.2%)
  3: paint_drip    # 도장흘림    — 42개 (12.4%)
  4: dust          # 이물질      — 48개 (14.2%)
  5: orange_peel   # 오렌지필    — 38개 (11.2%)
  6: crack         # 크랙        — 17개 (5.0%)
  7: gap_fault     # Gap불량     — 28개 (8.3%)
```

---

## 5. 이미지 파일명 패턴

```
{zone}_{color}_{id}.jpg
예: bumper_black_000223.jpg
    hood_pearl_000391.jpg
```

**Zone (16종)**
- 일반: bumper, fender, front_door, hood, rear_door, rocker, roof, trunk
- 펄: bumper_pearl, fender_pearl, front_door_pearl, hood_pearl, rear_door_pearl, rocker_pearl, roof_pearl, trunk_pearl

**Color (9종)**
- black, blue, bronze, gray, green, navy, red, silver, white

---

## 6. 라벨 파일 형식

```
# YOLO 형식 (공백 구분, 정규화 좌표)
class_id  cx  cy  w  h
예: 0 0.45 0.32 0.08 0.04

# 빈 파일 = 결함 없는 이미지 (Negative sample)
```

---

## 7. 클래스 불균형

- 불균형 비율: **4.9:1** (scratch 83개 / crack 17개)
- 5:1 미만 → class_weights 불필요, 기본 증강으로 충분

---

## 8. 학습 설정 (베이스라인)

```python
from ultralytics import YOLO

model = YOLO('yolov8s.pt')

results = model.train(
    data='data.yaml',       # 경로는 절대경로 또는 yaml 위치 기준 상대경로
    epochs=300,
    imgsz=640,
    batch=16,               # VRAM 부족 시 8로 조정
    seed=42,
    patience=50,
    project='runs/baseline',
    name='yolov8s_exp01',
    exist_ok=True,
)
```

**RTX 3070 VRAM 가이드**

| 설정 | VRAM |
|---|---|
| imgsz=640, batch=16 | ~5GB ✅ 권장 |
| imgsz=640, batch=32 | ~7GB 시도 가능 |
| imgsz=832, batch=8  | ~7.5GB 한계 근처 |

---

## 9. 평가 지표

```python
best_model = YOLO('runs/baseline/yolov8s_exp01/weights/best.pt')
val_results = best_model.val(data='data.yaml')

# 주요 지표
# val_results.box.map50    → mAP@0.5
# val_results.box.map      → mAP@0.5:0.95
# val_results.box.mp       → Precision
# val_results.box.mr       → Recall
```

---

## 10. 비교 실험 계획

| 실험 | 모델 | 변경사항 |
|---|---|---|
| EXP-01 | YOLOv8s | 베이스라인 |
| EXP-02 | YOLOv11s | 동일 조건 비교 |
| EXP-03 | 최적 모델 | imgsz=832, batch=8 |

---

## 11. 진행 순서

```
[완료] 환경 설치 (conda: proj2, ultralytics, torch+cuda)
[완료] GPU 확인 (RTX 3070 인식)
[완료] 라벨 EDA — class_id 분포 확인
[완료] data.yaml 확정 (nc:8, 클래스 매핑 검증)

[진행 중] 베이스라인 학습 (EXP-01, YOLOv8s)
[예정] 검증 및 결과 해석
[예정] 비교 실험 (EXP-02, YOLOv11s)
[예정] YOLO 추론 결과 → master_defect_type JOIN → 재작업 비용 산출
```

---

## 12. 후처리 파이프라인 (학습 완료 후)

YOLO 탐지 결과를 `master_defect_type.csv`와 연결하여 재작업 비용을 산출한다.
두 데이터(이미지/정형)는 직접 JOIN이 불가하므로 결과 레벨에서만 연결한다.

```python
# class_id → defect_type_code 매핑
class_to_defect = {
    'scratch':      'SCR',
    'dent':         'DNT',
    'paint_bubble': 'PBB',
    'paint_drip':   'PDR',
    'dust':         'DCT',
    'orange_peel':  'ORG',
    'crack':        'CRK',
    'gap_fault':    'GAP',
}

# master_defect_type.csv 로드 후 JOIN
# → 탐지 건수 × std_rework_time_min = 총 재작업 예상 시간
```
