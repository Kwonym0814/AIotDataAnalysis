# Track B — YOLOv8 결함 탐지 분석 보고서

> 작성일: 2026-04-07  
> 프로젝트: 자동차 도장 표면 결함 탐지 (현대오토에버 Track A 데이터셋)

---

## 1. 프로젝트 개요

자동차 도장 표면 이미지에서 결함의 **위치(Bounding Box)** 와 **유형(클래스)** 을 자동 탐지하는 YOLOv8 모델을 개발한다.

### 1.1 환경

| 항목 | 내용 |
|---|---|
| OS | Windows 11 |
| Python | 3.10.20 (conda: proj2) |
| GPU | NVIDIA RTX 3070 8GB |
| 프레임워크 | Ultralytics YOLOv8 (v8.4.34) |
| PyTorch | 2.5.1+cu121 |

---

## 2. 데이터셋 구성

### 2.1 디렉토리 구조

```
dataset/track_a_images/
├── images/
│   ├── train/    800장 (.jpg)
│   └── val/      200장 (.jpg)
├── labels/
│   ├── train/    800개 (.txt, YOLO 형식)
│   └── val/      200개 (.txt)
└── data.yaml
```

### 2.2 이미지 파일명 패턴

```
{zone}_{color}_{id}.jpg
예: bumper_black_000223.jpg, hood_pearl_000391.jpg
```

- **Zone**: bumper, fender, front_door, hood, rear_door, rocker, roof, trunk (+ pearl 변형 16종)
- **Color**: black, blue, bronze, gray, green, navy, red, silver, white (9종)

---

## 3. EDA (탐색적 데이터 분석)

> 노트북: `02_EDA_track_b.ipynb`

### 3.1 라벨 파싱 결과

| 항목 | 수치 |
|---|---|
| 총 라벨(bbox) 수 | 1,177개 |
| 총 이미지 수 | 800장 |
| Positive sample (결함 있음) | 667장 (83.4%) |
| Negative sample (빈 라벨) | 133장 (16.6%) |

### 3.2 클래스 분포 (8개 클래스)

| class_id | 클래스명 | 라벨 수 | 비율 |
|---|---|---|---|
| 0 | scratch (스크래치) | 260 | 24.9% |
| 1 | dent (덴트) | 204 | 19.5% |
| 2 | paint_bubble (도장기포) | 135 | 12.9% |
| 3 | paint_drip (도장흘림) | 102 | 9.8% |
| 4 | dust (이물질) | 118 | 11.3% |
| 5 | orange_peel (오렌지필) | 98 | 9.4% |
| 6 | crack (크랙) | 49 | 4.7% |
| 7 | gap_fault (Gap불량) | 78 | 7.5% |

- **불균형 비율**: 5.3:1 (scratch 260개 / crack 49개)
- 5:1 수준 → class_weights 없이 기본 증강으로 충분

### 3.3 BBox 크기 통계 (정규화 좌표)

| 항목 | width | height | area |
|---|---|---|---|
| 평균 | 0.1092 | 0.1272 | 0.0095 |
| 최소 | 0.0125 | 0.0222 | 0.0013 |
| 최대 | 0.9195 | 0.8292 | 0.0408 |

### 3.4 클래스별 평균 BBox 면적

| 클래스 | 평균 면적 |
|---|---|
| scratch | 0.0112 |
| dent | 0.0099 |
| paint_bubble | 0.0046 |
| paint_drip | 0.0029 |
| dust | 0.0034 |
| orange_peel | 0.0115 |
| crack | 0.0172 |
| gap_fault | 0.0223 |

- gap_fault, crack은 상대적으로 큰 bbox
- paint_drip, dust는 매우 작은 결함

### 3.5 시각화 산출물

- `class_distribution.png` — 클래스별 라벨 수 막대 그래프
- `bbox_distribution.png` — BBox width/height 히스토그램
- `sample_overlay.png` — 샘플 이미지 10장 + BBox 오버레이

---

## 4. 모델 학습 (EXP-01)

> 스크립트: `train_exp01.py`

### 4.1 학습 설정

| 파라미터 | 값 |
|---|---|
| 모델 | YOLOv8s (pretrained) |
| epochs | 300 |
| imgsz | 640 |
| batch | 16 |
| optimizer | AdamW (auto) |
| patience | 50 (early stopping) |
| seed | 42 |
| AMP | True |
| VRAM 사용 | ~3.92 GB |

### 4.2 학습 과정

