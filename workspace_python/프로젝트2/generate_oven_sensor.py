"""
============================================================
자동차 도장 건조로(Oven) 센서 데이터 생성기
============================================================
Source  : KAMP 열풍건조 센서 데이터 (dataset/data_18/5공정_180sec)
변환    : 자동차 도장 건조 조건 (90~130°C, 15~25A)
연계    : MES work_order (date × plant_code)
Output  : dataset/mes_2025/mes_oven_sensor.csv
          dataset/mes_2025/mes_oven_anomaly_log.csv

공정 설계:
  - 도장 완료 차체 → 건조로(Oven) 진입
  - 건조 구간: Zone1(예열 90~110°C) → Zone2(피크 120~130°C)
              → Zone3(유지 120~130°C) → Zone4(서냉 90~110°C)
  - 1 Process = 차체 1대 × 180초(3분) 건조

MES 연계:
  - 각 공장의 라인별 건조로 ID 할당 (총 13개 오븐)
  - mes_work_order의 date × plant_code × line_code 매핑
  - 이상 발생 시 mes_production_result의 defect_qty 상승과 상관관계

예지보전 목적:
  - 히터 열화(전류 이상), 순환팬 고장(온도 불균형) 조기 탐지
  - LSTM-AutoEncoder 기반 Reconstruction Error 이상 감지
============================================================
"""
import pandas as pd
import numpy as np
import glob, os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

np.random.seed(2025)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

KAMP_DIR = '../KAMP/dataset/data_18/5공정_180sec'
OUTPUT_DIR = 'dataset/mes_2025/'

# ─── 1) KAMP 원본 데이터 로딩 ─────────────────────────
print("=" * 60)
print("  건조로 센서 데이터 생성 (KAMP 기반)")
print("=" * 60)
print("\n[1] KAMP 원본 데이터 로딩...")

csv_files = sorted(glob.glob(os.path.join(KAMP_DIR, 'kemp-abh-sensor-*.csv')))
df_list = []
for f in csv_files:
    df_list.append(pd.read_csv(f))
df_raw = pd.concat(df_list, ignore_index=True)
print(f"  원본: {len(csv_files)}일치, {df_raw.shape[0]:,}행")
print(f"  온도 범위: {df_raw['Temp'].min():.1f}~{df_raw['Temp'].max():.1f}°C")
print(f"  전류 범위: {df_raw['Current'].min():.3f}~{df_raw['Current'].max():.3f}A")
print(f"  일 최대 Process: {df_raw['Process'].max()}")

# Error Lot 로딩
err_df = pd.read_csv(os.path.join(KAMP_DIR, 'Error Lot list.csv'), encoding='cp949', header=None)
err_df.columns = ['Date'] + [f'E{i}' for i in range(1, 12)]
error_dict = {}
for _, row in err_df.iterrows():
    lots = [int(v) for v in row[1:].dropna().values]
    if lots:
        error_dict[row['Date']] = lots

# 전체 이상 Process 번호
all_error_processes = set()
for lots in error_dict.values():
    all_error_processes.update(lots)

# ─── 2) 자동차 건조로 조건 변환 파라미터 ──────────────
# 온도 변환: 64~134°C → 90~130°C
TEMP_SRC_MIN, TEMP_SRC_MAX = df_raw['Temp'].min(), df_raw['Temp'].max()
TEMP_TGT_MIN, TEMP_TGT_MAX = 90.0, 130.0

# 전류 변환: 0.84~2.06A → 15~25A (히터 전류)
CURR_SRC_MIN, CURR_SRC_MAX = df_raw['Current'].min(), df_raw['Current'].max()
CURR_TGT_MIN, CURR_TGT_MAX = 15.0, 25.0

def transform_temp(t):
    return TEMP_TGT_MIN + (t - TEMP_SRC_MIN) / (TEMP_SRC_MAX - TEMP_SRC_MIN) * (TEMP_TGT_MAX - TEMP_TGT_MIN)

def transform_curr(c):
    return CURR_TGT_MIN + (c - CURR_SRC_MIN) / (CURR_SRC_MAX - CURR_SRC_MIN) * (CURR_TGT_MAX - CURR_TGT_MIN)

