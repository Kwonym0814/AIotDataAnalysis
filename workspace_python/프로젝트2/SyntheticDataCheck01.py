import os
import pandas as pd

# 데이터 경로 (환경에 맞게 수정)
data_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\현대_오토에버\\track_a_data\\'
mes_path = 'C:\\IT\\workspace_python\\프로젝트2\\dataset\\mes_2025\\'

print("===Track A (도장 공정) ===")
for f in os.listdir(data_path):
    if f.endswith(".csv"):
        size = os.path.getsize(data_path + f) / (1024*1024)
        df = pd.read_csv(data_path + f, nrows=1)
        print(f"{f}: {size:.1f}MB | {list(df.columns)}")


print("\n=== MES 합성 데이터 ===")
for f in os.listdir(mes_path):
    if f.endswith(".csv"):
        size = os.path.getsize(mes_path + f) / (1024*1024)
        df = pd.read_csv(mes_path + f, nrows=1)
        print(f"{f}: {size:.1f}MB | 컬럼: {list(df.columns)}")
