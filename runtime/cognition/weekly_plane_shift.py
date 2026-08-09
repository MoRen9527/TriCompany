"""weekly_plane_shift — 定时周平面迁移包装（紧急任务，2026-08-06）

完整 ADE 执行链：
  Agent plans (小贾，SOP Step 1-3)  →  CLI executes (本脚本，确定性)  →  Agent closes (小贾审核 .shift-ade.json)

串行执行：
  1. create 新周（幂等）
  2. migrate 旧周→新周（内含 retire）
  3. carry-over 平移：旧周 unresolved-items §1 表 → 新周 unresolved-items.md
     （active/frozen 保留、周数+1、done 关闭、4w+/8w+ 标 ⚠️/⚠️⚠️）
  4. validate 新周
  5. 聚合 ADE JSON 写 <new_week>/.shift-ade.json

用法:
  python -m runtime.cognition.weekly_plane_shift --from W32 --to W33 \
    --start-date 2026-08-10 --operating-root <abs> [--sync]
"""

from __future__ import annotations

import argparse
import json as _json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from runtime.cognition.weekly_plane import (
    create_weekly_plane,
    migrate_weekly_plane,
    validate_index,
)


def _check_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return None


def _index_object_id(week_str: str, start_date: str) -> str:
    dt = datetime.fromisoformat(start_date)
    return f"OP-{dt.year}{dt.month:02d}-{week_str}-001"


def _week_dir(operating_root: Path, week_str: str, start_date: str) -> Path:
    dt = datetime.fromisoformat(start_date)
    return operating_root / f"{dt.year}-{week_str}"


def shift_carry_over(from_week: str, to_week: str, operating_root: Path, start_date: str, dry_run: bool) -> dict:
    """Carry over unresolved-items §1 from old week to new week."""
    to_dir = _week_dir(operating_root, to_week, start_date)
    from_md = operating_root / f"{from_week}" and None  # resolved below via pattern

    # Locate source unresolved-items (pattern: OP-*-Wxx-001.unresolved-items.md)
    candidates = list(operating_root.glob(f"*/OP-*-{from_week}-001.unresolved-items.md"))
    if not candidates:
        return {"status": "skip", "reason": "source unresolved-items not found"}
    src = candidates[0]

    dst = to_dir / f"{_index_object_id(to_week, start_date)}.unresolved-items.md"
    if dst.exists():
        return {"status": "skip", "reason": "target unresolved-items already exists"}

    text = src.read_text(encoding="utf-8")

    # Update header (lambda repl avoids backtick escape issues in re.sub templates)
    text = re.sub(
        r"> \*\*继承自\*\*：[^\n]+",
        lambda m: f"> **继承自**：`{src.relative_to(operating_root)}`（{from_week}）",
        text, count=1,
    )
    text = re.sub(
        r"> \*\*平移日期\*\*：[^\n]+",
        lambda m: f"> **平移日期**：{date.fromisoformat(start_date).isoformat()}（{to_week} 起始日）",
        text, count=1,
    )

    # Bump week counters on CARRY/RISK rows: Nw+ → (N+1)w+ and ⚠️ escalation
    def bump(match: re.Match) -> str:
        prefix, weeks, suffix = match.group(1), int(match.group(2)), match.group(3)
        new_weeks = weeks + 1
        marks = ""
        if new_weeks >= 8:
            marks = " ⚠️⚠️"
        elif new_weeks >= 4:
            marks = " ⚠️"
        return f"{prefix}{new_weeks}w+{marks}{suffix}"

    text = re.sub(r"(CARRY-\d+[^|]*\|\s*)(\d+)w\+(\s*[^|]*\|)", bump, text)

    if dry_run:
        return {"status": "would-write", "target": str(dst), "bumped": True}
    to_dir.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    return {"status": "written", "target": str(dst)}


