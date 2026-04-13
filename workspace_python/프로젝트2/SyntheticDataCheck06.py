import pandas as pd
import numpy as np

data_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\현대_오토에버\\track_a_data\\'
mes_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\mes_2025\\'

wo = pd.read_csv(mes_path + 'mes_work_order.csv')
pr = pd.read_csv(mes_path + 'mes_production_result.csv')
pr['date'] = pd.to_datetime(pr['date'])
inv = pd.read_csv(mes_path + 'mes_inventory_daily.csv')
inv['date'] = pd.to_datetime(inv['date'])
oven = pd.read_csv(mes_path + 'mes_oven_sensor.csv')
ins = pd.read_csv(data_path + 'inspection_master.csv')
ins['inspection_datetime'] = pd.to_datetime(ins['inspection_datetime'])

# =============================================
# 1. 교대조 생산 가능량 물리적 검증
# 교대조 = 8시간(28,800초), 택트타임으로 나누면 최대 생산 가능 대수
# =============================================
print("=" * 55)
print("1. 교대조별 물리적 생산 가능량 초과 여부")
print("   [기준] 8시간(28,800초) / 택트타임 = 최대 생산 가능 대수")
print("=" * 55)

pr['max_possible'] = (28800 / pr['takt_time_sec']).astype(int)
pr['over_capacity'] = pr['actual_qty'] > pr['max_possible']
over = pr[pr['over_capacity']]
print(f"  초과 건수: {len(over):,}건 / 전체 {len(pr):,}건")
if len(over) > 0:
    print(f"  초과 샘플:")
    print(over[['date','plant_code','line_code','shift','actual_qty','max_possible','takt_time_sec']].head())

# =============================================
# 2. 다운타임 반영 시 생산량 타당성
# 실제 가동시간 = 8시간 - 다운타임
# =============================================
print("\n" + "=" * 55)
print("2. 다운타임 반영 후 생산 가능량 초과 여부")
print("   [기준] (28,800 - downtime_sec) / takt_time = 최대 생산량")
print("=" * 55)

pr['downtime_sec'] = pr['downtime_min'] * 60
pr['effective_time'] = 28800 - pr['downtime_sec']
pr['max_with_downtime'] = (pr['effective_time'] / pr['takt_time_sec']).astype(int)
pr['over_with_downtime'] = pr['actual_qty'] > pr['max_with_downtime']
over2 = pr[pr['over_with_downtime']]
print(f"  초과 건수: {len(over2):,}건")
if len(over2) > 0:
    print(over2[['date','shift','actual_qty','max_with_downtime','downtime_min','takt_time_sec']].head())

# =============================================
# 3. 불량률 논리적 패턴 검증
# C조 불량률이 항상 A/B조보다 높아야 하는가 (일별)
# 월요일 불량률이 다른 요일보다 높아야 하는가
# =============================================
print("\n" + "=" * 55)
print("3. 불량률 패턴 논리 검증")
print("=" * 55)

pr['defect_rate'] = pr['defect_qty'] / pr['actual_qty'] * 100

# 교대조별
shift_defect = pr.groupby('shift')['defect_rate'].mean().round(2)
print(f"  교대조별 평균 불량률: {shift_defect.to_dict()}")
c_highest = shift_defect['C'] > shift_defect['A'] and shift_defect['C'] > shift_defect['B']
print(f"  {'✅' if c_highest else '❌'} C조 불량률이 A/B조보다 높음")

# 요일별
pr['weekday'] = pr['date'].dt.day_name()
weekday_defect = pr.groupby('weekday')['defect_rate'].mean().round(2)
mon = weekday_defect.get('Monday', 0)
others = weekday_defect.drop('Monday', errors='ignore').mean()
print(f"\n  요일별 평균 불량률:")
print(f"  {weekday_defect.to_dict()}")
print(f"  {'✅' if mon > others else '❌'} 월요일({mon:.2f}%) 불량률이 다른 요일 평균({others:.2f}%)보다 높음")

# =============================================
# 4. 건조로 Zone 온도 순서 물리적 검증
# 정상 상태: Z1(예열) < Z2(피크), Z2 ≈ Z3(유지), Z3 > Z4(서냉)
# =============================================
print("\n" + "=" * 55)
print("4. 건조로 Zone 온도 순서 물리적 검증")
print("   [기준] 정상: Z1<Z2, Z2≈Z3(Z2>=Z3), Z3>Z4")
print("=" * 55)

normal = oven[oven['label'] == 0]

z1_lt_z2 = (normal['zone1_avg_temp'] < normal['zone2_avg_temp']).mean() * 100
z2_ge_z3 = (normal['zone2_avg_temp'] >= normal['zone3_avg_temp']).mean() * 100
z3_gt_z4 = (normal['zone3_avg_temp'] > normal['zone4_avg_temp']).mean() * 100

