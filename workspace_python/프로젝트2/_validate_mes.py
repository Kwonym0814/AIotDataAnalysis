"""MES 데이터셋 품질 검증"""
import pandas as pd
import numpy as np

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
DIR = 'dataset/mes_2025/'
OLD = 'dataset/현대_오토에버/track_a_data/'

# 데이터 로딩
demand = pd.read_csv(f'{DIR}mes_demand_forecast.csv')
plan = pd.read_csv(f'{DIR}mes_production_plan.csv')
wo = pd.read_csv(f'{DIR}mes_work_order.csv')
pr = pd.read_csv(f'{DIR}mes_production_result.csv', parse_dates=['date'])
inv = pd.read_csv(f'{DIR}mes_inventory_daily.csv', parse_dates=['date'])
color_prod = pd.read_csv(f'{DIR}mes_color_production.csv')

m_model = pd.read_csv(f'{OLD}master_model.csv')
m_color = pd.read_csv(f'{OLD}master_color.csv')
m_plant = pd.read_csv(f'{OLD}master_plant_line.csv')
old_daily = pd.read_csv(f'{OLD}daily_summary.csv', parse_dates=['date'])

print('=' * 70)
print('  MES 데이터셋 품질 검증 리포트')
print('=' * 70)

# ═══════════════════════════════════════════════
# 1. FK 정합성
# ═══════════════════════════════════════════════
print('\n[1] FK 정합성 검증 (기존 마스터 테이블과의 호환성)')
checks = {
    'work_order.model_code → master_model':
        wo['model_code'].isin(m_model['model_code']).all(),
    'work_order.color_code → master_color':
        wo['color_code'].isin(m_color['color_code']).all(),
    'work_order.plant+line → master_plant_line':
        wo.merge(m_plant, on=['plant_code','line_code'], how='left')['plant_name'].notna().all(),
    'production_result.work_order_id → work_order':
        pr['work_order_id'].isin(wo['work_order_id']).all(),
    'demand_forecast.model_code → master_model':
        demand['model_code'].isin(m_model['model_code']).all(),
    'production_plan.model_code → master_model':
        plan['model_code'].isin(m_model['model_code']).all(),
    'inventory.model_code → master_model':
        inv['model_code'].isin(m_model['model_code']).all(),
}
for name, ok in checks.items():
    status = 'OK' if ok else '** FAIL **'
    print(f'  {status:10s} {name}')

# ═══════════════════════════════════════════════
# 2. 차종 비율 비교
# ═══════════════════════════════════════════════
print('\n[2] 차종 비율: 기존 도장검사 vs MES 생산실적')
old_mp = old_daily.groupby('model_code')['total_inspections'].sum()
old_mp = (old_mp / old_mp.sum() * 100).round(2)
new_mp = pr.groupby('model_code')['actual_qty'].sum()
new_mp = (new_mp / new_mp.sum() * 100).round(2)
print(f'  {"모델":6s} {"기존(%)":>8s} {"MES(%)":>8s} {"차이(pp)":>8s}  판정')
for m in old_mp.sort_values(ascending=False).index:
    ov = old_mp.get(m, 0)
    nv = new_mp.get(m, 0)
    d = nv - ov
    flag = '⚠️ 편차' if abs(d) > 0.5 else 'OK'
    print(f'  {m:6s} {ov:>8.2f} {nv:>8.2f} {d:>+8.2f}  {flag}')

# ═══════════════════════════════════════════════
# 3. 색상 비율 비교
# ═══════════════════════════════════════════════
print('\n[3] 색상 비율: 기존 도장검사 vs MES 생산실적')
old_cp = {
    'B3L':20.02,'P2W':18.00,'SWP':11.99,'ABP':9.98,'N5M':8.01,'YW6':8.01,
    'R4M':5.00,'SSS':5.00,'TW3':4.01,'W8Y':3.00,'C5G':2.00,'WC9':1.99,
    'V5P':1.00,'K3B':1.00,'U3G':0.99
}
nc = pr.groupby('color_code')['actual_qty'].sum()
nc_pct = (nc / nc.sum() * 100).round(2)
print(f'  {"색상":6s} {"기존(%)":>8s} {"MES(%)":>8s} {"차이(pp)":>8s}  판정')
for c in sorted(old_cp.keys(), key=lambda x: -old_cp[x]):
    ov = old_cp[c]
    nv = nc_pct.get(c, 0)
    d = nv - ov
    flag = '⚠️ 편차' if abs(d) > 1.0 else 'OK'
    print(f'  {c:6s} {ov:>8.2f} {nv:>8.2f} {d:>+8.2f}  {flag}')

# ═══════════════════════════════════════════════
# 4. 공장/라인 비율 비교
# ═══════════════════════════════════════════════
print('\n[4] 공장 비율: 기존 vs MES')
old_pl = old_daily.groupby('plant_code')['total_inspections'].sum()
old_pl_pct = (old_pl / old_pl.sum() * 100).round(2)
new_pl = pr.groupby('plant_code')['actual_qty'].sum()
new_pl_pct = (new_pl / new_pl.sum() * 100).round(2)
for p in old_pl_pct.sort_values(ascending=False).index:
    ov = old_pl_pct.get(p, 0)
    nv = new_pl_pct.get(p, 0)
    d = nv - ov
    print(f'  {p:6s} {ov:>8.2f} {nv:>8.2f} {d:>+8.2f}')

