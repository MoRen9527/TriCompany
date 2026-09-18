# -*- coding: utf-8 -*-
# 段一：13 席 memory/colleagues/social 契约件「运行资产落点」双腿表述批量改写
# （执行令 20260919-cognition-landing-exec 段一；素材=joint-plan §一.B 标准表述）
import io, os

SEATS = ['ceo-chief-of-staff', 'chief-administrative-officer', 'chief-financial-officer',
         'chief-human-resources-officer', 'chief-marketing-officer', 'chief-operating-officer',
         'chief-product-officer', 'chief-technology-officer', 'customer-success-officer',
         'deployment-engineer', 'full-stack-developer', 'rd-trainer', 'senior-test-engineer']
ROOT = r'D:\Code\ai\TriCompany\source-agents'
SUFFIXES = ['memory.agent.md', 'colleagues.agent.md', 'social.agent.md']
# CSO/DE=colleagues-social 合并件形态席（V1.0 起然）；存在即纳入改写

# 双腿行模板（<席> 代入 seat 目录名；joint-plan §一.B 标准表述行级化）
LEARN_LINE = '- 学习腿（知识工作区）：`TriCompany-copilot-host-assets/knowledge/employees/<席>/`（inbox/wiki/workbench/audit 四区，hermes-gov-p2 员工层管道落点）'
RUN_LINE = '- 运行腿：`TRICOMPANY_COGNITION_HOME`（.tricompany-cognition：employee 私域运行态/org 运行共享记忆/org 运行审计——机器写入，runtime cognition backend 驱动，复活时初始化）'

# 形态 A：主表述（认知层状态与派生资产落点）→ 双腿两行
A_OLD = '- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME`（认知层状态与派生资产落点）'
# 形态 B：知识工作区行 → 学习腿行（席名代入）
B_OLD = '- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）'
# 形态 C：colleagues/social 精紧行 → 运行腿+学习腿两行
C_OLD = '- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend'

changed = 0
for seat in SEATS:
    files = [os.path.join(ROOT, seat, suf) for suf in SUFFIXES]
    merged = os.path.join(ROOT, seat, 'colleagues-social.agent.md')
    if os.path.exists(merged):
        files.append(merged)
    for p in files:
        if not os.path.exists(p):
            continue
        s = io.open(p, encoding='utf-8').read()
        orig = s
        learn = LEARN_LINE.replace('<席>', seat)
        run = RUN_LINE
        # A：主表述 → 双腿块
        s = s.replace(A_OLD, learn + '\n' + run)
        # B：知识工作区 → 学习腿（席名代入）
        s = s.replace(B_OLD, learn.replace('<席>', seat))
        # C：精紧行 → 运行腿+学习腿（席名代入）
        s = s.replace(C_OLD, run + '\n' + learn.replace('<席>', seat))
        if s != orig:
            io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
            changed += 1
print('changed files:', changed)
