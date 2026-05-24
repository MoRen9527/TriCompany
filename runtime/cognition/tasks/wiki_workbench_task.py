from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.cognition.chief_of_staff_wiki_paths import (
    chief_of_staff_audit_root,
    chief_of_staff_schedule_root,
    chief_of_staff_wiki_root,
    chief_of_staff_workbench_root,
)
from runtime.cognition.kernel.schedule_registry import ScheduleRegistry
from runtime.cognition.kernel.wiki_page_registry import StoredWikiPage, WikiPageRegistry
from runtime.cognition.tasks.approval_timing import evaluate_approval_timing
from runtime.cognition.tasks.registry_closeout_summary import build_registry_closeout_bridge
from runtime.cognition.tasks.wiki_governance_summary import build_wiki_governance_summary


def build_chief_of_staff_knowledge_workbench(
    *,
    workspace_root: str | None = None,
    trigger_mode: str = "manual",
) -> dict[str, object]:
    page_registry = WikiPageRegistry(chief_of_staff_wiki_root(workspace_root))
    schedule_registry = ScheduleRegistry(chief_of_staff_schedule_root(workspace_root))

    pages = page_registry.list_pages()
    schedules = schedule_registry.list_specs()
    audits = _load_recent_audits(workspace_root)
    generated_at = _timestamp_now()
    page_snapshots = [_page_snapshot(page, generated_at) for page in pages]
    approval_queue = [
        page
        for page in page_snapshots
        if page["pageStatus"] == "reviewing" and page["approvalStatus"] != "approved"
    ]
    governance = build_wiki_governance_summary(page_snapshots)
    snapshot = {
        "generatedAt": generated_at,
        "triggerMode": trigger_mode,
        "overview": _build_overview(page_snapshots),
        "governance": governance,
        "pages": page_snapshots,
        "approvalQueue": approval_queue,
        "approvalReport": _build_approval_report(approval_queue, generated_at, governance),
        "closeoutBridge": build_registry_closeout_bridge(
            schedules=schedules,
            workspace_root=workspace_root,
        ),
        "schedules": [
            {
                "scheduleId": schedule.object_id,
                "title": schedule.title,
                "targetType": schedule.payload.target_type,
                "targetRef": schedule.payload.target_ref,
                "scheduleType": schedule.payload.schedule_type,
                "scheduleExpression": schedule.payload.schedule_expression,
                "enabled": schedule.payload.enabled,
                "approvalGate": schedule.payload.approval_gate,
                "failurePolicy": schedule.payload.failure_policy,
                "note": schedule.payload.note or schedule.summary,
            }
            for schedule in schedules
        ],
        "audits": audits,
    }

    workbench_root = chief_of_staff_workbench_root(workspace_root)
    workbench_root.mkdir(parents=True, exist_ok=True)
    html_path = workbench_root / "index.html"
    json_path = workbench_root / "snapshot.json"
    json_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    html_path.write_text(_render_workbench_html(snapshot), encoding="utf-8")
    return {
        "status": "completed",
        "artifactPaths": [html_path.as_posix(), json_path.as_posix()],
        "note": "knowledge workbench rebuilt",
    }


def _build_overview(pages: list[dict[str, Any]]) -> dict[str, int]:
    stable_pages = sum(1 for page in pages if page["pageStatus"] == "stable")
    reviewing_pages = sum(1 for page in pages if page["pageStatus"] == "reviewing")
    working_pages = sum(1 for page in pages if page["pageStatus"] == "working")
    approval_pending = sum(
        1
        for page in pages
        if page["pageStatus"] == "reviewing" and page["approvalStatus"] != "approved"
    )
    warning_approvals = sum(1 for page in pages if page["approvalWarning"])
    overdue_approvals = sum(1 for page in pages if page["approvalOverdue"])
    return {
        "pageCount": len(pages),
        "stableCount": stable_pages,
        "reviewingCount": reviewing_pages,
        "workingCount": working_pages,
        "allRecallCount": len(pages),
        "approvalPendingCount": approval_pending,
        "warningApprovalCount": warning_approvals,
        "overdueApprovalCount": overdue_approvals,
    }


