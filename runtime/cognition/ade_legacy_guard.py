"""ade_legacy_guard — ADE 退役术语回流红守卫。

fade-protocol-spec v2.0.0 明文 ADE 概念退役（ade-legacy-sweep 线，
task-charter-20260921-ade-legacy-sweep）。本守卫扫活类文件中的未审定
ADE 用法：出现即红（exit 1）；批准形与在途背账文件豁免。

批准形白名单（对照表审定，CTO 2026-09-21 四裁）：
  「前称 ADE」溯源注记形 / ADE-B 等时代标签 / ADE_PROTOCOL / ADE_ACTIONS
  / ade-report 契约值 / ADE 整合阶段 等历史记叙。
豁免文件清单（在途背账，随 P2/P3/P4 批落地收缩）：见 EXEMPT_FILES。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WORD_ADE = re.compile(r"\bADE\b")

APPROVED_PATTERNS = [
    r"前称 ADE",
    r"ADE-B",
    r"ADE phase[- ]",
    r"ADE consolidation phase",
    r"ADE 整合阶段",
    r"ADE_PROTOCOL",
    r"ADE_ACTIONS",
    r"ade-report",
    r"ADE-B 存档",
]

# 在途背账文件（P2/P3/P4 未落批前豁免；批毕逐一移出——清单只缩不长）
EXEMPT_FILES = {
    # P3 规范文档面（候文档窗）
    "TriCompany/docs/engineering/ROADMAP.md",
    "TriCompany/docs/engineering/STATE.md",
    "TriCompany/docs/engineering/governance-memory-index.md",
    "TriCompany/docs/engineering/trilc-trimc-runtime-parity.md",
    "TriCompany/docs/registry/code-state.md",
    "TriCompany/docs/registry/test-state.md",
    "TriCompany/docs/testing/evidence/lg-025-m0e-graft/lg-025-d16-vs-publish-check-gate-note.md",
    "TriCompany/docs/training/fade-002-deep-dive.md",
    "TriCompany/docs/training/fade-002/03-code-map.md",
    "TriCompany/docs/training/fade-002/04-deep-research.md",
    "TriCompany/docs/training/fade-003-deep-dive.md",
    "TriCompany/docs/training/fade-004-deep-dive.md",
    "TriCompany/docs/training/fade-005-deep-dive.md",
    "TriCompany/docs/training/fade-beginner-course.md",
    "TriCompany/docs/training/fade-code-deep-dive.md",
    "TriCompany/docs/training/fade-product-guide.md",
    "TriCompany/docs/training/project-source-document-sync-fade-tutorial.md",
    "TriCompany/docs/workflow/README.md",
    "TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md",
    "TriCompany/docs/workflow/company-work-plane-principles.md",
    "TriCompany/docs/workflow/dynamic-task-tree-protocol.md",
    "TriCompany/docs/workflow/engineering-disciplines.md",
    "TriCompany/docs/workflow/project-source-document-sync-ade.md",
    "TriCompany/runtime/cognition/ade_envelope.py",
    "TriCompany/runtime/cognition/source_publish_check.py",
    "TriCompany/runtime/cognition/source_publish_check_validation.py",
    "TriCompany/runtime/cognition/employee_host_publish.py",
    "TriCompany/runtime/cognition/employee_host_publish_validation.py",
    "TriCompany/runtime/cognition/employee_onboard.py",
    "TriCompany/runtime/cognition/employee_onboard_validation.py",
    "TriCompany/runtime/cognition/host_object_generation.py",
    "TriCompany/runtime/cognition/rule_injection.py",
    "TriCompany/runtime/cognition/tree_op.py",
    "TriCompany/runtime/cognition/weekly_plane.py",
    "TriCompany/runtime/cognition/weekly_plane_shift.py",
    "TriCompany/runtime/cognition/employee_host_binding_profile_generation_validation.py",
    "TriCompany/runtime/cognition/lg024_session_upgrade_validation.py",
    "TriCompany/runtime/cognition/rd_trainer_host_object_generation_validation.py",
    "TriCompany/runtime/cognition/employee_source_kit_validation.py",
    "TriMetaverse/docs/engineering/experiment-runbook.md",
    "TriMetaverse/docs/engineering/ROADMAP.md",
    "TriMetaverse/docs/engineering/STATE.md",
    "TriMetaverse/docs/execution/2026-08-24/mmc-host-driver-design-draft.md",
    "TriMetaverse/docs/execution/candidate-staffing-fade.md",
    "TriMetaverse/docs/execution/fade-005-roster-gating-spec.md",
    "TriMetaverse/docs/execution/fade-instances-retrospective.md",
    "TriMetaverse/docs/execution/init-to-collab-design.md",
    "TriMetaverse/docs/execution/knowledge-injection-spec.md",
    "TriMetaverse/docs/execution/lg-024-session-contract-upgrade-plan.md",
    "TriMetaverse/docs/execution/lg-028-content-routing-review.md",
    "TriMetaverse/docs/execution/module-cooperation-plan.md",
    "TriMetaverse/docs/execution/tmv-fade-reading-map.md",
    "TriMetaverse/docs/execution/tricade-implementation-playbook.md",
}

SCAN_ROOTS = [
    "TriCompany/docs",
    "TriCompany/source-agents",
    "TriCompany/runtime",
    "TriMetaverse/docs",
    "TriMetaverse/.claude",
    "TriMetaverse/TriCompany-copilot-host-assets",
]

INCLUDE_SUFFIXES = {".md", ".yaml", ".json", ".py"}


def approved_forms_absent(text: str) -> bool:
    """无批准形（前称注记/时代标签/契约值/历史记叙）时返回 True。"""
    return not any(re.search(p, text) for p in APPROVED_PATTERNS)


def unapproved_hits(text: str) -> list[str]:
    """返回未审定 ADE 用法行（批准形行豁免）。"""
    hits = []
    for line in text.splitlines():
        if WORD_ADE.search(line) and approved_forms_absent(line):
            hits.append(line.strip())
    return hits


def scan_repo(repo_root: Path) -> list[str]:
    """扫活类面（豁免文件与 operating-records/重目录除外），返回红行清单。"""
    reds: list[str] = []
    base_map = {
        "TriCompany": repo_root.parent / "TriCompany",
        "TriMetaverse": repo_root,
    }
    for root in SCAN_ROOTS:
        face, _, rest = root.partition("/")
        base = base_map[face] / rest
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.suffix not in INCLUDE_SUFFIXES or not p.is_file():
                continue
            rel = f"{face}/{p.relative_to(base).as_posix()}"
            if "operating-records" in rel:
                continue
            if rel in EXEMPT_FILES:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for h in unapproved_hits(text):
                reds.append(f"{rel}: {h}")
    return reds


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    reds = scan_repo(repo_root)
    for r in reds:
        print(f"ade_legacy_red: {r}")
    print(f"ade_legacy_guard: {len(reds)} unapproved ADE usage(s)")
    return 1 if reds else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
