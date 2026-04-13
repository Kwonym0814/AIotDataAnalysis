"""노트북에서 코드 및 마크다운 셀 내용을 추출"""
import json, sys

def extract_notebook(path, label):
    with open(path, encoding='utf-8') as f:
        nb = json.load(f)

    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    print(f"  커널: {nb.get('metadata',{}).get('kernelspec',{}).get('display_name','')}")
    print(f"  총 셀: {len(nb['cells'])}개\n")

    for i, cell in enumerate(nb['cells']):
        ct = cell['cell_type']
        src = ''.join(cell['source'])
        if not src.strip():
            continue
        if ct == 'markdown':
            print(f"--- [MD {i}] ---")
            print(src[:400])
            print()
        elif ct == 'code':
            print(f"--- [CODE {i}] ---")
            print(src[:800])
            print()

extract_notebook(r'C:\IT\workspace_python\KAMP\자동차도장_건조공정_이상탐지.ipynb',
                 '자동차도장_건조공정_이상탐지.ipynb')