def _page_snapshot(page: StoredWikiPage, generated_at: str) -> dict[str, Any]:
    return {
        "pageId": page.page_id,
        "title": page.title,
        "pageStatus": page.page_status,
        "approvalStatus": page.approval_status,
        "reviewerRoute": list(page.reviewer_route),
        "primaryReviewer": page.primary_reviewer,
        "approvalSlaHours": page.approval_sla_hours,
        "approvalDueAt": page.approval_due_at,
        "reviewedBy": page.reviewed_by,
        "reviewedAt": page.reviewed_at,
        "approvalNote": page.approval_note,
        "updatedAt": page.updated_at,
        "sourceRefCount": len(page.source_refs),
        "sourceRefs": list(page.source_refs),
        "pagePath": page.page_path.as_posix(),
        "summary": _extract_section(page.body, "## 摘要"),
        "facts": _extract_bullets(_extract_section(page.body, "## 当前整理事实"))[:3],
        "openQuestions": _extract_bullets(_extract_section(page.body, "## 待确认问题"))[:3],
        **evaluate_approval_timing(
            approval_due_at=page.approval_due_at,
            approval_sla_hours=page.approval_sla_hours,
            reference_time=generated_at,
        ),
    }


def _build_approval_report(
    approval_queue: list[dict[str, Any]],
    generated_at: str,
    governance: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generatedAt": generated_at,
        "pendingCount": governance["pendingCount"],
        "warningCount": governance["warningCount"],
        "overdueCount": governance["overdueCount"],
        "routeCoverageCount": governance["routeCoverageCount"],
        "primaryReviewerCoverageCount": governance["primaryReviewerCoverageCount"],
        "slaCoverageCount": governance["slaCoverageCount"],
        "dueTrackedCount": governance["dueTrackedCount"],
        "dueTrackedExpectedCount": governance["dueTrackedExpectedCount"],
        "reviewerOwners": governance["reviewerOwners"],
        "reviewerRoutes": governance["reviewerRoutes"],
        "missingPolicyPages": governance["missingPolicyPages"],
        "pages": approval_queue,
    }


def _load_recent_audits(workspace_root: str | None) -> list[dict[str, Any]]:
    audit_root = chief_of_staff_audit_root(workspace_root)
    if not audit_root.exists():
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(audit_root.glob("*.json"), reverse=True)[:24]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        records.append(
            {
                "auditId": str(
                    payload.get("runId")
                    or payload.get("checkpointId")
                    or path.stem
                ),
                "kind": _audit_kind(path.name),
                "status": str(
                    payload.get("status") or payload.get("decision") or "recorded"
                ),
                "note": str(
                    payload.get("note")
                    or payload.get("closeoutSubject")
                    or payload.get("reason")
                    or payload.get("subject")
                    or ""
                ),
                "pageId": str(
                    payload.get("pageId")
                    or payload.get("closeoutId")
                    or payload.get("objectId")
                    or payload.get("checkpointId")
                    or ""
                ),
                "recordedAt": str(
                    payload.get("startedAt")
                    or payload.get("checkedAt")
                    or payload.get("reviewedAt")
                    or payload.get("generatedAt")
                    or ""
                ),
                "path": path.as_posix(),
            }
        )
    return records


def _audit_kind(file_name: str) -> str:
    prefixes = (
        "registry-closeout",
        "wiki-approval-report",
        "wiki-refresh",
        "wiki-promotion",
        "wiki-approval",
        "wiki-recall-checkpoint",
        "schedule-run",
        "reminder-delivery",
        "email-delivery",
        "checkpoint-approval-queue",
        "checkpoint-generic",
    )
    for prefix in prefixes:
        if file_name.startswith(prefix):
            return prefix
    return "audit"


def _extract_section(body: str, heading: str) -> str:
    start = body.find(heading)
    if start == -1:
        return ""
    start = body.find("\n", start)
    if start == -1:
        return ""
    start += 1
    next_heading = body.find("\n## ", start)
    if next_heading == -1:
        return body[start:].strip()
    return body[start:next_heading].strip()


def _extract_bullets(section: str) -> list[str]:
    bullets: list[str] = []
    for line in section.splitlines():
        text = line.strip()
        if text.startswith("- "):
            bullets.append(text[2:].strip())
    return bullets


