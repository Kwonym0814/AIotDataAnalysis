from pathlib import Path

LABEL_TRAIN = Path('./dataset/track_a_images/labels/train')
LABEL_VAL   = Path('./dataset/track_a_images/labels/val')

train_files = list(LABEL_TRAIN.glob('*.txt'))
val_files   = list(LABEL_VAL.glob('*.txt'))

def count_labels(files):
    total, empty, positive, defects = 0, 0, 0, 0
    for f in files:
        total += 1
        lines = [l for l in f.read_text().strip().splitlines() if l.strip()]
        if not lines:
            empty += 1
        else:
            positive += 1
            defects += len(lines)
    return total, empty, positive, defects

tr_total, tr_empty, tr_pos, tr_def = count_labels(train_files)
vl_total, vl_empty, vl_pos, vl_def = count_labels(val_files)

print(f'[train] 전체: {tr_total} | 빈 파일: {tr_empty} | 결함 있는 파일: {tr_pos} | 결함 수: {tr_def}')
print(f'[val]   전체: {vl_total} | 빈 파일: {vl_empty} | 결함 있는 파일: {vl_pos} | 결함 수: {vl_def}')
print(f'[전체]  전체: {tr_total+vl_total} | 빈 파일: {tr_empty+vl_empty} | 결함 있는 파일: {tr_pos+vl_pos} | 결함 수: {tr_def+vl_def}')

