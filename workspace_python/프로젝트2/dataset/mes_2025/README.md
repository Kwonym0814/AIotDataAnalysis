# 현대자동차그룹 2025 MES 합성 데이터셋

## 개요

자동차 제조 공정의 MES(Manufacturing Execution System) 데이터를 시뮬레이션한 합성 데이터셋.
**수요예측 → 생산계획 → 작업지시 → 생산실적 → 재고관리**의 5-Layer MES 파이프라인을 재현한다.

### 데이터 기반
| 소스 | 내용 | 활용 |
|------|------|------|
| 도장검사 데이터셋 (Track A) | 300만건, 12모델, 15색상, 4공장 13라인 | 차종·색상·공장 비율, 불량률 패턴 |
| 2025 현대차 판매 실적 | 국내 712,954대, 글로벌 4,138,180대 | 수요예측(주문량), 계절성 지수 |

### 기존 데이터와의 연속성
```
[기존 도장검사 데이터]        [MES 합성 데이터]
2023-01-01 ────────── 2025-01-24  2025-02-01 ────────── 2025-12-31
        3,000,000건                    1,129,615건
     (동일 마스터 테이블 공유: model / color / plant_line)
```
- 1월분은 기존 도장검사 데이터(~01-24)로 커버, MES는 2월부터 시작하여 **날짜 겹침 없음**
- 기존 마스터 테이블(model, color, plant_line)을 **그대로 재사용** → FK 정합성 100%

### 시뮬레이션 파라미터
| 항목 | 값 |
|------|-----|
| 기간 | 2025-02-01 ~ 2025-12-31 (11개월) |
| 영업일 | 276일 (월~토, 공휴일 11일 제외) |
| 생산량 | ~1,130,000대 (연율 ~1,390,000대) |
| 안전재고일수 | 7일 |
| 생산 편차 | ±2% (정규분포) |
| 출하 편차 | ±5% |
| 불량률 | A조 4.21%, B조 3.81%, C조 6.27% (기존 패턴 반영) |

### 품질 검증 결과 (v2)
| 검증 항목 | 결과 |
|-----------|------|
| FK 정합성 (마스터 테이블) | ✅ 7/7 항목 OK |
| 차종 비율 편차 | ✅ 최대 ±0.13pp (기존 대비) |
| 색상 비율 편차 | ✅ 최대 ±0.14pp |
| 공장 비율 편차 | ✅ 최대 ±0.13pp |
| 교대조 불량률 | ✅ A=4.21%, B=3.81%, C=6.27% |
| 재고 연속성 | ✅ 불연속 0건, 마이너스 0건 |
| WO↔실적 1:1 관계 | ✅ 누락/중복 0건 |
| NULL 값 | ✅ 전 테이블 0건 |
| 날짜 겹침 | ✅ 없음 (MES 2/1~ vs 기존 ~1/24) |

---

## 파일 구조

```
dataset/mes_2025/
├── mes_demand_forecast.csv      5.5 KB     132행   수요예측 (월×모델, 2~12월)
├── mes_production_plan.csv      6.8 KB     132행   생산계획 (월×모델, 2~12월)
├── mes_work_order.csv           7.7 MB  129,168행   작업지시 (일×라인×모델×교대조)
├── mes_production_result.csv   10.4 MB  129,168행   생산실적 (일×라인×모델×교대조)
├── mes_inventory_daily.csv    159.0 KB   4,008행   재고현황 (일×모델)
├── mes_color_production.csv    59.3 KB   1,980행   색상별 생산집계 (월×모델×색상)
│
│   ── 건조로 예지보전 (KAMP 기반) ──
├── mes_oven_sensor.csv         ~10 MB  154,284행   건조로 센서 (Process 단위)
├── mes_oven_anomaly_log.csv              12,861행   이상 감지 이벤트 로그
│
├── master_model.csv                        12행   차종 마스터
├── master_color.csv                        15행   색상 마스터
└── master_plant_line.csv                   13행   공장-라인 마스터
```