def _render_workbench_html(snapshot: dict[str, Any]) -> str:
    overview = snapshot["overview"]
    governance = snapshot["governance"]
    approval_report = snapshot["approvalReport"]
    closeout_bridge = snapshot["closeoutBridge"]

    page_cards = "".join(_render_page_card(page) for page in snapshot["pages"])
    if not page_cards:
        page_cards = '<div class="empty-card">当前还没有可展示的 wiki 页面。</div>'

    approval_cards = "".join(
        _render_approval_card(page) for page in snapshot["approvalQueue"]
    )
    if not approval_cards:
        approval_cards = (
            '<div class="empty-card">当前没有待人工审批的 reviewing 页面。</div>'
        )

    schedule_cards = "".join(
        _render_schedule_card(schedule) for schedule in snapshot["schedules"]
    )
    if not schedule_cards:
        schedule_cards = '<div class="empty-card">当前没有启用中的 schedule。</div>'

    closeout_cards = "".join(
        _render_closeout_card(item) for item in closeout_bridge["entries"]
    )
    if not closeout_cards:
        closeout_cards = (
            '<div class="empty-card">当前还没有接入前台可见的中央收口桥接任务。</div>'
        )

    audit_cards = "".join(_render_audit_card(audit) for audit in snapshot["audits"])
    if not audit_cards:
        audit_cards = '<div class="empty-card">当前没有审计记录。</div>'

    governance_cards = "".join(
        (
            _render_signal_card(
                "Route 覆盖",
                f"{governance['routeCoverageCount']} / {governance['pageCount']}",
                "已配置 reviewer route 的页面数量。",
            ),
            _render_signal_card(
                "Owner 覆盖",
                (
                    f"{governance['primaryReviewerCoverageCount']} / "
                    f"{governance['pageCount']}"
                ),
                "已配置 primary reviewer 的页面数量。",
            ),
            _render_signal_card(
                "SLA 覆盖",
                f"{governance['slaCoverageCount']} / {governance['pageCount']}",
                "已配置 approval SLA 的页面数量。",
            ),
            _render_signal_card(
                "Due 跟踪",
                (
                    f"{governance['dueTrackedCount']} / "
                    f"{governance['dueTrackedExpectedCount']}"
                ),
                "reviewing 待审批页中已生成审批截止的数量。",
            ),
            _render_signal_card(
                "预警页",
                str(governance["warningCount"]),
                "reviewing 待审批页里已进入 SLA 预警窗口的数量。",
            ),
            _render_signal_card(
                "审批压力",
                str(governance["pendingCount"]),
                (
                    f"当前预警 {governance['warningCount']} 页，"
                    f"SLA 超时 {governance['overdueCount']} 页。"
                ),
            ),
        )
    )

    reviewer_lane_cards = "".join(
        _render_lane_card(owner) for owner in governance["reviewerOwners"]
    )
    if not reviewer_lane_cards:
        reviewer_lane_cards = (
            '<div class="empty-card">当前没有可展示的 reviewer owner 负载。</div>'
        )

    route_cards = "".join(_render_route_card(route) for route in governance["reviewerRoutes"])
    if not route_cards:
        route_cards = '<div class="empty-card">当前没有可展示的 Reviewer route。</div>'

    policy_cards = "".join(
        _render_policy_card(item) for item in governance["missingPolicyPages"]
    )
    if not policy_cards:
        policy_cards = (
            '<article class="policy-card success-card">'
            '<h3>治理配置完整</h3>'
            '<p>当前所有页面都已具备 Reviewer route、Primary reviewer 和 SLA 字段。'
            'reviewing 页面如进入审批队列，会继续追加 approvalDueAt。</p>'
            '</article>'
        )

    generated_at = html.escape(str(snapshot["generatedAt"]))
    queue_note = html.escape(
        (
            f"当前审批报表显示 {approval_report['pendingCount']} 个待审批页、"
            f"{approval_report['warningCount']} 个即将超时页、"
            f"{approval_report['overdueCount']} 个 SLA 超时页；"
            f"route / owner / SLA 覆盖为 "
            f"{approval_report['routeCoverageCount']} / {governance['pageCount']}、"
            f"{approval_report['primaryReviewerCoverageCount']} / {governance['pageCount']}、"
            f"{approval_report['slaCoverageCount']} / {governance['pageCount']}。"
        )
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>总助知识工作台</title>
  <style>
    :root {{
      --bg: #f5efe6;
      --panel: rgba(255, 251, 245, 0.92);
      --ink: #1d1a16;
      --muted: #64594e;
      --accent: #bc5a2c;
      --accent-deep: #7d3312;
      --line: rgba(125, 51, 18, 0.14);
      --stable: #1f6f50;
      --reviewing: #8b5a00;
      --working: #7a3e2a;
      --shadow: 0 24px 60px rgba(81, 45, 24, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Aptos, "Segoe UI Variable Display", "Microsoft YaHei UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(188, 90, 44, 0.16), transparent 24%),
        radial-gradient(circle at bottom right, rgba(31, 111, 80, 0.12), transparent 22%),
        linear-gradient(145deg, #f8f2e8 0%, #efe6da 100%);
    }}
    .shell {{ width: min(1440px, calc(100vw - 40px)); margin: 0 auto; padding: 24px 0 40px; }}
    .hero, .panel {{ border: 1px solid var(--line); border-radius: 24px; background: var(--panel); box-shadow: var(--shadow); }}
    .hero {{ padding: 28px; }}
    .hero-grid {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 20px; align-items: start; }}
    .eyebrow {{ letter-spacing: 0.18em; text-transform: uppercase; font-size: 12px; color: var(--accent-deep); margin-bottom: 10px; }}
    h1 {{ margin: 0; font-size: clamp(32px, 4vw, 56px); line-height: 1.02; font-weight: 760; }}
    .hero p {{ margin: 14px 0 0; color: var(--muted); line-height: 1.7; }}
    .stamp {{ padding: 14px 16px; border: 1px solid var(--line); border-radius: 18px; background: rgba(255,255,255,0.68); text-align: right; }}
    .stamp strong {{ display: block; font-size: 13px; color: var(--accent-deep); }}
    .stamp span {{ display: block; margin-top: 8px; color: var(--muted); }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 14px; margin-top: 22px; }}
    .metric {{ border-radius: 18px; background: rgba(255,255,255,0.72); border: 1px solid var(--line); padding: 16px; }}
    .metric .label {{ font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }}
    .metric .value {{ margin-top: 8px; font-size: 30px; font-weight: 760; }}
    .grid-two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 20px; }}
    .section-grid {{ display: grid; grid-template-columns: 1.35fr 0.95fr; gap: 18px; margin-top: 20px; }}
    .stack {{ display: grid; gap: 18px; }}
    .panel {{ padding: 22px; }}
    .panel h2 {{ margin: 0; font-size: 22px; }}
    .panel-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 14px; }}
    .panel-head p {{ margin: 0; color: var(--muted); font-size: 14px; }}
    .page-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .signal-grid, .policy-grid, .lane-grid, .route-grid, .queue-grid, .schedule-grid, .closeout-grid, .audit-grid {{ display: grid; gap: 12px; }}
    .lane-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .page-card, .queue-card, .schedule-card, .closeout-card, .audit-card, .empty-card, .signal-card, .lane-card, .route-card, .policy-card {{
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.74);
      padding: 16px;
    }}
    .signal-card .label {{ font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }}
    .signal-card .value {{ margin-top: 8px; font-size: 28px; font-weight: 760; }}
    .signal-card p, .page-card p, .queue-card p, .schedule-card p, .closeout-card p, .audit-card p, .lane-card p, .route-card p, .policy-card p {{ margin: 10px 0 0; color: var(--muted); line-height: 1.65; }}
    .card-top {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }}
    .status-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    .pill {{ display: inline-flex; align-items: center; padding: 6px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; background: rgba(125, 51, 18, 0.08); color: var(--accent-deep); }}
    .stable {{ background: rgba(31, 111, 80, 0.14); color: var(--stable); }}
    .reviewing {{ background: rgba(139, 90, 0, 0.16); color: var(--reviewing); }}
    .working {{ background: rgba(122, 62, 42, 0.14); color: var(--working); }}
    .approved {{ background: rgba(31, 111, 80, 0.12); color: var(--stable); }}
    .pending {{ background: rgba(139, 90, 0, 0.14); color: var(--reviewing); }}
    .rejected {{ background: rgba(122, 62, 42, 0.14); color: var(--working); }}
    .warning {{ background: rgba(188, 90, 44, 0.14); color: var(--accent-deep); }}
    .facts, .questions, .meta-list {{ margin: 12px 0 0; padding-left: 18px; line-height: 1.7; }}
    .facts li, .questions li, .meta-list li {{ margin-top: 6px; }}
    .panel-note {{ margin-bottom: 14px; padding: 12px 14px; border-radius: 16px; border: 1px solid var(--line); background: rgba(188, 90, 44, 0.06); color: var(--muted); line-height: 1.65; }}
    .success-card {{ background: rgba(31, 111, 80, 0.08); }}
    .warning-card {{ background: rgba(139, 90, 0, 0.08); }}
    .path-link {{ color: var(--accent-deep); text-decoration: none; word-break: break-all; }}
    .path-link:hover {{ text-decoration: underline; }}
    @media (max-width: 1120px) {{
      .hero-grid, .grid-two, .section-grid {{ grid-template-columns: 1fr; }}
      .page-grid, .lane-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="hero-grid">
        <div>
          <div class="eyebrow">Chief Of Staff Knowledge Workbench</div>
          <h1>总助知识工作台</h1>
          <p>前台工作台与后台执行链现在共用同一份页索引、审批状态和 schedule 总线。所有 wiki 页都可进入 recall，但 stable 仍保留更高可信级别和人工审批语义。</p>
        </div>
        <div class="stamp">
          <strong>最近生成时间</strong>
          <span>{generated_at}</span>
        </div>
      </div>
      <div class="metrics">
        {_render_metric('总页数', overview['pageCount'])}
        {_render_metric('全量 Recall', overview['allRecallCount'])}
        {_render_metric('Stable', overview['stableCount'])}
        {_render_metric('Reviewing', overview['reviewingCount'])}
        {_render_metric('Working', overview['workingCount'])}
        {_render_metric('待审批', overview['approvalPendingCount'])}
        {_render_metric('即将超时', overview['warningApprovalCount'])}
        {_render_metric('SLA 超时', overview['overdueApprovalCount'])}
      </div>
    </section>

    <div class="grid-two">
      <section class="panel">
        <div class="panel-head">
          <div>
            <h2>治理态势</h2>
            <p>把 Reviewer route、primary reviewer、SLA 与 due tracking 聚合成统一治理视图。</p>
          </div>
        </div>
        <div class="signal-grid">{governance_cards}</div>
        <div class="policy-grid">{policy_cards}</div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <div>
            <h2>Reviewer Lanes</h2>
            <p>按 primary reviewer 和 Reviewer route 观察页面负载与审批压力。</p>
          </div>
        </div>
        <div class="lane-grid">{reviewer_lane_cards}</div>
        <div class="route-grid">{route_cards}</div>
      </section>
    </div>

    <div class="section-grid">
      <section class="panel">
        <div class="panel-head">
          <div>
            <h2>Wiki 页面总览</h2>
            <p>工作台直接读取 knowledge/employees/ceo-chief-of-staff/wiki 下的实际页面对象。</p>
          </div>
        </div>
        <div class="page-grid">{page_cards}</div>
      </section>

      <div class="stack">
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>审批队列</h2>
              <p>reviewing 页面进入 stable 前必须经过人工审批，并按 Reviewer route 与 SLA 跟踪。</p>
            </div>
          </div>
          <div class="panel-note">{queue_note}</div>
          <div class="queue-grid">{approval_cards}</div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Schedule / Task Bus</h2>
              <p>同一总线承接 wiki、reminder、email、checkpoint、workbench、registry-closeout 和 operating-review-closeout 任务。</p>
            </div>
          </div>
          <div class="schedule-grid">{schedule_cards}</div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Central Registry Closeout</h2>
              <p>把中央收口 bridge 的 schedule 配置、最近一次派发结果和 operating review trigger source 直接挂到前台工作台里。</p>
            </div>
          </div>
          <div class="closeout-grid">{closeout_cards}</div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>最近审计</h2>
              <p>这里聚合 refresh、promotion、approval、delivery、checkpoint 和 closeout bridge 结果。</p>
            </div>
          </div>
          <div class="audit-grid">{audit_cards}</div>
        </section>
      </div>
    </div>
  </div>
</body>
</html>
"""


def _render_metric(label: str, value: int) -> str:
    return (
        '<div class="metric">'
        f'<div class="label">{html.escape(label)}</div>'
        f'<div class="value">{value}</div>'
        "</div>"
    )


def _render_signal_card(label: str, value: str, note: str) -> str:
    return (
        '<article class="signal-card">'
        f'<div class="label">{html.escape(label)}</div>'
        f'<div class="value">{html.escape(value)}</div>'
        f'<p>{html.escape(note)}</p>'
        "</article>"
    )


def _render_lane_card(owner: dict[str, Any]) -> str:
    route_labels = (
        " / ".join(str(item) for item in owner["routeLabels"] if str(item).strip())
        or "未配置"
    )
    return (
        '<article class="lane-card">'
        f'<h3>{html.escape(str(owner["reviewer"]))}</h3>'
        '<div class="status-row">'
        f'<span class="pill">页面 {owner["pageCount"]}</span>'
        f'<span class="pill">待审批 {owner["pendingCount"]}</span>'
        f'{_status_pill("warning") if owner["warningCount"] else ""}'
        f'{_status_pill("overdue") if owner["overdueCount"] else ""}'
        "</div>"
        '<ul class="meta-list">'
        f'<li>Stable / Reviewing / Working：{owner["stableCount"]} / {owner["reviewingCount"]} / {owner["workingCount"]}</li>'
        f'<li>当前预警：{owner["warningCount"]}</li>'
        f'<li>当前超时：{owner["overdueCount"]}</li>'
        f'<li>涉及 Reviewer route：{html.escape(route_labels)}</li>'
        "</ul>"
        "</article>"
    )


def _render_route_card(route: dict[str, Any]) -> str:
    primary_reviewers = (
        ", ".join(
            str(item) for item in route["primaryReviewers"] if str(item).strip()
        )
        or "未配置"
    )
    earliest_due_at = str(route["earliestDueAt"] or "当前无审批截止")
    card_class = "route-card warning-card" if route["overdueCount"] else "route-card"
    return (
        f'<article class="{card_class}">'
        f'<h3>{html.escape(str(route["routeLabel"]))}</h3>'
        '<div class="status-row">'
        f'<span class="pill">页面 {route["pageCount"]}</span>'
        f'<span class="pill">待审批 {route["pendingCount"]}</span>'
        f'{_status_pill("warning") if route["warningCount"] else ""}'
        f'{_status_pill("overdue") if route["overdueCount"] else ""}'
        "</div>"
        '<ul class="meta-list">'
        f'<li>Stable / Reviewing / Working：{route["stableCount"]} / {route["reviewingCount"]} / {route["workingCount"]}</li>'
        f'<li>当前预警：{route["warningCount"]}</li>'
        f'<li>Primary reviewer：{html.escape(primary_reviewers)}</li>'
        f'<li>最早审批截止：{html.escape(earliest_due_at)}</li>'
        "</ul>"
        "</article>"
    )


def _render_policy_card(item: dict[str, Any]) -> str:
    missing_fields = ", ".join(
        str(field) for field in item["missingFields"] if str(field).strip()
    )
    return (
        '<article class="policy-card warning-card">'
        f'<h3>{html.escape(str(item["title"]))}</h3>'
        f'<p>页面状态：{html.escape(str(item["pageStatus"]))}</p>'
        '<ul class="meta-list">'
        f'<li>页面 ID：{html.escape(str(item["pageId"]))}</li>'
        f'<li>待补字段：{html.escape(missing_fields)}</li>'
        "</ul>"
        "</article>"
    )


def _render_page_card(page: dict[str, Any]) -> str:
    facts = "".join(f"<li>{html.escape(item)}</li>" for item in page["facts"])
    questions = "".join(
        f"<li>{html.escape(item)}</li>" for item in page["openQuestions"]
    )
    facts_block = (
        f'<ul class="facts">{facts}</ul>'
        if facts
        else "<p>当前没有提取到事实摘要。</p>"
    )
    questions_block = (
        f'<ul class="questions">{questions}</ul>'
        if questions
        else "<p>当前没有待确认问题。</p>"
    )
    reviewed_line = ""
    if page["reviewedBy"] or page["reviewedAt"]:
        reviewed_line = (
            "<li>"
            f'最近审批：{html.escape(str(page["reviewedBy"]))} '
            f'{html.escape(str(page["reviewedAt"]))}'
            "</li>"
        )
    route = (
        ", ".join(str(item) for item in page["reviewerRoute"] if str(item).strip())
        or "未配置"
    )
    due_line = (
        f'<li>审批截止：{html.escape(str(page["approvalDueAt"]))}</li>'
        if page["approvalDueAt"]
        else ""
    )
    return (
        '<article class="page-card">'
        '<div class="card-top">'
        f'<h3>{html.escape(str(page["title"]))}</h3>'
        f'<a class="path-link" href="../wiki/{html.escape(Path(str(page["pagePath"])).name)}">打开页面</a>'
        "</div>"
        f'<p>{html.escape(str(page["summary"]))}</p>'
        '<div class="status-row">'
        f'{_status_pill(str(page["pageStatus"]))}'
        f'{_status_pill(str(page["approvalStatus"]))}'
        f'{_status_pill("warning") if page["approvalWarning"] else ""}'
        f'{_status_pill("overdue") if page["approvalOverdue"] else ""}'
        f'<span class="pill">来源 {page["sourceRefCount"]}</span>'
        "</div>"
        '<ul class="meta-list">'
        f'<li>页面 ID：{html.escape(str(page["pageId"]))}</li>'
        f'<li>更新时间：{html.escape(str(page["updatedAt"]))}</li>'
        f'<li>Primary reviewer：{html.escape(str(page["primaryReviewer"] or "未配置"))}</li>'
        f'<li>Reviewer route：{html.escape(route)}</li>'
        f'<li>审批 SLA：{html.escape(str(page["approvalSlaHours"] or "未配置"))}</li>'
        f"{due_line}"
        f'<li>审批态势：{html.escape(str(page["approvalTimeToDue"]))}</li>'
        f"{reviewed_line}"
        "</ul>"
        f"{facts_block}"
        f"{questions_block}"
        "</article>"
    )


def _render_approval_card(page: dict[str, Any]) -> str:
    note = (
        html.escape(str(page["approvalNote"]))
        if page["approvalNote"]
        else "尚无审批备注。"
    )
    route = (
        ", ".join(str(item) for item in page["reviewerRoute"] if str(item).strip())
        or "未配置"
    )
    return (
        '<article class="queue-card">'
        f'<h3>{html.escape(str(page["title"]))}</h3>'
        f'<p>{html.escape(str(page["summary"]))}</p>'
        '<div class="status-row">'
        f'{_status_pill(str(page["pageStatus"]))}'
        f'{_status_pill(str(page["approvalStatus"]))}'
        f'{_status_pill("warning") if page["approvalWarning"] else ""}'
        f'{_status_pill("overdue") if page["approvalOverdue"] else ""}'
        "</div>"
        '<ul class="meta-list">'
        f'<li>页面 ID：{html.escape(str(page["pageId"]))}</li>'
        f'<li>更新时间：{html.escape(str(page["updatedAt"]))}</li>'
        f'<li>Primary reviewer：{html.escape(str(page["primaryReviewer"] or "未配置"))}</li>'
        f'<li>Reviewer route：{html.escape(route)}</li>'
        f'<li>审批 SLA：{html.escape(str(page["approvalSlaHours"] or "未配置"))}</li>'
        f'<li>审批截止：{html.escape(str(page["approvalDueAt"] or "未生成"))}</li>'
        f'<li>审批态势：{html.escape(str(page["approvalTimeToDue"]))}</li>'
        f'<li>审批备注：{note}</li>'
        "</ul>"
        "</article>"
    )


def _render_schedule_card(schedule: dict[str, Any]) -> str:
    return (
        '<article class="schedule-card">'
        f'<h3>{html.escape(str(schedule["title"]))}</h3>'
        '<div class="status-row">'
        f'<span class="pill">{html.escape(str(schedule["targetType"]))}</span>'
        f'<span class="pill">{html.escape(str(schedule["scheduleType"]))}</span>'
        f'{_status_pill("enabled" if schedule["enabled"] else "disabled")}'
        "</div>"
        '<ul class="meta-list">'
        f'<li>targetRef：{html.escape(str(schedule["targetRef"]))}</li>'
        f'<li>表达式：{html.escape(str(schedule["scheduleExpression"]))}</li>'
        f'<li>审批门：{html.escape(str(schedule["approvalGate"]))}</li>'
        f'<li>失败策略：{html.escape(str(schedule["failurePolicy"]))}</li>'
        "</ul>"
        f'<p>{html.escape(str(schedule["note"]))}</p>'
        "</article>"
    )


def _render_closeout_card(item: dict[str, Any]) -> str:
    latest_subject = str(item["latestCloseoutSubject"] or "尚未执行 closeout bridge")
    latest_generated_at = str(item["latestGeneratedAt"] or "尚未生成")
    latest_audit_path = str(item["latestAuditPath"] or "")
    target_type = str(item["targetType"] or "registry-closeout")
    operating_review_path = str(item["operatingReviewPath"] or "")
    latest_trigger_object_type = str(item["latestTriggerObjectType"] or "")
    latest_trigger_object_id = str(item["latestTriggerObjectId"] or "")
    trigger_source = "未记录"
    if latest_trigger_object_type or latest_trigger_object_id:
        trigger_source = (
            f"{latest_trigger_object_type or 'unknown'} / "
            f"{latest_trigger_object_id or 'unknown'}"
        )

    audit_link = (
        f'<li><a class="path-link" href="../audit/{html.escape(Path(latest_audit_path).name)}">查看最近 closeout 审计</a></li>'
        if latest_audit_path
        else "<li>最近审计：尚未生成</li>"
    )
    delivery_target = str(
        item["latestDeliveryTarget"] or "knowledge/employees/ceo-chief-of-staff/audit"
    )
    source_path = str(item["sourcePath"] or "未配置")
    operating_review_line = (
        f'<li>operatingReviewPath：{html.escape(operating_review_path)}</li>'
        if operating_review_path
        else ""
    )

    return (
        '<article class="closeout-card">'
        f'<h3>{html.escape(str(item["title"]))}</h3>'
        f'<p>{html.escape(latest_subject)}</p>'
        '<div class="status-row">'
        f'<span class="pill">{html.escape(target_type)}</span>'
        f'{_status_pill("enabled" if item["enabled"] else "disabled")}'
        f'{_status_pill(str(item["latestDeliveryStatus"])) if item["latestDeliveryStatus"] != "not-run" else ""}'
        "</div>"
        '<ul class="meta-list">'
        f'<li>scheduleId：{html.escape(str(item["scheduleId"]))}</li>'
        f'<li>targetRef：{html.escape(str(item["targetRef"]))}</li>'
        f'<li>表达式：{html.escape(str(item["scheduleExpression"]))}</li>'
        f'<li>审批门：{html.escape(str(item["approvalGate"]))}</li>'
        f'<li>sourcePath：{html.escape(source_path)}</li>'
        f"{operating_review_line}"
        f'<li>最近派发：{html.escape(latest_generated_at)}</li>'
        f'<li>最近触发源：{html.escape(trigger_source)}</li>'
        f'<li>最近 findings：{item["latestRegistryFindingCount"]}</li>'
        f'<li>最近 delivery target：{html.escape(delivery_target)}</li>'
        f"{audit_link}"
        "</ul>"
        f'<p>{html.escape(str(item["note"]))}</p>'
        "</article>"
    )


def _render_audit_card(audit: dict[str, Any]) -> str:
    return (
        '<article class="audit-card">'
        f'<h3>{html.escape(str(audit["kind"]))}</h3>'
        '<div class="status-row">'
        f'{_status_pill(str(audit["status"]))}'
        f'<span class="pill">{html.escape(str(audit["recordedAt"]))}</span>'
        "</div>"
        f'<p>{html.escape(str(audit["note"]))}</p>'
        '<ul class="meta-list">'
        f'<li>对象：{html.escape(str(audit["pageId"]))}</li>'
        f'<li><a class="path-link" href="../audit/{html.escape(Path(str(audit["path"])).name)}">查看记录</a></li>'
        "</ul>"
        "</article>"
    )


def _status_pill(value: str) -> str:
    normalized = value.strip().lower()
    css_class = (
        normalized
        if normalized
        in {
            "stable",
            "reviewing",
            "working",
            "approved",
            "pending",
            "rejected",
            "warning",
            "overdue",
        }
        else ""
    )
    return f'<span class="pill {css_class}">{html.escape(value)}</span>'


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")