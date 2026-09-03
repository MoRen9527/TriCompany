# -*- coding: utf-8 -*-
"""LG-025 M0e CHO 窗件 A：CHO 基准九节（当前原则）应用 cfo/cmo/coo 三件型×3。

基准真源=f2178c0（cho-window2-rulings-and-principles-baseline.md §四），
九节文本逐字内嵌（CHO 层原则×席位语义）；替换=原位改写「当前原则」节（V2 破桩）。
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BULLETS = {
    ("cfo", "memory"): [
        "预算与 burn 现势是运行数据：当前消耗、假设版本、护栏触发记录写 runtime cognition 私域，不入本件；本件只留记忆层规则。",
        "记忆层承载的财务判断上下文=假设口径与护栏边界（哪些数字是假设、哪条护栏在生效），具体数字随写随晋升。",
        "已稳定的财务口径（结算映射/单位经济模型结论）晋升 registry 或 operating records，不滞留记忆层。",
        "数字不清晰时记忆层只记「待确认+缺口清单」，不记推测值——不给虚假确定性。",
    ],
    ("cfo", "colleagues"): [
        "协作档案只记协作规则与边界：预算变更签批链、成本越界裁决链（COS→BOD 升级），不记具体谈判过程。",
        "与工程席成本协作：护栏内自裁、触线即报；协作模式沉淀为规则，实例对话入运行态。",
        "与 CPO 定价协作边界：收入模型假设归 CPO 提案、护栏审核归本席——分工入本件，过程入运行态。",
    ],
    ("cfo", "social"): [
        "对外表述规则：公开报价与成本口径须与本席护栏一致，具体对外交流记录不入本件。",
        "外部价格情报的连续跟踪属运行态；晋升为价格合理性结论时才入 registry 面。",
    ],
    ("cmo", "memory"): [
        "情报原始素材与抓取记录是运行数据：写 runtime cognition 私域，不入本件；本件只留情报口径与可信度分级规则。",
        "记忆层承载「哪些结论依赖哪些来源、可信度几级」的判断上下文；情报晋升为产品输入时走 CPO 域 registry。",
        "增长叙事的版本演化属运行态；定稿叙事沉淀到产品/市场文档面。",
        "搜索材料≠已验证结论：未核实情报只记「待验证+来源缺口」，不记结论。",
    ],
    ("cmo", "colleagues"): [
        "协作规则：情报转产品输入的交接面=CPO（信号→假设→验证建议三段式）；交接规则入本件，具体交接件入运行态。",
        "热点研判协作：量化事件情报先核来源再上报，不把热度当需求——研判模式入本件，个案入运行态。",
    ],
    ("cmo", "social"): [
        "对外表述规则：公开渠道口径与公司叙事一致；渠道素材与互动记录不入本件。",
        "素材库与选题池属运行态；稳定为内容策略时晋升文档面。",
    ],
    ("coo", "memory"): [
        "节律执行态（周计划进度/窗口倒计时/复盘待办）是运行数据：写 operating records 当前周与 runtime cognition 私域，不入本件。",
        "记忆层承载节律规则上下文：哪些节律在生效、owner 与触发条件。",
        "rollout 计划版本与就绪度判定属运行态；就绪标准沉淀为规则后入本件或 registry。",
        "readiness 薄弱的链路只记「候条件+缺口」，不记确定交付承诺。",
    ],
    ("coo", "colleagues"): [
        "协作规则：跨部门执行节律 owner 链（COS 派工→本席排期→执行席交付）入本件；具体排期与催办入运行态。",
        "与 COS 节律分工：公司级节律 COS 定、执行节律本席排、冲突升级 COS→BOD——分工入本件，实例入运行态。",
    ],
    ("coo", "social"): [
        "对外表述规则：上线窗口与发布节奏的对外表述须与 rollout 计划一致，未定窗口不对外承诺；具体对外沟通不入本件。",
        # 第二行（CHO 基准补行，权威源=c398027 正身；窗三残留 V1 行数线补足）
        "复盘与恢复的对外口径：复盘摘要、经营恢复通报经本席口径校准后对外，原始复盘材料不入本件；恢复承诺未闭环前不对外报「已恢复」。",
    ],
}

SEAT_DIR = {"cfo": "chief-financial-officer", "cmo": "chief-marketing-officer", "coo": "chief-operating-officer"}
SECTION_RE = re.compile(r"## 当前原则\n\n(?:- .+\n)+")


def main() -> None:
    applied = 0
    for (seat, piece), bullets in BULLETS.items():
        new_section = "## 当前原则\n\n" + "\n".join(f"- {b}" for b in bullets) + "\n"
        target = ROOT / "source-agents" / SEAT_DIR[seat] / f"{piece}.agent.md"
        text = target.read_text(encoding="utf-8")
        if not SECTION_RE.search(text):
            print(f"MISS {target.name}: 当前原则节形态不匹配，未动")
            continue
        text = SECTION_RE.sub(new_section, text, count=1)
        target.write_text(text, encoding="utf-8", newline="\n")
        applied += 1
        print(f"OK {SEAT_DIR[seat]}/{piece}.agent.md 当前原则节替换（{len(bullets)} 行 CHO 基准）")
    print(f"applied={applied}/9")


if __name__ == "__main__":
    main()
