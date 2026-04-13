import pandas as pd
import numpy as np

mes_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\mes_2025\\'
rng = np.random.default_rng(42)

print("mes_oven_sensor.csv 로드 중...")
oven = pd.read_csv(mes_path + 'mes_oven_sensor.csv')

normal = oven[oven['label'] == 0]
normal_means = {
    'avg_oven_temp':  normal['avg_oven_temp'].mean(),
    'zone1_avg_temp': normal['zone1_avg_temp'].mean(),
    'zone2_avg_temp': normal['zone2_avg_temp'].mean(),
    'zone3_avg_temp': normal['zone3_avg_temp'].mean(),
    'zone4_avg_temp': normal['zone4_avg_temp'].mean(),
    'std_oven_temp':  normal['std_oven_temp'].mean(),
}
print(f"  정상 기준값 확인: avg_temp={normal_means['avg_oven_temp']:.2f}, std={normal_means['std_oven_temp']:.2f}")

zone_cols = ['zone1_avg_temp', 'zone2_avg_temp', 'zone3_avg_temp', 'zone4_avg_temp']

# =============================================
# 문제 1: HEATER_DEGRADATION 온도 방향 수정
# 전류 감소(-7.17A)에 맞게 온도도 정상 대비 하락
# =============================================
print("\n[문제 1] HEATER_DEGRADATION 온도 수정 중...")
hd_mask = oven['anomaly_type'] == 'HEATER_DEGRADATION'
hd_count = hd_mask.sum()
hd_idx = oven[hd_mask].index

# 정상 대비 -8 ~ -15°C 하락 (전류 감소폭에 비례)
temp_drop = rng.uniform(8, 15, size=hd_count)
noise = rng.normal(0, 0.5, size=hd_count)

# Zone별 온도 하락 (Zone마다 약간 다른 편차)
for i, col in enumerate(zone_cols):
    zone_noise = rng.normal(0, 0.3, size=hd_count)
    oven.loc[hd_idx, col] = (normal_means[col] - temp_drop + zone_noise).round(2)

# avg/max/min 재계산
oven.loc[hd_idx, 'avg_oven_temp'] = oven.loc[hd_idx, zone_cols].mean(axis=1).round(2)
oven.loc[hd_idx, 'max_oven_temp'] = (oven.loc[hd_idx, 'avg_oven_temp'] + rng.uniform(2, 5, size=hd_count)).round(2)
oven.loc[hd_idx, 'min_oven_temp'] = (oven.loc[hd_idx, 'avg_oven_temp'] - rng.uniform(2, 5, size=hd_count)).round(2)
# std는 약간 증가 (온도 불안정 반영)
oven.loc[hd_idx, 'std_oven_temp'] = (normal_means['std_oven_temp'] + rng.uniform(0.5, 1.5, size=hd_count)).round(2)

print(f"  수정 전 avg_oven_temp: 이상={oven.loc[hd_idx, 'avg_oven_temp'].mean():.2f}")
print(f"  기대값: 정상({normal_means['avg_oven_temp']:.2f}) 대비 -8~15°C 하락")

# =============================================
# 문제 2-A: TEMP_SENSOR_ERR 스파이크 패턴 반영
# 특정 Zone 급등 + std 급증
# =============================================
print("\n[문제 2-A] TEMP_SENSOR_ERR 스파이크 패턴 수정 중...")
te_mask = oven['anomaly_type'] == 'TEMP_SENSOR_ERR'
te_count = te_mask.sum()
te_idx = oven[te_mask].index

# 먼저 정상값으로 초기화
for col in zone_cols:
    noise = rng.normal(0, 0.3, size=te_count)
    oven.loc[te_idx, col] = (normal_means[col] + noise).round(2)

# 각 행마다 1~2개 Zone에 스파이크 삽입
for idx in te_idx:
    n_spike = rng.integers(1, 3)
    spike_zones = rng.choice(zone_cols, size=n_spike, replace=False)
    for z in spike_zones:
        spike = rng.uniform(20, 40)
        oven.loc[idx, z] = round(oven.loc[idx, z] + spike, 2)

# std 급증 (스파이크 반영)
oven.loc[te_idx, 'std_oven_temp'] = rng.uniform(15, 25, size=te_count).round(2)