| Epoch | box_loss | cls_loss | dfl_loss | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|---|
| 1 | 1.341 | 4.059 | 1.070 | 0.705 | 0.429 |
| 5 | 1.053 | 0.847 | 0.976 | 0.954 | 0.690 |
| 50 | 0.542 | 0.383 | 0.848 | 0.991 | 0.921 |
| 100 | 0.475 | 0.314 | 0.824 | 0.995 | 0.939 |
| 200 | 0.424 | 0.291 | 0.807 | 0.995 | 0.944 |
| 300 | 0.372 | 0.245 | 0.788 | 0.995 | 0.943 |

- 300 epoch 풀 학습 완료 (patience 50 미도달 = 끝까지 미세 개선 유지)
- **소요 시간: 77.3분 (약 1시간 17분)**

### 4.3 학습 시 문제 및 해결

| 문제 | 원인 | 해결 |
|---|---|---|
| 커널 사망 | Windows 절전모드 진입 시 GPU 연결 끊김 | `powercfg`로 절전 해제 + `.py` CLI 실행으로 전환 |
| OMP Error #15 | conda MKL과 PyTorch의 OpenMP 런타임 중복 로드 | `KMP_DUPLICATE_LIB_OK=TRUE` 환경변수 설정 |
| 한글 깨짐 | matplotlib 기본 폰트 한글 미지원 | `Malgun Gothic` 폰트 + `axes.unicode_minus=False` |

---

## 5. 평가 결과

### 5.1 전체 지표

| 지표 | 값 |
|---|---|
| **mAP@0.5** | **0.9950** |
| **mAP@0.5:0.95** | **0.9522** |
| **Precision** | **0.9904** |
| **Recall** | **0.9929** |

### 5.2 클래스별 성능

| 클래스 | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|
| scratch | 0.996 | 1.000 | 0.995 | 0.988 |
| dent | 0.995 | 1.000 | 0.995 | **0.995** |
| paint_bubble | 0.993 | 1.000 | 0.995 | 0.981 |
| paint_drip | 0.993 | 1.000 | 0.995 | 0.940 |
| dust | 0.994 | 1.000 | 0.995 | 0.939 |
| orange_peel | 0.991 | 1.000 | 0.995 | 0.954 |
| crack | 0.962 | 1.000 | 0.995 | 0.957 |
| gap_fault | 1.000 | 0.943 | 0.995 | 0.865 |

### 5.3 성능 분석

- **전체적으로 매우 높은 성능** (mAP@0.5 = 0.995)
- **최고 성능**: dent (mAP@0.5:0.95 = 0.995) — bbox 크기가 일정하고 특징이 뚜렷
- **상대적 약점**: gap_fault (mAP@0.5:0.95 = 0.865, Recall = 0.943)
  - 샘플 수 78개로 적은 편
  - bbox가 큰 편이라 위치 정확도(IoU) 기준에서 손실 발생 추정
- **추론 속도**: 이미지당 5.8ms (inference) → 실시간 적용 가능

---

## 6. 산출물 목록

| 파일 | 설명 |
|---|---|
| `02_EDA_track_b.ipynb` | EDA 노트북 (라벨 파싱, 분포, 시각화) |
| `04_training.ipynb` | 학습 노트북 (환경 확인, yaml 생성, 학습/검증/추론) |
| `train_exp01.py` | CLI 학습 스크립트 (독립 실행용) |
| `dataset.yaml` | YOLO 데이터셋 설정 파일 |
| `yolov8s_exp01_log.txt` | 학습 로그 (타임스탬프 포함) |
| `runs/baseline/yolov8s_exp01/` | 학습 결과 (weights, 그래프, confusion matrix 등) |
| `class_distribution.png` | 클래스 분포 시각화 |
| `bbox_distribution.png` | BBox 크기 분포 시각화 |
| `sample_overlay.png` | 샘플 이미지 BBox 오버레이 |
| `copilot_context.md` | 프로젝트 컨텍스트 문서 |

---

## 7. 다음 단계

| 순서 | 작업 | 상태 |
|---|---|---|
| 1 | EDA — 클래스 분포, BBox 분석 | ✅ 완료 |
| 2 | EXP-01 — YOLOv8s 베이스라인 학습 | ✅ 완료 |
| 3 | EXP-02 — YOLOv11s 동일 조건 비교 | 예정 |
| 4 | EXP-03 — 최적 모델 imgsz=832, batch=8 | 예정 |
| 5 | YOLO 추론 결과 → master_defect_type JOIN → 재작업 비용 산출 | 예정 |
