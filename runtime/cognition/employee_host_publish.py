from __future__ import annotations

import argparse
import hashlib
import json as _json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.host_object_generation import (
    DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE,
    DECLARED_HOST_OBJECT_SETS,
    GeneratedHostObjectSet,
    HostObjectSetDefinition,
    _render_host_binding_profile,
    generate_host_object_set,
    host_binding_profile_path,
    write_host_binding_profiles,
)


EMPLOYEE_CHOICES = {
    "all": None,
    **{employee_id: (employee_id,) for employee_id in sorted(DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE)},
}


@dataclass(frozen=True)
class PublishedEmployeeHostAssets:
    employee_ids: tuple[str, ...]
    generated_host_object_sets: tuple[GeneratedHostObjectSet, ...]
    binding_profile_paths: tuple[Path, ...]


def publish_declared_employee_host_assets(
    *,
    source_root: str | Path,
    support_root: str | Path,
    employee_ids: tuple[str, ...] | None = None,
) -> PublishedEmployeeHostAssets:
    definitions = _selected_definitions(employee_ids)
    generated_host_object_sets = tuple(
        generate_host_object_set(support_root=support_root, definition=definition) for definition in definitions
    )
    normalized_employee_ids = tuple(definition.employee_id for definition in definitions)
    binding_profile_paths = write_host_binding_profiles(source_root, employee_ids=normalized_employee_ids)
    return PublishedEmployeeHostAssets(
        employee_ids=normalized_employee_ids,
        generated_host_object_sets=generated_host_object_sets,
        binding_profile_paths=binding_profile_paths,
    )


def _selected_definitions(employee_ids: tuple[str, ...] | None):
    if employee_ids is None:
        return DECLARED_HOST_OBJECT_SETS
    return tuple(DECLARED_HOST_OBJECT_SET_BY_EMPLOYEE[employee_id] for employee_id in employee_ids)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish declared TriCompany employee support payloads and source-side binding profiles together."
    )
    parser.add_argument("--source-root", default=".", help="Path to the TriCompany source root.")
    parser.add_argument("--support-root", required=True, help="Path to TriCompany-copilot-host-assets.")
    parser.add_argument(
        "--employee",
        default="all",
        choices=sorted(EMPLOYEE_CHOICES),
        help="Employee publish target. Defaults to all declared employees.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: 'text' (default) includes human-readable summary; 'json' emits only structured JSON on stdout.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Compute what would be generated/published without writing any files. "
             "This is the default when neither --dry-run nor --execute is given.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Explicitly write generated files. Required for any write; without it "
             "the CLI runs dry-run only (ADE safety gate: default is no write).",
    )
    args = parser.parse_args()

    if args.dry_run and args.execute:
        print("error: --dry-run and --execute are mutually exclusive", file=sys.stderr)
        return 2

    # Default behaviour (neither flag): dry-run (no writes) — ADE §2.4 safety gate.
    # Writing requires explicit --execute.
    execute = args.execute

    employee_ids = EMPLOYEE_CHOICES[args.employee]
    definitions = _selected_definitions(employee_ids)

    check_time = datetime.now(timezone.utc).isoformat()
    changes: list[dict] = []
    errors_list: list[dict] = []

    if execute:
        # ── Execute mode: full generation + write ──
        published: PublishedEmployeeHostAssets | None = None
        try:
            published = publish_declared_employee_host_assets(
                source_root=args.source_root,
                support_root=args.support_root,
                employee_ids=employee_ids,
            )
        except Exception as exc:
            errors_list.append({"employee_id": "*", "reason": f"publish_declared_employee_host_assets: {exc}"})

        if published is not None:
            _collect_execute_changes(published, definitions, changes, errors_list)

            if args.format == "text":
                for generated_host_object_set in published.generated_host_object_sets:
                    print(f"object_set={generated_host_object_set.object_set_id}")
                    print(f"role_workspace={generated_host_object_set.role_workspace.root.as_posix()}")
                    print(f"employee_workspace={generated_host_object_set.employee_workspace.root.as_posix()}")
                for binding_profile_path in published.binding_profile_paths:
                    print(f"binding_profile={binding_profile_path.as_posix()}")
                if published.generated_host_object_sets:
                    print(f"manifest={published.generated_host_object_sets[-1].manifest_path.as_posix()}")

        # ── Q3 Phase 2: delegate agent live entry publish to source_publish_check ─
        _delegate_agent_publish(source_root=args.source_root, support_root=args.support_root)
    else:
        # ── Dry-run mode: compute without writing ──
        _collect_dry_run_changes(definitions, args.source_root, args.support_root, changes, errors_list)

        if args.format == "text":
            print(
                f"[dry-run] Would process {len(definitions)} employee(s) "
                f"({', '.join(d.employee_id for d in definitions)})",
                file=sys.stderr,
            )

    # ── Build ADE structured self-check report ──
    total_employees = len(definitions)
    generated = sum(1 for c in changes if c["action"] == "generated")
    published_count = sum(1 for c in changes if c["action"] == "published")

    if errors_list:
        status = "fail"
    elif not execute:
        status = "pass"
    else:
        status = "pass"

    report = {
        "status": status,
        "check_time": check_time,
        "summary": {
            "total_employees": total_employees,
            "generated": generated,
            "published": published_count,
            "errors": len(errors_list),
        },
        "changes": changes,
        "errors": errors_list,
    }

    if args.format == "json":
        # ADE 合同出口：强制 UTF-8（Windows 中文环境默认 GBK 会破坏 JSON）。
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
        print(_json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_json.dumps(report, ensure_ascii=False))

    return 1 if errors_list else 0


