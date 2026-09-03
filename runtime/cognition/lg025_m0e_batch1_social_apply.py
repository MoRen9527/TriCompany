# -*- coding: utf-8 -*-
"""LG-025 M0e 批 1 并单追加：CHO 窗四三席 social 第二句补注 apply（权威源=2a09bca）。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TEXTS = {
    "chief-administrative-officer": (
        "对外表述规则：制度状态与会议结论的对外表述以已入册版本为准，草案不外述；"
        "具体对外行政沟通不入本件。"
        "外部协作与供应商的制度口径问询按已入册版本答复，未定稿条款不对外承诺；"
        "往来记录属运行态不入本件。"
    ),
    "chief-technology-officer": (
        "对外表述规则：交付状态对外表述以门禁读数为准，未过门禁不称已交付；"
        "具体对外技术沟通不入本件。"
        "对外技术承诺附回滚边界与已知风险，未做回滚预案的变更不对外给确定性时间；"
        "选型争议对外口径经本席校准。"
    ),
    "chief-human-resources-officer": (
        "对外表述规则：岗位状态对外表述以验收状态机为准，草案与试岗不称正式到岗；"
        "具体对外组织沟通不入本件。"
        "组织规模与 headcount 问询以在册岗位事实作答，扩张计划不对外预披露；"
        "外部人才线索记录属运行态不入本件。"
    ),
}

SECTION_RE = re.compile(r"## 当前原则\n\n(?:- [^\n]+\n)+")
# 句界拆分锚（第二主句起始——纯形态适配：权威段单 bullet 拆两行过 V1 行数线，
# 语义零改动）
SECOND_SENTENCE_ANCHOR = {
    "chief-administrative-officer": "外部协作与供应商",
    "chief-technology-officer": "对外技术承诺",
    "chief-human-resources-officer": "组织规模与 headcount",
}

for seat, text in TEXTS.items():
    target = ROOT / "source-agents" / seat / "social.agent.md"
    content = target.read_text(encoding="utf-8")
    anchor = SECOND_SENTENCE_ANCHOR[seat]
    idx = text.find(anchor)
    line1, line2 = text[:idx].strip(), text[idx:].strip()
    new_section = f"## 当前原则\n\n- {line1}\n- {line2}\n"
    if not SECTION_RE.search(content):
        print(f"MISS {seat}: 形态不匹配")
        continue
    content = SECTION_RE.sub(new_section, content, count=1)
    target.write_text(content, encoding="utf-8", newline="\n")
    print(f"OK {seat}/social.agent.md 当前原则补注两行（{len(text)} 字符）")
