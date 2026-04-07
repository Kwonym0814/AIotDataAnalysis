"""Range Join 1:1 매칭 — train+val 라벨 → defect_detail 1:1 매핑
매칭 전략:
  1) exact: defect_type + zone + color
  2) range: area 퍼센타일 ±15% 범위
  3) rank:  x, y, area 퍼센타일 거리 최소 → 1건 선택
"""
import pandas as pd
import numpy as np
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

AREA_RANGE_TOL = 0.15  # 퍼센타일 ±15% 범위

# ── 1. 정형 데이터 로드 ───────────────────────────────────
dd = pd.read_csv('dataset/track_a_data/defect_detail.csv', encoding='utf-8-sig')
im = pd.read_csv('dataset/track_a_data/inspection_master.csv',
                  encoding='utf-8-sig',
                  usecols=['inspection_id', 'color_code'])
dd = dd.merge(im, on='inspection_id', how='left')
print(f'defect_detail: {len(dd):,}행 (color_code JOIN 완료)')

# defect_detail에 퍼센타일 컬럼 추가 (defect_type별)
for col in ['x_position_mm', 'y_position_mm', 'area_mm2']:
    dd[f'{col}_pctile'] = dd.groupby('defect_type_code')[col].rank(pct=True)

# ── 2. train + val 라벨 파일 파싱 ─────────────────────────
def parse_labels(label_dir):
    records = []
    for txt_file in sorted(Path(label_dir).glob('*.txt')):
        lines = txt_file.read_text().strip().splitlines()
        if not lines:
            continue

        parts = txt_file.stem.split('_')
        if 'pearl' in parts:
            pearl_idx = parts.index('pearl')
            zone = '_'.join(parts[:pearl_idx])
            color = parts[pearl_idx + 1]
        else:
            zone = '_'.join(parts[:-2])
            color = parts[-2]

        for line in lines:
            tokens = line.split()
            if len(tokens) < 5:
                continue
            cls_id = int(float(tokens[0]))
            cx, cy, w, h = float(tokens[1]), float(tokens[2]), float(tokens[3]), float(tokens[4])
            records.append({
                'file': txt_file.stem,
                'split': 'train' if 'train' in str(label_dir) else 'val',
                'zone_raw': zone,
                'color_raw': color,
                'class_id': cls_id,
                'defect_code': class_to_defect.get(cls_id),
                'bbox_cx': cx,
                'bbox_cy': cy,
                'bbox_w': w,
                'bbox_h': h,
                'bbox_area': round(w * h, 6),
            })
    return records

records = []
records += parse_labels('dataset/track_a_images/labels/train')
records += parse_labels('dataset/track_a_images/labels/val')
label_df = pd.DataFrame(records)
print(f'라벨 파싱: train {(label_df["split"]=="train").sum()}건 + val {(label_df["split"]=="val").sum()}건 = 총 {len(label_df)}건')

# bbox area 퍼센타일 (defect_type별)
label_df['bbox_area_pctile'] = label_df.groupby('defect_code')['bbox_area'].rank(pct=True)
label_df['bbox_cx_pctile'] = label_df.groupby('defect_code')['bbox_cx'].rank(pct=True)
label_df['bbox_cy_pctile'] = label_df.groupby('defect_code')['bbox_cy'].rank(pct=True)

# zone, color 코드
label_df['zone_codes'] = label_df['zone_raw'].map(lambda z: zone_to_code.get(z, [None]))
label_df['color_code'] = label_df['color_raw'].map(color_to_code)

print(f'\ncolor 매핑 가능: {label_df["color_code"].notna().sum()}건')
print(f'color 매핑 불가: {label_df["color_code"].isna().sum()}건 (bronze/green/navy)')

# ── 3. 1:1 Range Join 매칭 ───────────────────────────────
print('\n매칭 시작...')

matched_rows = []
match_stats = {'exact_3': 0, 'exact_2': 0, 'range_hit': 0, 'range_miss_fallback': 0, 'no_match': 0}

