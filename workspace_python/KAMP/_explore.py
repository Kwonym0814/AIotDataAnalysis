import pandas as pd, glob, os

p = r'C:\IT\workspace_python\KAMP\dataset\data_18\5공정_180sec'

# 샘플 CSV 구조 파악
f = os.path.join(p, 'kemp-abh-sensor-2021.09.06.csv')
df = pd.read_csv(f)
print('=== CSV 컬럼 및 샘플 ===')
print(df.dtypes)
print()
print(df.head(10).to_string())
print(f'\n크기: {df.shape}')

# Error Lot 확인
err = pd.read_csv(os.path.join(p, 'Error Lot list.csv'), encoding='cp949')
print('\n=== Error Lot list ===')
print(err.to_string())

# 전체 파일 통계
files = sorted(glob.glob(os.path.join(p, 'kemp-abh-sensor-*.csv')))
dfall = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
print(f'\n=== 전체 데이터 ({dfall.shape}) ===')
print(dfall.describe().to_string())
print(f'\n고유 Process 수: {dfall["Process"].nunique()}')
print(f'고유 Zone 수: {dfall["Zone"].nunique()}')
col_int = [c for c in dfall.columns if 'nterval' in c or 'ec' in c.lower()]
print(f'Interval 관련 컬럼: {col_int}')
print(f'전체 컬럼: {list(dfall.columns)}')

