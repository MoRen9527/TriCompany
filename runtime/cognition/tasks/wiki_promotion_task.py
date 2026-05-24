from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.chief_of_staff_wiki_paths import chief_of_staff_audit_root, chief_of_staff_wiki_root
from runtime.cognition.kernel.wiki_page_registry import WikiPageRegistry


REQUIRED_SECTION_HEADERS = (
    "## 摘要",
    "## 当前整理事实",
    "## 当前判断",
    "## 待确认问题",
    "## 来源",
)


@dataclass(frozen=True)
class PromotionDecision:
    page_id: str
    from_status: str
    to_status: str | None
    rule_id: str
    status: str
    evidence: dict[str, object]
    reason: str
    audit_path: Path
    page_path: Path


def promote_chief_of_staff_page(
    *,
    page_id: str,
    workspace_root: str | None = None,
    trigger_mode: str = "manual",
) -> dict[str, object]:
    page_registry = WikiPageRegistry(chief_of_staff_wiki_root(workspace_root))
    page = page_registry.load_page(page_id)
    if page is None:
        raise FileNotFoundError(f"Wiki page not found: {page_id}")

    evidence = _collect_evidence(
        page_id=page_id,
        page_body=page.body,
        source_refs=page.source_refs,
        approval_status=page.approval_status,
        reviewed_by=page.reviewed_by,
        reviewed_at=page.reviewed_at,
        workspace_root=workspace_root,
    )
    to_status, rule_id, status, reason = _decide_next_status(page.page_status, evidence)
    now = _timestamp_now()
    if to_status is not None:
        page_registry.update_page_status(page_id, new_status=to_status, updated_at=now)
    audit_path = _write_promotion_audit(
        page_id=page_id,
        page_path=page.page_path,
        from_status=page.page_status,
        to_status=to_status,
        rule_id=rule_id,
        status=status,
        reason=reason,
        evidence=evidence,
        trigger_mode=trigger_mode,
        workspace_root=workspace_root,
    )
    return {
        "status": status,
        "artifactPaths": [page.page_path.as_posix(), audit_path.as_posix()],
        "note": reason,
    }


def _collect_evidence(
    *,
    page_id: str,
    page_body: str,
    source_refs: tuple[str, ...],
    approval_status: str,
    reviewed_by: str,
    reviewed_at: str,
    workspace_root: str | None,
) -> dict[str, object]:
    audit_root = chief_of_staff_audit_root(workspace_root)
    refresh_records: list[dict[str, object]] = []
    for path in sorted(audit_root.glob("wiki-refresh-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        output_pages = payload.get("outputPages") or []
        if page_id in output_pages and payload.get("status") == "completed":
            refresh_records.append(payload)
    completed_refresh_count = len(refresh_records)
    scheduled_refresh_count = sum(1 for item in refresh_records if item.get("triggerMode") == "scheduled")
    missing_sections = [header for header in REQUIRED_SECTION_HEADERS if header not in page_body]
    return {
        "sourceRefCount": len(source_refs),
        "completedRefreshCount": completed_refresh_count,
        "scheduledRefreshCount": scheduled_refresh_count,
        "missingSections": missing_sections,
        "requiredSections": list(REQUIRED_SECTION_HEADERS),
        "approvalStatus": approval_status,
        "reviewedBy": reviewed_by,
        "reviewedAt": reviewed_at,
    }


def _decide_next_status(
    current_status: str,
    evidence: dict[str, object],
) -> tuple[str | None, str, str, str]:
    missing_sections = tuple(str(item) for item in (evidence.get("missingSections") or []))
    source_ref_count = int(evidence.get("sourceRefCount") or 0)
    scheduled_refresh_count = int(evidence.get("scheduledRefreshCount") or 0)
    approval_status = str(evidence.get("approvalStatus") or "draft").lower()

    if missing_sections:
        return None, "page-promotion-missing-sections-v1", "blocked", "page missing required sections"
    if source_ref_count < 3:
        return None, "page-promotion-insufficient-sources-v1", "blocked", "page has fewer than 3 source refs"
    if current_status == "working":
        if scheduled_refresh_count >= 1:
            return "reviewing", "working-to-reviewing-v1", "completed", "page promoted from working to reviewing"
        return None, "working-to-reviewing-v1", "blocked", "requires at least one scheduled refresh evidence"
    if current_status == "reviewing":
        if approval_status == "rejected":
            return None, "reviewing-to-stable-rejected-v1", "blocked", "page was rejected during manual approval"
        if approval_status != "approved":
            return None, "reviewing-to-stable-awaiting-approval-v1", "blocked", "requires manual approval before stable promotion"
        if scheduled_refresh_count >= 2:
            return "stable", "reviewing-to-stable-v1", "completed", "page promoted from reviewing to stable"
        return None, "reviewing-to-stable-v1", "blocked", "requires at least two scheduled refresh evidence records"
    if current_status == "stable":
        return None, "stable-noop-v1", "completed", "page already stable"
    return None, "unsupported-status-v1", "blocked", f"unsupported status: {current_status}"


def _write_promotion_audit(
    *,
    page_id: str,
    page_path: Path,
    from_status: str,
    to_status: str | None,
    rule_id: str,
    status: str,
    reason: str,
    evidence: dict[str, object],
    trigger_mode: str,
    workspace_root: str | None,
) -> Path:
    audit_root = chief_of_staff_audit_root(workspace_root)
    audit_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("wiki-promotion-%Y-%m-%d-%H%M%S-%f")
    path = audit_root / f"{run_id}.json"
    payload = {
        "runId": run_id,
        "triggerMode": trigger_mode,
        "pageId": page_id,
        "pagePath": page_path.as_posix(),
        "fromStatus": from_status,
        "toStatus": to_status,
        "ruleId": rule_id,
        "status": status,
        "reason": reason,
        "evidence": evidence,
        "startedAt": _timestamp_now(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")