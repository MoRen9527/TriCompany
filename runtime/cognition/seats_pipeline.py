# ── seats.json 管线派生器（LG-035 后续，CEO 23:2x 令+CTO 深化五点）──────────
#
# 从 manifest claudeCodeTarget 登记+agent-body fm name+seats-operations.json
# 席级常量册派生生成 TriMetaverse/.claude/seats.json（意见件 §2.1 九字段契约；
# 派生产物勿手编——与 compass 渲染纪律同构，零双真源）。
#
# CLI:
#   python -m runtime.cognition.seats_pipeline                     # dry-run（diff 摘要）
#   python -m runtime.cognition.seats_pipeline --execute           # 写盘
#   python -m runtime.cognition.seats_pipeline --source-root <r>   # 仓根覆盖
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MANIFEST_REL = "source-agents/registries/trimetaverse-live-agent-publish-manifest.json"
OPERATIONS_REL = "source-agents/registries/seats-operations.json"
SEATS_OUTPUT_REL = ".claude/seats.json"
COMPASS_REL_FMT = "TriMetaverse/.claude/compass/{seat}.session.md"

HEADER_NOTE = (
    "派生产物勿手编（publish-pipeline seats_pipeline 派生；真源=manifest "
    "claudeCodeTarget+agent-body fm+seats-operations.json 册——手改会在下次派生被覆盖，"
    "与 compass 渲染纪律同构零双真源）。"
)
LAUNCH_ENV_POLICY_SOURCE = "seats-operations.json launchEnvPolicy（全局统一）"


def _fm_name(agent_body_path: Path) -> str:
    """agent-body fm name 提取（无段/无键=空串）。"""
    try:
        text = agent_body_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return ""
    for line in m.group(1).split("\n"):
        mm = re.match(r"^name:\s*(.+)$", line)
        if mm:
            return mm.group(1).strip()
    return ""


def derive_seats(source_root: Path, trimetaverse_root: Path | None = None) -> dict:
    """manifest+operations 册+fm → seats.json 文档（意见件 §2.1 契约）。"""
    manifest = json.loads((source_root / MANIFEST_REL).read_text(encoding="utf-8"))
    ops_doc = json.loads((source_root / OPERATIONS_REL).read_text(encoding="utf-8"))
    ops_seats: dict = ops_doc.get("seats", {})
    env_policy = ops_doc.get("launchEnvPolicy", {})
    notify_default = ops_doc.get("notifyTargetDefault", "bod-addressable: false")

    if trimetaverse_root is None:
        trimetaverse_root = source_root.parent / "TriMetaverse"

    seats: list[dict] = []
    seen: set[str] = set()
    for entry in manifest.get("liveEntries", []):
        claude_target = entry.get("claudeCodeTarget")
        if not claude_target:
            continue
        source = entry.get("source", "")
        # seat slug=source-agents/<seat>/agent-body.agent.md 中段
        parts = source.replace("\\", "/").split("/")
        seat = parts[parts.index("source-agents") + 1] if "source-agents" in parts else ""
        if not seat or seat in seen:
            continue
        seen.add(seat)
        ops = ops_seats.get(seat, {})
        agent_name = _fm_name(source_root / "source-agents" / seat / "agent-body.agent.md")
        session_prompt = COMPASS_REL_FMT.format(seat=seat)
        ops_name = ops.get("opsName") or seat
        seats.append({
            "seat": seat,
            "opsName": ops_name,
            "workName": ops.get("workName", ""),
            "agent": agent_name,
            "hostFace": "local",
            "sessionPrompt": session_prompt,
            "launchCommand": f"claude -n {ops_name.upper()} --append-system-prompt-file <{session_prompt}>",
            "launchEnvPolicy": env_policy,
            "launchEnvPolicySource": LAUNCH_ENV_POLICY_SOURCE,
            "notifyTarget": ops.get("notifyTarget", notify_default),
            "health": ops.get("health", {"daemonPort": None, "watchdogTask": None}),
            "revivalPolicy": ops.get("revivalPolicy", "manual"),
            "claudeAgent": claude_target.replace("TriMetaverse/", "", 1),
        })

    # operations 册有而 manifest 未登记的席=漂移（一致性信号的生成侧暴露）
    for seat in sorted(set(ops_seats) - seen):
        seats.append({
            "seat": seat, "opsName": ops_seats[seat].get("opsName", seat),
            "workName": ops_seats[seat].get("workName", ""), "agent": "",
            "hostFace": "local", "sessionPrompt": "", "launchCommand": "",
            "launchEnvPolicy": env_policy, "launchEnvPolicySource": LAUNCH_ENV_POLICY_SOURCE,
            "notifyTarget": ops_seats[seat].get("notifyTarget", notify_default),
            "health": ops_seats[seat].get("health", {}), "revivalPolicy": ops_seats[seat].get("revivalPolicy", "manual"),
            "claudeAgent": "", "manifest_drift": "no claudeCodeTarget entry",
        })

    seats.sort(key=lambda s: s["seat"])
    return {
        "version": "2.0",
        "description": HEADER_NOTE,
        "generatedBy": "publish-pipeline seats_pipeline (derived from manifest claudeCodeTarget)",
        "launchEnvPolicySource": LAUNCH_ENV_POLICY_SOURCE,
        "seats": seats,
    }