# ═══════════════════════════════════════════════
# 5. 교대조 비율 & 불량률
# ═══════════════════════════════════════════════
print('\n[5] 교대조 비율 & 불량률: 기존 vs MES')
old_s = old_daily.groupby('shift').agg(tot=('total_inspections','sum'), fail=('fail_count','sum'))
old_s['pct'] = (old_s['tot'] / old_s['tot'].sum() * 100).round(2)
old_s['fr'] = (old_s['fail'] / old_s['tot'] * 100).round(2)
new_s = pr.groupby('shift').agg(tot=('actual_qty','sum'), dft=('defect_qty','sum'))
new_s['pct'] = (new_s['tot'] / new_s['tot'].sum() * 100).round(2)
new_s['fr'] = (new_s['dft'] / new_s['tot'] * 100).round(2)
print(f'  조  기존점유  MES점유   기존불량  MES불량')
for s in ['A','B','C']:
    print(f'  {s}   {old_s.loc[s,"pct"]:>6.2f}%  {new_s.loc[s,"pct"]:>6.2f}%   {old_s.loc[s,"fr"]:>6.2f}%  {new_s.loc[s,"fr"]:>6.2f}%')

# ═══════════════════════════════════════════════
# 6. 내부 정합성: plan vs actual 크로스체크
# ═══════════════════════════════════════════════
print('\n[6] 내부 정합성: 생산계획 vs 실제 생산')
plan_total = plan.groupby('model_code')['planned_production'].sum()
actual_total = pr.groupby('model_code')['actual_qty'].sum()
merged = pd.DataFrame({'계획': plan_total, '실적': actual_total}).fillna(0)
merged['달성률'] = (merged['실적'] / merged['계획'] * 100).round(1)
merged['차이'] = merged['실적'] - merged['계획']
print(f'  {"모델":6s} {"계획":>10s} {"실적":>10s} {"달성률":>8s} {"차이":>10s}')
for m, r in merged.iterrows():
    print(f'  {m:6s} {r["계획"]:>10,.0f} {r["실적"]:>10,.0f} {r["달성률"]:>7.1f}% {r["차이"]:>+10,.0f}')
print(f'  {"합계":6s} {merged["계획"].sum():>10,.0f} {merged["실적"].sum():>10,.0f} '
      f'{merged["실적"].sum()/merged["계획"].sum()*100:>7.1f}% {merged["실적"].sum()-merged["계획"].sum():>+10,.0f}')

# ═══════════════════════════════════════════════
# 7. 재고 연속성 검증
# ═══════════════════════════════════════════════
print('\n[7] 재고 연속성 검증')
issues = 0
for model in inv['model_code'].unique():
    m_inv = inv[inv['model_code'] == model].sort_values('date').reset_index(drop=True)
    for i in range(1, len(m_inv)):
        prev_close = m_inv.loc[i-1, 'closing_stock']
        curr_open = m_inv.loc[i, 'opening_stock']
        if prev_close != curr_open:
            issues += 1
    # 재고 마이너스 체크
    neg = (m_inv['closing_stock'] < 0).sum()
    if neg > 0:
        issues += neg
        print(f'  ⚠️ {model}: 마이너스 재고 {neg}건')

neg_total = (inv['closing_stock'] < 0).sum()
continuity_breaks = 0
for model in inv['model_code'].unique():
    m_inv = inv[inv['model_code'] == model].sort_values('date').reset_index(drop=True)
    for i in range(1, len(m_inv)):
        if m_inv.loc[i-1, 'closing_stock'] != m_inv.loc[i, 'opening_stock']:
            continuity_breaks += 1

print(f'  마이너스 재고: {neg_total}건')
print(f'  연속성 불일치(전일종료!=당일시작): {continuity_breaks}건')
urgent_cnt = (inv['urgent_flag'] == 'Y').sum()
print(f'  긴급(urgent) 발생 일수: {urgent_cnt}건 ({urgent_cnt/len(inv)*100:.1f}%)')

# ═══════════════════════════════════════════════
# 8. 날짜 범위 & grain 일관성
# ═══════════════════════════════════════════════
print('\n[8] 날짜 범위 & 데이터 grain 검증')
print(f'  기존 데이터 범위: {old_daily["date"].min().date()} ~ {old_daily["date"].max().date()}')
print(f'  MES 생산실적 범위: {pr["date"].min().date()} ~ {pr["date"].max().date()}')
print(f'  MES 재고 범위: {inv["date"].min().date()} ~ {inv["date"].max().date()}')

# 기존 데이터와 겹치는 기간
overlap = old_daily[old_daily['date'] >= '2025-01-01']
if len(overlap) > 0:
    print(f'  ⚠️ 기존 데이터와 겹치는 기간: 2025-01-01 ~ {overlap["date"].max().date()} ({overlap["date"].nunique()}일)')
