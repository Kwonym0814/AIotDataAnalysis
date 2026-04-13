import pandas as pd
import numpy as np

data_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\현대_오토에버\\track_a_data\\'
mes_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\mes_2025\\'

# 마스터 테이블 로드
m_model = pd.read_csv(mes_path + 'master_model.csv')
m_color = pd.read_csv(mes_path + 'master_color.csv')
m_plant = pd.read_csv(mes_path + 'master_plant_line.csv')

wo = pd.read_csv(mes_path + 'mes_work_order.csv')
pr = pd.read_csv(mes_path + 'mes_production_result.csv')
inv = pd.read_csv(mes_path + 'mes_inventory_daily.csv')
oven = pd.read_csv(mes_path + 'mes_oven_sensor.csv')
anomaly = pd.read_csv(mes_path + 'mes_oven_anomaly_log.csv')

results = []

# =============================================
# 1. FK 정합성
# =============================================
print("=" * 50)
print("1. FK 정합성 검증")
print("=" * 50)

checks = {
    "WO - model_code": (wo['model_code'], m_model['model_code']),
    "WO - color_code": (wo['color_code'], m_color['color_code']),
    "WO - plant_code": (wo['plant_code'], m_plant['plant_code']),
    "WO - line_code":  (wo['line_code'],  m_plant['line_code']),
    "PR - model_code": (pr['model_code'], m_model['model_code']),
    "PR - color_code": (pr['color_code'], m_color['color_code']),
    "PR - plant_code": (pr['plant_code'], m_plant['plant_code']),
    "Oven - plant_code": (oven['plant_code'], m_plant['plant_code']),
    "Anomaly - plant_code": (anomaly['plant_code'], m_plant['plant_code']),
}
for name, (col, master) in checks.items():
    invalid = ~col.isin(master)
    status = "✅" if invalid.sum() == 0 else "❌"
    print(f"  {status} {name}: 미매핑 {invalid.sum():,}건")

# =============================================
# 2. WO ↔ PR 1:1 관계
# =============================================
print("\n" + "=" * 50)
print("2. work_order ↔ production_result 1:1 관계")
print("=" * 50)

wo_ids = set(wo['work_order_id'])
pr_ids = set(pr['work_order_id'])
only_wo = wo_ids - pr_ids
only_pr = pr_ids - wo_ids
dup_pr = pr[pr.duplicated('work_order_id', keep=False)]

print(f"  {'✅' if len(only_wo)==0 else '❌'} WO에만 있는 ID: {len(only_wo):,}건")
print(f"  {'✅' if len(only_pr)==0 else '❌'} PR에만 있는 ID: {len(only_pr):,}건")
print(f"  {'✅' if len(dup_pr)==0 else '❌'} PR 중복 work_order_id: {len(dup_pr):,}건")

# =============================================
# 3. 수치 논리 검증
# =============================================
print("\n" + "=" * 50)
print("3. 수치 논리 검증")
print("=" * 50)

# 3-1. good + defect = actual
pr['qty_check'] = pr['good_qty'] + pr['defect_qty'] - pr['actual_qty']
invalid_qty = (pr['qty_check'].abs() > 0.01).sum()
print(f"  {'✅' if invalid_qty==0 else '❌'} good_qty + defect_qty = actual_qty: 불일치 {invalid_qty:,}건")

# 3-2. yield_rate = good / actual * 100
pr['yield_check'] = (pr['good_qty'] / pr['actual_qty'] * 100 - pr['yield_rate']).abs()
invalid_yield = (pr['yield_check'] > 0.1).sum()
print(f"  {'✅' if invalid_yield==0 else '❌'} yield_rate 계산 일치: 불일치 {invalid_yield:,}건")

# 3-3. achievement_rate = actual / planned * 100
pr['ach_check'] = (pr['actual_qty'] / pr['planned_qty'] * 100 - pr['achievement_rate']).abs()
invalid_ach = (pr['ach_check'] > 0.1).sum()
print(f"  {'✅' if invalid_ach==0 else '❌'} achievement_rate 계산 일치: 불일치 {invalid_ach:,}건")

# 3-4. 재고: opening + produced - shipped = closing
inv['inv_check'] = (inv['opening_stock'] + inv['produced_qty'] - inv['shipped_qty'] - inv['closing_stock']).abs()
invalid_inv = (inv['inv_check'] > 0.01).sum()
print(f"  {'✅' if invalid_inv==0 else '❌'} 재고 연속성(opening+produced-shipped=closing): 불일치 {invalid_inv:,}건")

# 3-5. 음수 재고
neg_inv = (inv['closing_stock'] < 0).sum()
print(f"  {'✅' if neg_inv==0 else '❌'} 음수 재고: {neg_inv:,}건")

# =============================================
# 4. 날짜 연속성
# =============================================
print("\n" + "=" * 50)
print("4. 날짜 연속성 검증")
print("=" * 50)

inv['date'] = pd.to_datetime(inv['date'])
for model in inv['model_code'].unique():
    sub = inv[inv['model_code']==model].sort_values('date')
    gaps = sub['date'].diff().dropna()
    if (gaps > pd.Timedelta(days=1)).any():
        print(f"  ❌ {model}: 날짜 누락 있음")
        break
else:
    print(f"  ✅ 전 모델 재고 날짜 연속성 이상 없음")

# =============================================
# 5. 센서값 범위 검증
# =============================================
print("\n" + "=" * 50)
print("5. 건조로 센서값 범위 검증")
print("=" * 50)

sensor_ranges = {
    'avg_oven_temp':    (80, 140),
    'max_oven_temp':    (80, 150),
    'min_oven_temp':    (70, 135),
    'avg_heater_curr':  (10, 30),
    'zone1_avg_temp':   (80, 115),
    'zone2_avg_temp':   (110, 135),
    'zone3_avg_temp':   (110, 135),
    'zone4_avg_temp':   (80, 115),
}
for col, (lo, hi) in sensor_ranges.items():
    out = ((oven[col] < lo) | (oven[col] > hi)).sum()
    status = "✅" if out == 0 else "⚠️ "
    print(f"  {status} {col} ({lo}~{hi}): 범위 이탈 {out:,}건")

# =============================================
# 6. NULL 검증
# =============================================
print("\n" + "=" * 50)
print("6. NULL 값 검증")
print("=" * 50)

tables = {
    "mes_work_order": wo,
    "mes_production_result": pr,
    "mes_inventory_daily": inv,
    "mes_oven_sensor": oven,
    "mes_oven_anomaly_log": anomaly,
}
for name, df in tables.items():
    nulls = df.isnull().sum().sum()
    status = "✅" if nulls == 0 else "❌"
    print(f"  {status} {name}: NULL {nulls:,}개")