#!/bin/bash

echo "========================================"
echo "  라벨 데이터 수 검증"
echo "========================================"

# 전체 파일 수
total=$(ls dataset/track_a_images/labels/train/*.txt dataset/track_a_images/labels/val/*.txt 2>/dev/null | wc -l)
echo ""
echo "=== 전체 파일 수 ==="
echo "  $total 개"

# 빈 파일 수 (Negative sample)
empty=$(find dataset/track_a_images/labels/train dataset/track_a_images/labels/val -name "*.txt" -empty | wc -l)
echo ""
echo "=== 빈 파일 수 (Negative sample) ==="
echo "  $empty 개"

# 결함 있는 파일 수
positive=$(find dataset/track_a_images/labels/train dataset/track_a_images/labels/val -name "*.txt" ! -empty | wc -l)
echo ""
echo "=== 결함 있는 파일 수 (Positive sample) ==="
echo "  $positive 개"

# 전체 결함(라벨) 수
# awk 'NF' : 비어 있지 않은 줄만, END {print lines} : 마지막 줄 \n 없어도 정확히 카운트
defects=$(awk 'NF {lines++} END {print lines+0}' \
    dataset/track_a_images/labels/train/*.txt \
    dataset/track_a_images/labels/val/*.txt 2>/dev/null)
echo ""
echo "=== 전체 결함(라벨) 수 ==="
echo "  $defects 개"

# split별 통계
echo ""
echo "=== split별 상세 ==="
train_total=$(ls dataset/track_a_images/labels/train/*.txt 2>/dev/null | wc -l)
train_empty=$(find dataset/track_a_images/labels/train -name "*.txt" -empty | wc -l)
train_positive=$(find dataset/track_a_images/labels/train -name "*.txt" ! -empty | wc -l)
train_defects=$(awk 'NF {lines++} END {print lines+0}' \
    dataset/track_a_images/labels/train/*.txt 2>/dev/null)

val_total=$(ls dataset/track_a_images/labels/val/*.txt 2>/dev/null | wc -l)
val_empty=$(find dataset/track_a_images/labels/val -name "*.txt" -empty | wc -l)
val_positive=$(find dataset/track_a_images/labels/val -name "*.txt" ! -empty | wc -l)
val_defects=$(awk 'NF {lines++} END {print lines+0}' \
    dataset/track_a_images/labels/val/*.txt 2>/dev/null)

echo "  [train] 전체: $train_total | 빈 파일: $train_empty | 결함 있는 파일: $train_positive | 결함 수: $train_defects"
echo "  [val]   전체: $val_total   | 빈 파일: $val_empty   | 결함 있는 파일: $val_positive   | 결함 수: $val_defects"

# 검증
echo ""
echo "========================================"
echo "  검증"
echo "========================================"

sum_files=$((empty + positive))
echo ""
echo "  빈 파일($empty) + 결함 있는 파일($positive) = $sum_files"
if [ "$sum_files" -eq "$total" ]; then
    echo "  ✅ PASS: 합산($sum_files) = 전체 파일 수($total)"
else
    echo "  ❌ FAIL: 합산($sum_files) ≠ 전체 파일 수($total)"
fi

echo ""
echo "  [참고] 결함 수($defects) ≠ 전체 파일 수($total)"
echo "  → 한 파일에 결함 여러 개 가능하므로 정상"
echo "========================================"