### 전체 파이프라인
```
[수요/생산 계획] → [작업지시] → [생산실적] → [재고관리]
                                    ↓
                          [도장 공정 검사]  ←── inspection_master (기존)
                                    ↓
                          [건조로 통과]      ←── mes_oven_sensor (신규)
                                    ↓
                          [예지보전 모델]    ←── LSTM-AutoEncoder
```

---

## 테이블 상세

### 1. mes_demand_forecast.csv (수요예측)
> 월별 × 차종별 판매 수요 예측. B2C 특성상 연간 판매량 예측 기반.

| 컬럼 | 설명 |
|------|------|
| year, month | 연월 |
| model_code | 차종 코드 (→ master_model) |
| domestic_forecast | 국내 판매 예측 (대) |
| export_forecast | 해외 수출 예측 (대) |
| total_forecast | 총 수요 예측 (대) |
| annual_domestic_sales | 연간 국내 판매 기준 (2025 실적) |
| seasonality_index | 월별 계절 지수 (1.0 = 평균) |

**수요 산출 로직:**
- 국내: 2025 실적 (HMC 6모델 실적 + KIA 4모델 추정 + GEN 2모델 실적)
- 해외: (연간 생산량 - 국내 판매) × 계절지수 / 12
- 계절성: 공개된 5개월(4,6,9,10,11월) 실적에서 추출 + 자동차 산업 패턴 보간

---

### 2. mes_production_plan.csv (생산계획)
> 월별 × 차종별 생산 목표 수량. 수요 + 안전재고를 고려한 MRP 로직.

| 컬럼 | 설명 |
|------|------|
| total_demand_forecast | 총 수요 예측 |
| opening_inventory | 기초 재고 |
| safety_stock_target | 안전재고 목표 (7일분) |
| net_requirement | 순소요량 = 수요 + 안전재고 - 기초재고 |
| production_capacity | 월 생산 능력 (라인 Capa 기반) |
| planned_production | 계획 생산량 = min(순소요량, Capa) |
| closing_inventory | 기말 재고 = 기초 + 생산 - 수요 |
| capacity_utilization_pct | 설비 가동률 (%) |

---

### 3. mes_work_order.csv (작업지시)
> 일별 생산 작업지시. 라인-교대조-차종-색상 단위.

| 컬럼 | 설명 |
|------|------|
| work_order_id | 작업지시 ID (WO로 시작) |
| order_date | 작업일 |
| model_code | 차종 코드 |
| color_code | 색상 코드 |
| plant_code, line_code | 공장/라인 |
| shift | 교대조 (A/B/C) |
| planned_qty | 계획 수량 (대) |
| priority | 우선순위 (HIGH/NORMAL/LOW) |
| status | 상태 (COMPLETED) |

**우선순위 규칙:**
- HIGH: 프리미엄 모델 (GV80, GV70, EV9)
- NORMAL: 일반 모델
- LOW: C조(야간) 작업

---

### 4. mes_production_result.csv (생산실적)
> 작업지시 대비 실제 생산 실적. work_order_id로 1:1 조인.

| 컬럼 | 설명 |
|------|------|
| result_id | 실적 ID (PR로 시작) |
| work_order_id | 작업지시 ID (→ mes_work_order) |
| planned_qty | 계획 수량 |
| actual_qty | 실제 생산량 (계획 ±2% 편차) |
| good_qty | 양품 수량 |
| defect_qty | 불량 수량 |
| yield_rate | 양품률 (%) |
| achievement_rate | 달성률 (%) = 실적/계획 |
| takt_time_sec | 택트 타임 (초) |
| downtime_min | 비계획 정지 시간 (분, 8% 확률 발생) |

**불량률 패턴:**
- A조(주간): 4.12% — 교대 시작 직후(06시) 약간 상승
- B조(오후): 3.77% — 가장 안정적
- C조(야간): 6.02% — 평균 대비 +48%
- 월요일 불량률 +10% (주말 후 워밍업 효과)

---

### 5. mes_inventory_daily.csv (재고현황)
> 일별 × 차종별 완성차 재고 추적.