# avg/max 재계산
oven.loc[te_idx, 'avg_oven_temp'] = oven.loc[te_idx, zone_cols].mean(axis=1).round(2)
oven.loc[te_idx, 'max_oven_temp'] = oven.loc[te_idx, zone_cols].max(axis=1).round(2)
oven.loc[te_idx, 'min_oven_temp'] = oven.loc[te_idx, zone_cols].min(axis=1).round(2)

print(f"  수정 후 std_oven_temp 평균: {oven.loc[te_idx,'std_oven_temp'].mean():.2f} (정상: {normal_means['std_oven_temp']:.2f})")
print(f"  수정 후 avg_oven_temp 평균: {oven.loc[te_idx,'avg_oven_temp'].mean():.2f}")

# =============================================
# 문제 2-B: CONVEYOR_SPEED Zone간 편차 패턴 반영
# Z1/Z2 정상, Z3/Z4 온도 부족 + std 증가
# =============================================
print("\n[문제 2-B] CONVEYOR_SPEED Zone 편차 패턴 수정 중...")
cs_mask = oven['anomaly_type'] == 'CONVEYOR_SPEED'
cs_count = cs_mask.sum()
cs_idx = oven[cs_mask].index

# Z1/Z2는 정상 유지
for col in ['zone1_avg_temp', 'zone2_avg_temp']:
    noise = rng.normal(0, 0.3, size=cs_count)
    oven.loc[cs_idx, col] = (normal_means[col] + noise).round(2)

# Z3/Z4는 온도 부족 (컨베이어 빠름 → 체류시간 부족)
z3_drop = rng.uniform(5, 10, size=cs_count)
z4_drop = rng.uniform(8, 15, size=cs_count)
noise3 = rng.normal(0, 0.3, size=cs_count)
noise4 = rng.normal(0, 0.3, size=cs_count)

oven.loc[cs_idx, 'zone3_avg_temp'] = (normal_means['zone3_avg_temp'] - z3_drop + noise3).round(2)
oven.loc[cs_idx, 'zone4_avg_temp'] = (normal_means['zone4_avg_temp'] - z4_drop + noise4).round(2)

# Zone간 편차 증가 → std 증가
oven.loc[cs_idx, 'std_oven_temp'] = rng.uniform(10, 20, size=cs_count).round(2)

# avg/max/min 재계산
oven.loc[cs_idx, 'avg_oven_temp'] = oven.loc[cs_idx, zone_cols].mean(axis=1).round(2)
oven.loc[cs_idx, 'max_oven_temp'] = oven.loc[cs_idx, zone_cols].max(axis=1).round(2)
oven.loc[cs_idx, 'min_oven_temp'] = oven.loc[cs_idx, zone_cols].min(axis=1).round(2)

print(f"  수정 후 std_oven_temp 평균: {oven.loc[cs_idx,'std_oven_temp'].mean():.2f} (정상: {normal_means['std_oven_temp']:.2f})")
print(f"  수정 후 zone3_avg_temp 평균: {oven.loc[cs_idx,'zone3_avg_temp'].mean():.2f} (정상: {normal_means['zone3_avg_temp']:.2f})")
print(f"  수정 후 zone4_avg_temp 평균: {oven.loc[cs_idx,'zone4_avg_temp'].mean():.2f} (정상: {normal_means['zone4_avg_temp']:.2f})")

# =============================================
# 저장 및 최종 검증
# =============================================
print("\n저장 중...")
oven.to_csv(mes_path + 'mes_oven_sensor.csv', index=False)
print("  ✅ mes_oven_sensor.csv 저장 완료")

print("\n=== 최종 검증 ===")
oven_v = pd.read_csv(mes_path + 'mes_oven_sensor.csv')
normal_v = oven_v[oven_v['label'] == 0]

print(f"\n{'이상유형':<25} {'avg_temp':>10} {'std':>8} {'z3_temp':>10} {'z4_temp':>10}")
print("-" * 65)
for atype in ['NORMAL', 'HEATER_DEGRADATION', 'TEMP_SENSOR_ERR', 'CIRCULATION_FAN', 'CONVEYOR_SPEED']:
    sub = oven_v[oven_v['anomaly_type'] == atype]
    print(f"{atype:<25} {sub['avg_oven_temp'].mean():>10.2f} "
          f"{sub['std_oven_temp'].mean():>8.2f} "
          f"{sub['zone3_avg_temp'].mean():>10.2f} "
          f"{sub['zone4_avg_temp'].mean():>10.2f}")