# ─── 3) Zone 할당 (Process 내 단계별 위치) ────────────
# 1 Process = 180초 = 36 steps (5초 간격)
# Zone 구분: 1~9=예열(Z1), 10~18=피크(Z2), 19~27=유지(Z3), 28~36=서냉(Z4)
def get_zone(step_in_process):  # 0-based
    if step_in_process < 9:   return 'Z1'
    elif step_in_process < 18: return 'Z2'
    elif step_in_process < 27: return 'Z3'
    else:                      return 'Z4'

# Zone별 온도 편차 (물리적 특성)
ZONE_TEMP_OFFSET = {'Z1': -8.0, 'Z2': +5.0, 'Z3': +2.0, 'Z4': -6.0}
ZONE_CURR_FACTOR = {'Z1': 1.15, 'Z2': 1.05, 'Z3': 1.00, 'Z4': 0.85}

# ─── 4) 건조로 ID 및 MES 매핑 ─────────────────────────
# 공장별 건조로: 각 라인에 1개씩 (13개 총)
OVEN_MAP = {
    'ULN': ['OV-UL1', 'OV-UL2', 'OV-UL3', 'OV-UL4', 'OV-UL5'],
    'ASN': ['OV-AS1', 'OV-AS2', 'OV-AS3'],
    'GWJ': ['OV-GW1', 'OV-GW2'],
    'HWS': ['OV-HW1', 'OV-HW2', 'OV-HW3'],
}
LINE_TO_OVEN = {
    'UL1':'OV-UL1','UL2':'OV-UL2','UL3':'OV-UL3','UL4':'OV-UL4','UL5':'OV-UL5',
    'AS1':'OV-AS1','AS2':'OV-AS2','AS3':'OV-AS3',
    'GW1':'OV-GW1','GW2':'OV-GW2',
    'HW1':'OV-HW1','HW2':'OV-HW2','HW3':'OV-HW3',
}

# ─── 5) 2025년 영업일 캘린더 ──────────────────────────
HOLIDAYS_2025 = {
    datetime(2025,3,1), datetime(2025,5,5), datetime(2025,5,6),
    datetime(2025,6,6), datetime(2025,8,15), datetime(2025,10,3),
    datetime(2025,10,5), datetime(2025,10,6), datetime(2025,10,7),
    datetime(2025,10,9), datetime(2025,12,25),
}
start, end = datetime(2025, 2, 1), datetime(2025, 12, 31)
working_days = []
d = start
while d <= end:
    if d.weekday() < 6 and d not in HOLIDAYS_2025:
        working_days.append(d)
    d += timedelta(days=1)
print(f"\n[2] 2025 영업일: {len(working_days)}일 (2/1~12/31)")

# ─── 6) 원본 데이터 날짜 → 패턴 인덱스 매핑 ──────────
# 33일치 원본 패턴을 276일에 순환 반복
kamp_dates = sorted(df_raw['Date'].unique())
n_kamp = len(kamp_dates)

def get_kamp_date_for_day(day_idx):
    """276일 순환 → 33일 원본 패턴 매핑 + 노이즈 seed 분리"""
    return kamp_dates[day_idx % n_kamp]

# ─── 7) Process 단위 집계 데이터 생성 ─────────────────
print("[3] Process 단위 집계 센서 데이터 생성 중...")
print("    (각 차체 1대 = 1 Process = 180초 통과 기록)")

# KAMP 원본에서 Process별 온도/전류 통계 미리 계산
# (날짜별, Process별)
df_raw_t = df_raw.copy()
df_raw_t['oven_temp'] = df_raw_t['Temp'].apply(transform_temp)
df_raw_t['heater_curr'] = df_raw_t['Current'].apply(transform_curr)
df_raw_t['step_in_proc'] = df_raw_t.groupby(['Date','Process']).cumcount()
df_raw_t['zone'] = df_raw_t['step_in_proc'].apply(get_zone)

# Zone 오프셋 적용
df_raw_t['oven_temp'] += df_raw_t['zone'].map(ZONE_TEMP_OFFSET)
df_raw_t['heater_curr'] *= df_raw_t['zone'].map(ZONE_CURR_FACTOR)