| 컬럼 | 설명 |
|------|------|
| date | 일자 (365일 전체) |
| model_code | 차종 코드 |
| opening_stock | 기초 재고 |
| produced_qty | 당일 생산 (양품만) |
| shipped_qty | 당일 출하 |
| closing_stock | 기말 재고 = 기초 + 생산 - 출하 |
| safety_stock_target | 안전재고 기준 (7일분) |
| days_of_supply | 재고일수 (DOS) = 기말재고 / 일평균출하 |
| urgent_flag | 긴급 플래그 (Y/N, 재고 < 안전재고 50%) |

**재고 로직:**
- 영업일 출하량: 일평균 × 1.1 (±8% 노이즈)
- 휴일 출하량: 일평균 × 0.4 (딜러/물류 운영)
- 기초 재고: 10일분 → 안전재고 7일 기준 운영

---

### 6. mes_color_production.csv (색상별 생산집계)
> 월별 × 차종별 × 색상별 생산 집계.

| 컬럼 | 설명 |
|------|------|
| total_produced | 총 생산량 |
| total_good | 양품 수량 |
| total_defect | 불량 수량 |
| work_order_count | 작업지시 건수 |

---

### 7. mes_oven_sensor.csv (건조로 센서)
> 도장 후 건조로(Oven) 통과 기록. 차체 1대 = 1 Process = 180초(3분).
> KAMP 열풍건조 센서 데이터를 자동차 도장 건조 조건(90~130°C, 15~25A)으로 변환.

| 컬럼 | 설명 |
|------|------|
| date | 작업일 |
| oven_id | 건조로 ID (OV-UL1 ~ OV-HW3, 13개) |
| plant_code | 공장 코드 (→ master_plant_line) |
| process_no | 차체 통과 순번 (1~43/일) |
| avg_oven_temp | 평균 건조 온도 (°C) |
| max/min/std_oven_temp | 최대/최저/표준편차 온도 |
| avg_heater_curr | 평균 히터 전류 (A) |
| zone1~4_avg_temp | Zone별 평균 온도 (예열→피크→유지→서냉) |
| label | 이상 여부 (0=정상, 1=이상) |
| anomaly_type | 이상 유형 (NORMAL / HEATER_DEGRADATION / TEMP_SENSOR_ERR / CIRCULATION_FAN / CONVEYOR_SPEED) |

**건조로 Zone 구성:**
```
Z1 예열 (0~45s, 90~110°C) → Z2 피크 (45~90s, 120~130°C)
→ Z3 유지 (90~135s, 120~130°C) → Z4 서냉 (135~180s, 90~110°C)
```

**이상 유형 & 센서 패턴:**
| 유형 | 원인 | 패턴 | 심각도 |
|------|------|------|--------|
| HEATER_DEGRADATION | 히터 열화 | 전류 감소 + 온도 하강 | MEDIUM |
| TEMP_SENSOR_ERR | 온도센서 오류 | 온도 급등 (스파이크) | HIGH |
| CIRCULATION_FAN | 순환팬 고장 | 온도 편차(std) 급증 | MEDIUM |
| CONVEYOR_SPEED | 컨베이어 속도 이상 | Zone간 온도 편차 변화 | MEDIUM |

---

### 8. mes_oven_anomaly_log.csv (이상 감지 이벤트)
> 건조로 이상 감지 이벤트 로그. 예지보전 알람 기록.

| 컬럼 | 설명 |
|------|------|
| event_id | 이벤트 ID (AE로 시작) |
| date / oven_id / plant_code | 발생 위치 |
| process_no | 이상 발생 차체 순번 |
| anomaly_type | 이상 유형 |
| avg_temp_at_event / avg_curr_at_event | 이상 시점 센서값 |
| severity | 심각도 (HIGH / MEDIUM) |
| maintenance_required | 점검 필요 여부 (Y/N) |

---

## 테이블 관계도

