"""
현대자동차 도장 검사 기반 생산량 통계 리포트 생성기
실행: python production_report.py
결과: production_report.html (브라우저로 열기)
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import numpy as np
import base64
import io
import os

# ── 한글 폰트 ──────────────────────────────────────────
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

DATA_DIR = 'dataset/현대_오토에버/track_a_data/'

# ── 데이터 로딩 ────────────────────────────────────────
print("데이터 로딩 중...")
daily        = pd.read_csv(f'{DATA_DIR}daily_summary.csv', parse_dates=['date'])
master_model = pd.read_csv(f'{DATA_DIR}master_model.csv')
master_plant = pd.read_csv(f'{DATA_DIR}master_plant_line.csv')

daily = daily.merge(master_model[['model_code','model_name','brand']], on='model_code', how='left')
daily = daily.merge(master_plant[['plant_code','plant_name','line_code']].drop_duplicates(),
                    on=['plant_code','line_code'], how='left')

daily['year']       = daily['date'].dt.year
daily['month']      = daily['date'].dt.month
daily['year_month'] = daily['date'].dt.to_period('M')
daily['weekday']    = daily['date'].dt.dayofweek
daily['weekday_name'] = daily['date'].dt.day_name()

total       = daily['total_inspections'].sum()
total_pass  = daily['pass_count'].sum()
total_fail  = daily['fail_count'].sum()
total_days  = daily['date'].nunique()
daily_total = daily.groupby('date')['total_inspections'].sum()

# ── 집계 ───────────────────────────────────────────────
# 연도별
yearly = daily.groupby('year').agg(
    총생산=('total_inspections','sum'), 합격=('pass_count','sum'),
    불합격=('fail_count','sum'), 운영일수=('date','nunique')
).reset_index()
yearly['양품률'] = yearly['합격'] / yearly['총생산'] * 100

# 공장별
by_plant = daily.groupby(['plant_code','plant_name']).agg(
    총=('total_inspections','sum'), 합격=('pass_count','sum'),
    불합격=('fail_count','sum'), 라인=('line_code','nunique')
).reset_index().sort_values('총', ascending=False)
by_plant['점유율'] = by_plant['총'] / total * 100
by_plant['양품률'] = by_plant['합격'] / by_plant['총'] * 100

# 브랜드별
brand_map = {'HMC':'현대자동차','KIA':'기아','GEN':'제네시스'}
by_brand = daily.groupby('brand').agg(
    총=('total_inspections','sum'), 모델수=('model_code','nunique')
).reset_index().sort_values('총', ascending=False)
by_brand['브랜드명'] = by_brand['brand'].map(brand_map)
by_brand['점유율'] = by_brand['총'] / total * 100

# 차종별
by_model = daily.groupby(['model_code','model_name','brand']).agg(
    총=('total_inspections','sum'), 합격=('pass_count','sum'), 불합격=('fail_count','sum')
).reset_index().sort_values('총', ascending=False)
by_model['점유율'] = by_model['총'] / total * 100
by_model['불량률'] = by_model['불합격'] / by_model['총'] * 100
by_model['누적'] = by_model['점유율'].cumsum()
by_model['브랜드명'] = by_model['brand'].map(brand_map)

# 교대조별
shift_desc = {'A':'A조 (주간 06~13시)','B':'B조 (오후 14~21시)','C':'C조 (야간 22시~)'}
by_shift = daily.groupby('shift').agg(
    총=('total_inspections','sum'), 합격=('pass_count','sum'), 불합격=('fail_count','sum')
).reset_index()
by_shift['불량률'] = by_shift['불합격'] / by_shift['총'] * 100
by_shift['점유율'] = by_shift['총'] / total * 100
by_shift['교대조명'] = by_shift['shift'].map(shift_desc)

# 라인별
by_line = daily.groupby(['plant_name','line_code']).agg(
    총=('total_inspections','sum'), 불합격=('fail_count','sum')
).reset_index().sort_values('총', ascending=False)
by_line['불량률'] = by_line['불합격'] / by_line['총'] * 100
by_line['라인명'] = by_line['plant_name'] + ' - ' + by_line['line_code']

# 월별
monthly = daily.groupby('year_month').agg(
    총=('total_inspections','sum'), 불합격=('fail_count','sum')
).reset_index()
monthly['불량률'] = monthly['불합격'] / monthly['총'] * 100
monthly['x'] = monthly['year_month'].astype(str)

# 요일별
weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
weekday_kr    = ['월','화','수','목','금','토','일']
by_weekday = daily.groupby('weekday_name').agg(
    총=('total_inspections','sum'), 일수=('date','nunique')
).reindex(weekday_order)
by_weekday['일평균'] = (by_weekday['총'] / by_weekday['일수']).astype(int)

print("차트 생성 중...")

# ── 차트 → base64 변환 함수 ────────────────────────────
def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f'data:image/png;base64,{b64}'

COLORS_PLANT  = ['#2196F3','#FF9800','#4CAF50','#9C27B0']
COLORS_BRAND  = ['#003DA5','#BB162B','#9B7B56']
COLORS_SHIFT  = ['#FFC107','#FF9800','#455A64']

# ── Chart 1: 연도별 생산량 ─────────────────────────────
fig, ax = plt.subplots(figsize=(7,4))
bars = ax.bar(yearly['year'].astype(str), yearly['총생산'],
              color=['#2196F3','#FF9800','#4CAF50'], alpha=0.85, width=0.5)
for bar, v in zip(bars, yearly['총생산']):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+8000,
            f'{v:,.0f}', ha='center', fontsize=11, fontweight='bold')
ax.set_ylabel('생산량 (대)', fontsize=11)
ax.set_title('연도별 총 생산량', fontsize=13, fontweight='bold', pad=10)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'{x/10000:.0f}만'))
ax.grid(axis='y', alpha=0.3)
img_yearly = fig_to_b64(fig)

# ── Chart 2: 월별 생산량 + 불량률 ─────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7))
x = range(len(monthly))
ax1.fill_between(x, monthly['총'], alpha=0.2, color='#2196F3')
ax1.plot(x, monthly['총'], '-o', color='#2196F3', markersize=3, linewidth=1.5)
ax1.set_ylabel('생산량 (대)', fontsize=10)
ax1.set_title('월별 생산량 추이', fontsize=12, fontweight='bold')
ax1.set_xticks(range(0, len(monthly), 3))
ax1.set_xticklabels(monthly['x'].iloc[::3], rotation=45, ha='right', fontsize=8)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'{v/10000:.1f}만'))
ax1.grid(axis='y', alpha=0.3)

ax2.plot(x, monthly['불량률'], '-s', color='#d62728', markersize=3, linewidth=1.5)
ax2.axhline(monthly['불량률'].mean(), color='gray', linestyle='--', alpha=0.7,
            label=f'평균 {monthly["불량률"].mean():.2f}%')
ax2.set_ylabel('불량률 (%)', fontsize=10)
ax2.set_title('월별 불량률 추이', fontsize=12, fontweight='bold')
ax2.set_xticks(range(0, len(monthly), 3))
ax2.set_xticklabels(monthly['x'].iloc[::3], rotation=45, ha='right', fontsize=8)
ax2.legend(fontsize=9)
ax2.grid(axis='y', alpha=0.3)
plt.tight_layout()
img_monthly = fig_to_b64(fig)

# ── Chart 3: 공장별 ────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
bars = ax1.barh(by_plant['plant_name'], by_plant['총'],
                color=COLORS_PLANT, alpha=0.85)
for bar, v in zip(bars, by_plant['총']):
    ax1.text(v+3000, bar.get_y()+bar.get_height()/2,
             f'{v:,.0f}', va='center', fontsize=10, fontweight='bold')
ax1.set_xlabel('생산량 (대)', fontsize=10)
ax1.set_title('공장별 총 생산량', fontsize=12, fontweight='bold')
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'{v/10000:.0f}만'))

ax2.pie(by_plant['총'], labels=by_plant['plant_name'],
        autopct='%1.1f%%', colors=COLORS_PLANT, startangle=90,
        textprops={'fontsize':11})
ax2.set_title('공장별 생산 비중', fontsize=12, fontweight='bold')
plt.tight_layout()
img_plant = fig_to_b64(fig)

# ── Chart 4: 브랜드별 ─────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
ax1.pie(by_brand['총'], labels=by_brand['브랜드명'],
        autopct='%1.1f%%', colors=COLORS_BRAND, startangle=90,
        textprops={'fontsize':12, 'fontweight':'bold'})
ax1.set_title('브랜드별 생산 비중', fontsize=12, fontweight='bold')

bars = ax2.bar(by_brand['브랜드명'], by_brand['총'], color=COLORS_BRAND, alpha=0.85)
for bar, v in zip(bars, by_brand['총']):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5000,
             f'{v:,.0f}', ha='center', fontsize=11, fontweight='bold')
ax2.set_ylabel('생산량 (대)', fontsize=10)
ax2.set_title('브랜드별 생산량', fontsize=12, fontweight='bold')
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'{v/10000:.0f}만'))
ax2.grid(axis='y', alpha=0.3)
plt.tight_layout()
img_brand = fig_to_b64(fig)

# ── Chart 5: 차종별 ────────────────────────────────────
brand_colors_m = {'HMC':'#003DA5','KIA':'#BB162B','GEN':'#9B7B56'}
bar_colors_m = [brand_colors_m[b] for b in by_model['brand']]
fig, ax = plt.subplots(figsize=(13, 5))
bars = ax.bar(by_model['model_name'], by_model['총'], color=bar_colors_m, alpha=0.85)
for bar, v, s in zip(bars, by_model['총'], by_model['점유율']):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+2000,
            f'{v:,.0f}\n({s:.1f}%)', ha='center', fontsize=8.5, fontweight='bold')
ax.set_ylabel('생산량 (대)', fontsize=10)
ax.set_title('차종별 총 생산량', fontsize=13, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'{v/10000:.0f}만'))
legend_handles = [Patch(facecolor=c, label=p) for p,c in brand_colors_m.items()]
ax.legend(handles=legend_handles, title='브랜드', fontsize=9)
ax.grid(axis='y', alpha=0.3)
plt.xticks(rotation=20, ha='right')
plt.tight_layout()
img_model = fig_to_b64(fig)

# ── Chart 6: 교대조별 ─────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
bars = ax1.bar(by_shift['교대조명'], by_shift['총'], color=COLORS_SHIFT, alpha=0.85)
for bar, v in zip(bars, by_shift['총']):
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5000,
             f'{v:,.0f}', ha='center', fontsize=11, fontweight='bold')
ax1.set_ylabel('생산량 (대)', fontsize=10)
ax1.set_title('교대조별 생산량', fontsize=12, fontweight='bold')
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'{v/10000:.0f}만'))
ax1.grid(axis='y', alpha=0.3)

bars2 = ax2.bar(by_shift['교대조명'], by_shift['불량률'], color=COLORS_SHIFT, alpha=0.85)
for bar, v in zip(bars2, by_shift['불량률']):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
             f'{v:.2f}%', ha='center', fontsize=12, fontweight='bold', color='red')
avg_fail = (total_fail/total*100)
ax2.axhline(avg_fail, color='gray', linestyle='--', alpha=0.7, label=f'전체 평균 {avg_fail:.2f}%')
ax2.set_ylabel('불량률 (%)', fontsize=10)
ax2.set_title('교대조별 불량률', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(axis='y', alpha=0.3)
plt.tight_layout()
img_shift = fig_to_b64(fig)

# ── Chart 7: 라인별 생산량 ────────────────────────────
plant_clr = {'울산공장':'#2196F3','아산공장':'#FF9800','광주공장':'#4CAF50','화성공장':'#9C27B0'}
lc = [plant_clr.get(p,'gray') for p in by_line['plant_name']]
fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(by_line['라인명'], by_line['총'], color=lc, alpha=0.85)
for bar, v in zip(bars, by_line['총']):
    ax.text(v+500, bar.get_y()+bar.get_height()/2,
            f'{v:,.0f}', va='center', fontsize=9)
ax.set_xlabel('생산량 (대)', fontsize=10)
ax.set_title('생산 라인별 총 생산량', fontsize=13, fontweight='bold')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f'{v/10000:.0f}만'))
legend_handles = [Patch(facecolor=c, label=p) for p,c in plant_clr.items()]
ax.legend(handles=legend_handles, fontsize=9)
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
img_line = fig_to_b64(fig)

# ── Chart 8: 요일별 ────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 4))
colors_wd = ['#2196F3']*5 + ['#FF5722']*2
bars = ax.bar(weekday_kr, by_weekday['일평균'], color=colors_wd, alpha=0.85)
for bar, v in zip(bars, by_weekday['일평균']):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+30,
            f'{v:,}', ha='center', fontsize=10, fontweight='bold')
ax.set_ylabel('일 평균 생산량 (대)', fontsize=10)
ax.set_title('요일별 일 평균 생산량', fontsize=12, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
img_weekday = fig_to_b64(fig)

print("HTML 리포트 생성 중...")

# ── HTML 빌더 헬퍼 ─────────────────────────────────────
def kv(label, value, highlight=False):
    style = ' style="color:#d62728;font-weight:700;"' if highlight else ''
    return f'<tr><td class="kl">{label}</td><td{style}>{value}</td></tr>'

def tbl_header(*cols):
    return '<thead><tr>' + ''.join(f'<th>{c}</th>' for c in cols) + '</tr></thead>'

# ── HTML 생성 ──────────────────────────────────────────
monthly_max_label = monthly.loc[monthly['총'].idxmax(), 'x']
monthly_min_label = monthly.loc[monthly['총'].idxmin(), 'x']

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>현대자동차 생산량 통계 리포트</title>
<style>
  :root {{
    --blue:#1565C0; --blue-light:#E3F2FD; --accent:#FF6F00;
    --pass:#2E7D32; --fail:#C62828; --bg:#F8F9FA;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif;
          background:var(--bg); color:#212121; line-height:1.6; }}
  .header {{ background:linear-gradient(135deg,#0D47A1,#1976D2);
             color:#fff; padding:36px 40px; }}
  .header h1 {{ font-size:1.9rem; margin-bottom:6px; }}
  .header p  {{ font-size:.95rem; opacity:.85; }}
  .container {{ max-width:1200px; margin:0 auto; padding:28px 20px; }}
  .card {{ background:#fff; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,.08);
           padding:28px; margin-bottom:28px; }}
  .card h2 {{ font-size:1.15rem; color:var(--blue); border-left:4px solid var(--blue);
              padding-left:12px; margin-bottom:18px; }}
  /* KPI 카드 */
  .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
               gap:16px; margin-bottom:8px; }}
  .kpi {{ background:var(--blue-light); border-radius:10px; padding:18px 16px; text-align:center; }}
  .kpi .val {{ font-size:1.6rem; font-weight:700; color:var(--blue); }}
  .kpi .lbl {{ font-size:.82rem; color:#555; margin-top:4px; }}
  .kpi.pass .val {{ color:var(--pass); }}
  .kpi.fail .val {{ color:var(--fail); }}
  /* 테이블 */
  table {{ width:100%; border-collapse:collapse; font-size:.88rem; }}
  th {{ background:#1565C0; color:#fff; padding:9px 12px; text-align:center; }}
  td {{ padding:8px 12px; border-bottom:1px solid #e0e0e0; text-align:center; }}
  tr:nth-child(even) td {{ background:#F5F5F5; }}
  td.kl {{ text-align:left; font-weight:600; color:#555; }}
  /* 차트 */
  .chart-wrap {{ text-align:center; margin-top:12px; }}
  .chart-wrap img {{ max-width:100%; border-radius:8px; }}
  /* 배지 */
  .badge {{ display:inline-block; padding:2px 10px; border-radius:20px;
            font-size:.78rem; font-weight:700; }}
  .badge-hmc {{ background:#E3F2FD; color:#0D47A1; }}
  .badge-kia {{ background:#FFEBEE; color:#B71C1C; }}
  .badge-gen {{ background:#FFF8E1; color:#795548; }}
  /* 2열 레이아웃 */
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  @media(max-width:720px){{ .two-col {{ grid-template-columns:1fr; }} }}
  /* 주의 배너 */
  .warn {{ background:#FFF3E0; border-left:4px solid #FF6F00;
           padding:14px 18px; border-radius:0 8px 8px 0; font-size:.9rem; margin-top:8px; }}
  footer {{ text-align:center; font-size:.8rem; color:#9E9E9E; padding:28px 0 40px; }}
  .rank {{ font-weight:700; color:var(--blue); }}
</style>
</head>
<body>

<div class="header">
  <h1>🚗 현대자동차 도장 검사 기반 생산량 통계 리포트</h1>
  <p>분석 기간: 2023-01-01 ~ 2025-01-24 &nbsp;|&nbsp;
     데이터: 도장 품질 AI 검사 기록 &nbsp;|&nbsp;
     총 검사(생산) 건수: 3,000,000대</p>
</div>

<div class="container">

<!-- KPI 요약 -->
<div class="card">
  <h2>📌 핵심 지표 요약</h2>
  <div class="kpi-grid">
    <div class="kpi">
      <div class="val">3,000,000</div>
      <div class="lbl">총 생산(검사) 건수 (대)</div>
    </div>
    <div class="kpi pass">
      <div class="val">2,877,908</div>
      <div class="lbl">합격 (PASS) · 95.93%</div>
    </div>
    <div class="kpi fail">
      <div class="val">122,092</div>
      <div class="lbl">불합격 (FAIL) · 4.07%</div>
    </div>
    <div class="kpi">
      <div class="val">755</div>
      <div class="lbl">총 운영일수 (일)</div>
    </div>
    <div class="kpi">
      <div class="val">3,974</div>
      <div class="lbl">일 평균 생산량 (대/일)</div>
    </div>
    <div class="kpi">
      <div class="val">~120,000</div>
      <div class="lbl">월 평균 생산량 (대/월)</div>
    </div>
  </div>
</div>

<!-- 연도별 -->
<div class="card">
  <h2>📅 연도별 생산량</h2>
  <table>
    {tbl_header('연도','총 생산량','합격 (PASS)','불합격 (FAIL)','양품률','운영일수')}
    <tbody>
"""
for _, r in yearly.iterrows():
    html += f"""
      <tr>
        <td><b>{int(r['year'])}년</b></td>
        <td>{r['총생산']:,.0f}대</td>
        <td style="color:var(--pass)">{r['합격']:,.0f}대</td>
        <td style="color:var(--fail)">{r['불합격']:,.0f}대</td>
        <td>{r['양품률']:.2f}%</td>
        <td>{int(r['운영일수'])}일</td>
      </tr>"""
