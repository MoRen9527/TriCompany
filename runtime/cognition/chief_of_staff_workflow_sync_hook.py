from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


DEBUG_ENABLED = os.environ.get("TRICOMPANY_COGNITION_HOOK_DEBUG") == "1"
SYNC_SUCCESS_MESSAGE = (
    "chief-of-staff workflow bridge auto-synced repo memory after workflow writeback"
)


class HookSkip(RuntimeError):
    """Early exit that is only surfaced in debug mode."""


class HookSystemMessage(RuntimeError):
    """Early exit that should surface a system message to the host."""


def emit(system_message: str | None = None) -> int:
    payload: dict[str, Any] = {"continue": True}
    if system_message:
        payload["systemMessage"] = system_message
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def extract_command_text(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    if not isinstance(tool_input, dict):
        return ""

    for key in ("commandLine", "command", "text"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value

    args = tool_input.get("args")
    if isinstance(args, list):
        return " ".join(str(item) for item in args)
    return ""


def load_hook_input(stdin: Any = None) -> Mapping[str, Any]:
    input_stream = stdin or sys.stdin
    try:
        hook_input = json.load(input_stream)
    except json.JSONDecodeError as exc:
        raise HookSkip("hook debug: failed to decode stdin JSON") from exc

    if not isinstance(hook_input, dict):
        raise HookSkip("hook debug: stdin JSON was not an object")
    return hook_input


def validate_terminal_command(hook_input: Mapping[str, Any]) -> None:
    tool_name = str(hook_input.get("tool_name") or "").strip().lower()
    if "runinterminal" not in tool_name and "run_in_terminal" not in tool_name:
        raise HookSkip(f"hook debug: unsupported tool_name {tool_name}")

    command_text = extract_command_text(hook_input.get("tool_input")).strip()
    if not command_text:
        raise HookSkip("hook debug: command text missing from tool_input")

    normalized_command = command_text.lower()
    if "chief_of_staff_workflow_bridge" not in normalized_command:
        raise HookSkip(f"hook debug: ignored non-workflow command {command_text}")
    if "sync-memory" in normalized_command:
        raise HookSkip("hook debug: ignored sync-memory to avoid recursion")
    if not any(
        token in normalized_command
        for token in ("meeting-start", "meeting-end", "daily-close")
    ):
        raise HookSkip(
            f"hook debug: workflow command missing target token {command_text}"
        )


def resolve_roots(
    *,
    repo_root: Path | None = None,
    support_root: Path | None = None,
) -> tuple[Path, Path, str | None]:
    resolved_repo_root = repo_root or Path(
        os.environ.get("TRIMETAVERSE_REPO_ROOT") or Path(__file__).resolve().parents[2]
    )
    resolved_support_root = support_root or Path(
        os.environ.get("TRICOMPANY_COGNITION_SUPPORT_ROOT") or resolved_repo_root
    )
    storage_root = os.environ.get("TRICOMPANY_COGNITION_STORAGE_ROOT")
    return resolved_repo_root, resolved_support_root, storage_root


def build_sync_command(repo_root: Path, storage_root: str | None) -> list[str]:
    sync_command = [
        sys.executable or "python",
        "-m",
        "runtime.cognition.chief_of_staff_workflow_bridge",
        "--workspace-root",
        str(repo_root),
    ]
    if storage_root:
        sync_command.extend(["--storage-root", storage_root])
    sync_command.append("sync-memory")
    return sync_command


def parse_json_stdout(raw_output: str) -> dict[str, Any] | None:
    trimmed_output = raw_output.strip()
    if not trimmed_output:
        return None
    try:
        return json.loads(trimmed_output)
    except json.JSONDecodeError:
        return None


def run_sync_memory(repo_root: Path, support_root: Path, storage_root: str | None) -> str:
    if not support_root.exists():
        raise HookSystemMessage(
            f"chief-of-staff workflow hook skipped: support root not found at {support_root}"
        )

    result = subprocess.run(
        build_sync_command(repo_root, storage_root),
        cwd=support_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    parsed_stdout = parse_json_stdout(result.stdout or "")

    if result.returncode == 0 and parsed_stdout and parsed_stdout.get("exported"):
        return SYNC_SUCCESS_MESSAGE

    error_output = (result.stderr or result.stdout or "unknown sync error").strip()
    raise HookSystemMessage(
        f"chief-of-staff workflow hook could not run sync-memory: {error_output}"
    )


def run_hook(
    *,
    stdin: Any = None,
    repo_root: Path | None = None,
    support_root: Path | None = None,
) -> str:
    hook_input = load_hook_input(stdin)
    validate_terminal_command(hook_input)
    resolved_repo_root, resolved_support_root, storage_root = resolve_roots(
        repo_root=repo_root,
        support_root=support_root,
    )
    return run_sync_memory(resolved_repo_root, resolved_support_root, storage_root)


def main() -> int:
    try:
        system_message = run_hook()
    except HookSkip as exc:
        return emit(str(exc) if DEBUG_ENABLED else None)
    except HookSystemMessage as exc:
        return emit(str(exc))
    return emit(system_message)


if __name__ == "__main__":
    raise SystemExit(main())