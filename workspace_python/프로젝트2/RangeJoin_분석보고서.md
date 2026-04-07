# Range Join 1:1 매칭 분석 보고서

> 작성일: 2026-04-07  
> 프로젝트: 자동차 도장 표면 결함 탐지 (현대오토에버 Track A)

---

## 1. 목적

YOLO 라벨 파일(bbox)을 정형 데이터(defect_detail.csv)와 **1:1 매핑**하여,
비정형 데이터(이미지 결함 탐지)와 정형 데이터(결함 이력·재작업 비용)를 연결하는 브릿지를 구축한다.

---

## 2. 데이터 원본

| 데이터 | 경로 | 규모 |
|---|---|---|
| YOLO 라벨 (train) | `dataset/track_a_images/labels/train/` | 800파일, 1,044 bbox |
| YOLO 라벨 (val) | `dataset/track_a_images/labels/val/` | 200파일, 240 bbox |
| defect_detail.csv | `dataset/track_a_data/` | 170,904행 |
| inspection_master.csv | `dataset/track_a_data/` | 3,000,000행 (color_code 추출용) |
| master_defect_type.csv | `dataset/track_a_data/` | 10행 (재작업 비용 기준) |

---

## 3. 매핑 테이블

### 3-1. class_id → defect_type_code

| class_id | 클래스명 | defect_type_code |
|---|---|---|
| 0 | scratch | SCR |
| 1 | dent | DNT |
| 2 | paint_bubble | PBB |
| 3 | paint_drip | PDR |
| 4 | dust | **DST** (초기 DCT로 잘못 설정 → 수정) |
| 5 | orange_peel | ORG |
| 6 | crack | CRK |
| 7 | gap_fault | GAP |

### 3-2. zone 매핑 (파일명 → zone_code)

| 파일명 zone | zone_code | 비고 |
|---|---|---|
| bumper | BUMPER_F, BUMPER_R | 1:2 모호 — 둘 다 포함 |
| fender | FF, RF | 전/후 구분 불가 |
| front_door | FD | |
| rear_door | RD | |
| hood | HOOD | |
| roof | ROOF | |
| trunk | TRUNK | |
| rocker | ROCKER | |

### 3-3. color 매핑 (파일명 → color_code)

| 파일명 color | color_code | 매핑 |
|---|---|---|
| black | B3L | ✓ |
| white | P2W | ✓ |
| silver | SWP | ✓ |
| red | R4M | ✓ |
| blue | ABP | ✓ |
| gray | YW6 | ✓ |
| bronze | NaN | master_color에 없음 |
| green | NaN | master_color에 없음 |
| navy | NaN | master_color에 없음 |

---

## 4. 매칭 전략

### 4-1. 핵심 문제

- YOLO bbox 좌표: **정규화(0~1)** — 이미지 내 상대 위치
- defect_detail 좌표: **mm 단위** — 차체 내 절대 위치
- **직접 좌표 비교 불가** → 퍼센타일 기반 간접 매칭

### 4-2. 매칭 알고리즘 (5단계)

```
Step 1: defect_type 필터 (필수, exact match)
         ↓
Step 2: zone 필터 (exact match)
         ↓
Step 3: color 필터 (가능한 경우 exact match)
         ↓
Step 4: area 퍼센타일 범위 필터 (±15% range)
         ↓
Step 5: x, y, area 퍼센타일 유클리드 거리 최소 → 1건 선택
```

### 4-3. 각 단계 설명

| 단계 | 조건 | 유형 | 설명 |
|---|---|---|---|
| Step 1 | defect_type_code | exact | class_id → defect_type_code 매핑 |
| Step 2 | zone_code | exact | 파일명에서 추출한 zone → zone_code 매핑 |
| Step 3 | color_code | exact | inspection_master JOIN으로 color 확보. bronze/green/navy는 스킵 |
| Step 4 | area 퍼센타일 ±15% | **range** | bbox_area와 area_mm2를 각각 defect_type별 퍼센타일로 변환 후 범위 필터 |
| Step 5 | (x, y, area) 거리 | rank | 3차원 퍼센타일 유클리드 거리 최소인 1건 선택 |