html += f"""
    </tbody>
  </table>
  <div class="chart-wrap"><img src="{img_yearly}" alt="연도별 생산량"></div>
</div>

<!-- 월별 -->
<div class="card">
  <h2>📈 월별 생산량 추이</h2>
  <table>
    {tbl_header('항목','값')}
    <tbody>
      <tr><td class="kl">월 평균 생산량</td><td>{monthly['총'].mean():,.0f}대</td></tr>
      <tr><td class="kl">월 최대 생산량</td><td>{monthly['총'].max():,.0f}대 ({monthly_max_label})</td></tr>
      <tr><td class="kl">월 최소 생산량</td><td>{monthly['총'].min():,.0f}대 ({monthly_min_label})</td></tr>
      <tr><td class="kl">월 평균 불량률</td><td>{monthly['불량률'].mean():.2f}%</td></tr>
    </tbody>
  </table>
  <div class="chart-wrap"><img src="{img_monthly}" alt="월별 추이"></div>
</div>

<!-- 공장별 -->
<div class="card">
  <h2>🏭 공장별 생산량</h2>
  <table>
    {tbl_header('공장','공장 코드','총 생산량','점유율','합격','불합격','양품률','라인 수')}
    <tbody>
"""
for _, r in by_plant.iterrows():
    html += f"""
      <tr>
        <td><b>{r['plant_name']}</b></td>
        <td>{r['plant_code']}</td>
        <td>{r['총']:,.0f}대</td>
        <td>{r['점유율']:.1f}%</td>
        <td style="color:var(--pass)">{r['합격']:,.0f}대</td>
        <td style="color:var(--fail)">{r['불합격']:,.0f}대</td>
        <td>{r['양품률']:.2f}%</td>
        <td>{int(r['라인'])}개</td>
      </tr>"""
