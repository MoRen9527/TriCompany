# -*- coding: utf-8 -*-
# D1c（ruling §三，CTO CP1 挂缺补做）：13 复合件退役注记头——「本件已退役出渲染链；
# 真源=同目录 agent-body.agent.md（D1b manifest 已切源）」。插在 frontmatter 后首行。
import io, os

SEATS = ['ceo-chief-of-staff','chief-administrative-officer','chief-financial-officer',
         'chief-human-resources-officer','chief-marketing-officer','chief-operating-officer',
         'chief-product-officer','chief-technology-officer','customer-success-officer',
         'deployment-engineer','full-stack-developer','rd-trainer','senior-test-engineer']
ROOT = r'D:\Code\ai\TriCompany\source-agents'
NOTE = '> 本件已退役出渲染链；真源=同目录 agent-body.agent.md（D1b manifest 已切源）。\n'

changed = 0
for seat in SEATS:
    p = os.path.join(ROOT, seat, seat + '.agent.md')
    if not os.path.exists(p):
        print('MISSING:', seat); continue
    s = io.open(p, encoding='utf-8').read()
    if '本件已退役出渲染链' in s:
        print('SKIP (already noted):', seat); continue
    # frontmatter（--- ... ---）闭合后插注记行
    if s.startswith('---'):
        close = s.index('\n---', 3) + 4  # 含闭合 --- 行
        body_head = s[:close]
        rest = s[close:]
        s = body_head + '\n' + NOTE + rest.lstrip('\n')
    else:
        s = NOTE + '\n' + s
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    changed += 1
print('D1c noted:', changed, '/13')
