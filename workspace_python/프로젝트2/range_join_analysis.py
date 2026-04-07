"""Range Join 매칭 규모 파악 — val 라벨 파일 기반"""
import pandas as pd
from pathlib import Path
import os

os.chdir(Path(__file__).resolve().parent)

# ── 0. 매핑 테이블 ────────────────────────────────────────
class_to_defect = {
    0: 'SCR', 1: 'DNT', 2: 'PBB', 3: 'PDR',
    4: 'DST', 5: 'ORG', 6: 'CRK', 7: 'GAP',
}

zone_to_code = {
    'bumper':     ['BUMPER_F', 'BUMPER_R'],
    'fender':     ['FF', 'RF'],
    'front_door': ['FD'],
    'rear_door':  ['RD'],
    'hood':       ['HOOD'],
    'roof':       ['ROOF'],
    'trunk':      ['TRUNK'],
    'rocker':     ['ROCKER'],
}

color_to_code = {
    'black': 'B3L', 'white': 'P2W', 'silver': 'SWP',
    'red': 'R4M', 'blue': 'ABP', 'gray': 'YW6',
}

# ── 1. 정형 데이터 로드 ───────────────────────────────────
dd = pd.read_csv('dataset/track_a_data/defect_detail.csv', encoding='utf-8-sig')
print(f'defect_detail 행 수: {len(dd):,}')

# inspection_master에서 color_code 가져오기 (조건 3용)
im = pd.read_csv('dataset/track_a_data/inspection_master.csv',
                  encoding='utf-8-sig',
                  usecols=['inspection_id', 'color_code'])
print(f'inspection_master 행 수: {len(im):,}')

dd = dd.merge(im, on='inspection_id', how='left', suffixes=('', '_insp'))
print(f'defect_detail + color JOIN 완료 (color_code 컬럼 추가)')
print(f'  color_code NaN: {dd["color_code"].isna().sum():,}건')

# ── 2. val 라벨 파일 파싱 ─────────────────────────────────
label_dir = Path('dataset/track_a_images/labels/val')
records = []

for txt_file in sorted(label_dir.glob('*.txt')):
    lines = txt_file.read_text().strip().splitlines()
    if not lines:
        continue  # 빈 파일(Negative sample) 스킵

    # 파일명에서 zone, color 추출
    parts = txt_file.stem.split('_')
    if 'pearl' in parts:
        pearl_idx = parts.index('pearl')
        zone = '_'.join(parts[:pearl_idx])
        color = parts[pearl_idx + 1]  # pearl 다음 = 실제 색상(white 등)
    else:
        # 마지막 요소는 ID, 그 앞이 color, 나머지가 zone
        zone = '_'.join(parts[:-2])
        color = parts[-2]

    for line in lines:
        tokens = line.split()
        if len(tokens) < 5:
            continue
        cls_id, cx, cy, w, h = float(tokens[0]), float(tokens[1]), float(tokens[2]), float(tokens[3]), float(tokens[4])
        records.append({
            'file':         txt_file.stem,
            'zone_raw':     zone,
            'color_raw':    color,
            'class_id':     int(cls_id),
            'defect_code':  class_to_defect.get(int(cls_id)),
            'bbox_area':    round(w * h, 6),
        })

label_df = pd.DataFrame(records)
print(f'\n라벨 파싱 결과: {len(label_df)}건')
print(label_df['defect_code'].value_counts().to_string())

# ── 3. zone, color 코드 매핑 ──────────────────────────────
label_df['zone_codes'] = label_df['zone_raw'].map(
    lambda z: zone_to_code.get(z, [None])
)
label_df['color_code'] = label_df['color_raw'].map(color_to_code)

print('\n=== color 매핑 결과 ===')
print(label_df[['color_raw', 'color_code']].drop_duplicates().to_string(index=False))

# ── 4. Range Join 매칭 (조건별 3단계) ────────────────────
# 조건 1: defect_type만
# 조건 2: defect_type + zone
# 조건 3: defect_type + zone + color (color 매핑 없는 경우 None)
results = []

for _, row in label_df.iterrows():
    defect  = row['defect_code']
    zones   = row['zone_codes']
    color   = row['color_code']

    # 조건 1: defect_type만
    cond1 = dd['defect_type_code'] == defect
    count1 = dd[cond1].shape[0]

    # 조건 2: defect_type + zone
    if zones and zones[0] is not None:
        cond2 = cond1 & dd['zone_code'].isin(zones)
    else:
        cond2 = cond1
    count2 = dd[cond2].shape[0]

    # 조건 3: defect_type + zone + color
    if color is not None and pd.notna(color):
        cond3 = cond2 & (dd['color_code'] == color)
        count3 = dd[cond3].shape[0]
    else:
        count3 = None  # color 매핑 불가 (bronze, green, navy)

    results.append({
        'file':         row['file'],
        'defect_code':  defect,
        'zone_raw':     row['zone_raw'],
        'color_raw':    row['color_raw'],
        'color_code':   color,
        'matched_defect_only':      count1,
        'matched_defect_zone':      count2,
        'matched_defect_zone_color': count3,
    })