html += f"""
    </tbody>
  </table>
  <div class="chart-wrap"><img src="{img_plant}" alt="공장별 생산량"></div>
</div>

<!-- 브랜드별 -->
<div class="card">
  <h2>🏷 브랜드별 생산량</h2>
  <table>
    {tbl_header('브랜드','총 생산량','점유율','모델 수')}
    <tbody>
"""
for _, r in by_brand.iterrows():
    badge = f'badge-{r["brand"].lower()}'
    html += f"""
      <tr>
        <td><span class="badge {badge}">{r['브랜드명']}</span></td>
        <td>{r['총']:,.0f}대</td>
        <td>{r['점유율']:.1f}%</td>
        <td>{int(r['모델수'])}개</td>
      </tr>"""
html += f"""
    </tbody>
  </table>
  <div class="chart-wrap"><img src="{img_brand}" alt="브랜드별 생산량"></div>
</div>

<!-- 차종별 -->
<div class="card">
  <h2>🚙 차종별 생산량 (12개 모델)</h2>
  <table>
    {tbl_header('순위','차종','브랜드','총 생산량','점유율','누적 점유율','불량률')}
    <tbody>
"""
for i, (_, r) in enumerate(by_model.iterrows(), 1):
    badge = f'badge-{r["brand"].lower()}'
    html += f"""
      <tr>
        <td class="rank">{i}위</td>
        <td><b>{r['model_name']}</b></td>
        <td><span class="badge {badge}">{r['브랜드명']}</span></td>
        <td>{r['총']:,.0f}대</td>
        <td>{r['점유율']:.1f}%</td>
        <td>{r['누적']:.1f}%</td>
        <td style="color:var(--fail)">{r['불량률']:.2f}%</td>
      </tr>"""
