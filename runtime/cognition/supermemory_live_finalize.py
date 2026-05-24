from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ACTOR_ID = "ceo-chief-of-staff"
REQUIRED_NAMESPACES = {
    f"employee/{ACTOR_ID}",
    "org/shared",
    "org/audit",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _report_path() -> Path:
    return (
        _repo_root()
        / "docs"
        / "execution"
        / "hermes-copilot-host"
        / "phase-1"
        / "SUPERMEMORY-LIVE-VALIDATION.latest.json"
    )


def _state_path() -> Path:
    return _repo_root() / "docs" / "engineering" / "STATE.md"


def _record_path() -> Path:
    return (
        _repo_root()
        / "docs"
        / "execution"
        / "hermes-copilot-host"
        / "phase-1"
        / "SUPERMEMORY-LIVE-VALIDATION.md"
    )


def _load_report(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Live validation report must be a JSON object: {path}")
    return payload


def _validate_context_markers(report: dict[str, Any], errors: list[str]) -> None:
    context_markers = report.get("contextMarkers")
    if not isinstance(context_markers, dict):
        errors.append("contextMarkers must be an object")
        return
    if context_markers.get("private") is not True:
        errors.append("contextMarkers.private must be true")
    if context_markers.get("orgShared") is not True:
        errors.append("contextMarkers.orgShared must be true")


def _validate_recalled_namespaces(report: dict[str, Any], errors: list[str]) -> None:
    recalled_namespaces = report.get("recalledNamespaces")
    if not isinstance(recalled_namespaces, list):
        errors.append("recalledNamespaces must be an array")
        return

    missing = sorted(REQUIRED_NAMESPACES.difference(str(item) for item in recalled_namespaces))
    if missing:
        errors.append(f"missing namespaces: {', '.join(missing)}")


def _validate_results_by_namespace(report: dict[str, Any], errors: list[str]) -> None:
    results_by_namespace = report.get("resultsByNamespace")
    if not isinstance(results_by_namespace, dict):
        errors.append("resultsByNamespace must be an object")
        return

    for namespace in REQUIRED_NAMESPACES:
        value = results_by_namespace.get(namespace)
        if not isinstance(value, int) or value < 1:
            errors.append(f"resultsByNamespace.{namespace} must be >= 1")


def _validate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("status") != "passed":
        errors.append("status must be passed")
    if not isinstance(report.get("validatedAtUtc"), str):
        errors.append("validatedAtUtc must be present")
    if report.get("actorId") != ACTOR_ID:
        errors.append(f"actorId must be {ACTOR_ID}")
    if not isinstance(report.get("queryText"), str) or not report["queryText"].strip():
        errors.append("queryText must be present")

    _validate_context_markers(report, errors)
    _validate_recalled_namespaces(report, errors)
    _validate_results_by_namespace(report, errors)

    match_count = report.get("matchingResultCount")
    if not isinstance(match_count, int) or match_count < 3:
        errors.append("matchingResultCount must be >= 3")

    return errors


def _replace_once(text: str, old: str, new: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise ValueError(f"Expected text not found during finalize: {old}")


def _update_state() -> None:
    path = _state_path()
    text = path.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        "状态：已完成 Supermemory 官方 schema 与 SDK seam 验证",
        "状态：已完成 Supermemory 官方 schema、SDK seam 与 live smoke 验证",
    )
    text = _replace_once(
        text,
        "- 本地 provider-backed 集成、production 风格后端落盘/审计验证、模拟外部后端兼容性验证、HTTP 外部后端认证/网络验证，以及 Supermemory 官方 schema 与 SDK seam 验证已完成，但真实 Supermemory API key 下的 live 调用、账号级限流/配额语义与远端后端差异仍待验证",
        "- 本地 provider-backed 集成、production 风格后端落盘/审计验证、模拟外部后端兼容性验证、HTTP 外部后端认证/网络验证，以及 Supermemory 官方 schema、SDK seam 与首轮 live smoke 验证已完成，但账号级限流/配额语义、持续稳定性与远端后端差异仍待验证",
    )
    text = _replace_once(
        text,
        "- 已提供 live smoke 入口，但在未显式启用环境变量和 API key 前，不能据此宣称真实 provider 已验证",
        "- 已完成首轮 live smoke 并生成结构化证据，但这仍不等于账号级限流/配额语义、持续稳定性和真实官方 SDK 包接入已全部验证",
    )
    text = _replace_once(
        text,
        "- 当前已具备把 TriCompany/.github 以 shadow-test 方式回迁 TriMetaverse 的准备结构；其中 runtime/cognition 最小 smoke test、Hermes 核心契约验证、本地 provider-backed 集成验证、后端落盘/审计验证、模拟外部后端兼容性验证、HTTP 外部后端认证/网络验证，以及 Supermemory 官方 schema 与 SDK seam 验证均已通过",
        "- 当前已具备把 TriCompany/.github 以 shadow-test 方式回迁 TriMetaverse 的准备结构；其中 runtime/cognition 最小 smoke test、Hermes 核心契约验证、本地 provider-backed 集成验证、后端落盘/审计验证、模拟外部后端兼容性验证、HTTP 外部后端认证/网络验证，以及 Supermemory 官方 schema、SDK seam 与首轮 live smoke 验证均已通过",
    )
    text = _replace_once(
        text,
        "- 在 live smoke 入口上补充真实执行记录，并据结果决定是否允许升到 real provider validated",
        "- 复核 live smoke 证据、账号级限流/配额语义与持续稳定性后，再决定是否允许升到 real provider validated",
    )
    path.write_text(text, encoding="utf-8")


def _update_record(report: dict[str, Any], report_path: Path) -> None:
    path = _record_path()
    text = path.read_text(encoding="utf-8")
    text = _replace_once(text, "状态：待执行", "状态：已完成首轮 live smoke")
    old_block = (
        "## 本次记录\n\n"
        "- 当前尚未执行真实 Supermemory live smoke\n"
        "- 当前不存在真实 API key 下的执行结果与账号级限流/配额语义证据\n"
    )
    recalled_namespaces = report.get("recalledNamespaces", [])
    new_block = (
        "## 本次记录\n\n"
        f"- 最近一次执行时间：{report.get('validatedAtUtc', 'unknown')}\n"
        f"- JSON 证据路径：{report_path.as_posix()}\n"
        f"- 召回命名空间：{', '.join(str(item) for item in recalled_namespaces)}\n"
        f"- 远端端点：<{report.get('baseUrl', 'unknown')}>\n"
        f"- 鉴权模式：{report.get('authMode', 'unknown')}\n"
        f"- 结果计数：{report.get('matchingResultCount', 'unknown')}\n"
    )
    text = _replace_once(text, old_block, new_block)
    path.write_text(text, encoding="utf-8")


def _print_pending(report_path: Path) -> None:
    print(f"pending: live validation report not found at {report_path.as_posix()}")
    print("No status files were changed.")


def _print_preview(report: dict[str, Any], report_path: Path) -> None:
    print(f"eligible: live validation report found at {report_path.as_posix()}")
    print(f"validatedAtUtc: {report.get('validatedAtUtc')}")
    print(f"recalledNamespaces: {report.get('recalledNamespaces')}")
    print("apply target files:")
    print(f"- {_state_path().as_posix()}")
    print(f"- {_record_path().as_posix()}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    report_path = _report_path()
    report = _load_report(report_path)
    if report is None:
        _print_pending(report_path)
        return 0

    errors = _validate_report(report)
    if errors:
        for item in errors:
            print(f"invalid: {item}")
        return 1

    _print_preview(report, report_path)
    if not args.apply:
        print("dry-run: pass --apply to update status files.")
        return 0

    _update_state()
    _update_record(report, report_path)
    print("applied: source live validation status updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())