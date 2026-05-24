from __future__ import annotations


def decide_failure_status(policy: str, error_message: str) -> tuple[str, str | None]:
    if policy == "freeze":
        return "frozen", error_message
    if policy == "retry-then-freeze":
        return "frozen", error_message
    if policy == "escalate":
        return "escalated", error_message
    return "failed", error_message