html += f"""
    </tbody>
  </table>
  <div class="chart-wrap"><img src="{img_model}" alt="차종별 생산량"></div>
</div>

<!-- 교대조별 -->
<div class="card">
  <h2>⏰ 교대조별 생산량 및 품질</h2>
  <table>
    {tbl_header('교대조','총 생산량','점유율','불합격','불량률')}
    <tbody>
"""
for _, r in by_shift.iterrows():
    fr_style = ' style="color:var(--fail);font-weight:700;"' if r['불량률'] > 5 else ''
    html += f"""
      <tr>
        <td><b>{r['교대조명']}</b></td>
        <td>{r['총']:,.0f}대</td>
        <td>{r['점유율']:.1f}%</td>
        <td style="color:var(--fail)">{r['불합격']:,.0f}대</td>
        <td{fr_style}>{r['불량률']:.2f}%</td>
      </tr>"""
html += f"""
    </tbody>
  </table>
  <div class="warn">
    ⚠️ <b>C조(야간) 불량률 6.02%</b> — 전체 평균(4.07%) 대비 <b>+48% 높음</b>.
    야간 교대 직후 집중 품질 모니터링 권장.
  </div>
  <div class="chart-wrap"><img src="{img_shift}" alt="교대조별"></div>
</div>

<!-- 라인별 -->
<div class="card">
  <h2>⚙️ 생산 라인별 생산량 (13개 라인)</h2>
  <table>
    {tbl_header('라인','공장','총 생산량','불량률')}
    <tbody>
"""
for _, r in by_line.iterrows():
    html += f"""
      <tr>
        <td><b>{r['line_code']}</b></td>
        <td>{r['plant_name']}</td>
        <td>{r['총']:,.0f}대</td>
        <td style="color:var(--fail)">{r['불량률']:.2f}%</td>
      </tr>"""
