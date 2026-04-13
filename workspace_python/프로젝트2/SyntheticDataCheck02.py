import pandas as pd

data_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\현대_오토에버\\track_a_data\\'
mes_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\mes_2025\\'

# Track A 행 수
print("=== Track A 행 수 ===")
track_a_files = ["inspection_master.csv", "daily_summary.csv", "defect_detail.csv", "defect_summary.csv"]
for f in track_a_files:
    df = pd.read_csv(data_path + f)
    print(f"{f}: {len(df):,}행")

# MES 행 수 + 날짜 범위
print("\n=== MES 데이터 행 수 & 날짜 범위 ===")
date_cols = {
    "mes_demand_forecast.csv": ["year", "month"],
    "mes_production_plan.csv": ["year", "month"],
    "mes_work_order.csv": ["order_date"],
    "mes_production_result.csv": ["date"],
    "mes_inventory_daily.csv": ["date"],
    "mes_color_production.csv": ["year", "month"],
    "mes_oven_sensor.csv": ["date"],
    "mes_oven_anomaly_log.csv": ["date"],
}
for f, cols in date_cols.items():
    df = pd.read_csv(mes_path + f)
    print(f"\n{f}: {len(df):,}행")
    if len(cols) == 1:
        df[cols[0]] = pd.to_datetime(df[cols[0]])
        print(f"  날짜범위: {df[cols[0]].min()} ~ {df[cols[0]].max()}")
    else:
        print(f"  기간: {df[cols[0]].min()}년 {df[cols[1]].min()}월 ~ {df[cols[0]].max()}년 {df[cols[1]].max()}월")