# ── ADE helpers ──────────────────────────────────────────────────────────────


def _collect_execute_changes(
    published: PublishedEmployeeHostAssets,
    definitions: tuple[HostObjectSetDefinition, ...],
    changes: list[dict],
    errors_list: list[dict],
) -> None:
    """Populate changes and errors from an executed publish run."""
    for i, definition in enumerate(definitions):
        try:
            ghos = published.generated_host_object_sets[i]
        except IndexError:
            errors_list.append({"employee_id": definition.employee_id, "reason": "missing generated_host_object_set"})
            continue

        # Role workspace README
        role_readme = ghos.role_workspace.root / "README.md"
        changes.append({
            "employee_id": definition.employee_id,
            "action": "generated",
            "target": role_readme.as_posix(),
            "hash": _file_sha256(role_readme) if role_readme.is_file() else "",
        })

        # Employee workspace README
        emp_readme = ghos.employee_workspace.root / "README.md"
        changes.append({
            "employee_id": definition.employee_id,
            "action": "generated",
            "target": emp_readme.as_posix(),
            "hash": _file_sha256(emp_readme) if emp_readme.is_file() else "",
        })

    for bp_path in published.binding_profile_paths:
        employee_id = bp_path.stem
        changes.append({
            "employee_id": employee_id,
            "action": "published",
            "target": bp_path.as_posix(),
            "hash": _file_sha256(bp_path) if bp_path.is_file() else "",
        })


def _collect_dry_run_changes(
    definitions: tuple[HostObjectSetDefinition, ...],
    source_root: str,
    support_root: str,
    changes: list[dict],
    errors_list: list[dict],
) -> None:
    """Populate projected changes for a dry-run without touching disk."""
    source_root_path = Path(source_root)
    support_root_path = Path(support_root)
    for definition in definitions:
        # Binding profile projection
        bp_path = host_binding_profile_path(source_root_path, definition.employee_id)
        try:
            bp_content = _json.dumps(
                _render_host_binding_profile(definition), ensure_ascii=False, indent=2
            ) + "\n"
            bp_hash = hashlib.sha256(bp_content.encode("utf-8")).hexdigest()
        except Exception as exc:
            errors_list.append({"employee_id": definition.employee_id, "reason": f"render binding profile: {exc}"})
            bp_hash = ""

        # Host object projections (role + employee workspace README paths)
        role_readme = support_root_path / "knowledge" / "roles" / definition.role_id / "README.md"
        emp_readme = support_root_path / "knowledge" / "employees" / definition.employee_id / "README.md"

        changes.append({
            "employee_id": definition.employee_id,
            "action": "generated",
            "target": role_readme.as_posix(),
            "hash": hashlib.sha256(definition.object_set_id.encode()).hexdigest()[:16],
        })
        changes.append({
            "employee_id": definition.employee_id,
            "action": "generated",
            "target": emp_readme.as_posix(),
            "hash": hashlib.sha256(definition.employee_id.encode()).hexdigest()[:16],
        })
        changes.append({
            "employee_id": definition.employee_id,
            "action": "published",
            "target": bp_path.as_posix(),
            "hash": bp_hash,
        })


def _file_sha256(path: Path) -> str:
    """Return hex-encoded SHA-256 digest of a file, or empty string on failure."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _delegate_agent_publish(
    *,
    source_root: str,
    support_root: str,
) -> None:
    """Delegate agent live entry publish to source_publish_check --publish-agents.

    This is a subprocess call that runs after host object generation completes.
    The --publish-agents mode is dry-run by default; future phases may add
    --agent-execute when auto-write is approved.
    """
    source_publish_check_script = Path(source_root) / "runtime" / "cognition" / "source_publish_check.py"
    if not source_publish_check_script.exists():
        print(
            f"[employee_host_publish] source_publish_check not found at "
            f"{source_publish_check_script.as_posix()}; skipping agent publish delegation.",
            file=sys.stderr,
        )
        return

    print(
        "[employee_host_publish] delegating agent live entry publish to source_publish_check --publish-agents ...",
        file=sys.stderr,
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m", "runtime.cognition.source_publish_check",
            "--publish-agents",
            "--source-root", source_root,
            "--support-root", support_root,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )

    if result.returncode != 0:
        print(
            f"[employee_host_publish] agent publish delegation exited with code "
            f"{result.returncode}",
            file=sys.stderr,
        )
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return

    # Print human-readable summary from the agent publish output.
    # ADE phase 1: the delegation emits the unified envelope (protocol
    # ade-report, scope publish-agents) — either directly or inside a
    # reports container for combined runs. ADE phase 2: parsing is shared
    # via ade_envelope.extract_scope_envelope (container-branch defensive).
    from runtime.cognition.ade_envelope import extract_scope_envelope
    env = extract_scope_envelope(result.stdout, "publish-agents")
    if env is not None:
        summary = env.get("summary", {})
        counts = env.get("scope_specific", {}).get("counts", {})
        print(
            f"[employee_host_publish] agent publish complete — "
            f"total={summary.get('total', 0)}, "
            f"identical={counts.get('skipped_identical', 0)}, "
            f"would_sync={counts.get('skipped_dry_run', 0)}, "
            f"errors={summary.get('errors', 0)}",
            file=sys.stderr,
        )
    else:
        print(
            "[employee_host_publish] agent publish output has no "
            "publish-agents envelope; skipping summary.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    raise SystemExit(main())