html += f"""
    </tbody>
  </table>
  <div class="chart-wrap"><img src="{img_line}" alt="라인별 생산량"></div>
</div>

<!-- 요일별 -->
<div class="card">
  <h2>📆 요일별 일 평균 생산량</h2>
  <table>
    {tbl_header('요일','일 평균 생산량','운영 일수','총 생산량')}
    <tbody>
"""
for kr, wd in zip(weekday_kr, weekday_order):
    row = by_weekday.loc[wd]
    html += f"""
      <tr>
        <td><b>{kr}요일</b></td>
        <td>{int(row['일평균']):,}대</td>
        <td>{int(row['일수'])}일</td>
        <td>{int(row['총']):,}대</td>
      </tr>"""
html += f"""
    </tbody>
  </table>
  <div class="chart-wrap"><img src="{img_weekday}" alt="요일별 생산량"></div>
</div>

<!-- 종합 인사이트 -->
<div class="card">
  <h2>💡 종합 인사이트</h2>
  <table>
    {tbl_header('구분','주요 발견')}
    <tbody>
      <tr><td class="kl">생산 규모</td>
          <td>25개월간 300만대 생산, 월 평균 12만대 · 일 평균 3,974대 — 안정적 생산 유지</td></tr>
      <tr><td class="kl">공장 집중도</td>
          <td>울산공장 단독 45.0% 담당(5개 라인). 아산이 25%, 화성·광주 각 15%</td></tr>
      <tr><td class="kl">차종 편중</td>
          <td>쏘나타·아반떼·싼타페 상위 3종이 전체의 39%, 상위 5종이 59% 차지</td></tr>
      <tr><td class="kl">야간 품질 이슈</td>
          <td>C조(야간) 불량률 6.02% — A조(4.12%), B조(3.77%)보다 현저히 높음</td></tr>
      <tr><td class="kl">전반적 품질</td>
          <td>전체 양품률 95.93% 유지, 월별 불량률 3.97~4.20% 범위로 공정 안정적</td></tr>
      <tr><td class="kl">주요 결함</td>
          <td>스크래치(24.8%) · 덴트(15%) · 도장기포(12.1%) 순. 덴트가 재작업 비용 최대</td></tr>
    </tbody>
  </table>
</div>

</div><!-- /container -->

<footer>
  ※ 본 리포트는 도장 품질 AI 검사 기록(inspection_master + daily_summary) 기반이며,
     검사 건수 ≈ 생산 차체 수로 해석합니다.<br>
  생성일: 2026-04-13 &nbsp;|&nbsp; 데이터 출처: 현대 오토에버 Track A Dataset
</footer>

</body>
</html>
"""

output_path = 'production_report.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n✅ 리포트 생성 완료: {os.path.abspath(output_path)}')
print('   브라우저에서 해당 파일을 열어 확인하세요.')