result_df = pd.DataFrame(results)

# ── 5. 매칭 규모 출력 ────────────────────────────────────
print('\n' + '='*60)
print('=== 조건 1: defect_type만 ===')
print(result_df['matched_defect_only'].describe().round(1).to_string())

print('\n=== 조건 2: defect_type + zone ===')
print(result_df['matched_defect_zone'].describe().round(1).to_string())

print('\n=== 조건 3: defect_type + zone + color ===')
cond3_valid = result_df['matched_defect_zone_color'].dropna()
cond3_skip = result_df['matched_defect_zone_color'].isna().sum()
print(f'(color 매핑 가능: {len(cond3_valid)}건, 매핑 불가(bronze/green/navy): {cond3_skip}건)')
print(cond3_valid.describe().round(1).to_string())

print('\n=== 결함 유형별 평균 매칭 수 ===')
agg_defect = result_df.groupby('defect_code').agg(
    cond2_mean=('matched_defect_zone', 'mean'),
    cond3_mean=('matched_defect_zone_color', 'mean'),
    count=('defect_code', 'size')
).round(1).sort_values('cond2_mean')
print(agg_defect.to_string())

print('\n=== zone별 평균 매칭 수 ===')
agg_zone = result_df.groupby('zone_raw').agg(
    cond2_mean=('matched_defect_zone', 'mean'),
    cond3_mean=('matched_defect_zone_color', 'mean'),
    count=('zone_raw', 'size')
).round(1).sort_values('cond2_mean')
print(agg_zone.to_string())

print('\n=== color별 평균 매칭 수 (조건 3) ===')
cond3_by_color = result_df.dropna(subset=['matched_defect_zone_color']).groupby('color_raw').agg(
    cond3_mean=('matched_defect_zone_color', 'mean'),
    cond3_min=('matched_defect_zone_color', 'min'),
    cond3_max=('matched_defect_zone_color', 'max'),
    count=('color_raw', 'size')
).round(1).sort_values('cond3_mean')
print(cond3_by_color.to_string())

print('\n=== 매칭 0건 비율 ===')
# 조건 2
zero2 = (result_df['matched_defect_zone'] == 0).sum()
total = len(result_df)
print(f'조건 2: {zero2}/{total} ({zero2/total*100:.1f}%)')
# 조건 3 (color 매핑 가능한 건만)
zero3 = (cond3_valid == 0).sum()
total3 = len(cond3_valid)
print(f'조건 3: {zero3}/{total3} ({zero3/total3*100:.1f}%) — color 매핑 가능한 건 기준')

# ── 6. 판정 ──────────────────────────────────────────────
avg2 = result_df['matched_defect_zone'].mean()
avg3 = cond3_valid.mean()
zero2_pct = zero2 / total * 100
zero3_pct = zero3 / total3 * 100

print('\n' + '='*60)
print('=== 최종 판정 ===')
print(f'  조건 2 평균 매칭 수: {avg2:.1f}건 (기준: > 100)')
print(f'  조건 2 매칭 0건:    {zero2_pct:.1f}% (기준: < 10%)')
print(f'  조건 3 평균 매칭 수: {avg3:.1f}건 (기준: > 100)')
print(f'  조건 3 매칭 0건:    {zero3_pct:.1f}% (기준: < 10%)')
print()

for label, avg, zpct in [('조건 2', avg2, zero2_pct), ('조건 3', avg3, zero3_pct)]:
    if avg > 100 and zpct < 10:
        print(f'  {label}: 방법론 진행 가능 ✓')
    else:
        reasons = []
        if avg <= 100:
            reasons.append(f'평균 매칭 수 부족({avg:.1f})')
        if zpct >= 10:
            reasons.append(f'0건 비율 과다({zpct:.1f}%)')
        print(f'  {label}: 방법론 재고 필요 — {", ".join(reasons)}')

# ── 7. 결과 저장 ─────────────────────────────────────────
result_df.to_csv('range_join_match_result.csv', index=False, encoding='utf-8-sig')
print('\n저장 완료: range_join_match_result.csv')
