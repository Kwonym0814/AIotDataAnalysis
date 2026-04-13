import pandas as pd

data_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\현대_오토에버\\track_a_data\\'
mes_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\mes_2025\\'

# === 1단계: 도장공정 ===
print("=== 1단계: 도장공정 검증 ===")
ins = pd.read_csv(data_path + "inspection_master.csv")
print(f"검사기간: {ins['inspection_datetime'].min()} ~ {ins['inspection_datetime'].max()}")
print(f"PASS/FAIL 비율:\n{ins['result'].value_counts(normalize=True).round(4)}")
print(f"교대조별 건수:\n{ins['shift'].value_counts()}")
print(f"공장별 건수:\n{ins['plant_code'].value_counts()}")

# === 3단계: 생산/수요/재고 ===
print("\n=== 3단계: 생산/수요/재고 검증 ===")
result = pd.read_csv(mes_path + "mes_production_result.csv")
print(f"총 생산량(actual_qty 합계): {result['actual_qty'].sum():,}대")
print(f"평균 양품률: {result['yield_rate'].mean():.2f}%")
print(f"교대조별 평균 불량률:")
result['defect_rate'] = result['defect_qty'] / result['actual_qty'] * 100
print(result.groupby('shift')['defect_rate'].mean().round(2))

inv = pd.read_csv(mes_path + "mes_inventory_daily.csv")
print(f"\n재고 urgent_flag Y 비율: {(inv['urgent_flag']=='Y').mean()*100:.1f}%")
print(f"평균 재고일수(DOS): {inv['days_of_supply'].mean():.1f}일")

# === 4단계: 건조로 예지보전 ===
print("\n=== 4단계: 건조로 검증 ===")
oven = pd.read_csv(mes_path + "mes_oven_sensor.csv")
print(f"정상/이상 비율:\n{oven['label'].value_counts()}")
print(f"이상 유형별 건수:\n{oven['anomaly_type'].value_counts()}")

anomaly = pd.read_csv(mes_path + "mes_oven_anomaly_log.csv")
print(f"\n심각도별 이상 이벤트:\n{anomaly['severity'].value_counts()}")
print(f"점검필요(maintenance_required=Y): {(anomaly['maintenance_required']=='Y').sum():,}건")