```
mes_demand_forecast (수요예측)
    │
    ▼
mes_production_plan (생산계획)
    │ [월별 계획 → 일별 분배]
    ▼
mes_work_order (작업지시)  ←──── master_model / master_color / master_plant_line
    │ [1:1 매핑]
    ▼
mes_production_result (생산실적)  ──────────────────────────┐
    │ [양품 집계]                                            │ [date × plant_code 조인]
    ▼                                                       ▼
mes_inventory_daily (재고현황)          mes_oven_sensor (건조로 센서)
                                                │ [label=1 집계]
                                                ▼
                                   mes_oven_anomaly_log (이상 이벤트)
                                                │ [LSTM-AE 예지보전 모델]
                                                ▼
                                    models/oven_lstm_ae_OV_UL1.keras
```

---

## 차종별 비율 (기존 도장검사 데이터 기반)

| 순위 | 모델 | 브랜드 | 생산비율 | 2025 국내판매 | 비고 |
|------|------|--------|---------|-------------|------|
| 1 | SS3 쏘나타 | HMC | 14.96% | 52,435대 | 실적 |
| 2 | CN7 아반떼 | HMC | 12.01% | 79,335대 | 실적, 세단 1위 |
| 3 | SV7 싼타페 | HMC | 12.00% | 57,889대 | 실적, -25% YoY |
| 4 | NQ5 투싼 | HMC | 10.03% | 53,901대 | 실적 |
| 5 | MQ4 스포티지 | KIA | 10.02% | ~68,500대 | 추정 |
| 6 | LX2 팰리세이드 | HMC | 8.02% | 60,909대 | 실적, 2세대 흥행 |
| 7 | NE1 아이오닉5 | HMC | 8.02% | ~38,500대 | 추정 |
| 8 | CK K5 | KIA | 7.97% | ~42,000대 | 추정 |
| 9 | CV 카니발 | KIA | 6.99% | ~55,000대 | 추정 |
| 10 | EV9 | KIA | 3.99% | ~12,500대 | 추정 |
| 11 | GV80 | GEN | 3.00% | 32,396대 | 실적 |
| 12 | GV70 | GEN | 2.99% | 34,710대 | 실적 |

> ※ KIA/NE1 국내 판매는 2025 KIA 시장점유율 기반 추정치

---

## 색상 비율 (기존 도장검사 데이터 기반)

| 색상코드 | 색상명 | 비율 |
|----------|--------|------|
| B3L | 아비스블랙 | 20.0% |
| P2W | 퓨어화이트 | 18.0% |
| SWP | 스노우화이트펄 | 12.0% |
| ABP | 오로라블랙펄 | 10.0% |
| N5M | 나이트섀도우그레이 | 8.0% |
| YW6 | 문라이트클라우드 | 8.0% |
| R4M | 플레임레드 | 5.0% |
| SSS | 스타더스트실버 | 5.0% |
| TW3 | 티타늄그레이 | 4.0% |
| 기타 6색 | — | 9.0% |

> 흑백계열(B3L+P2W+SWP+ABP) = 60%, 한국 시장 선호 반영

---

## 생성 스크립트

```bash
# 1단계: MES 주문/생산/재고 데이터 생성
python generate_mes_dataset.py

# 2단계: 건조로 센서 데이터 생성 (KAMP 기반)
python generate_oven_sensor.py

# 3단계: 예지보전 LSTM-AE 모델 학습 + 리포트
python train_oven_anomaly.py
```

| 스크립트 | 출력 | 비고 |
|----------|------|------|
| `generate_mes_dataset.py` | MES CSV 6종 | seed=42 |
| `generate_oven_sensor.py` | `mes_oven_sensor.csv`, `mes_oven_anomaly_log.csv` | KAMP 33일 → 276일 확장 |
| `train_oven_anomaly.py` | `models/oven_lstm_ae_OV_UL1.keras`, `oven_anomaly_report.html` | TensorFlow 필요 |

---

*생성일: 2026-04-13*  
*데이터 소스: 현대 오토에버 Track A Dataset + 현대차 2025 공식 판매 실적 + KAMP 열풍건조 센서 데이터*



