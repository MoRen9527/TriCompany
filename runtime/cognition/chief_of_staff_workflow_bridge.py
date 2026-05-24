from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.chief_of_staff_cognition import (
    CHIEF_OF_STAFF_ID,
    build_ceo_chief_of_staff_kernel,
)
from runtime.cognition.providers.storage import FileBackedCognitionStore


WORKFLOW_PROVIDER_NAME = "chief-of-staff-workflow-bridge"
WORKFLOW_ENTRY_TITLES = {
    "workflow-meeting-start",
    "workflow-meeting-end",
    "workflow-daily-close",
}
REPO_MEMORY_IMPORT_TITLE = "repo-memory-import"
MEMORY_FILE_PARTS = (".github", "source-agents", "ceo-chief-of-staff", "ceo-chief-of-staff.memory.md")
EVENT_LINE_MEETING_START = "- event-type: meeting-start"
EVENT_LINE_MEETING_END = "- event-type: meeting-end"
EVENT_LINE_DAILY_CLOSE = "- event-type: daily-close"
KERNEL_ENTRY_LINE = "- kernel-entry: build_ceo_chief_of_staff_kernel"
MANAGED_SECTION_TITLE = "## Cognition 同步摘录"
MANAGED_SECTION_START = "<!-- chief-of-staff-cognition-sync:start -->"
MANAGED_SECTION_END = "<!-- chief-of-staff-cognition-sync:end -->"
MANAGED_SECTION_NOTE = (
    "本节由 runtime/cognition workflow bridge 维护，只回收 "
    "TRICOMPANY_COGNITION_HOME 中需要回写到仓库主档的摘录，不覆盖上面的手工记忆。"
)
ENTRY_PATTERN = re.compile(
    r"^## (?P<title>[^\n]+)\n"
    r"- provider: (?P<provider>[^\n]+)\n"
    r"- timestamp: (?P<timestamp>[^\n]+)\n\n"
    r"(?P<body>.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)


@dataclass(frozen=True)
class ActionItem:
    owner: str
    action: str
    due_at: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ActionItem:
        return cls(
            owner=str(_first_present(payload, "owner", default="")).strip(),
            action=str(_first_present(payload, "action", default="")).strip(),
            due_at=str(
                _first_present(payload, "due_at", "dueAt", default="")
            ).strip(),
        )


@dataclass(frozen=True)
class MeetingStartPayload:
    meeting_name: str
    purpose: str
    participants: tuple[str, ...]
    background: str
    agenda: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    recording_boundary: str = ""
    gaps: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> MeetingStartPayload:
        return cls(
            meeting_name=str(
                _first_present(payload, "meeting_name", "meetingName", default="")
            ).strip(),
            purpose=str(_first_present(payload, "purpose", default="")).strip(),
            participants=_string_tuple(
                _first_present(payload, "participants", "participantRoles", default=())
            ),
            background=str(_first_present(payload, "background", default="")).strip(),
            agenda=_string_tuple(_first_present(payload, "agenda", default=())),
            expected_outputs=_string_tuple(
                _first_present(payload, "expected_outputs", "expectedOutputs", default=())
            ),
            recording_boundary=str(
                _first_present(
                    payload,
                    "recording_boundary",
                    "recordingBoundary",
                    default="",
                )
            ).strip(),
            gaps=_string_tuple(_first_present(payload, "gaps", default=())),
        )


@dataclass(frozen=True)
class MeetingEndPayload:
    meeting_name: str
    conclusions: tuple[str, ...]
    frozen_items: tuple[str, ...]
    escalations: tuple[str, ...]
    action_items: tuple[ActionItem, ...]
    backfill_targets: tuple[str, ...]
    follow_up_entry: str
    gaps: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> MeetingEndPayload:
        return cls(
            meeting_name=str(
                _first_present(payload, "meeting_name", "meetingName", default="")
            ).strip(),
            conclusions=_string_tuple(
                _first_present(payload, "conclusions", default=())
            ),
            frozen_items=_string_tuple(
                _first_present(payload, "frozen_items", "frozenItems", default=())
            ),
            escalations=_string_tuple(
                _first_present(payload, "escalations", default=())
            ),
            action_items=_action_items_tuple(
                _first_present(payload, "action_items", "actionItems", default=())
            ),
            backfill_targets=_string_tuple(
                _first_present(payload, "backfill_targets", "backfillTargets", default=())
            ),
            follow_up_entry=str(
                _first_present(payload, "follow_up_entry", "followUpEntry", default="")
            ).strip(),
            gaps=_string_tuple(_first_present(payload, "gaps", default=())),
        )


@dataclass(frozen=True)
class DailyClosePayload:
    date_label: str
    summary: str
    completed_items: tuple[str, ...]
    unresolved_items: tuple[str, ...]
    next_actions: tuple[ActionItem, ...]
    docs_to_update: tuple[str, ...]
    notes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> DailyClosePayload:
        return cls(
            date_label=str(
                _first_present(payload, "date_label", "dateLabel", "day", default="")
            ).strip(),
            summary=str(_first_present(payload, "summary", default="")).strip(),
            completed_items=_string_tuple(
                _first_present(payload, "completed_items", "completedItems", default=())
            ),
            unresolved_items=_string_tuple(
                _first_present(payload, "unresolved_items", "unresolvedItems", default=())
            ),
            next_actions=_action_items_tuple(
                _first_present(payload, "next_actions", "nextActions", default=())
            ),
            docs_to_update=_string_tuple(
                _first_present(payload, "docs_to_update", "docsToUpdate", default=())
            ),
            notes=_string_tuple(_first_present(payload, "notes", default=())),
        )


@dataclass(frozen=True)
class WorkflowWriteResult:
    event_type: str
    private_namespace: str
    org_shared_namespace: str
    audit_namespace: str


@dataclass(frozen=True)
class MemorySyncResult:
    imported: bool
    exported: bool
    managed_entry_count: int


@dataclass(frozen=True)
class StoredMarkdownEntry:
    title: str
    provider_name: str
    timestamp: str
    body: str


class ChiefOfStaffWorkflowBridge:
    """Workflow writeback bridge for meeting and daily-close events."""

    def __init__(
        self,
        *,
        storage_root: str | Path | None = None,
        workspace_root: str | Path | None = None,
    ) -> None:
        self.workspace_root = _workspace_root(workspace_root)
        self.store = FileBackedCognitionStore(storage_root)
        self.kernel = build_ceo_chief_of_staff_kernel(
            storage_root=str(self.store.storage_root),
            workspace_root=self.workspace_root,
        )

    @property
    def memory_repo_path(self) -> Path:
        return self.workspace_root.joinpath(*MEMORY_FILE_PARTS)

    def record_meeting_start(self, payload: MeetingStartPayload) -> WorkflowWriteResult:
        summary = f"{payload.meeting_name} 已进入正式会议记录口径"
        private_body = _join_sections(
            EVENT_LINE_MEETING_START,
            f"- meeting-name: {payload.meeting_name}",
            f"- summary: {summary}",
            f"- purpose: {payload.purpose}",
            f"- participants: {_csv_or_placeholder(payload.participants)}",
            f"- background: {payload.background or '未提供'}",
            _multiline_items("agenda", payload.agenda),
            _multiline_items("expected-outputs", payload.expected_outputs),
            f"- recording-boundary: {payload.recording_boundary or '从开始会议确认起进入正式记录口径'}",
            _multiline_items("gaps", payload.gaps),
        )
        shared_body = _join_sections(
            EVENT_LINE_MEETING_START,
            f"- meeting-name: {payload.meeting_name}",
            f"- summary: {summary}",
            f"- purpose: {payload.purpose}",
            f"- participants: {_csv_or_placeholder(payload.participants)}",
        )
        audit_body = _join_sections(
            EVENT_LINE_MEETING_START,
            "- source-entrypoint: 开始会议",
            f"- meeting-name: {payload.meeting_name}",
            KERNEL_ENTRY_LINE,
            f"- repo-memory-path: {_display_path(self.memory_repo_path, self.workspace_root)}",
        )
        return self._record_event(
            title="workflow-meeting-start",
            user_content=(
                "请把以下开始会议结果写入 cognition。\n" f"{private_body}"
            ),
            assistant_content=(
                "已按开始会议口径写回 cognition。\n" f"{shared_body}"
            ),
            private_body=private_body,
            shared_body=shared_body,
            audit_body=audit_body,
            event_type="meeting-start",
        )

    def record_meeting_end(self, payload: MeetingEndPayload) -> WorkflowWriteResult:
        summary = f"{payload.meeting_name} 已完成正式收口"
        private_body = _join_sections(
            EVENT_LINE_MEETING_END,
            f"- meeting-name: {payload.meeting_name}",
            f"- summary: {summary}",
            _multiline_items("conclusions", payload.conclusions),
            _multiline_items("frozen-items", payload.frozen_items),
            _multiline_items("escalations", payload.escalations),
            _multiline_action_items("action-items", payload.action_items),
            _multiline_items("backfill-targets", payload.backfill_targets),
            f"- follow-up-entry: {payload.follow_up_entry or '待补'}",
            _multiline_items("gaps", payload.gaps),
        )
        shared_body = _join_sections(
            EVENT_LINE_MEETING_END,
            f"- meeting-name: {payload.meeting_name}",
            f"- summary: {summary}",
            _multiline_items("conclusions", payload.conclusions[:3]),
            _multiline_action_items("action-items", payload.action_items[:3]),
        )
        audit_body = _join_sections(
            EVENT_LINE_MEETING_END,
            "- source-entrypoint: 结束会议",
            f"- meeting-name: {payload.meeting_name}",
            KERNEL_ENTRY_LINE,
            f"- follow-up-entry: {payload.follow_up_entry or '待补'}",
        )
        return self._record_event(
            title="workflow-meeting-end",
            user_content=(
                "请把以下结束会议结果写入 cognition。\n" f"{private_body}"
            ),
            assistant_content=(
                "已按结束会议口径写回 cognition。\n" f"{shared_body}"
            ),
            private_body=private_body,
            shared_body=shared_body,
            audit_body=audit_body,
            event_type="meeting-end",
        )

    def record_daily_close(self, payload: DailyClosePayload) -> WorkflowWriteResult:
        summary = payload.summary or f"{payload.date_label} 日常收口已记录"
        private_body = _join_sections(
            EVENT_LINE_DAILY_CLOSE,
            f"- day: {payload.date_label}",
            f"- summary: {summary}",
            _multiline_items("completed-items", payload.completed_items),
            _multiline_items("unresolved-items", payload.unresolved_items),
            _multiline_action_items("next-actions", payload.next_actions),
            _multiline_items("docs-to-update", payload.docs_to_update),
            _multiline_items("notes", payload.notes),
        )
        shared_body = _join_sections(
            EVENT_LINE_DAILY_CLOSE,
            f"- day: {payload.date_label}",
            f"- summary: {summary}",
            _multiline_action_items("next-actions", payload.next_actions[:3]),
        )
        audit_body = _join_sections(
            EVENT_LINE_DAILY_CLOSE,
            "- source-entrypoint: 日常收口",
            f"- day: {payload.date_label}",
            KERNEL_ENTRY_LINE,
            _multiline_items("docs-to-update", payload.docs_to_update),
        )
        return self._record_event(
            title="workflow-daily-close",
            user_content=(
                "请把以下日常收口结果写入 cognition。\n" f"{private_body}"
            ),
            assistant_content=(
                "已按日常收口口径写回 cognition。\n" f"{shared_body}"
            ),
            private_body=private_body,
            shared_body=shared_body,
            audit_body=audit_body,
            event_type="daily-close",
        )

    def import_repo_memory_snapshot(self) -> bool:
        if not self.memory_repo_path.exists():
            raise FileNotFoundError(self.memory_repo_path)

        content = self.memory_repo_path.read_text(encoding="utf-8").strip()
        source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        private_namespace = self.kernel.namespaces_for(CHIEF_OF_STAFF_ID).private_namespace.key
        existing = self.store.read_namespace(private_namespace)
        if f"- source-hash: {source_hash}" in existing:
            return False

        relative_path = _display_path(self.memory_repo_path, self.workspace_root)
        body = _join_sections(
            "- event-type: repo-memory-import",
            f"- source: {relative_path}",
            f"- source-hash: {source_hash}",
            "- summary: 已把仓库主档快照导入 cognition private namespace",
            content,
        )
        bundle = self.kernel.namespaces_for(CHIEF_OF_STAFF_ID)
        self.store.append_entry(
            bundle.private_namespace.key,
            title=REPO_MEMORY_IMPORT_TITLE,
            body=body,
            provider_name=WORKFLOW_PROVIDER_NAME,
        )
        self.store.append_entry(
            bundle.audit_namespace.key,
            title=REPO_MEMORY_IMPORT_TITLE,
            body=_join_sections(
                "- event-type: repo-memory-import",
                f"- source: {relative_path}",
                f"- source-hash: {source_hash}",
                f"- target-namespace: {bundle.private_namespace.key}",
            ),
            provider_name=WORKFLOW_PROVIDER_NAME,
        )
        return True

    def export_cognition_digest_to_repo_memory(self, *, limit: int = 5) -> tuple[bool, int]:
        if not self.memory_repo_path.exists():
            raise FileNotFoundError(self.memory_repo_path)

        private_namespace = self.kernel.namespaces_for(CHIEF_OF_STAFF_ID).private_namespace.key
        entries = _parse_markdown_entries(self.store.read_namespace(private_namespace))
        workflow_entries = [
            entry
            for entry in entries
            if entry.provider_name == WORKFLOW_PROVIDER_NAME
            and entry.title in WORKFLOW_ENTRY_TITLES
        ]
        import_entries = [
            entry
            for entry in entries
            if entry.provider_name == WORKFLOW_PROVIDER_NAME
            and entry.title == REPO_MEMORY_IMPORT_TITLE
        ]
        workflow_entries.sort(key=lambda item: item.timestamp, reverse=True)
        import_entries.sort(key=lambda item: item.timestamp, reverse=True)
        selected_workflows = workflow_entries[:limit]
        managed_block = self._managed_section_block(
            workflow_entries=selected_workflows,
            import_entries=import_entries[:1],
        )
        original = self.memory_repo_path.read_text(encoding="utf-8")
        updated = _replace_or_append_managed_section(original, managed_block)
        if updated == original:
            return False, len(selected_workflows)
        self.memory_repo_path.write_text(updated, encoding="utf-8")
        return True, len(selected_workflows)

    def sync_repo_memory_bidirectional(self, *, limit: int = 5) -> MemorySyncResult:
        imported = self.import_repo_memory_snapshot()
        exported, managed_entry_count = self.export_cognition_digest_to_repo_memory(
            limit=limit
        )
        return MemorySyncResult(
            imported=imported,
            exported=exported,
            managed_entry_count=managed_entry_count,
        )

    def _managed_section_block(
        self,
        *,
        workflow_entries: Sequence[StoredMarkdownEntry],
        import_entries: Sequence[StoredMarkdownEntry],
    ) -> str:
        lines = [
            MANAGED_SECTION_TITLE,
            "",
            MANAGED_SECTION_NOTE,
            "",
            MANAGED_SECTION_START,
            "### 最近 workflow 写回",
        ]
        if workflow_entries:
            lines.extend(_summarize_workflow_entry(entry) for entry in workflow_entries)
        else:
            lines.append("- 暂无 runtime workflow 写回。")

        lines.extend(["", "### 最近同步状态"])
        if import_entries:
            lines.extend(_summarize_import_entry(entry) for entry in import_entries)
        else:
            lines.append("- 暂无 repo memory 导入记录。")

        lines.extend([MANAGED_SECTION_END, ""])
        return "\n".join(lines)

    def _record_event(
        self,
        *,
        title: str,
        user_content: str,
        assistant_content: str,
        private_body: str,
        shared_body: str,
        audit_body: str,
        event_type: str,
    ) -> WorkflowWriteResult:
        bundle = self.kernel.namespaces_for(CHIEF_OF_STAFF_ID)
        self.kernel.sync_turn(CHIEF_OF_STAFF_ID, user_content, assistant_content)
        self.kernel.session_end(
            CHIEF_OF_STAFF_ID,
            [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content},
            ],
        )
        self.store.append_entry(
            bundle.private_namespace.key,
            title=title,
            body=private_body,
            provider_name=WORKFLOW_PROVIDER_NAME,
        )
        self.store.append_entry(
            bundle.org_shared_namespace.key,
            title=title,
            body=shared_body,
            provider_name=WORKFLOW_PROVIDER_NAME,
        )
        self.store.append_entry(
            bundle.audit_namespace.key,
            title=title,
            body=audit_body,
            provider_name=WORKFLOW_PROVIDER_NAME,
        )
        return WorkflowWriteResult(
            event_type=event_type,
            private_namespace=bundle.private_namespace.key,
            org_shared_namespace=bundle.org_shared_namespace.key,
            audit_namespace=bundle.audit_namespace.key,
        )