def review_shift(root: Path, to_week: str, start_date: str, from_week: str) -> dict:
    """Agent close (REQ-020 ④): verify migration results + extract 8w escalation list.

    Called after create/migrate/carry_over. Produces the review input for
    CEOChiefOfStaff (小贾) to make carry-over upgrade rulings.
    """
    to_dir = _week_dir(root, to_week, start_date)
    idx_path = to_dir / f"{_index_object_id(to_week, start_date)}.json"
    md_path = to_dir / f"{_index_object_id(to_week, start_date)}.unresolved-items.md"
    errors = []

    # 1. New week index must be active
    idx = _load_json(idx_path)
    if not idx:
        errors.append({"item": str(idx_path), "reason": "index_missing"})
    elif idx.get("status") != "active":
        errors.append({"item": "index.status", "reason": f"expected active, got {idx.get('status')}"})

    # 2. New week unresolved-items must exist
    if not md_path.exists():
        errors.append({"item": str(md_path), "reason": "unresolved_items_missing"})

    # 3. Extract 8w+ escalation items from unresolved table
    escalation = []
    if md_path.exists():
        text = md_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "8w" in line and "⚠️" in line and "CARRY" in line:
                escalation.append(line.strip().strip("|").strip())

    return {
        "status": "pass" if not errors else "fail",
        "from_week": from_week,
        "to_week": to_week,
        "checks": {
            "new_index_active": idx.get("status") == "active" if idx else False,
            "unresolved_items_present": md_path.exists(),
        },
        "escalation_8w": escalation,
        "errors": errors,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="ADE weekly plane shift")
    p.add_argument("--from", dest="from_week", required=True)
    p.add_argument("--to", dest="to_week", required=True)
    p.add_argument("--start-date", required=True, help="New week start date YYYY-MM-DD")
    p.add_argument("--operating-root", default="docs/workflow/operating-records")
    p.add_argument("--sync", action="store_true", default=False)
    args = p.parse_args()

    root = Path(args.operating_root)
    results = []
    status = "pass"

    # 1. create (idempotent: already_exists is not a failure)
    r = create_weekly_plane(root, args.to_week,
                            start_date=args.start_date,
                            previous_week=args.from_week, dry_run=not args.sync)
    already = any("already_exists" in (e.get("reason") or "") for e in r.errors)
    results.append({"step": "create", "result": {**r.to_ade_json(), "status": "pass" if already else r.status}})
    if r.status == "fail" and not already:
        status = "fail"

    # 2. migrate
    r = migrate_weekly_plane(root, args.from_week, args.to_week, dry_run=not args.sync)
    results.append({"step": "migrate", "result": r.to_ade_json()})
    if r.status == "fail":
        status = "fail"

    # 3. carry-over shift
    co = shift_carry_over(args.from_week, args.to_week, root, args.start_date, dry_run=not args.sync)
    results.append({"step": "carry_over", "result": co})
    if co.get("status") == "fail":
        status = "fail"

    # 4. validate new week
    idx_path = _week_dir(root, args.to_week, args.start_date) / f'{_index_object_id(args.to_week, args.start_date)}.json'
    r = validate_index(idx_path)
    results.append({"step": "validate", "result": r.to_ade_json()})
    if r.status == "fail":
        status = "fail"

    # 5. agent close review (REQ-020 ④): verify + extract 8w escalation list
    review = review_shift(root, args.to_week, args.start_date, args.from_week)
    results.append({"step": "agent_close", "result": review})
    if review.get("status") == "fail":
        status = "fail"

    # 6. aggregate ADE JSON (operation record = ⑤ cli finalize)
    shift_ade = {
        "objectType": "ADE_SHIFT",
        "status": status,
        "from_week": args.from_week,
        "to_week": args.to_week,
        "start_date": args.start_date,
        "dry_run": not args.sync,
        "steps": results,
        "escalation_8w": review.get("escalation_8w", []),
        "check_time": _check_time(),
    }
    out = _week_dir(root, args.to_week, args.start_date) / ".shift-ade.json"
    if args.sync:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_json.dumps(shift_ade, ensure_ascii=False, indent=2), encoding="utf-8")

    # ⑦ notify (REQ-020 ⑤): email the CEO on completion
    if args.sync:
        notify_email(shift_ade)

    print(_json.dumps(shift_ade, ensure_ascii=False, indent=2))
    return 0 if status == "pass" else 1


def notify_email(shift_ade: dict) -> None:
    """Send a summary email after a successful shift (best-effort, non-blocking).

    SMTP config from env:
      WEEKLY_SHIFT_SMTP_HOST / PORT / USER / PASS / TO / FROM
    Missing config → logged skip (no crash).
    """
    import os
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header

    host = os.environ.get("WEEKLY_SHIFT_SMTP_HOST")
    if not host:
        print("[weekly_shift] SMTP not configured (WEEKLY_SHIFT_SMTP_HOST) — email skipped")
        return
    port = int(os.environ.get("WEEKLY_SHIFT_SMTP_PORT", "465"))
    user = os.environ.get("WEEKLY_SHIFT_SMTP_USER", "")
    pwd = os.environ.get("WEEKLY_SHIFT_SMTP_PASS", "")
    to = os.environ.get("WEEKLY_SHIFT_SMTP_TO", "")
    frm = os.environ.get("WEEKLY_SHIFT_SMTP_FROM", user)

    try:
        status = shift_ade.get("status", "?")
        subject = f"[TriCade] 周平面迁移完成 {shift_ade['from_week']}→{shift_ade['to_week']} ({status})"
        carry = len(shift_ade.get("escalation_8w", []))
        body_lines = [
            f"周工作平面迁移完成（TriCade 定时）",
            "",
            f"状态: {status}",
            f"迁移: {shift_ade['from_week']} → {shift_ade['to_week']}（起始 {shift_ade['start_date']}）",
            f"8w+ 升级事项: {carry} 项",
            "",
            "8w+ 事项清单:",
        ]
        if shift_ade.get("escalation_8w"):
            for item in shift_ade["escalation_8w"]:
                body_lines.append(f"  - {item}")
        else:
            body_lines.append("  （无）")
        body_lines += [
            "",
            "请 CEO 在 W" + shift_ade["to_week"].lstrip("W") + " 首周做 carry-over 裁决（推进/冻结/关闭）。",
        ]
        msg = MIMEText("\n".join(body_lines), "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = frm
        msg["To"] = to

        with smtplib.SMTP_SSL(host, port, timeout=20) as s:
            if user:
                s.login(user, pwd)
            s.sendmail(frm, [to], msg.as_string())
        print(f"[weekly_shift] email sent to {to}")
    except Exception as e:  # best-effort: never fail the shift because of email
        print(f"[weekly_shift] email failed (non-blocking): {e}")


if __name__ == "__main__":
    sys.exit(main())
