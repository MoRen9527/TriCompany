# -*- coding: utf-8 -*-
"""LG-025 M0d 回填：publish manifest liveEntries 13 条补登 sourceFiles 键。

键集对齐 contract.yaml paths 六键（snake_case）：soul/agent_body/agent_frontmatter/
memory/colleagues/social；CSO/DE 合并席双键同指合法（agent_body=agent_frontmatter
同文件）；sessionBody 现役独立键（仅 ceo）不动。
"""
from __future__ import annotations

import json
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[2] / "source-agents" / "registries" / "trimetaverse-live-agent-publish-manifest.json"

# 合并席双键同指（CHO/M0c 既裁合法形态）
MERGED_SEATS = {"customer-success-officer", "deployment-engineer"}


def source_files_for(employee_id: str) -> dict[str, str]:
    agent_frontmatter = f"{employee_id}/agent-frontmatter.agent.md"
    if employee_id in MERGED_SEATS:
        agent_frontmatter = f"{employee_id}/agent-body.agent.md"  # 双键同指
    return {
        "soul": f"{employee_id}/soul.agent.md",
        "agent_body": f"{employee_id}/agent-body.agent.md",
        "agent_frontmatter": agent_frontmatter,
        "memory": f"{employee_id}/memory.agent.md",
        "colleagues": f"{employee_id}/colleagues.agent.md",
        "social": f"{employee_id}/social.agent.md",
    }


def main() -> None:
    raw = MANIFEST.read_text(encoding="utf-8-sig")
    manifest = json.loads(raw)
    entries = manifest["liveEntries"]
    assert sum(1 for e in entries if e.get("kind") == "role-agent") == 13, (
        "role-agent 条目预期 13"
    )
    backfilled = 0
    for entry in entries:
        if entry.get("kind") != "role-agent":
            continue  # M0d 范围=13 席 role-agent 条目（registry/module 族不在 kit 契约域）
        target = entry.get("target", "")
        # target 形如 TriMetaverse/.github/agents/<id>.agent.md
        employee_id = target.rsplit("/", 1)[-1].removesuffix(".agent.md")
        entry["sourceFiles"] = source_files_for(employee_id)
        backfilled += 1
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"backfilled={backfilled}")
    print(f"scanned {len(entries)} liveEntries")


if __name__ == "__main__":
    main()