for idx, row in label_df.iterrows():
    defect = row['defect_code']
    zones = row['zone_codes']
    color = row['color_code']
    area_pctile = row['bbox_area_pctile']
    cx_pctile = row['bbox_cx_pctile']
    cy_pctile = row['bbox_cy_pctile']

    # Step 1: defect_type 필터 (필수)
    mask = dd['defect_type_code'] == defect

    # Step 2: zone 필터
    if zones and zones[0] is not None:
        mask = mask & dd['zone_code'].isin(zones)

    # Step 3: color 필터 (가능한 경우)
    if pd.notna(color):
        mask_with_color = mask & (dd['color_code'] == color)
        if mask_with_color.sum() > 0:
            mask = mask_with_color
            match_level = 'exact_3'
        else:
            match_level = 'exact_2'
    else:
        match_level = 'exact_2'

    candidates = dd[mask]

    if len(candidates) == 0:
        match_stats['no_match'] += 1
        matched_rows.append({
            'label_idx': idx,
            'match_level': 'no_match',
            'defect_id': None,
            'distance': None,
        })
        continue

    # Step 4: area range 필터 (퍼센타일 ± tolerance)
    area_lo = max(0, area_pctile - AREA_RANGE_TOL)
    area_hi = min(1, area_pctile + AREA_RANGE_TOL)
    range_mask = (candidates['area_mm2_pctile'] >= area_lo) & (candidates['area_mm2_pctile'] <= area_hi)
    range_candidates = candidates[range_mask]

    if len(range_candidates) > 0:
        match_stats['range_hit'] += 1
        pool = range_candidates
    else:
        # range 내 후보 없으면 전체 후보에서 거리 기반 선택
        match_stats['range_miss_fallback'] += 1
        pool = candidates

    match_stats[match_level] = match_stats.get(match_level, 0) + 1

    # Step 5: 거리 계산 (x, y, area 퍼센타일 유클리드 거리)
    dist = np.sqrt(
        (pool['x_position_mm_pctile'].values - cx_pctile) ** 2 +
        (pool['y_position_mm_pctile'].values - cy_pctile) ** 2 +
        (pool['area_mm2_pctile'].values - area_pctile) ** 2
    )

    best_idx = pool.index[np.argmin(dist)]
    best_dist = dist.min()

    matched_rows.append({
        'label_idx': idx,
        'match_level': match_level,
        'defect_id': dd.loc[best_idx, 'defect_id'],
        'inspection_id': dd.loc[best_idx, 'inspection_id'],
        'distance': round(best_dist, 4),
        'dd_defect_type': dd.loc[best_idx, 'defect_type_code'],
        'dd_zone': dd.loc[best_idx, 'zone_code'],
        'dd_color': dd.loc[best_idx, 'color_code'],
        'dd_severity': dd.loc[best_idx, 'severity'],
        'dd_rework': dd.loc[best_idx, 'rework_required'],
        'dd_rework_min': dd.loc[best_idx, 'estimated_rework_min'],
        'dd_area_mm2': dd.loc[best_idx, 'area_mm2'],
        'dd_x_mm': dd.loc[best_idx, 'x_position_mm'],
        'dd_y_mm': dd.loc[best_idx, 'y_position_mm'],
        'dd_confidence': dd.loc[best_idx, 'confidence'],
    })

    if (idx + 1) % 200 == 0:
        print(f'  {idx+1}/{len(label_df)} 처리 완료...')

match_df = pd.DataFrame(matched_rows)

# ── 4. 결과 합치기 ───────────────────────────────────────
result = pd.concat([label_df.reset_index(drop=True), match_df.reset_index(drop=True)], axis=1)

# ── 5. 결과 출력 ─────────────────────────────────────────
print('\n' + '='*60)
print('=== 매칭 통계 ===')
print(f'  총 라벨(bbox): {len(result)}건')
print(f'  매칭 성공:     {result["defect_id"].notna().sum()}건')
print(f'  매칭 실패:     {result["defect_id"].isna().sum()}건')

print(f'\n=== 매칭 레벨 ===')
print(result['match_level'].value_counts().to_string())

print(f'\n=== 매칭 프로세스 ===')
for k, v in match_stats.items():
    print(f'  {k}: {v}건')

print(f'\n=== 거리 통계 (낮을수록 좋음) ===')
dist_stats = result['distance'].dropna()
print(f'  mean: {dist_stats.mean():.4f}')
print(f'  median: {dist_stats.median():.4f}')
print(f'  min: {dist_stats.min():.4f}')
print(f'  max: {dist_stats.max():.4f}')
print(f'  std: {dist_stats.std():.4f}')

print(f'\n=== defect_type별 매칭 거리 ===')
print(result.groupby('defect_code')['distance']
      .agg(['mean', 'median', 'count']).round(4).to_string())

print(f'\n=== split별 ===')
print(result.groupby('split')['distance']
      .agg(['mean', 'count']).round(4).to_string())

print(f'\n=== 매칭 결과 severity 분포 ===')
print(result['dd_severity'].value_counts().to_string())

print(f'\n=== 매칭 결과 rework 분포 ===')
print(result['dd_rework'].value_counts().to_string())

print(f'\n=== defect_type별 평균 재작업 시간 (분) ===')
print(result.groupby('defect_code')['dd_rework_min']
      .agg(['mean', 'min', 'max']).round(1).to_string())

# 1:1 고유성 검증
dup = result['defect_id'].dropna()
dup_count = dup.duplicated().sum()
print(f'\n=== 1:1 고유성 ===')
print(f'  중복 매칭된 defect_id: {dup_count}건 ({dup_count/len(dup)*100:.1f}%)')
print(f'  고유 매칭:            {dup.nunique()}건 / {len(dup)}건')

# ── 6. 저장 ──────────────────────────────────────────────
save_cols = ['file', 'split', 'zone_raw', 'color_raw', 'defect_code',
             'bbox_cx', 'bbox_cy', 'bbox_area',
             'match_level', 'distance',
             'defect_id', 'inspection_id',
             'dd_defect_type', 'dd_zone', 'dd_color',
             'dd_severity', 'dd_rework', 'dd_rework_min',
             'dd_area_mm2', 'dd_x_mm', 'dd_y_mm', 'dd_confidence']
result[save_cols].to_csv('range_join_1to1_result.csv', index=False, encoding='utf-8-sig')
print(f'\n저장 완료: range_join_1to1_result.csv')
