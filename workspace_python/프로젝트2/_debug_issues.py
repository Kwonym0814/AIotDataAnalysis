import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd

pr = pd.read_csv('dataset/mes_2025/mes_production_result.csv')

# C조 불량률 상세
for s in ['A','B','C']:
    d = pr[pr['shift']==s]
    fr = d['defect_qty'].sum()/d['actual_qty'].sum()*100
    print(f'{s}조: actual={d["actual_qty"].sum():,}  defect={d["defect_qty"].sum():,}  불량률={fr:.2f}%  행수={len(d):,}')

# C조 샘플
c = pr[pr['shift']=='C']
print('\nC조 샘플 (defect_qty 분포):')
print(c['defect_qty'].describe())
print(f'defect_qty==0 비율: {(c["defect_qty"]==0).mean()*100:.1f}%')
print(f'actual_qty 분포: mean={c["actual_qty"].mean():.1f}  min={c["actual_qty"].min()}  max={c["actual_qty"].max()}')

# urgent 분석
inv = pd.read_csv('dataset/mes_2025/mes_inventory_daily.csv')
print(f'\nurgent 분석:')
print(f'urgent=Y: {(inv["urgent_flag"]=="Y").sum()} / {len(inv)} = {(inv["urgent_flag"]=="Y").mean()*100:.1f}%')
print(f'closing_stock 평균: {inv["closing_stock"].mean():.0f}')
print(f'safety_stock_target 평균: {inv["safety_stock_target"].mean():.0f}')
print(f'closing_stock 0인 행: {(inv["closing_stock"]==0).sum()}')

# 모델별 urgent 비율
for m in inv['model_code'].unique():
    mi = inv[inv['model_code']==m]
    u_rate = (mi['urgent_flag']=='Y').mean()*100
    avg_close = mi['closing_stock'].mean()
    avg_safety = mi['safety_stock_target'].mean()
    print(f'  {m}: urgent={u_rate:.0f}%  avg_close={avg_close:.0f}  safety={avg_safety:.0f}  ratio={avg_close/avg_safety:.2f}')

