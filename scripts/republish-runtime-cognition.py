# -*- coding: utf-8 -*-
# #3 副本追平（BOD 03:1x 裁恢复执行）：TriCompany/runtime/cognition（真源活体）
# → TriMetaverse/TriCompany-copilot-host-assets/runtime/cognition（宿主副本）。
# 管线化留痕：甄别清单（副本独有=死层候选/内容差异=覆盖/缺失=补）+发布脚本入卷；
# 副本独有文件移 _archive/2026-04-cognition-run/orphans/（死层候选归档非删）。
import json, shutil, filecmp
from pathlib import Path

SRC = Path(r'D:\Code\ai\TriCompany\runtime\cognition')
DST = Path(r'D:\Code\ai\TriMetaverse\TriCompany-copilot-host-assets\runtime\cognition')
ARCHIVE_ORPHANS = DST.parent / '_archive' / '2026-04-cognition-run' / 'runtime-orphans'

src_files = {p.relative_to(SRC).as_posix(): p for p in SRC.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
dst_files = {p.relative_to(DST).as_posix(): p for p in DST.rglob('*') if p.is_file() and '__pycache__' not in p.parts}

orphans = sorted(set(dst_files) - set(src_files))          # 副本独有=死层候选
missing = sorted(set(src_files) - set(dst_files))          # 副本缺=补
diff = sorted(f for f in set(src_files) & set(dst_files)
              if filecmp.cmp(src_files[f], dst_files[f], shallow=False) is False)

report = {'orphan_count': len(orphans), 'missing_count': len(missing), 'diff_count': len(diff)}
print('甄别:', json.dumps(report, ensure_ascii=False))

# 副本独有 → 死层候选归档（非删）
if orphans:
    ARCHIVE_ORPHANS.mkdir(parents=True, exist_ok=True)
    for rel in orphans:
        tgt = ARCHIVE_ORPHANS / rel
        tgt.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst_files[rel], tgt)
        dst_files[rel].unlink()
    print(f'orphans archived → {ARCHIVE_ORPHANS}')

# 覆盖/补齐（真源为准；逐文件留痕清单落 exec）
written = []
for rel in sorted(set(src_files)):
    tgt = DST / rel
    tgt.parent.mkdir(parents=True, exist_ok=True)
    data = src_files[rel].read_bytes()
    if not tgt.exists() or tgt.read_bytes() != data:
        tgt.write_bytes(data)
        written.append(rel)
print('written:', len(written))
for rel in written:
    print('  ', rel)