### 4-4. 퍼센타일 기반 매칭 이유

좌표 체계가 다르므로(정규화 vs mm) **값이 아닌 순위(rank)** 를 비교한다.

- bbox_area → 해당 defect_type 내에서 면적 순위 (0~1)
- area_mm2 → 해당 defect_type 내에서 면적 순위 (0~1)
- 두 퍼센타일이 가까우면 "같은 유형 중 비슷한 크기의 결함"으로 간주

x, y 좌표도 동일 원리로 퍼센타일 변환 후 거리 계산.

---

## 5. 사전 규모 검증 (3조건 매칭)

1:1 매칭 전에 조건별 매칭 규모를 사전 파악하였다.

| 조건 | 매칭 키 | 평균 매칭 수 | 0건 비율 | 판정 |
|---|---|---|---|---|
| 조건 1 | defect_type | 25,297건 | 0% | ✓ |
| 조건 2 | defect_type + zone | 2,728건 | 0% | ✓ |
| 조건 3 | defect_type + zone + color | 369건 | 0% | ✓ |

> 3개 조건 모두 "방법론 진행 가능" 판정 (평균 > 100, 0건 비율 < 10%)

### 초기 오류 및 수정

| 문제 | 원인 | 해결 |
|---|---|---|
| dust 매칭 0건 (33건 전수) | class_id 4의 코드를 `DCT`로 설정 | `DST`로 수정 (master_defect_type 기준) |

---

## 6. 1:1 매칭 결과

### 6-1. 전체 통계

| 항목 | 수치 |
|---|---|
| 총 bbox (train + val) | **1,284건** |
| 매칭 성공 | **1,284건 (100%)** |
| 매칭 실패 | 0건 |
| 3조건 매칭 (type + zone + color) | 953건 (74.2%) |
| 2조건 매칭 (type + zone) | 331건 (25.8%) — bronze/green/navy |
| area range 내 매칭 | 1,284건 (100%) — fallback 0건 |

### 6-2. 매칭 거리 통계

| 지표 | 값 |
|---|---|
| 평균 | 0.0813 |
| 중앙값 | 0.0728 |
| 최소 | 0.0047 |
| 최대 | 0.4762 |
| 표준편차 | 0.0477 |

> 거리 범위 0~√3 (≈1.732) 중 대부분 0.1 이하 → 매칭 품질 양호

### 6-3. defect_type별 매칭 거리

| defect_type | 평균 거리 | 중앙값 | 건수 |
|---|---|---|---|
| SCR (scratch) | 0.0633 | 0.0578 | 325 |
| DNT (dent) | 0.0722 | 0.0612 | 252 |
| PDR (paint_drip) | 0.0807 | 0.0745 | 116 |
| PBB (paint_bubble) | 0.0842 | 0.0783 | 166 |
| DST (dust) | 0.0898 | 0.0822 | 151 |
| ORG (orange_peel) | 0.1000 | 0.0921 | 121 |
| GAP (gap_fault) | 0.1044 | 0.0915 | 99 |
| CRK (crack) | 0.1172 | 0.0984 | 54 |

- SCR, DNT: 샘플 수가 많아 퍼센타일 분포가 세밀 → 거리 낮음
- CRK: 샘플 수 54건으로 가장 적어 퍼센타일 해상도 낮음 → 거리 상대적으로 높음

### 6-4. split별

| split | 평균 거리 | 건수 |
|---|---|---|
| train | 0.0807 | 1,044 |
| val | 0.0840 | 240 |

train/val 편차 거의 없음 → 매칭 편향 없음

### 6-5. 1:1 고유성 검증

| 항목 | 수치 |
|---|---|
| 고유 매칭 | 1,273건 / 1,284건 |
| 중복 매칭 (동일 defect_id) | 11건 (0.9%) |

> 99.1% 고유 매칭 — defect_detail 170,904행 중 1,284건만 사용하므로 충돌 확률 극히 낮음

