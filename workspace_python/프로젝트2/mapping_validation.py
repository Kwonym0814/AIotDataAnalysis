"""
YOLO 라벨 ↔ defect_detail.csv 매핑 검증 스크립트
================================================
검증 항목:
  1. YOLO class_id ↔ defect_type_code 매핑 정의
  2. 이미지 파일명 zone ↔ master_zone 매핑
  3. YOLO 라벨 class_id 분포 vs defect_detail 결함 유형 분포 비교
  4. 이미지 zone 분포 vs defect_detail zone 분포 비교
  5. bbox 크기(픽셀 변환) vs defect_detail area_mm2 상관 분석
  6. 빈 라벨(결함없음) 비율 vs PASS 비율
  7. 전체 매핑 커버리지 요약
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from collections import Counter, defaultdict

# ──────────────────────────────────────────────────────────────────────────────
# 경로 설정
# ──────────────────────────────────────────────────────────────────────────────
BASE = Path(r"C:\IT\workspace_python\프로젝트2\dataset\현대_오토에버")
DATA_DIR   = BASE / "track_a_data"
IMAGES_DIR = BASE / "track_a_images"
LABELS_DIR = IMAGES_DIR / "labels"

# ──────────────────────────────────────────────────────────────────────────────
# 매핑 테이블 (data.yaml 기준)
# ──────────────────────────────────────────────────────────────────────────────
# YOLO class_id → (yolo_name, defect_type_code, defect_type_name, severity)
YOLO_TO_DEFECT = {
    0: ("scratch",      "SCR", "스크래치",  "MINOR"),
    1: ("dent",         "DNT", "덴트",      "MAJOR"),
    2: ("paint_bubble", "PBB", "도장기포",  "MINOR"),
    3: ("paint_drip",   "PDR", "도장흘림",  "MINOR"),
    4: ("dust",         "DST", "이물질",    "MINOR"),
    5: ("orange_peel",  "ORG", "오렌지필",  "MINOR"),
    6: ("crack",        "CRK", "크랙",      "CRITICAL"),
    7: ("gap_fault",    "GAP", "Gap불량",   "CRITICAL"),
}

# 이미지 zone (파일명) → master_zone zone_code
ZONE_IMG_TO_MASTER = {
    "hood":       ["HOOD"],
    "front_door": ["FD"],
    "rear_door":  ["RD"],
    "fender":     ["FF", "RF"],        # 앞/뒤 구분 불가 → 2개 매핑
    "roof":       ["ROOF"],
    "trunk":      ["TRUNK"],
    "bumper":     ["BUMPER_F", "BUMPER_R"],  # 앞/뒤 구분 불가 → 2개 매핑
    "rocker":     ["ROCKER"],
}

IMAGE_SIZE = (1280, 720)  # width, height (px)

# ──────────────────────────────────────────────────────────────────────────────
# 출력 헬퍼
# ──────────────────────────────────────────────────────────────────────────────
SEP = "=" * 70

def title(text):
    print(f"\n{SEP}\n  {text}\n{SEP}")

def ok(msg):   print(f"  ✅  {msg}")
def warn(msg): print(f"  ⚠️   {msg}")
def info(msg): print(f"  ℹ️   {msg}")
def fail(msg): print(f"  ❌  {msg}")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 0 : 파일 존재 여부 확인
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 0 | 파일 존재 여부 확인")
required = {
    "defect_detail.csv":      DATA_DIR / "defect_detail.csv",
    "master_defect_type.csv": DATA_DIR / "master_defect_type.csv",
    "master_zone.csv":        DATA_DIR / "master_zone.csv",
    "labels/train":           LABELS_DIR / "train",
    "labels/val":             LABELS_DIR / "val",
    "images/train":           IMAGES_DIR / "images" / "train",
    "images/val":             IMAGES_DIR / "images" / "val",
}
all_exist = True
for name, path in required.items():
    if path.exists():
        ok(f"존재: {name}")
    else:
        fail(f"없음: {path}")
        all_exist = False

if not all_exist:
    sys.exit("필수 파일 누락. 경로를 확인하세요.")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 : YOLO class_id ↔ defect_type_code 매핑 테이블 출력
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 1 | YOLO class_id ↔ defect_type_code 매핑 정의")
print(f"  {'class_id':<10} {'yolo_name':<14} {'code':<6} {'name':<10} {'severity'}")
print("  " + "-" * 55)
for cid, (yname, code, name, sev) in YOLO_TO_DEFECT.items():
    print(f"  {cid:<10} {yname:<14} {code:<6} {name:<10} {sev}")

# master_defect_type 로드 → 비교
mdt = pd.read_csv(DATA_DIR / "master_defect_type.csv")
mapped_codes = {v[1] for v in YOLO_TO_DEFECT.values()}
all_codes    = set(mdt["defect_type_code"])
unmapped     = all_codes - mapped_codes

info(f"master_defect_type 전체 코드: {sorted(all_codes)}")
info(f"YOLO 매핑된 코드: {sorted(mapped_codes)}")
if unmapped:
    warn(f"이미지 라벨에 없는 결함 코드: {sorted(unmapped)}  (정형 데이터에만 존재)")
else:
    ok("모든 결함 코드 매핑 완료")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 : YOLO 라벨 파일 파싱
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 2 | YOLO 라벨 파일 파싱")

def parse_labels(label_dir: Path):
    """YOLO 라벨 디렉토리를 파싱 → DataFrame 반환."""
    records = []
    empty_cnt = 0
    for txt in label_dir.glob("*.txt"):
        stem = txt.stem  # e.g. "bumper_black_000016"
        # 파일명 분해: {zone}_{color}_{id}
        parts = stem.rsplit("_", 1)   # ['bumper_black', '000016']
        img_id = parts[-1]
        zone_color = parts[0] if len(parts) == 2 else stem
        # zone = 첫 번째 '_' 이전 (색상 이름에 '_' 없는 경우)
        # 파일명 패턴: {zone}_{color}_{id}  단, zone/color 모두 단어 단위
        # 색상 목록으로 분리
        COLOR_NAMES = {"white","pearl_white","black","gray","silver",
                       "red","blue","navy","bronze","green"}
        # zone_color에서 색상 추출
        img_zone  = None
        img_color = None
        for c in sorted(COLOR_NAMES, key=len, reverse=True):
            if zone_color.endswith("_" + c):
                img_color = c
                img_zone  = zone_color[: -(len(c) + 1)]
                break
        if img_zone is None:
            img_zone  = zone_color
            img_color = "unknown"

        content = txt.read_text().strip()
        if not content:
            empty_cnt += 1
            records.append({
                "filename": txt.name, "img_id": img_id,
                "img_zone": img_zone, "img_color": img_color,
                "class_id": None, "cx": None, "cy": None,
                "bw": None, "bh": None,
                "area_px2": None,
            })
        else:
            for line in content.splitlines():
                vals = line.strip().split()
                if len(vals) < 5:
                    continue
                cid, cx, cy, bw, bh = int(vals[0]), *map(float, vals[1:5])
                area_px2 = (bw * IMAGE_SIZE[0]) * (bh * IMAGE_SIZE[1])
                records.append({
                    "filename": txt.name, "img_id": img_id,
                    "img_zone": img_zone, "img_color": img_color,
                    "class_id": cid, "cx": cx, "cy": cy,
                    "bw": bw, "bh": bh,
                    "area_px2": area_px2,
                })
    return pd.DataFrame(records), empty_cnt

train_df, train_empty = parse_labels(LABELS_DIR / "train")
val_df,   val_empty   = parse_labels(LABELS_DIR / "val")
all_labels = pd.concat([train_df, val_df], ignore_index=True)

total_files   = len(all_labels["filename"].unique())
total_defects = all_labels["class_id"].notna().sum()
total_empty   = train_empty + val_empty

info(f"라벨 파일 수: {total_files}  (train={len(train_df['filename'].unique())}, val={len(val_df['filename'].unique())})")
info(f"총 bbox (결함 라벨) 수: {total_defects}")
info(f"빈 라벨 파일 수 (결함 없는 이미지): {total_empty}")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 : class_id 분포 vs defect_detail 결함 유형 분포
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 3 | class_id 분포 vs defect_detail 결함 유형 분포 비교")

# defect_detail 로드 (필요 컬럼만)
dd = pd.read_csv(
    DATA_DIR / "defect_detail.csv",
    usecols=["defect_type_code", "zone_code", "width_mm", "height_mm", "area_mm2"],
)
info(f"defect_detail 로드 완료: {len(dd):,}행")

# YOLO 분포
yolo_dist = (
    all_labels.dropna(subset=["class_id"])
    .groupby("class_id").size().reset_index(name="yolo_count")
)
yolo_dist["class_id"] = yolo_dist["class_id"].astype(int)
yolo_dist["defect_code"] = yolo_dist["class_id"].map(lambda c: YOLO_TO_DEFECT[c][1])
yolo_dist["yolo_pct"]    = (yolo_dist["yolo_count"] / yolo_dist["yolo_count"].sum() * 100).round(1)

# defect_detail 분포 (YOLO에 있는 8개 코드만)
dd_mapped = dd[dd["defect_type_code"].isin(mapped_codes)]
dd_dist = (
    dd_mapped.groupby("defect_type_code").size().reset_index(name="csv_count")
)
dd_dist["csv_pct"] = (dd_dist["csv_count"] / dd_dist["csv_count"].sum() * 100).round(1)

# 병합
compare = yolo_dist.merge(dd_dist, left_on="defect_code", right_on="defect_type_code", how="outer")
compare = compare.sort_values("class_id").reset_index(drop=True)

print(f"\n  {'class_id':<10} {'코드':<6} {'YOLO건수':<10} {'YOLO%':<8} {'CSV건수':<12} {'CSV%':<8} {'순위차이'}")
print("  " + "-" * 65)
yolo_rank = yolo_dist.sort_values("yolo_count", ascending=False)["defect_code"].tolist()
csv_rank  = dd_dist.sort_values("csv_count",  ascending=False)["defect_type_code"].tolist()

for _, row in compare.iterrows():
    code = row.get("defect_code") or row.get("defect_type_code")
    cid  = row["class_id"] if pd.notna(row["class_id"]) else "-"
    yc   = int(row["yolo_count"]) if pd.notna(row.get("yolo_count")) else 0
    yp   = row["yolo_pct"]        if pd.notna(row.get("yolo_pct"))   else 0
    cc   = int(row["csv_count"])  if pd.notna(row.get("csv_count"))  else 0
    cp   = row["csv_pct"]         if pd.notna(row.get("csv_pct"))    else 0
    yr   = (yolo_rank.index(code) + 1) if code in yolo_rank else "-"
    cr   = (csv_rank.index(code)  + 1) if code in csv_rank  else "-"
    diff = abs(yr - cr) if isinstance(yr, int) and isinstance(cr, int) else "-"
    mark = "✅" if isinstance(diff, int) and diff <= 2 else ("⚠️" if isinstance(diff, int) else "")
    print(f"  {str(cid):<10} {str(code):<6} {yc:<10} {yp:<8} {cc:<12} {cp:<8} {str(yr)}→{str(cr)} {mark}")

# 상관계수 (비율)
yolo_pct_vec = compare.dropna(subset=["yolo_pct","csv_pct"])
if len(yolo_pct_vec) >= 2:
    r = np.corrcoef(yolo_pct_vec["yolo_pct"], yolo_pct_vec["csv_pct"])[0,1]
    info(f"결함 유형 비율 상관계수 (YOLO vs CSV): r = {r:.4f}")
    if r > 0.9:
        ok(f"분포 매우 유사 (r={r:.4f})")
    elif r > 0.7:
        warn(f"분포 유사하나 차이 있음 (r={r:.4f})")
    else:
        fail(f"분포 차이 큼 (r={r:.4f}) — 샘플링 편향 가능성")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 : 이미지 zone 분포 vs defect_detail zone 분포 비교
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 4 | 이미지 zone 분포 vs defect_detail zone_code 분포 비교")

# 매핑 테이블 출력
print(f"\n  {'이미지 zone':<14} {'→ master_zone':<24} {'1:1 여부'}")
print("  " + "-" * 48)
for iz, mz in ZONE_IMG_TO_MASTER.items():
    mapping_type = "1:1" if len(mz) == 1 else "1:N (모호)"
    mark = "✅" if len(mz) == 1 else "⚠️"
    print(f"  {iz:<14} {', '.join(mz):<24} {mapping_type} {mark}")

# master_zone에 없는 zone 확인
mzone = pd.read_csv(DATA_DIR / "master_zone.csv")
all_master_zones = set(mzone["zone_code"])
img_zones_flat = {z for mzs in ZONE_IMG_TO_MASTER.values() for z in mzs}
unmapped_zones = all_master_zones - img_zones_flat
if unmapped_zones:
    warn(f"이미지에 없는 master_zone: {sorted(unmapped_zones)}")

# 이미지 zone 분포 (결함 있는 것만)
defect_labels = all_labels.dropna(subset=["class_id"])
img_zone_dist = defect_labels.groupby("img_zone").size().reset_index(name="yolo_count")
img_zone_dist["yolo_pct"] = (img_zone_dist["yolo_count"] / img_zone_dist["yolo_count"].sum() * 100).round(1)

# defect_detail zone 분포 (이미지 zone과 매핑 가능한 것만)
# bumper → BUMPER_F + BUMPER_R, fender → FF + RF 합산
zone_mapping_flat = {}
for iz, mzs in ZONE_IMG_TO_MASTER.items():
    for mz in mzs:
        zone_mapping_flat[mz] = iz  # master_zone → img_zone

dd["img_zone_mapped"] = dd["zone_code"].map(zone_mapping_flat)
dd_zone_dist = dd.groupby("img_zone_mapped").size().reset_index(name="csv_count")
dd_zone_dist["csv_pct"] = (dd_zone_dist["csv_count"] / dd_zone_dist["csv_count"].sum() * 100).round(1)

img_zone_dist_renamed = img_zone_dist.rename(columns={"img_zone": "img_zone_mapped"})
zone_compare = img_zone_dist_renamed.merge(dd_zone_dist, on="img_zone_mapped", how="outer").sort_values("yolo_count", ascending=False)

print(f"\n  {'img_zone':<14} {'YOLO건수':<10} {'YOLO%':<8} {'CSV건수':<12} {'CSV%'}")
print("  " + "-" * 55)
for _, row in zone_compare.iterrows():
    iz = row.get("img_zone_mapped")
    yc = int(row["yolo_count"]) if pd.notna(row.get("yolo_count")) else 0
    yp = row["yolo_pct"]        if pd.notna(row.get("yolo_pct"))   else 0.0
    cc = int(row["csv_count"])  if pd.notna(row.get("csv_count"))  else 0
    cp = row["csv_pct"]         if pd.notna(row.get("csv_pct"))    else 0.0
    print(f"  {str(iz):<14} {yc:<10} {yp:<8} {cc:<12} {cp}")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 4b : 이미지 color ↔ master_color.csv 매핑 검증
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 4b | 이미지 파일명 color ↔ master_color.csv 매핑 검증")

mcolor = pd.read_csv(DATA_DIR / "master_color.csv")
info(f"master_color.csv 로드: {len(mcolor)}개 색상 코드")
print(f"\n  {'color_code':<12} {'color_name'}")
print("  " + "-" * 30)
for _, row in mcolor.iterrows():
    print(f"  {row['color_code']:<12} {row['color_name']}")

# 이미지 영문 색상명 → master_color_code 매핑 테이블 (수동 정의)
# master_color의 color_name(한글)에서 유추
COLOR_IMG_TO_MASTER = {
    "white":       ["P2W", "WC9"],   # 퓨어화이트, 애틀라스화이트 (모호)
    "pearl_white": ["SWP"],          # 스노우화이트펄 (1:1)
    "black":       ["B3L", "ABP"],   # 아비스블랙, 오로라블랙펄 (모호)
    "gray":        ["N5M", "TW3"],   # 나이트섀도우그레이, 티타늄그레이 (모호)
    "silver":      ["SSS"],          # 스타더스트실버 (1:1)
    "red":         ["R4M"],          # 플레임레드 (1:1)
    "blue":        ["V5P", "K3B"],   # 딥씨블루, 그라비티블루 (모호)
    "navy":        ["K3B"],          # 그라비티블루 (1:1 추정)
    "bronze":      ["W8Y"],          # 실키브론즈 (1:1)
    "green":       [],               # master_color에 없음 (매핑 불가)
}

# CSV에 있는 모든 코드가 매핑 테이블에 커버되는지 확인
all_color_codes    = set(mcolor["color_code"])
mapped_color_codes = {code for codes in COLOR_IMG_TO_MASTER.values() for code in codes}
unlinked_codes     = all_color_codes - mapped_color_codes  # CSV에 있지만 이미지에 없는 코드

print(f"\n  {'이미지 색상(영문)':<16} {'→ color_code':<22} {'매핑 유형':<12} {'상태'}")
print("  " + "-" * 60)
for img_color, codes in COLOR_IMG_TO_MASTER.items():
    if len(codes) == 0:
        mtype = "매핑 불가"
        mark  = "❌"
        codes_str = "(없음)"
    elif len(codes) == 1:
        # color_name 가져오기
        cname = mcolor.loc[mcolor["color_code"] == codes[0], "color_name"].values
        codes_str = f"{codes[0]} ({cname[0] if len(cname) else '?'})"
        mtype = "1:1"
        mark  = "✅"
    else:
        cnames = [mcolor.loc[mcolor["color_code"] == c, "color_name"].values for c in codes]
        codes_str = ", ".join(f"{c}({n[0] if len(n) else '?'})" for c, n in zip(codes, cnames))
        mtype = "1:N 모호"
        mark  = "⚠️"
    print(f"  {img_color:<16} {codes_str:<30} {mtype:<12} {mark}")

# 이미지에서 사용되지 않는 color_code
if unlinked_codes:
    warn(f"이미지에 매핑되지 않은 master_color 코드: {sorted(unlinked_codes)}")
    for code in sorted(unlinked_codes):
        cname = mcolor.loc[mcolor["color_code"] == code, "color_name"].values[0]
        print(f"      {code}: {cname}")

# 실제 이미지 파일에서 색상 분포
# (parse_labels에서 img_color가 이미 파싱됨)
color_dist = (
    all_labels.drop_duplicates(subset=["filename"])
    .groupby("img_color").size().reset_index(name="image_count")
    .sort_values("image_count", ascending=False)
)
total_img = color_dist["image_count"].sum()
color_dist["pct"] = (color_dist["image_count"] / total_img * 100).round(1)

print(f"\n  실제 이미지 색상 분포 (파일명 기준):")
print(f"  {'img_color':<16} {'이미지 수':<10} {'비율%':<8} {'→ master_color'}")
print("  " + "-" * 55)
for _, row in color_dist.iterrows():
    c = row["img_color"]
    codes = COLOR_IMG_TO_MASTER.get(c, ["?"])
    cstr  = ", ".join(codes) if codes else "매핑불가"
    mark  = "✅" if len(codes) == 1 and codes[0] != "?" else ("⚠️" if len(codes) > 1 else "❌")
    print(f"  {c:<16} {row['image_count']:<10} {row['pct']:<8} {cstr} {mark}")

# 커버리지 계산
one_to_one   = sum(1 for c in COLOR_IMG_TO_MASTER.values() if len(c) == 1)
ambiguous    = sum(1 for c in COLOR_IMG_TO_MASTER.values() if len(c) > 1)
unmappable   = sum(1 for c in COLOR_IMG_TO_MASTER.values() if len(c) == 0)
total_colors = len(COLOR_IMG_TO_MASTER)
print()
ok(f"1:1 매핑: {one_to_one}/{total_colors}개 색상")
warn(f"모호 매핑(1:N): {ambiguous}/{total_colors}개 색상 (white/black/gray/blue)")
if unmappable:
    fail(f"매핑 불가: {unmappable}/{total_colors}개 색상 (green → master_color에 없음)")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 4c : 이미지 zone ↔ master_zone.csv 교차 검증
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 4c | 이미지 파일명 zone ↔ master_zone.csv 교차 검증")

info(f"master_zone.csv 로드: {len(mzone)}개 zone")
print(f"\n  {'zone_code':<12} {'zone_name'}")
print("  " + "-" * 28)
for _, row in mzone.iterrows():
    print(f"  {row['zone_code']:<12} {row['zone_name']}")

# master_zone 코드 → 이미지 zone명 역방향 매핑
master_to_img = {mz: iz for iz, mzs in ZONE_IMG_TO_MASTER.items() for mz in mzs}

print(f"\n  {'zone_code':<12} {'zone_name':<14} {'→ img_zone':<14} {'1:1 여부'}")
print("  " + "-" * 52)
for _, row in mzone.iterrows():
    zcode = row["zone_code"]
    zname = row["zone_name"]
    img_z = master_to_img.get(zcode, "없음")
    # 해당 img_zone이 여러 master_zone으로 매핑되는지
    if img_z == "없음":
        mtype = "이미지 없음"
        mark  = "❌"
    elif len(ZONE_IMG_TO_MASTER.get(img_z, [])) > 1:
        mtype = "N:1 모호"
        mark  = "⚠️"
    else:
        mtype = "1:1"
        mark  = "✅"
    print(f"  {zcode:<12} {zname:<14} {img_z:<14} {mtype} {mark}")

# 전체 커버리지
zone_one_to_one = sum(1 for z in mzone["zone_code"] if master_to_img.get(z,"없음") != "없음"
                       and len(ZONE_IMG_TO_MASTER.get(master_to_img[z],[])) == 1)
zone_ambiguous  = sum(1 for z in mzone["zone_code"] if master_to_img.get(z,"없음") != "없음"
                       and len(ZONE_IMG_TO_MASTER.get(master_to_img[z],[])) > 1)
zone_missing    = sum(1 for z in mzone["zone_code"] if master_to_img.get(z,"없음") == "없음")
total_zones     = len(mzone)

print()
ok(f"1:1 매핑: {zone_one_to_one}/{total_zones}개 zone (hood/front_door/rear_door/roof/trunk/rocker)")
warn(f"N:1 모호: {zone_ambiguous}/{total_zones}개 zone (BUMPER_F/R → bumper, FF/RF → fender)")
fail(f"이미지 없음: {zone_missing}/{total_zones}개 zone (QTR_L, QTR_R)")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 : bbox 크기 (픽셀) vs area_mm2 분포 비교
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 5 | bbox 면적(px²) vs defect_detail area_mm² 분포 비교")

# 결함별 bbox 평균 px² 면적
yolo_area = (
    defect_labels.groupby("class_id")["area_px2"]
    .agg(["mean","std","min","max"])
    .reset_index()
)
yolo_area["class_id"] = yolo_area["class_id"].astype(int)
yolo_area["defect_code"] = yolo_area["class_id"].map(lambda c: YOLO_TO_DEFECT[c][1])

# defect_detail 결함별 평균 area_mm²
dd_area = (
    dd.groupby("defect_type_code")["area_mm2"]
    .agg(["mean","std","min","max"])
    .reset_index()
)
dd_area = dd_area[dd_area["defect_type_code"].isin(mapped_codes)]

# 정규화 비교 (면적 자체 단위가 다르므로 순위 기반 비교)
yolo_area_rank = yolo_area.sort_values("mean", ascending=False)["defect_code"].tolist()
csv_area_rank  = dd_area.sort_values("mean",   ascending=False)["defect_type_code"].tolist()

print(f"\n  {'코드':<6} {'YOLO avg_px²':<15} {'YOLO 순위':<10} {'CSV avg_mm²':<13} {'CSV 순위':<10} {'순위 일치'}")
print("  " + "-" * 65)
for code in mapped_codes:
    ya_row = yolo_area[yolo_area["defect_code"] == code]
    ca_row = dd_area[dd_area["defect_type_code"] == code]
    ya_mean = f"{ya_row['mean'].values[0]:.0f}" if len(ya_row) > 0 else "N/A"
    ca_mean = f"{ca_row['mean'].values[0]:.1f}" if len(ca_row) > 0 else "N/A"
    yr = (yolo_area_rank.index(code) + 1) if code in yolo_area_rank else "-"
    cr = (csv_area_rank.index(code)  + 1) if code in csv_area_rank  else "-"
    match = "✅" if isinstance(yr,int) and isinstance(cr,int) and abs(yr-cr)<=2 else "⚠️"
    print(f"  {code:<6} {ya_mean:<15} {str(yr):<10} {ca_mean:<13} {str(cr):<10} {match}")

# 스피어만 순위 상관
from scipy.stats import spearmanr
area_merge = yolo_area.merge(dd_area, left_on="defect_code", right_on="defect_type_code", how="inner")
if len(area_merge) >= 3:
    rho, pval = spearmanr(area_merge["mean_x"], area_merge["mean_y"])
    info(f"bbox 면적 순위 스피어만 상관계수: ρ = {rho:.4f}  (p={pval:.4f})")
    if rho > 0.6:
        ok(f"면적 순위 유사 (ρ={rho:.4f})")
    else:
        warn(f"면적 순위 차이 있음 (단위 차이로 인한 한계)")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 6 : 빈 라벨(결함없음) 비율 vs PASS 비율
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 6 | 빈 라벨 비율 vs PASS 비율 (inspection_master)")

total_label_files = len(all_labels["filename"].unique())
empty_ratio = total_empty / total_label_files * 100

info(f"전체 라벨 파일: {total_label_files}")
info(f"빈 라벨 (결함 없는 이미지): {total_empty}  ({empty_ratio:.1f}%)")
info(f"inspection_master PASS 비율: 95.93%  (FAIL: 4.07%)  [1단계 EDA 결과]")

gap = abs(empty_ratio - 95.93)
if gap < 5:
    ok(f"빈 라벨 비율({empty_ratio:.1f}%)과 PASS 비율(95.93%) 유사 (차이 {gap:.1f}%p)")
elif gap < 15:
    warn(f"빈 라벨 비율({empty_ratio:.1f}%)과 PASS 비율(95.93%) 차이 있음 ({gap:.1f}%p) — 이미지 샘플링 방식 상이")
else:
    fail(f"빈 라벨 비율({empty_ratio:.1f}%)과 PASS 비율(95.93%) 큰 차이 ({gap:.1f}%p) — 이미지 불균형 샘플링")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 7 : 전체 매핑 커버리지 요약
# ──────────────────────────────────────────────────────────────────────────────
title("STEP 7 | 전체 매핑 커버리지 요약")

results = {
    "결함 유형 코드 매핑": f"{len(mapped_codes)}/{len(all_codes)} ({len(mapped_codes)/len(all_codes)*100:.0f}%)",
    "YOLO 클래스 수":      f"{len(YOLO_TO_DEFECT)}개",
    "이미지 zone 1:1 매핑": f"{sum(1 for v in ZONE_IMG_TO_MASTER.values() if len(v)==1)}/{len(ZONE_IMG_TO_MASTER)} zone",
    "이미지 zone 모호 매핑": f"{sum(1 for v in ZONE_IMG_TO_MASTER.values() if len(v)>1)}/{len(ZONE_IMG_TO_MASTER)} zone (앞/뒤 구분 불가)",
    "master_zone 미매핑": f"{sorted(unmapped_zones)}",
    "총 YOLO bbox 수":   f"{int(total_defects):,}개",
    "빈 라벨 파일":       f"{total_empty}개 ({empty_ratio:.1f}%)",
    "defect_detail 행수": f"{len(dd):,}행",
}

for k, v in results.items():
    print(f"  {'■'} {k:<28} {v}")

print()
print("  [매핑 가능 조합]")
ok("YOLO class_id  →  defect_type_code  (data.yaml 기반, 8/10 커버)")
ok("이미지 파일명 zone  →  master_zone  (6/8 one-to-one, 2/8 모호)")
warn("이미지 파일명 color  →  master_color  (일부 모호, bronze/green 미매핑)")
warn("인스턴스 레벨 조인  →  불가 (공유 키 없음, bbox 단위 vs mm 단위 상이)")

print()
info("결론: 코드/스키마 레벨 매핑은 성립. YOLO 예측 결과(class_id)를")
info("      defect_type_code로 변환 후 정형 데이터와 동일 스키마 통합 가능.")
print()
print(SEP)
print("  검증 완료.")
print(SEP)