def _action_items_tuple(value: Any) -> tuple[ActionItem, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    result: list[ActionItem] = []
    for item in value:
        if isinstance(item, Mapping):
            action_item = ActionItem.from_dict(item)
        else:
            action_item = ActionItem(owner="", action=str(item).strip())
        if action_item.action:
            result.append(action_item)
    return tuple(result)


def _csv_or_placeholder(items: Sequence[str]) -> str:
    return ", ".join(items) if items else "未提供"


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _first_present(mapping: Mapping[str, Any], *keys: str, default: Any) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


def _join_sections(*parts: str) -> str:
    return "\n".join(part for part in parts if part).strip()


def _multiline_action_items(label: str, items: Sequence[ActionItem]) -> str:
    if not items:
        return f"- {label}: 无"
    lines = [f"- {label}:"]
    for item in items:
        detail = item.action
        if item.owner:
            detail += f" | owner: {item.owner}"
        if item.due_at:
            detail += f" | due: {item.due_at}"
        lines.append(f"  - {detail}")
    return "\n".join(lines)


def _multiline_items(label: str, items: Sequence[str]) -> str:
    if not items:
        return f"- {label}: 无"
    lines = [f"- {label}:"]
    for item in items:
        lines.append(f"  - {item}")
    return "\n".join(lines)


def _parse_markdown_entries(content: str) -> list[StoredMarkdownEntry]:
    if not content:
        return []
    entries: list[StoredMarkdownEntry] = []
    for match in ENTRY_PATTERN.finditer(content.strip()):
        entries.append(
            StoredMarkdownEntry(
                title=match.group("title").strip(),
                provider_name=match.group("provider").strip(),
                timestamp=match.group("timestamp").strip(),
                body=match.group("body").strip(),
            )
        )
    return entries


def _replace_or_append_managed_section(content: str, block: str) -> str:
    pattern = re.compile(
        rf"\n?{re.escape(MANAGED_SECTION_TITLE)}.*?{re.escape(MANAGED_SECTION_END)}\n?",
        re.DOTALL,
    )
    if pattern.search(content):
        replaced = pattern.sub(f"\n\n{block}\n", content).strip()
        return f"{replaced}\n"
    stripped = content.rstrip()
    return f"{stripped}\n\n{block}\n"


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    result = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return tuple(result)


def _summarize_import_entry(entry: StoredMarkdownEntry) -> str:
    source = _value_from_body(entry.body, "source") or "未知来源"
    source_hash = _value_from_body(entry.body, "source-hash") or "unknown"
    summary = _value_from_body(entry.body, "summary") or "已导入仓库主档"
    return f"- {entry.timestamp} | {summary} | {source} | hash: {source_hash}"


def _summarize_workflow_entry(entry: StoredMarkdownEntry) -> str:
    event_type = _value_from_body(entry.body, "event-type") or entry.title
    label = _value_from_body(entry.body, "meeting-name") or _value_from_body(
        entry.body, "day"
    )
    summary = _value_from_body(entry.body, "summary") or "已写回 cognition"
    if label:
        return f"- {entry.timestamp} | {event_type} | {label} | {summary}"
    return f"- {entry.timestamp} | {event_type} | {summary}"


def _value_from_body(body: str, key: str) -> str:
    prefix = f"- {key}:"
    for line in body.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def _workspace_root(path: str | Path | None) -> Path:
    if path is not None:
        return _workspace_root_with_memory(Path(path))

    source_root = Path(__file__).resolve().parents[2]
    resolved_root = _workspace_root_with_memory(source_root)
    if resolved_root.joinpath(*MEMORY_FILE_PARTS).exists():
        return resolved_root

    return source_root


def _workspace_root_with_memory(root: Path) -> Path:
    candidates = (
        root,
        root / "TriCompany",
        root.parent / "TriCompany",
        root.parent.parent / "TriCompany",
    )
    for candidate in candidates:
        if candidate.joinpath(*MEMORY_FILE_PARTS).exists():
            return candidate
    return root


def _load_json(path: str | Path) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_json_from_stdin() -> Mapping[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("stdin JSON payload is empty")
    return json.loads(raw)


def _load_payload(*, json_path: str | None, json_stdin: bool) -> Mapping[str, Any]:
    if json_stdin:
        return _load_json_from_stdin()
    if json_path is None:
        raise ValueError("either --json or --json-stdin is required")
    return _load_json(json_path)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Chief-of-staff workflow bridge for cognition writeback and sync."
    )
    parser.add_argument("--workspace-root", dest="workspace_root")
    parser.add_argument("--storage-root", dest="storage_root")

    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("meeting-start", "meeting-end", "daily-close"):
        command_parser = subparsers.add_parser(command)
        input_group = command_parser.add_mutually_exclusive_group(required=True)
        input_group.add_argument("--json", dest="json_path")
        input_group.add_argument(
            "--json-stdin",
            action="store_true",
            dest="json_stdin",
        )

    subparsers.add_parser("import-memory")

    export_parser = subparsers.add_parser("export-memory")
    export_parser.add_argument("--limit", type=int, default=5)

    sync_parser = subparsers.add_parser("sync-memory")
    sync_parser.add_argument("--limit", type=int, default=5)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    bridge = ChiefOfStaffWorkflowBridge(
        storage_root=args.storage_root,
        workspace_root=args.workspace_root,
    )

    if args.command == "meeting-start":
        payload = _load_payload(json_path=args.json_path, json_stdin=args.json_stdin)
        result = bridge.record_meeting_start(MeetingStartPayload.from_dict(payload))
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0

    if args.command == "meeting-end":
        payload = _load_payload(json_path=args.json_path, json_stdin=args.json_stdin)
        result = bridge.record_meeting_end(MeetingEndPayload.from_dict(payload))
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0

    if args.command == "daily-close":
        payload = _load_payload(json_path=args.json_path, json_stdin=args.json_stdin)
        result = bridge.record_daily_close(DailyClosePayload.from_dict(payload))
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0

    if args.command == "import-memory":
        print(
            json.dumps(
                {"imported": bridge.import_repo_memory_snapshot()},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "export-memory":
        exported, managed_entry_count = bridge.export_cognition_digest_to_repo_memory(
            limit=args.limit
        )
        print(
            json.dumps(
                {
                    "exported": exported,
                    "managed_entry_count": managed_entry_count,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "sync-memory":
        result = bridge.sync_repo_memory_bidirectional(limit=args.limit)
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())