### 6-6. 매칭 결과 분포

**Severity:**

| 등급 | 건수 | 비율 |
|---|---|---|
| MINOR | 879 | 68.5% |
| MAJOR | 252 | 19.6% |
| CRITICAL | 153 | 11.9% |

**재작업 필요 여부:**

| rework | 건수 | 비율 |
|---|---|---|
| Y | 688 | 53.6% |
| N | 596 | 46.4% |

**defect_type별 재작업 시간 (분):**

| defect_type | 재작업 시간 | 비고 |
|---|---|---|
| DST (dust) | 10분 | MINOR |
| SCR (scratch) | 15분 | MINOR |
| ORG (orange_peel) | 20분 | MINOR |
| PDR (paint_drip) | 25분 | MINOR |
| PBB (paint_bubble) | 30분 | MINOR |
| DNT (dent) | 45분 | MAJOR |
| GAP (gap_fault) | 60분 | CRITICAL |
| CRK (crack) | 90분 | CRITICAL |

> 재작업 시간은 master_defect_type의 `std_rework_time_min`과 동일 (defect_type별 고정)

---

## 7. 산출물

| 파일 | 설명 |
|---|---|
| `range_join_analysis.py` | 사전 규모 검증 스크립트 (3조건 매칭 통계) |
| `range_join_match_result.csv` | 사전 규모 검증 결과 (조건별 매칭 수) |
| `range_join_1to1.py` | 1:1 매칭 스크립트 |
| `range_join_1to1_result.csv` | **최종 1:1 매칭 결과** (1,284행) |
| `range_join_label_based.md` | 방법론 설계 문서 (원본 컨텍스트) |

### range_join_1to1_result.csv 컬럼 구조

| 컬럼 | 설명 |
|---|---|
| file | 이미지 파일명 (확장자 제외) |
| split | train / val |
| zone_raw, color_raw | 파일명에서 추출한 zone, color |
| defect_code | YOLO class → defect_type_code |
| bbox_cx, bbox_cy, bbox_area | bbox 정규화 좌표·면적 |
| match_level | exact_3 (type+zone+color) / exact_2 (type+zone) |
| distance | 퍼센타일 유클리드 거리 (낮을수록 매칭 품질 좋음) |
| defect_id | 매칭된 defect_detail 행 ID |
| inspection_id | 매칭된 검사 ID |
| dd_severity | 매칭된 결함 심각도 |
| dd_rework | 재작업 필요 여부 (Y/N) |
| dd_rework_min | 예상 재작업 시간 (분) |
| dd_area_mm2, dd_x_mm, dd_y_mm | defect_detail의 좌표·면적 |
| dd_confidence | 탐지 신뢰도 |

---

## 8. 한계 및 고려사항

| 항목 | 내용 |
|---|---|
| 좌표 체계 차이 | YOLO (정규화 0~1) vs defect_detail (mm) — 퍼센타일로 우회했으나 직접 대응은 불가 |
| color 미매핑 | bronze, green, navy (331건, 25.8%) → zone+type만으로 매칭 (정확도 상대적 저하 가능) |
| bumper/fender 모호성 | bumper → BUMPER_F or R, fender → FF or RF 구분 불가 → 양쪽 모두 포함 |
| 재작업 시간 고정 | defect_type별 고정값 — 실제 재작업 시간은 severity·위치에 따라 달라질 수 있음 |
| 중복 매칭 0.9% | 11건의 defect_id가 2개 bbox에 할당 — 전체 대비 무시 가능 |

---

## 9. 다음 단계

| 순서 | 작업 | 상태 |
|---|---|---|
| 1 | Range Join 사전 규모 검증 (3조건) | ✅ 완료 |
| 2 | Range Join 1:1 매칭 (train + val) | ✅ 완료 |
| 3 | YOLO 추론 결과로 동일 파이프라인 적용 | 예정 |
| 4 | 매칭 결과 + master_defect_type → 재작업 비용 산출 | 예정 |
| 5 | 비용 기반 시각화·대시보드 | 예정 |
