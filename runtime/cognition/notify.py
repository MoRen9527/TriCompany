"""notify — 通用经营通知能力（canonical 实现，CPO/CTO 裁决）

职责：主题/正文/收件人 → 投递（SMTP 邮件），best-effort 非阻塞。
内容组装是调用方职责（周平面 8w 清单等业务语义在调用方）。

短期待办：通道执行层未来可能随 TriGateway 扩展（对外通信网关）迁移，
通知编排层（谁/何时/什么内容）保留在 TriCompany。

用法（CLI）:
  python -m runtime.cognition.notify send --to a@x,b@y --subject "..." --body "..."

配置（env）:
  NOTIFY_SMTP_HOST / PORT / USER / PASS / FROM   (canonical)
  WEEKLY_SHIFT_SMTP_*                            (兼容回退, 过渡期)
"""

from __future__ import annotations

import argparse
import json as _json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.header import Header
from email.mime.text import MIMEText
from pathlib import Path


def _check_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit_root() -> Path | None:
    """Audit JSON dir (chief_of_staff_audit_root pattern), best-effort."""
    root = os.environ.get("TRICOMPANY_AUDIT_ROOT")
    if root:
        return Path(root) / "notifications"
    return None


def _config_path() -> Path:
    """Config file: NOTIFY_CONFIG env → ~/.trimetaverse/notify.json."""
    env = os.environ.get("NOTIFY_CONFIG")
    if env:
        return Path(env)
    home = Path.home()
    return home / ".trimetaverse" / "notify.json"


def _load_config() -> dict:
    """Load notify config JSON (best-effort). Sensitive pass stays in the file (chmod 600)."""
    try:
        p = _config_path()
        if p.exists():
            import json as _j
            with open(p, "r", encoding="utf-8") as f:
                data = _j.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def send_notification(
    *,
    subject: str,
    body: str,
    to: list[str],
    cc: list[str] | None = None,
    context_id: str | None = None,
    trigger_mode: str = "manual",
    dry_run: bool = False,
) -> dict:
    """Send a notification email (best-effort, never raises).

    Returns {status: sent|render_only|email_failed, ...}.
    """
    result: dict = {
        "objectType": "NOTIFICATION",
        "status": "render_only",  # downgrade default: no SMTP config → render only
        "subject": subject,
        "to": to,
        "cc": cc or [],
        "context_id": context_id,
        "trigger_mode": trigger_mode,
        "dry_run": dry_run,
        "check_time": _check_time(),
    }

    if dry_run:
        result["status"] = "render_only"
        result["note"] = "dry-run: no SMTP attempt"
        _write_audit(result)
        return result

    # Config precedence: config file > env (env overrides for ad-hoc)
    cfg = _load_config()
    host = cfg.get("smtp", {}).get("host") or os.environ.get("NOTIFY_SMTP_HOST") or os.environ.get("WEEKLY_SHIFT_SMTP_HOST")
    if not host:
        result["note"] = "SMTP not configured (config file or NOTIFY_SMTP_HOST)"
        _write_audit(result)
        return result

    port = int(cfg.get("smtp", {}).get("port")
               or os.environ.get("NOTIFY_SMTP_PORT") or os.environ.get("WEEKLY_SHIFT_SMTP_PORT", "465"))
    user = cfg.get("smtp", {}).get("user") or os.environ.get("NOTIFY_SMTP_USER") or os.environ.get("WEEKLY_SHIFT_SMTP_USER", "")
    pwd = cfg.get("smtp", {}).get("pass") or os.environ.get("NOTIFY_SMTP_PASS") or os.environ.get("WEEKLY_SHIFT_SMTP_PASS", "")
    frm = cfg.get("smtp", {}).get("from") or os.environ.get("NOTIFY_SMTP_FROM") or os.environ.get("WEEKLY_SHIFT_SMTP_FROM", user)
    # Default recipients from config when caller passes none
    if not to and cfg.get("default_to"):
        to = list(cfg["default_to"])
    to_addr = ",".join(to)
    cc_addr = ",".join(cc) if cc else ""

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = frm
        msg["To"] = to_addr
        if cc_addr:
            msg["Cc"] = cc_addr
        recipients = to + (cc or [])

        with smtplib.SMTP_SSL(host, port, timeout=20) as s:
            if user:
                s.login(user, pwd)
            s.sendmail(frm, recipients, msg.as_string())
        result["status"] = "sent"
    except Exception as e:  # best-effort: never raise
        result["status"] = "email_failed"
        result["error"] = str(e)

    _write_audit(result)
    return result


def _write_audit(result: dict) -> None:
    """Write audit JSON (best-effort)."""
    try:
        root = _audit_root()
        if not root:
            return
        root.mkdir(parents=True, exist_ok=True)
        name = result.get("context_id") or "notify"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        (root / f"{name}-{stamp}.json").write_text(
            _json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass  # audit is best-effort


def main() -> int:
    p = argparse.ArgumentParser(description="TriCompany notify (canonical)")
    sub = p.add_subparsers(dest="cmd", required=True)
    send = sub.add_parser("send", help="Send a notification")
    send.add_argument("--to", required=True, help="Comma-separated recipients")
    send.add_argument("--cc", help="Comma-separated CC")
    send.add_argument("--subject", required=True)
    send.add_argument("--body", required=True)
    send.add_argument("--context-id", default=None)
    send.add_argument("--trigger-mode", default="manual")
    send.add_argument("--dry-run", action="store_true", default=False)
    args = p.parse_args()

    result = send_notification(
        subject=args.subject,
        body=args.body,
        to=[x.strip() for x in args.to.split(",") if x.strip()],
        cc=[x.strip() for x in (args.cc or "").split(",") if x.strip()] or None,
        context_id=args.context_id,
        trigger_mode=args.trigger_mode,
        dry_run=args.dry_run,
    )
    print(_json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
