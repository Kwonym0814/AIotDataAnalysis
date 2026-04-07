# Range Join 매칭 규모 파악 (라벨 파일 기반)
> GitHub Copilot 전달용 | YOLO 추론 전 사전 검증용

---

## 1. 목적

val 라벨 파일(200장)을 정답 데이터로 활용하여
정형 데이터(defect_detail.csv)와의 Range Join 매칭 규모를 사전 파악한다.

- YOLO 추론 완료 전에 방법론 타당성을 미리 검증
- 매칭 규모가 충분하면 → YOLO 추론 결과로 동일 파이프라인 적용
- 매칭 규모가 부족하면 → 방법론 폐기, 브릿지 레이어만 사용

---

## 2. 데이터 경로

```
# 라벨 파일 (정답 데이터)
track_a_images/labels/val/         200개 (.txt, YOLO 형식)
track_a_images/images/val/         200장 (.jpg, 파일명에서 zone/color 추출)

# 정형 데이터
track_a_data/defect_detail.csv     170,904행
track_a_data/master_color.csv      15행
```

---

## 3. 사전 매핑 테이블

### 3-1. class_id → defect_type_code

```python
class_to_defect = {
    0: 'SCR',   # scratch
    1: 'DNT',   # dent
    2: 'PBB',   # paint_bubble
    3: 'PDR',   # paint_drip
    4: 'DCT',   # dust
    5: 'ORG',   # orange_peel
    6: 'CRK',   # crack
    7: 'GAP',   # gap_fault
}
```

### 3-2. zone → zone_code

```python
zone_to_code = {
    'bumper':     ['BUMPER_F', 'BUMPER_R'],  # 1:2 모호 — 둘 다 포함
    'fender':     ['FF', 'RF'],
    'front_door': ['FD'],
    'rear_door':  ['RD'],
    'hood':       ['HOOD'],
    'roof':       ['ROOF'],
    'trunk':      ['TRUNK'],
    'rocker':     ['ROCKER'],
}
```

### 3-3. color → color_code

```python
color_to_code = {
    'black':  'B3L',
    'white':  'P2W',
    'silver': 'SWP',
    'red':    'R4M',
    'blue':   'ABP',
    'gray':   'YW6',
    # green, navy, bronze → master_color.csv에 없으면 None
}
```

---

## 4. 구현 코드

```python
import pandas as pd
from pathlib import Path

# ── 0. 매핑 테이블 ────────────────────────────────────────
class_to_defect = {
    0: 'SCR', 1: 'DNT', 2: 'PBB', 3: 'PDR',
    4: 'DCT', 5: 'ORG', 6: 'CRK', 7: 'GAP',
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
dd = pd.read_csv('track_a_data/defect_detail.csv', encoding='utf-8-sig')
print(f'defect_detail 행 수: {len(dd)}')

# ── 2. val 라벨 파일 파싱 ─────────────────────────────────
label_dir = Path('track_a_images/labels/val')
records = []

for txt_file in sorted(label_dir.glob('*.txt')):
    lines = txt_file.read_text().strip().splitlines()
    if not lines:
        continue  # 빈 파일(Negative sample) 스킵

    # 파일명에서 zone, color 추출
    parts = txt_file.stem.split('_')
    if 'pearl' in parts:
        pearl_idx = parts.index('pearl')
        zone = '_'.join(parts[:pearl_idx])   # pearl 제거하여 zone 매핑
        color = parts[pearl_idx + 1]
    else:
        zone = parts[0]
        color = parts[1]

    for line in lines:
        cls_id, cx, cy, w, h = map(float, line.split())
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
print(label_df['defect_code'].value_counts())

# ── 3. zone, color 코드 매핑 ──────────────────────────────
label_df['zone_codes'] = label_df['zone_raw'].map(
    lambda z: zone_to_code.get(z, [None])
)
label_df['color_code'] = label_df['color_raw'].map(color_to_code)

print('\n=== color 매핑 결과 ===')
print(label_df[['color_raw', 'color_code']].drop_duplicates())

# ── 4. Range Join 매칭 (조건별 3단계) ────────────────────
# 조건 1: defect_type만
# 조건 2: defect_type + zone
# 조건 3: defect_type + zone + color (color 없으면 스킵)

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

    # 조건 3: defect_type + zone + color (inspection_master 조인 필요 — 우선 생략)
    count3 = None  # 추후 inspection_master JOIN 후 추가 가능

    results.append({
        'file':         row['file'],
        'defect_code':  defect,
        'zone_raw':     row['zone_raw'],
        'color_raw':    row['color_raw'],
        'matched_defect_only':      count1,
        'matched_defect_zone':      count2,
    })

result_df = pd.DataFrame(results)

# ── 5. 매칭 규모 출력 ────────────────────────────────────
print('\n' + '='*50)
print('=== 조건 1: defect_type만 ===')
print(result_df['matched_defect_only'].describe().round(1))

print('\n=== 조건 2: defect_type + zone ===')
print(result_df['matched_defect_zone'].describe().round(1))

print('\n=== 결함 유형별 평균 매칭 수 (조건 2) ===')
print(result_df.groupby('defect_code')['matched_defect_zone']
      .mean().round(1).sort_values())

print('\n=== zone별 평균 매칭 수 (조건 2) ===')
print(result_df.groupby('zone_raw')['matched_defect_zone']
      .mean().round(1).sort_values())

print('\n=== 매칭 0건 비율 ===')
zero_count = (result_df['matched_defect_zone'] == 0).sum()
total = len(result_df)
print(f'0건: {zero_count}/{total} ({zero_count/total*100:.1f}%)')

# ── 6. 결과 저장 ─────────────────────────────────────────
result_df.to_csv('range_join_match_result.csv', index=False, encoding='utf-8-sig')
print('\n저장 완료: range_join_match_result.csv')
```

---

## 5. 판단 기준

| 지표 | 기준 | 판단 |
|---|---|---|
| 조건 2 평균 매칭 수 | > 100건 | 방법론 진행 가능 |
| 매칭 0건 비율 | < 10% | 허용 범위 |
| 클래스별 편차 | 크지 않을수록 좋음 | 균등성 확인 |

---

## 6. 결과에 따른 다음 단계

```
매칭 규모 충분
      ↓
EXP-03 완료 후 YOLO 실제 추론 결과로 동일 파이프라인 적용
      ↓
매핑된 정형 데이터 + master_defect_type JOIN → 재작업 비용 산출

매칭 규모 부족 (0건 비율 높거나 평균 매칭 수 < 100)
      ↓
Range Join 방법론 폐기
      ↓
브릿지 레이어만 사용 (YOLO 탐지 결과 × master_defect_type → 재작업 비용)
```
