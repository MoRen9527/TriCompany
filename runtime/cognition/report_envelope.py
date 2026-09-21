"""ade_envelope — shared ADE envelope consumption helpers.

Single home for parsing ADE CLI output (source_publish_check and friends)
and locating a scope envelope inside it — either a bare envelope or the
combined-run reports container ``{protocol, version, reports: [...]}``.

Extracted in ADE phase 2 (work package 3) from two inline consumers:
  - employee_host_publish._delegate_agent_publish
  - employee_onboard.stage_6_check
Both previously inlined their own parse + container-branch logic; this
module is the one canonical consumer-side parser, with defensive handling
of malformed containers (reports not a list of dicts → None, never raise).
"""

from __future__ import annotations

import json
from typing import Any

# Must stay in sync with source_publish_check.ADE_PROTOCOL; duplicated here
# so consumer modules never need to import the heavyweight CLI module.
ADE_PROTOCOL: str = "ade-report"


def parse_cli_output(stdout_text: str) -> dict[str, Any] | None:
    """Parse CLI stdout as JSON; return None on invalid JSON / non-object."""
    try:
        data = json.loads(stdout_text)
    except (json.JSONDecodeError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def find_scope_envelope(data: dict[str, Any], scope: str) -> dict[str, Any] | None:
    """Locate the *scope* envelope inside an ADE CLI output payload.

    Accepts both a bare envelope and the combined-run reports container.
    Defensive: malformed containers (``reports`` not a list of dicts) yield
    None instead of raising, so consumers fall back to a "no envelope" path
    instead of crashing on a shape regression.
    """
    if data.get("protocol") == ADE_PROTOCOL and data.get("scope") == scope:
        return data
    reports = data.get("reports")
    if not isinstance(reports, list):
        return None
    for report in reports:
        if (
            isinstance(report, dict)
            and report.get("protocol") == ADE_PROTOCOL
            and report.get("scope") == scope
        ):
            return report
    return None


def extract_scope_envelope(
    stdout_text: str, scope: str
) -> dict[str, Any] | None:
    """Parse stdout and locate the *scope* envelope in one call.

    Returns None when the output is not valid JSON, is not an object, or
    contains no envelope for *scope* (bare or inside a reports container).
    """
    data = parse_cli_output(stdout_text)
    if data is None:
        return None
    return find_scope_envelope(data, scope)


def envelope_error_items(env: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the envelope's items whose action is ``error``."""
    items = env.get("items")
    if not isinstance(items, list):
        return []
    return [
        item for item in items
        if isinstance(item, dict) and item.get("action") == "error"
    ]