# Process 단위 집계 (날짜 × Process)
proc_stats = df_raw_t.groupby(['Date', 'Process']).agg(
    avg_temp=('oven_temp', 'mean'),
    max_temp=('oven_temp', 'max'),
    min_temp=('oven_temp', 'min'),
    std_temp=('oven_temp', 'std'),
    avg_curr=('heater_curr', 'mean'),
    max_curr=('heater_curr', 'max'),
    z1_temp=('oven_temp', lambda x: x.iloc[:9].mean() if len(x) >= 9 else x.mean()),
    z2_temp=('oven_temp', lambda x: x.iloc[9:18].mean() if len(x) >= 18 else x.mean()),
    z3_temp=('oven_temp', lambda x: x.iloc[18:27].mean() if len(x) >= 27 else x.mean()),
    z4_temp=('oven_temp', lambda x: x.iloc[27:36].mean() if len(x) >= 36 else x.mean()),
).reset_index()

# 이상 라벨 부여 (원본 Error Lot 기준)
proc_stats['label'] = 0
for _, row in proc_stats.iterrows():
    kdate = row['Date']
    proc = int(row['Process'])
    if kdate in error_dict and proc in error_dict[kdate]:
        proc_stats.at[_, 'label'] = 1

print(f"  원본 Process 통계 준비: {len(proc_stats)}행")

# ─── 8) 2025년 276일 × 13 오븐 데이터 생성 ───────────
sensor_rows = []
anomaly_rows = []

for day_idx, day in enumerate(working_days):
    day_str = day.strftime('%Y-%m-%d')
    kamp_date = get_kamp_date_for_day(day_idx)
    day_proc = proc_stats[proc_stats['Date'] == kamp_date].copy()

    if len(day_proc) == 0:
        continue

    # 요일별 온도 편차 (월요일 시동 직후 불안정)
    weekday_noise = 0.8 if day.weekday() == 0 else 0.3

    for plant_code, ovens in OVEN_MAP.items():
        for oven_id in ovens:
            # 오븐별 개성 (약간 다른 온도 특성)
            oven_seed = hash(oven_id) % 1000
            oven_rng = np.random.RandomState(oven_seed + day_idx)
            oven_bias = oven_rng.normal(0, 0.5)  # 고정 바이어스 (오븐 특성)

            for _, proc_row in day_proc.iterrows():
                process_no = int(proc_row['Process'])
                orig_label = int(proc_row['label'])

                # 노이즈 추가
                noise_t = np.random.normal(0, weekday_noise)
                noise_c = np.random.normal(0, 0.2)

                avg_t = proc_row['avg_temp'] + oven_bias + noise_t
                max_t = proc_row['max_temp'] + oven_bias + noise_t * 1.2
                min_t = proc_row['min_temp'] + oven_bias + noise_t * 0.8
                std_t = proc_row['std_temp'] + abs(noise_t) * 0.1
                avg_c = proc_row['avg_curr'] + noise_c
                z1_t = proc_row['z1_temp'] + oven_bias + noise_t
                z2_t = proc_row['z2_temp'] + oven_bias + noise_t
                z3_t = proc_row['z3_temp'] + oven_bias + noise_t
                z4_t = proc_row['z4_temp'] + oven_bias + noise_t

                # 이상 시나리오 (원본 이상 패턴 + 오븐별 추가 이상)
                label = orig_label
                anomaly_type = 'NORMAL'

                if orig_label == 1:
                    # 히터 열화: 전류 감소 + 온도 하강
                    avg_t -= np.random.uniform(5, 12)
                    avg_c -= np.random.uniform(2, 4)
                    anomaly_type = 'HEATER_DEGRADATION'

                # 오븐 자체 랜덤 이상 (0.5% 추가 확률)
                elif np.random.random() < 0.005:
                    anomaly_type = np.random.choice(
                        ['TEMP_SENSOR_ERR', 'CIRCULATION_FAN', 'CONVEYOR_SPEED'],
                        p=[0.5, 0.3, 0.2]
                    )
                    if anomaly_type == 'TEMP_SENSOR_ERR':
                        avg_t += np.random.uniform(8, 20)  # 온도 급상승
                    elif anomaly_type == 'CIRCULATION_FAN':
                        std_t *= 3  # 온도 불균일성 증가
                    else:  # CONVEYOR_SPEED
                        avg_t -= np.random.uniform(3, 8)  # 서냉 구간 처짐
                    label = 1

                sensor_rows.append({
                    'date': day_str,
                    'oven_id': oven_id,
                    'plant_code': plant_code,
                    'process_no': process_no,
                    'kamp_ref_date': kamp_date,
                    'avg_oven_temp': round(avg_t, 3),
                    'max_oven_temp': round(max_t, 3),
                    'min_oven_temp': round(min_t, 3),
                    'std_oven_temp': round(std_t, 3),
                    'avg_heater_curr': round(avg_c, 3),
                    'max_heater_curr': round(max_c if (max_c := proc_row['max_curr'] + noise_c) else avg_c, 3),
                    'zone1_avg_temp': round(z1_t, 3),
                    'zone2_avg_temp': round(z2_t, 3),
                    'zone3_avg_temp': round(z3_t, 3),
                    'zone4_avg_temp': round(z4_t, 3),
                    'label': label,
                    'anomaly_type': anomaly_type
                })

                # 이상 감지 로그 생성
                if label == 1:
                    anomaly_rows.append({
                        'event_id': f"AE{len(anomaly_rows)+1:07d}",
                        'date': day_str,
                        'oven_id': oven_id,
                        'plant_code': plant_code,
                        'process_no': process_no,
                        'anomaly_type': anomaly_type,
                        'avg_temp_at_event': round(avg_t, 3),
                        'avg_curr_at_event': round(avg_c, 3),
                        'severity': 'HIGH' if anomaly_type == 'TEMP_SENSOR_ERR' else 'MEDIUM',
                        'maintenance_required': 'Y' if anomaly_type != 'NORMAL' else 'N'
                    })

