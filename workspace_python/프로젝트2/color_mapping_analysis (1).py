"""
색상 매핑 분석 — inspection_master 실제 사용 빈도 기반
모호한 color 매핑 (white, gray, blue, navy) 추정
"""
import pandas as pd
from pathlib import Path

DATA = Path(r'C:\IT\workspace_python\프로젝트2\dataset\현대_오토에버\track_a_data')

# ── 1. 데이터 로드 ────────────────────────────────────────
m_color = pd.read_csv(DATA / 'master_color.csv', encoding='utf-8-sig')
im = pd.read_csv(DATA / 'inspection_master.csv',
                 encoding='utf-8-sig',
                 usecols=['color_code'])

print('=== master_color 전체 목록 ===')
print(m_color.to_string(index=False))

# ── 2. inspection_master 색상 사용 빈도 ───────────────────
print('\n=== inspection_master color_code 사용 빈도 ===')
freq = im['color_code'].value_counts().reset_index()
freq.columns = ['color_code', 'count']
freq['pct'] = (freq['count'] / len(im) * 100).round(2)
freq = freq.merge(m_color, on='color_code', how='left')
print(freq.to_string(index=False))

# ── 3. 모호한 색상 후보 분석 ──────────────────────────────
print('\n' + '='*50)
print('=== 모호한 색상 후보 분석 ===')

ambiguous = {
    'white': ['P2W', 'WC9'],
    'gray':  ['N5M', 'TW3'],
    'blue':  ['V5P', 'K3B'],
    'navy':  ['K3B', 'V5P'],
}

for img_color, candidates in ambiguous.items():
    print(f'\n[ 이미지 color: {img_color} ]')
    for code in candidates:
        row = freq[freq['color_code'] == code]
        name = m_color[m_color['color_code'] == code]['color_name'].values
        name_str = name[0] if len(name) > 0 else '?'
        if len(row) > 0:
            print(f'  {code} ({name_str}) → {row.iloc[0]["count"]:,}건 ({row.iloc[0]["pct"]}%)')
        else:
            print(f'  {code} ({name_str}) → 사용 없음')

# ── 4. 이미지 color 매핑 현황 ─────────────────────────────
print('\n' + '='*50)
print('=== 이미지 color 매핑 현황 ===')

confirmed = {
    'black':       ('B3L', '아비스블랙',     '✅ 확정'),
    'pearl_white': ('SWP', '스노우화이트펄', '✅ 확정'),
    'red':         ('R4M', '플레임레드',     '✅ 확정'),
    'silver':      ('SSS', '스타더스트실버', '✅ 확정'),
    'bronze':      ('W8Y', '실키브론즈',     '✅ 확정 (기존 None → 수정)'),
    'white':       (None,  None,             '⚠️ P2W vs WC9'),
    'gray':        (None,  None,             '⚠️ N5M vs TW3'),
    'blue':        (None,  None,             '⚠️ V5P vs K3B'),
    'navy':        (None,  None,             '⚠️ K3B 추정'),
    'green':       (None,  None,             '❌ 대응 없음'),
}

for img_c, (code, name, status) in confirmed.items():
    code_str = code if code else '—'
    name_str = name if name else '—'
    print(f'  {img_c:<12} → {code_str:<5} {name_str:<15} {status}')

# ── 5. master_color 중 이미지 미매핑 색상 ────────────────
print('\n=== master_color 중 이미지 미매핑 색상 ===')
confirmed_codes = {v[0] for v in confirmed.values() if v[0]}
unused = m_color[~m_color['color_code'].isin(confirmed_codes)]
print(unused.to_string(index=False))
