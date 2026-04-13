import pandas as pd
import numpy as np

mes_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\mes_2025\\'
data_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\현대_오토에버\\track_a_data\\'

oven = pd.read_csv(mes_path + 'mes_oven_sensor.csv')
inv = pd.read_csv(mes_path + 'mes_inventory_daily.csv')
inv['date'] = pd.to_datetime(inv['date'])
ins = pd.read_csv(data_path + 'inspection_master.csv')
ins['inspection_datetime'] = pd.to_datetime(ins['inspection_datetime'])

normal = oven[oven['label'] == 0]
normal_mean_temp = normal['avg_oven_temp'].mean()
normal_mean_curr = normal['avg_heater_curr'].mean()

# =============================================
# 문제 1: HEATER_DEGRADATION 온도 방향 모순
# =============================================
print("=" * 55)
print("문제 1: HEATER_DEGRADATION 온도/전류 상세")
print("=" * 55)
hd = oven[oven['anomaly_type'] == 'HEATER_DEGRADATION']
print(f"  대상 건수: {len(hd):,}건")
print(f"\n  정상 vs 이상 비교:")
print(f"  {'항목':<20} {'정상':>10} {'이상':>10} {'차이':>10}")
print(f"  {'-'*50}")
for col in ['avg_oven_temp', 'avg_heater_curr', 'zone1_avg_temp',
            'zone2_avg_temp', 'zone3_avg_temp', 'zone4_avg_temp']:
    n_val = normal[col].mean()
    h_val = hd[col].mean()
    diff = h_val - n_val
    print(f"  {col:<20} {n_val:>10.2f} {h_val:>10.2f} {diff:>+10.2f}")

# =============================================
# 문제 2: TEMP_SENSOR_ERR / CONVEYOR_SPEED 패턴
# =============================================
print("\n" + "=" * 55)
print("문제 2: 이상 유형별 센서 패턴 상세")
print("=" * 55)
for atype in ['TEMP_SENSOR_ERR', 'CONVEYOR_SPEED']:
    sub = oven[oven['anomaly_type'] == atype]
    print(f"\n  [{atype}] {len(sub):,}건")
    print(f"  {'항목':<20} {'정상':>10} {'이상':>10} {'차이':>10} {'기대방향':>10}")
    print(f"  {'-'*60}")
    expected = {
        'avg_oven_temp':   ('상승', 'Zone간편차'),
        'std_oven_temp':   ('급증', '급증'),
        'zone1_avg_temp':  ('상승', '변화'),
        'zone2_avg_temp':  ('상승', '변화'),
        'zone3_avg_temp':  ('상승', '변화'),
        'zone4_avg_temp':  ('상승', '변화'),
        'avg_heater_curr': ('-', '-'),
    }
    for col in ['avg_oven_temp', 'std_oven_temp', 'avg_heater_curr',
                'zone1_avg_temp', 'zone2_avg_temp', 'zone3_avg_temp', 'zone4_avg_temp']:
        n_val = normal[col].mean()
        s_val = sub[col].mean()
        diff = s_val - n_val
        exp = expected[col][0] if atype == 'TEMP_SENSOR_ERR' else expected[col][1]
        print(f"  {col:<20} {n_val:>10.2f} {s_val:>10.2f} {diff:>+10.2f} {exp:>10}")

# =============================================
# 문제 3: 주말 출하량 비율 상세
# =============================================
print("\n" + "=" * 55)
print("문제 3: 요일별 출하량 분포 상세")
print("=" * 55)
inv['weekday'] = inv['date'].dt.day_name()
inv['is_weekend'] = inv['date'].dt.weekday >= 5
day_ship = inv.groupby('weekday')['shipped_qty'].mean().round(1)
weekday_avg = inv[~inv['is_weekend']]['shipped_qty'].mean()
print(f"  요일별 평균 출하량:")
day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
for d in day_order:
    if d in day_ship.index:
        ratio = day_ship[d] / weekday_avg * 100
        flag = " ⚠️" if d in ['Saturday','Sunday'] else ""
        print(f"  {d:<12}: {day_ship[d]:>6.1f}대  (영업일 대비 {ratio:.1f}%){flag}")
print(f"\n  브리핑 설계 기준: 휴일 = 영업일 × 0.4 (40%)")
print(f"  현재 실제 비율:   휴일 = 영업일 × {inv[inv['is_weekend']]['shipped_qty'].mean()/weekday_avg:.2f} ({inv[inv['is_weekend']]['shipped_qty'].mean()/weekday_avg*100:.1f}%)")

# =============================================
# 문제 4: 동일 라인 동시 검사 (전체)
# =============================================
print("\n" + "=" * 55)
print("문제 4: 동일 라인 동시 검사 전체 규모")
print("=" * 55)
ins_sorted = ins.sort_values(['line_code', 'inspection_datetime'])
ins_sorted['time_diff'] = ins_sorted.groupby('line_code')['inspection_datetime'].diff().dt.total_seconds()
zero_gap = ins_sorted[ins_sorted['time_diff'] == 0]
print(f"  전체 300만건 기준 0초 간격: {len(zero_gap):,}건")
print(f"  2초 미만 간격: {(ins_sorted['time_diff'] < 2).sum():,}건")
if len(zero_gap) > 0:
    print(f"  라인별 분포:\n{zero_gap['line_code'].value_counts().head(10)}")