print(f"  생성 완료: {len(sensor_rows):,}행")

sensor_df = pd.DataFrame(sensor_rows)
anomaly_df = pd.DataFrame(anomaly_rows)

# ─── 9) 저장 ──────────────────────────────────────────
print("\n[4] 저장 중...")
sensor_df.to_csv(f'{OUTPUT_DIR}mes_oven_sensor.csv', index=False, encoding='utf-8-sig')
anomaly_df.to_csv(f'{OUTPUT_DIR}mes_oven_anomaly_log.csv', index=False, encoding='utf-8-sig')

# ─── 10) 요약 ─────────────────────────────────────────
total = len(sensor_df)
n_normal = (sensor_df['label'] == 0).sum()
n_anomaly = (sensor_df['label'] == 1).sum()

print("\n" + "=" * 60)
print("  건조로 센서 데이터 생성 완료")
print("=" * 60)
print(f"\n  기간          : 2025-02-01 ~ 2025-12-31")
print(f"  총 레코드     : {total:,}행 (1대 = 1 Process)")
print(f"  건조로 수      : 13개 (공장별 라인당 1개)")
print(f"  정상 가동     : {n_normal:,}건 ({n_normal/total*100:.2f}%)")
print(f"  이상 가동     : {n_anomaly:,}건 ({n_anomaly/total*100:.2f}%)")
print(f"  이상 이벤트   : {len(anomaly_df):,}건")

print(f"\n  [이상 유형별]")
for at, cnt in sensor_df[sensor_df['label']==1]['anomaly_type'].value_counts().items():
    print(f"    {at:25s}: {cnt:>8,}건")

print(f"\n  [오븐별 이상률]")
oven_stats = sensor_df.groupby('oven_id').agg(
    total=('label','count'), anomaly=('label','sum')
).reset_index()
oven_stats['rate'] = oven_stats['anomaly'] / oven_stats['total'] * 100
for _, r in oven_stats.iterrows():
    print(f"    {r['oven_id']:8s}: {r['anomaly']:>6,}/{r['total']:>7,} ({r['rate']:.2f}%)")

print(f"\n  파일: {os.path.abspath(OUTPUT_DIR)}mes_oven_sensor.csv")
print(f"  파일: {os.path.abspath(OUTPUT_DIR)}mes_oven_anomaly_log.csv")
print("=" * 60)

