# -*- coding: utf-8 -*-
# LG-035/BOD 席位件发布链：board 单条定向渲（claude+copilot 两面）
# 背景：--employees 滤网只认 kind=role-agent（员工席语义），board 镜像 bs 的
# registry-or-governance-agent kind 被滤；全量跑会抢 CHO 渲染窗（lg024 红在卷）
# ——故照 lg024 先例直调 _publish_single_agent 单条定向（写入面=board 两件）。
# 幂等：重复跑=derived_identical 零写。
import json
from pathlib import Path

from runtime.cognition.source_publish_check import _publish_single_agent

REPO = Path(__file__).resolve().parents[1]
TMV = REPO.parent / "TriMetaverse"

entry = {
    "status": "source-published-live-entry",
    "target": "TriMetaverse/.github/agents/board.agent.md",
    "source": "TriCompany/source-agents/board/agent-body.agent.md",
    "kind": "registry-or-governance-agent",
    "sourceFiles": {
        "agent_body": "TriCompany/source-agents/board/agent-body.agent.md",
        "agent_frontmatter": "TriCompany/source-agents/board/agent-frontmatter.agent.md",
    },
}
source_file = REPO / "source-agents" / "board" / "agent-body.agent.md"

for host, target in (
    ("claude", TMV / ".claude" / "agents" / "board.md"),
    ("copilot", TMV / ".github" / "agents" / "board.agent.md"),
):
    item = _publish_single_agent(
        source_file, target, entry, dry_run=False, host_id=host, source_root=REPO
    )
    print(f"[{host}] action={item.action} target={item.target} error={item.error!r} dropped_tools={item.dropped_tools}")