print(f"  {'✅' if z1_lt_z2 > 99 else '❌'} Z1 < Z2 (예열<피크): {z1_lt_z2:.1f}%")
print(f"  {'✅' if z2_ge_z3 > 99 else '❌'} Z2 >= Z3 (피크>=유지): {z2_ge_z3:.1f}%")
print(f"  {'✅' if z3_gt_z4 > 99 else '❌'} Z3 > Z4 (유지>서냉): {z3_gt_z4:.1f}%")

# =============================================
# 5. 건조로 이상 유형별 센서 패턴 물리적 검증
# HEATER_DEGRADATION: 전류 감소 + 온도 하강이어야 함
# TEMP_SENSOR_ERR: 온도 급등(스파이크)이어야 함
# CIRCULATION_FAN: 온도 편차(std) 급증이어야 함
# =============================================
print("\n" + "=" * 55)
print("5. 이상 유형별 센서 패턴 물리적 검증")
print("=" * 55)

normal_mean_temp = normal['avg_oven_temp'].mean()
normal_mean_curr = normal['avg_heater_curr'].mean()
normal_mean_std  = normal['std_oven_temp'].mean()

for atype in ['HEATER_DEGRADATION', 'TEMP_SENSOR_ERR', 'CIRCULATION_FAN', 'CONVEYOR_SPEED']:
    sub = oven[oven['anomaly_type'] == atype]
    if len(sub) == 0:
        continue
    print(f"\n  [{atype}] ({len(sub):,}건)")
    print(f"    avg_oven_temp: 정상={normal_mean_temp:.2f} → 이상={sub['avg_oven_temp'].mean():.2f}  "
          f"({'하강✅' if sub['avg_oven_temp'].mean() < normal_mean_temp else '상승⚠️ '})")
    print(f"    avg_heater_curr: 정상={normal_mean_curr:.2f} → 이상={sub['avg_heater_curr'].mean():.2f}  "
          f"({'감소✅' if atype=='HEATER_DEGRADATION' and sub['avg_heater_curr'].mean() < normal_mean_curr else '증가⚠️ ' if atype=='HEATER_DEGRADATION' else '참고'})")
    print(f"    std_oven_temp: 정상={normal_mean_std:.2f} → 이상={sub['std_oven_temp'].mean():.2f}  "
          f"({'증가✅' if sub['std_oven_temp'].mean() > normal_mean_std else '감소⚠️ '})")

# =============================================
# 6. 재고 출하 패턴 검증
# 영업일 출하 > 휴일 출하여야 함
# =============================================
print("\n" + "=" * 55)
print("6. 재고 출하 패턴 검증 (영업일 vs 휴일)")
print("   [기준] 영업일 출하량 > 휴일 출하량")
print("=" * 55)

inv['weekday'] = inv['date'].dt.weekday  # 0=월 ~ 6=일
inv['is_weekend'] = inv['weekday'] >= 5
weekday_ship = inv[~inv['is_weekend']]['shipped_qty'].mean()
weekend_ship = inv[inv['is_weekend']]['shipped_qty'].mean()
print(f"  영업일 평균 출하량: {weekday_ship:.1f}대")
print(f"  주말 평균 출하량: {weekend_ship:.1f}대")
print(f"  {'✅' if weekday_ship > weekend_ship else '❌'} 영업일 출하량이 주말보다 많음")
print(f"  주말/영업일 비율: {weekend_ship/weekday_ship*100:.1f}% (브리핑 기준 약 36%)")

# =============================================
# 7. 도장 검사 - 동일 라인 검사 간격 검증
# 같은 라인에서 택트타임보다 짧은 간격으로 연속 검사가 발생하면 비정상
# =============================================
print("\n" + "=" * 55)
print("7. 도장검사 - 동일 라인 검사 간격 검증")
print("   [기준] 같은 라인 연속 검사 간격 >= 택트타임(약 2.5~3초)")
print("=" * 55)

sample = ins.sample(n=100000, random_state=42).copy()
sample = sample.sort_values(['line_code', 'inspection_datetime'])
sample['time_diff'] = sample.groupby('line_code')['inspection_datetime'].diff().dt.total_seconds()
too_fast = sample[(sample['time_diff'] > 0) & (sample['time_diff'] < 2.0)]
print(f"  동일 라인 내 2초 미만 간격 검사: {len(too_fast):,}건 (샘플 100,000건 기준)")
print(f"  최소 검사 간격: {sample['time_diff'].dropna().min():.2f}초")
print(f"  평균 검사 간격: {sample['time_diff'].dropna().mean():.2f}초")