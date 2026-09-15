# -*- coding: utf-8 -*-
# 序③：旧名 TriCompanyCEOChiefOfStaff → CEOChiefOfStaff（prompts 双边 4+docs 双边 4+AGENTS 真源 1）
# backport manifest 历史记录面不列入（候裁）。
import io

FILES = [
    # TriCompany 侧
    r'D:\Code\ai\TriCompany\.github\prompts\开始会议.prompt.md',
    r'D:\Code\ai\TriCompany\.github\prompts\结束会议.prompt.md',
    r'D:\Code\ai\TriCompany\docs\workflow\chief-of-staff-rd-orchestration.md',
    r'D:\Code\ai\TriCompany\docs\workflow\github-backport-manifest.md',
    r'D:\Code\ai\TriCompany\docs\project-sources\trimetaverse-agents-md.md',
    # TMV 侧
    r'D:\Code\ai\TriMetaverse\.github\prompts\开始会议.prompt.md',
    r'D:\Code\ai\TriMetaverse\.github\prompts\结束会议.prompt.md',
    r'D:\Code\ai\TriMetaverse\docs\workflow\chief-of-staff-rd-orchestration.md',
    r'D:\Code\ai\TriMetaverse\docs\workflow\github-backport-manifest.md',
]
OLD, NEW = 'TriCompanyCEOChiefOfStaff', 'CEOChiefOfStaff'

for p in FILES:
    s = io.open(p, encoding='utf-8').read()
    n = s.count(OLD)
    if n == 0:
        print('NO-OLD-NAME:', p); continue
    s = s.replace(OLD, NEW)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print(f'replaced {n}x:', p)
print('done')