else:
    print(f'  기존 데이터와 겹침 없음')

# grain 중복 체크
wo_dup = wo.duplicated(subset=['order_date','plant_code','line_code','model_code','shift','color_code']).sum()
print(f'  작업지시 grain 중복: {wo_dup}건')

# ═══════════════════════════════════════════════
# 9. 일별 생산량 분포 비교
# ═══════════════════════════════════════════════
print('\n[9] 일별 생산량 분포: 기존 vs MES')
old_daily_tot = old_daily.groupby('date')['total_inspections'].sum()
new_daily_tot = pr.groupby('date')['actual_qty'].sum()
for label, series in [('기존', old_daily_tot), ('MES', new_daily_tot)]:
    print(f'  {label}: 평균={series.mean():,.0f}  std={series.std():,.0f}  '
          f'min={series.min():,}  max={series.max():,}  CV={series.std()/series.mean()*100:.1f}%')

# ═══════════════════════════════════════════════
# 10. work_order vs production_result 1:1 확인
# ═══════════════════════════════════════════════
print('\n[10] work_order ↔ production_result 관계 검증')
wo_only = set(wo['work_order_id']) - set(pr['work_order_id'])
pr_only = set(pr['work_order_id']) - set(wo['work_order_id'])
print(f'  작업지시만 있고 실적 없는 건: {len(wo_only)}건')
print(f'  실적만 있고 작업지시 없는 건: {len(pr_only)}건')
# 1:1 여부
pr_dup_wo = pr['work_order_id'].duplicated().sum()
print(f'  실적 기준 work_order_id 중복: {pr_dup_wo}건')

# ═══════════════════════════════════════════════
# 11. NULL 체크
# ═══════════════════════════════════════════════
print('\n[11] NULL 값 검사')
for name, df in [('demand_forecast', demand), ('production_plan', plan),
                  ('work_order', wo), ('production_result', pr),
                  ('inventory_daily', inv)]:
    null_cnt = df.isnull().sum().sum()
    print(f'  {name:25s}: {null_cnt}건 {"OK" if null_cnt == 0 else "⚠️ NULL 존재"}')

# ═══════════════════════════════════════════════
# 12. 종합 이슈 리스트
# ═══════════════════════════════════════════════
print('\n' + '=' * 70)
print('  종합 이슈 리스트')
print('=' * 70)

issues_found = []

# 날짜 겹침
if len(overlap) > 0:
    issues_found.append(
        f'[날짜겹침] 기존 도장검사 데이터(~2025-01-24)와 MES(2025-01-01~) 겹침 24일 '
        f'→ MES 시작을 2025-01-25로 바꾸거나, 기존 데이터 1월분과 merge 시 주의 필요'
    )

# grain 중복
if wo_dup > 0:
    issues_found.append(
        f'[작업지시 중복] 동일 date+plant+line+model+shift+color 조합 {wo_dup}건 중복 '
        f'→ 같은 라인-교대조에서 동일 모델·동일색상이 별도 WO로 분리됨. '
        f'MES 화면에서 1개 WO로 합치는 것이 자연스러움'
    )

# 생산량 스케일
plan_annual = plan['planned_production'].sum()
actual_annual = pr['actual_qty'].sum()
old_annual_rate = old_daily['total_inspections'].sum() / old_daily['date'].nunique() * 365
if abs(actual_annual - old_annual_rate) / old_annual_rate > 0.15:
    issues_found.append(
        f'[생산량 스케일] 기존 연율 {old_annual_rate:,.0f}대 vs MES {actual_annual:,.0f}대 '
        f'({(actual_annual-old_annual_rate)/old_annual_rate*100:+.1f}%) → 15% 이상 차이. '
        f'기존 데이터와 연속성 강조 시 스케일 조정 고려'
    )

# 재고 연속성
if continuity_breaks > 0:
    issues_found.append(
        f'[재고 불연속] 전일 기말재고 ≠ 당일 기초재고: {continuity_breaks}건'
    )

# C조 점유율
c_pct_old = old_s.loc['C','pct']
c_pct_new = new_s.loc['C','pct']
if abs(c_pct_new - c_pct_old) > 1.0:
    issues_found.append(
        f'[C조 점유율] 기존 {c_pct_old}% vs MES {c_pct_new}% (차이 {c_pct_new-c_pct_old:+.2f}pp)'
    )

# 불량률 차이
old_total_fr = old_daily['fail_count'].sum() / old_daily['total_inspections'].sum() * 100
new_total_fr = pr['defect_qty'].sum() / pr['actual_qty'].sum() * 100
if abs(new_total_fr - old_total_fr) > 0.5:
    issues_found.append(
        f'[전체 불량률] 기존 {old_total_fr:.2f}% vs MES {new_total_fr:.2f}% '
        f'(차이 {new_total_fr-old_total_fr:+.2f}pp) → 0.5pp 이상 차이'
    )

if not issues_found:
    print('  ✅ 발견된 이슈 없음!')
else:
    for i, issue in enumerate(issues_found, 1):
        print(f'  {i}. {issue}')
        print()

print('=' * 70)


