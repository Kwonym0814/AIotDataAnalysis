"""
============================================================
현대자동차그룹 2025 MES 합성 데이터셋 생성기  (v2 — 검증 반영)
============================================================
Source 1: 도장검사 데이터셋 (차종·색상·공장·라인 비율)
Source 2: 2025년 현대자동차 실제 판매 실적
Output  : dataset/mes_2025/ 폴더에 CSV 6개 생성

실행: python generate_mes_dataset.py

v2 변경사항:
  - 날짜 범위를 2025-02-01~12-31로 변경 (기존 데이터 2025-01-24와 겹침 해소)
  - C조 불량률 0% 버그 수정 (소량 생산 시 확률적 불량 판정)
  - 재고 출하량을 실제 생산량 기반으로 보정 (urgent 82% → 정상 수준)
============================================================
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os, warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ── 경로 ───────────────────────────────────────────────
DATA_DIR   = 'dataset/현대_오토에버/track_a_data/'
OUTPUT_DIR = 'dataset/mes_2025/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 기존 마스터 로딩 ───────────────────────────────────
master_model = pd.read_csv(f'{DATA_DIR}master_model.csv')
master_color = pd.read_csv(f'{DATA_DIR}master_color.csv')
master_plant = pd.read_csv(f'{DATA_DIR}master_plant_line.csv')

print("=" * 60)
print("  현대자동차그룹 2025 MES 합성 데이터셋 생성 (v2)")
print("=" * 60)

# ── 1) 기존 데이터셋 비율 추출 ─────────────────────────
print("\n[1/6] 기존 데이터셋 비율 추출...")

# 차종별 비율 (기존 도장검사 데이터 기반)
MODEL_PRODUCTION_PCT = {
    'SS3': 0.1496, 'CN7': 0.1201, 'SV7': 0.1200, 'NQ5': 0.1003,
    'MQ4': 0.1002, 'LX2': 0.0802, 'NE1': 0.0802, 'CK':  0.0797,
    'CV':  0.0699, 'EV9': 0.0399, 'GV80': 0.0300, 'GV70': 0.0299
}

# 색상별 비율 (기존 도장검사 데이터 기반)
COLOR_PCT = {
    'B3L': 0.2002, 'P2W': 0.1800, 'SWP': 0.1199, 'ABP': 0.0998,
    'N5M': 0.0801, 'YW6': 0.0801, 'R4M': 0.0500, 'SSS': 0.0500,
    'TW3': 0.0401, 'W8Y': 0.0300, 'C5G': 0.0200, 'WC9': 0.0199,
    'V5P': 0.0100, 'K3B': 0.0100, 'U3G': 0.0099
}

# ── 2) 2025 판매 데이터 & 수요 예측 ───────────────────
print("[2/6] 수요 예측 테이블 생성 (demand_forecast.csv)...")

# 연간 생산 규모: 기존 데이터 기준 일 ~3,974대 × 365일 ≒ 1,450,510대
# 2~12월(11개월)만 생성하므로 비례 조정
ANNUAL_PRODUCTION_TOTAL = 1_450_000

# 2025 국내 판매량 (실제 데이터 기반 + KIA/NE1 추정치)
DOMESTIC_SALES_2025 = {
    'SS3': 52_435,   # 쏘나타 (실적)
    'CN7': 79_335,   # 아반떼 (실적, 세단 1위)
    'SV7': 57_889,   # 싼타페 (실적, -25% YoY)
    'NQ5': 53_901,   # 투싼 (실적)
    'LX2': 60_909,   # 팰리세이드 (실적, 2세대 출시)
    'NE1': 38_500,   # 아이오닉5 (추정, EV 국내 판매 비율 기반)
    'MQ4': 68_500,   # 스포티지 (추정, KIA SUV 1위)
    'CK':  42_000,   # K5 (추정, KIA 세단)
    'CV':  55_000,   # 카니발 (추정, MPV 시장 1위)
    'EV9': 12_500,   # EV9 (추정, 프리미엄 EV)
    'GV80': 32_396,  # GV80 (실적)
    'GV70': 34_710,  # GV70 (실적)
}

# 월별 계절 지수
MONTHLY_SEASONALITY = {
    1: 0.90, 2: 0.85, 3: 1.02, 4: 1.05,
    5: 1.03, 6: 0.97, 7: 0.88, 8: 0.85,
    9: 1.03, 10: 0.84, 11: 0.95, 12: 0.98
}
season_sum = sum(MONTHLY_SEASONALITY.values())
MONTHLY_SEASONALITY = {k: v / season_sum * 12 for k, v in MONTHLY_SEASONALITY.items()}

# 수요 예측 테이블 (2~12월만)
demand_rows = []
for month in range(2, 13):
    season = MONTHLY_SEASONALITY[month]
    for model, annual_domestic in DOMESTIC_SALES_2025.items():
        model_pct = MODEL_PRODUCTION_PCT[model]
        annual_prod = int(ANNUAL_PRODUCTION_TOTAL * model_pct)

        domestic_forecast = int(annual_domestic * season / 12)
        export_annual = annual_prod - annual_domestic
        if export_annual < 0:
            export_annual = int(annual_domestic * 0.3)
            annual_prod = annual_domestic + export_annual
        export_forecast = int(export_annual * season / 12)
        total_forecast = domestic_forecast + export_forecast

        demand_rows.append({
            'year': 2025, 'month': month,
            'model_code': model,
            'domestic_forecast': domestic_forecast,
            'export_forecast': export_forecast,
            'total_forecast': total_forecast,
            'annual_domestic_sales': annual_domestic,
            'seasonality_index': round(season, 4)
        })

demand_df = pd.DataFrame(demand_rows)
demand_df.to_csv(f'{OUTPUT_DIR}mes_demand_forecast.csv', index=False, encoding='utf-8-sig')
print(f"  → mes_demand_forecast.csv: {len(demand_df)}행 (2~12월)")

# ── 3) 생산 계획 테이블 ────────────────────────────────
print("[3/6] 생산 계획 테이블 생성 (production_plan.csv)...")

SAFETY_STOCK_DAYS = 7
WORKING_DAYS_PER_MONTH = 25

plan_rows = []
initial_inventory = {}
for model, pct in MODEL_PRODUCTION_PCT.items():
    annual_prod = int(ANNUAL_PRODUCTION_TOTAL * pct)
    daily_total_demand = annual_prod / 365
    initial_inventory[model] = int(daily_total_demand * 10)  # 10일분

opening_inventory = dict(initial_inventory)

for month in range(2, 13):
    month_demand = demand_df[demand_df['month'] == month]
    for _, row in month_demand.iterrows():
        model = row['model_code']
        total_demand = row['total_forecast']

        daily_demand = total_demand / WORKING_DAYS_PER_MONTH
        safety_stock_target = int(daily_demand * SAFETY_STOCK_DAYS)

        net_requirement = total_demand + safety_stock_target - opening_inventory[model]
        production_target = max(net_requirement, 0)

        max_daily_capacity = 4_100
        max_monthly_capacity = max_daily_capacity * WORKING_DAYS_PER_MONTH
        model_capacity = int(max_monthly_capacity * MODEL_PRODUCTION_PCT[model])

        planned_production = min(production_target, model_capacity)

        closing_inventory = opening_inventory[model] + planned_production - total_demand
        closing_inventory = max(closing_inventory, 0)

        plan_rows.append({
            'year': 2025, 'month': month,
            'model_code': model,
            'total_demand_forecast': total_demand,
            'opening_inventory': opening_inventory[model],
            'safety_stock_target': safety_stock_target,
            'net_requirement': max(net_requirement, 0),
            'production_capacity': model_capacity,
            'planned_production': planned_production,
            'closing_inventory': closing_inventory,
            'capacity_utilization_pct': round(planned_production / model_capacity * 100, 1) if model_capacity > 0 else 0
        })
        opening_inventory[model] = closing_inventory

plan_df = pd.DataFrame(plan_rows)
plan_df.to_csv(f'{OUTPUT_DIR}mes_production_plan.csv', index=False, encoding='utf-8-sig')
print(f"  → mes_production_plan.csv: {len(plan_df)}행")

# ── 4) 2025년 영업일 캘린더 (2월~12월) ─────────────────
print("[4/6] 작업지시 & 생산실적 테이블 생성...")

HOLIDAYS_2025 = [
    datetime(2025,3,1),   # 삼일절
    datetime(2025,5,5),   # 어린이날/부처님오신날
    datetime(2025,5,6),   # 대체공휴일
    datetime(2025,6,6),   # 현충일
    datetime(2025,8,15),  # 광복절
    datetime(2025,10,3),  # 개천절
    datetime(2025,10,5), datetime(2025,10,6), datetime(2025,10,7),  # 추석
    datetime(2025,10,9),  # 한글날
    datetime(2025,12,25), # 크리스마스
]

def get_working_days():
    """2025-02-01 ~ 2025-12-31 영업일(월~토) - 공휴일 제외"""
    start = datetime(2025, 2, 1)
    end   = datetime(2025, 12, 31)
    days = []
    d = start
    while d <= end:
        if d.weekday() < 6 and d not in HOLIDAYS_2025:
            days.append(d)
        d += timedelta(days=1)
    return days

working_days = get_working_days()
working_days_set = set(working_days)
print(f"  영업일 수: {len(working_days)}일 (2025-02-01 ~ 2025-12-31)")

# ── 공장-라인 할당 ─────────────────────────────────────
PLANT_LINES = [
    ('ULN', 'UL1'), ('ULN', 'UL2'), ('ULN', 'UL3'), ('ULN', 'UL4'), ('ULN', 'UL5'),
    ('ASN', 'AS1'), ('ASN', 'AS2'), ('ASN', 'AS3'),
    ('GWJ', 'GW1'), ('GWJ', 'GW2'),
    ('HWS', 'HW1'), ('HWS', 'HW2'), ('HWS', 'HW3'),
]

LINE_CAPACITY_PCT = {
    'UL1': 0.0773, 'UL2': 0.0773, 'UL3': 0.0772, 'UL4': 0.0770, 'UL5': 0.0774,
    'AS1': 0.0717, 'AS2': 0.0717, 'AS3': 0.0716,
    'GW1': 0.0644, 'GW2': 0.0642,
    'HW1': 0.0430, 'HW2': 0.0429, 'HW3': 0.0428,
}
lc_sum = sum(LINE_CAPACITY_PCT.values())
LINE_CAPACITY_PCT = {k: v/lc_sum for k, v in LINE_CAPACITY_PCT.items()}

SHIFT_PCT = {'A': 0.470, 'B': 0.471, 'C': 0.059}
SHIFT_DEFECT_RATE = {'A': 0.0412, 'B': 0.0377, 'C': 0.0602}

# ── 5) 작업지시 + 생산실적 동시 생성 ──────────────────
work_order_rows = []
production_rows = []
wo_counter = 0

monthly_plans = plan_df.set_index(['month', 'model_code'])['planned_production'].to_dict()

for day in working_days:
    month = day.month
    day_str = day.strftime('%Y-%m-%d')

    month_working_days = [d for d in working_days if d.month == month]
    n_working_days = len(month_working_days)

    for plant_code, line_code in PLANT_LINES:
        line_pct = LINE_CAPACITY_PCT[line_code]

        for model_code in MODEL_PRODUCTION_PCT:
            model_pct = MODEL_PRODUCTION_PCT[model_code]

            monthly_target = monthly_plans.get((month, model_code), 0)
            daily_base = monthly_target / n_working_days
            daily_target_model = daily_base * line_pct

            if daily_target_model < 0.3:
                continue

            for shift, shift_pct in SHIFT_PCT.items():
                planned_qty = daily_target_model * shift_pct

                if planned_qty < 0.1:
                    continue

                # 반올림 + 노이즈
                noise = np.random.normal(0, 0.03)
                planned_qty_int = max(1, int(round(planned_qty * (1 + noise * 0.3))))

                # 실제 생산량
                prod_noise = np.random.normal(0, 0.02)
                actual_qty = max(1, int(round(planned_qty_int * (1 + prod_noise))))

                # ── FIX: 확률적 불량 판정 (소량 생산에서도 불량률 반영) ──
                defect_rate = SHIFT_DEFECT_RATE[shift]
                if day.weekday() == 0:  # 월요일 +10%
                    defect_rate *= 1.1
                # 각 대수를 독립 베르누이 시행으로 불량 판정
                defect_qty = np.random.binomial(actual_qty, defect_rate)
                good_qty = actual_qty - defect_qty

                # 색상 (확률적 선택)
                color_code = np.random.choice(
                    list(COLOR_PCT.keys()),
                    p=list(COLOR_PCT.values())
                )

                achievement = round(actual_qty / planned_qty_int * 100, 1) if planned_qty_int > 0 else 0
                yield_rate = round(good_qty / actual_qty * 100, 2) if actual_qty > 0 else 100.0

                downtime_min = 0
                if np.random.random() < 0.08:
                    downtime_min = int(np.random.exponential(15))

                takt_time = round(np.random.normal(2.80, 0.30), 2)
                takt_time = max(1.5, min(4.5, takt_time))

                wo_counter += 1
                wo_id = f"WO{wo_counter:08d}"

                priority = 'NORMAL'
                if shift == 'C':
                    priority = 'LOW'
                elif model_code in ('GV80', 'GV70', 'EV9'):
                    priority = 'HIGH'

                work_order_rows.append({
                    'work_order_id': wo_id,
                    'order_date': day_str,
                    'model_code': model_code,
                    'color_code': color_code,
                    'plant_code': plant_code,
                    'line_code': line_code,
                    'shift': shift,
                    'planned_qty': planned_qty_int,
                    'priority': priority,
                    'status': 'COMPLETED'
                })

                production_rows.append({
                    'result_id': f"PR{wo_counter:08d}",
                    'work_order_id': wo_id,
                    'date': day_str,
                    'model_code': model_code,
                    'color_code': color_code,
                    'plant_code': plant_code,
                    'line_code': line_code,
                    'shift': shift,
                    'planned_qty': planned_qty_int,
                    'actual_qty': actual_qty,
                    'good_qty': good_qty,
                    'defect_qty': defect_qty,
                    'yield_rate': yield_rate,
                    'achievement_rate': achievement,
                    'takt_time_sec': takt_time,
                    'downtime_min': downtime_min
                })

print(f"  작업지시 생성: {wo_counter:,}건")

work_order_df = pd.DataFrame(work_order_rows)
work_order_df.to_csv(f'{OUTPUT_DIR}mes_work_order.csv', index=False, encoding='utf-8-sig')
print(f"  → mes_work_order.csv: {len(work_order_df):,}행")

production_df = pd.DataFrame(production_rows)
production_df.to_csv(f'{OUTPUT_DIR}mes_production_result.csv', index=False, encoding='utf-8-sig')
print(f"  → mes_production_result.csv: {len(production_df):,}행")

# ── 6) 재고 관리 테이블 (출하량 = 실제 생산 기반 보정) ──
print("[5/6] 재고 관리 테이블 생성 (inventory_daily.csv)...")

# ── FIX: 출하량 기준을 실제 생산량 기반으로 보정 ──
# 먼저 모델별 실제 일평균 양품 생산량 계산
prod_good_daily = production_df.groupby('model_code')['good_qty'].sum()
n_working = len(working_days)
model_daily_good = {m: prod_good_daily.get(m, 0) / n_working for m in MODEL_PRODUCTION_PCT}

all_days = pd.date_range('2025-02-01', '2025-12-31', freq='D')
inventory_rows = []
inv_stock = dict(initial_inventory)

for day in all_days:
    day_str = day.strftime('%Y-%m-%d')
    is_working = day.to_pydatetime() in working_days_set

    for model_code in MODEL_PRODUCTION_PCT:
        opening = inv_stock.get(model_code, 0)

        # 생산량 (영업일만)
        if is_working:
            day_prod = production_df[
                (production_df['date'] == day_str) &
                (production_df['model_code'] == model_code)
            ]['good_qty'].sum()
        else:
            day_prod = 0

        # ── FIX: 출하량 = 실제 양품 기반 일평균 ──
        # 6일 영업(1.1배) + 1일 휴일(0.4배) = 6*1.1 + 1*0.4 = 7.0배/주
        # 주당 평균 = daily_good * 6 (영업일만 생산)
        # → 일 출하 = (daily_good * 6) / 7 ≈ daily_good * 0.857
        daily_avg_ship = model_daily_good[model_code] * 6 / 7  # 생산-출하 균형

        if is_working:
            ship_factor = np.random.normal(1.1, 0.05)
        else:
            ship_factor = np.random.normal(0.4, 0.05)

        shipment = max(0, int(round(daily_avg_ship * max(0.1, ship_factor))))
        shipment = min(shipment, opening + day_prod)

        closing = max(0, opening + day_prod - shipment)

        # 안전재고: 양품 기준 7일분
        safety_stock = int(model_daily_good[model_code] * SAFETY_STOCK_DAYS)

        dos = round(closing / daily_avg_ship, 1) if daily_avg_ship > 0 else 0
        urgent = 'Y' if closing < safety_stock * 0.5 else 'N'

        inventory_rows.append({
            'date': day_str,
            'model_code': model_code,
            'opening_stock': opening,
            'produced_qty': int(day_prod),
            'shipped_qty': shipment,
            'closing_stock': closing,
            'safety_stock_target': safety_stock,
            'days_of_supply': dos,
            'urgent_flag': urgent
        })
        inv_stock[model_code] = closing

inventory_df = pd.DataFrame(inventory_rows)
inventory_df.to_csv(f'{OUTPUT_DIR}mes_inventory_daily.csv', index=False, encoding='utf-8-sig')
print(f"  → mes_inventory_daily.csv: {len(inventory_df):,}행")

# ── 7) 월별 색상 생산 집계 ────────────────────────────
print("[6/6] 월별 색상 생산 집계 테이블 생성...")

production_df['date'] = pd.to_datetime(production_df['date'])
production_df['month'] = production_df['date'].dt.month

color_monthly = production_df.groupby(['month', 'model_code', 'color_code']).agg(
    total_produced=('actual_qty', 'sum'),
    total_good=('good_qty', 'sum'),
    total_defect=('defect_qty', 'sum'),
    work_order_count=('work_order_id', 'count')
).reset_index()
color_monthly['year'] = 2025
color_monthly = color_monthly[['year','month','model_code','color_code',
                                'total_produced','total_good','total_defect','work_order_count']]
color_monthly.to_csv(f'{OUTPUT_DIR}mes_color_production.csv', index=False, encoding='utf-8-sig')
print(f"  → mes_color_production.csv: {len(color_monthly):,}행")

# ── 마스터 테이블 복사 ─────────────────────────────────
master_model.to_csv(f'{OUTPUT_DIR}master_model.csv', index=False, encoding='utf-8-sig')
master_color.to_csv(f'{OUTPUT_DIR}master_color.csv', index=False, encoding='utf-8-sig')
master_plant.to_csv(f'{OUTPUT_DIR}master_plant_line.csv', index=False, encoding='utf-8-sig')
print(f"  → 마스터 테이블 3개 복사 완료")

# ── 검증 & 요약 ───────────────────────────────────────
print("\n" + "=" * 60)
print("  생성 결과 요약 (v2)")
print("=" * 60)

total_planned = work_order_df['planned_qty'].sum()
total_actual = production_df['actual_qty'].sum()
total_good = production_df['good_qty'].sum()
total_defect = production_df['defect_qty'].sum()

print(f"\n  기간           : 2025-02-01 ~ 2025-12-31")
print(f"  영업일 수      : {len(working_days)}일")
print(f"  작업지시 건수   : {len(work_order_df):,}건")
print(f"  계획 생산량     : {total_planned:,}대")
print(f"  실제 생산량     : {total_actual:,}대")
print(f"  양품 수량      : {total_good:,}대 ({total_good/total_actual*100:.2f}%)")
print(f"  불량 수량      : {total_defect:,}대 ({total_defect/total_actual*100:.2f}%)")

# 교대조별 불량률 확인
print(f"\n  [교대조별 불량률]")
for s in ['A','B','C']:
    sd = production_df[production_df['shift']==s]
    fr = sd['defect_qty'].sum() / sd['actual_qty'].sum() * 100
    print(f"    {s}조: {sd['actual_qty'].sum():>10,}대, 불량률 {fr:.2f}% (목표: {SHIFT_DEFECT_RATE[s]*100:.2f}%)")

# 재고 urgent 비율 확인
urgent_rate = (inventory_df['urgent_flag']=='Y').mean()*100
print(f"\n  재고 urgent 비율: {urgent_rate:.1f}%")

print(f"\n  [차종별 생산량]")
model_summary = production_df.groupby('model_code')['actual_qty'].sum().sort_values(ascending=False)
for model, qty in model_summary.items():
    name = master_model[master_model['model_code']==model]['model_name'].values[0]
    print(f"    {name:10s} ({model}): {qty:>10,}대 ({qty/total_actual*100:.1f}%)")

print(f"\n  출력 폴더: {os.path.abspath(OUTPUT_DIR)}")
print("=" * 60)

