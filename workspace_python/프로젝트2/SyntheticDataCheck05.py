import pandas as pd
import numpy as np

mes_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\mes_2025\\'
oven = pd.read_csv(mes_path + 'mes_oven_sensor.csv')

# Zone별 실제 분포 확인
print("=== Zone별 온도 실제 분포 (정상/이상 구분) ===")
for col in ['zone1_avg_temp', 'zone2_avg_temp', 'zone3_avg_temp', 'zone4_avg_temp']:
    print(f"\n[{col}]")
    print(oven.groupby('label')[col].describe().round(2))

# Zone2, Zone3 이탈 건의 anomaly_type 분포
print("\n=== Zone2 범위(110~135) 이탈 건의 anomaly_type ===")
z2_out = oven[(oven['zone2_avg_temp'] < 110) | (oven['zone2_avg_temp'] > 135)]
print(z2_out['anomaly_type'].value_counts())
print(f"이탈 건 중 label=0(정상): {(z2_out['label']==0).sum():,}건")
print(f"이탈 건 중 label=1(이상): {(z2_out['label']==1).sum():,}건")

# Zone2 전체 실제 min/max
print("\n=== Zone 전체 실제 min/max ===")
for col in ['zone1_avg_temp', 'zone2_avg_temp', 'zone3_avg_temp', 'zone4_avg_temp']:
    print(f"{col}: min={oven[col].min():.1f}, max={oven[col].max():.1f}, mean={oven[col].mean():.1f}")