def consistency_issues(source_root: Path, seats_doc: dict) -> list[str]:
    """名册↔manifest 一致性断言（意见件 §三漂移风险条）：席集/agent 名双侧核。"""
    issues: list[str] = []
    manifest = json.loads((source_root / MANIFEST_REL).read_text(encoding="utf-8"))
    registered = {
        entry.get("claudeCodeTarget", "").rsplit("/", 1)[-1].removesuffix(".md"): entry
        for entry in manifest.get("liveEntries", [])
        if entry.get("claudeCodeTarget")
    }
    for seat in seats_doc.get("seats", []):
        sid = seat.get("seat", "")
        if sid not in registered:
            issues.append(f"{sid}: seats 册有而 manifest 无 claudeCodeTarget 登记")
            continue
        entry = registered[sid]
        source = entry.get("source", "").replace("\\", "/")
        fm_name = _fm_name(source_root / source.removeprefix("TriCompany/"))
        if seat.get("agent") != fm_name:
            issues.append(f"{sid}: agent 名不一致（seats={seat.get('agent')!r} vs fm={fm_name!r}）")
        expected_target = f"TriMetaverse/.claude/agents/{sid}.md"
        if entry.get("claudeCodeTarget") != expected_target:
            issues.append(f"{sid}: claudeCodeTarget 非规范位（{entry.get('claudeCodeTarget')!r}）")
    for sid in registered:
        if sid not in {s.get("seat") for s in seats_doc.get("seats", [])}:
            issues.append(f"{sid}: manifest 登记有而 seats 册缺（operations 册缺席级常量）")
    return issues


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="seats.json pipeline derivation (LG-035 后续)")
    ap.add_argument("--source-root", default=".", help="TriCompany 仓根（默认 cwd）")
    ap.add_argument("--trimetaverse-root", default=None, help="TriMetaverse 仓根（默认 source_root.parent/TriMetaverse）")
    ap.add_argument("--execute", action="store_true", help="写盘（缺省 dry-run 打印摘要）")
    args = ap.parse_args(argv)

    source_root = Path(args.source_root).resolve()
    tmv_root = Path(args.trimetaverse_root).resolve() if args.trimetaverse_root else source_root.parent / "TriMetaverse"
    doc = derive_seats(source_root, tmv_root)
    issues = consistency_issues(source_root, doc)
    out_path = tmv_root / SEATS_OUTPUT_REL

    existing: dict | None = None
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = None  # 手改坏文件=视为漂移照常覆盖（验收锚②反向路径）
    identical = existing == doc
    print(f"[seats] derived seats={len(doc['seats'])} | consistency_issues={len(issues)} | "
          f"target={out_path} | mode={'execute' if args.execute else 'dry-run'} | identical_to_disk={identical}")
    for issue in issues:
        print(f"[seats][consistency] {issue}")
    if not args.execute:
        print("[seats] dry-run — rerun with --execute to write")
        return 0
    if identical:
        print("[seats] already identical — zero write")
        return 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"{out_path}.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out_path)  # Windows rename 目标存在即炸——replace 才是覆盖语义
    print(f"[seats] written: {out_path}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
