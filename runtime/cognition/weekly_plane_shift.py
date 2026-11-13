"""weekly_plane_shift — 定时周平面迁移包装（紧急任务，2026-08-06）

完整 ADE 执行链：
  Agent plans (小贾，SOP Step 1-3)  →  CLI executes (本脚本，确定性)  →  Agent closes (小贾审核 .shift-ade.json)

串行执行：
  0. preflight 分叉闸（P1 改点 A·仅 --sync 真跑：fetch-only 对表 sg-bare，
     left>0 = 本地分叉 bare → 双址 blocking 告警 + exit 3 候裁不硬跑）
  1. create 新周（幂等）
  2. migrate 旧周→新周（内含 retire）
  3. carry-over 平移：旧周 unresolved-items §1 表 → 新周 unresolved-items.md
     （active/frozen 保留、周数+1、done 关闭、4w+/8w+ 标 ⚠️/⚠️⚠️）
  4. validate 新周
  5. 聚合 ADE JSON 写 <new_week>/.shift-ade.json（P1 a2：写前单级轮转 .shift-ade.prev.json）
  6. notify（P1 改点 B：WEEKLY_SHIFT_NOTIFY_TO 双址 + blocking 重试 1 次，
     仍败 → 顶层 notify_failures 落卷 + exit 4）

用法:
  python -m runtime.cognition.weekly_plane_shift --from W32 --to W33 \
    --start-date 2026-08-10 --operating-root <abs> [--sync]
"""

from __future__ import annotations

import argparse
import json as _json
import os
import re
import shutil
import subprocess
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
    had_trailing_newline = text.endswith("\n")

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

    # Bump week counters on CARRY table rows: first Nw+ token → (N+1)w+ with
    # escalation marks recomputed from the counter (counter = single source of
    # truth). Line-based so column order does not matter (D1: §1 long rows
    # carry the counter in column 5; the old regex assumed column-2 adjacency
    # after the id and silently skipped them). RISK rows use a different
    # notation ("2w", no "+") and are out of scope. Old marks are stripped and
    # recomputed; manual strong annotations are transiently downgraded until
    # the counters are rectified (D1 part B, orchestration-layer checklist
    # before migration).
    _CARRY_ID_RE = re.compile(r"CARRY-\d+")
    _WEEK_CELL_RE = re.compile(r"(\d+)w\+[^\d|]*")

    def bump_row(line: str) -> str:
        if not (line.strip().startswith("|") and _CARRY_ID_RE.search(line)):
            return line

        def repl(m: re.Match) -> str:
            new_weeks = int(m.group(1)) + 1
            marks = ""
            if new_weeks >= 8:
                marks = " ⚠️⚠️"
            elif new_weeks >= 4:
                marks = " ⚠️"
            return f"{new_weeks}w+{marks} "

        return _WEEK_CELL_RE.sub(repl, line, count=1)

    text = "\n".join(bump_row(line) for line in text.splitlines())
    # O-D1-1: restore the trailing newline (splitlines drops it) so the
    # migrated file does not get flagged "\ No newline at end of file".
    if had_trailing_newline:
        text += "\n"

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

    # 3. Extract >=8w escalation items from the §1 active-items section.
    # D-ESC-1 (2026-08-24): literal "8w" substring only matched counters
    # ending in 8 (8w/18w/28w...) and silently missed 9w+/10w+/23w+ — the
    # escalation list went empty the week after items crossed 8w. Parse the
    # Nw+ counter and escalate on N >= 8.
    # D-ESC-1 R (CTO review rework): scope the scan to the §1 section —
    # stale advisory tables elsewhere (§4 assessment snapshots) carry their
    # own Nw+ counters and would echo closed items into the list. If no §1
    # header is found, degrade to a full scan rather than report empty.
    # The ⚠️/CARRY guards are substring checks and cannot distinguish
    # single/double marks — the numeric counter is the real >=8 gate.
    escalation = []
    if md_path.exists():
        text = md_path.read_text(encoding="utf-8")
        all_lines = text.splitlines()
        section_lines = []
        in_section = False
        header_found = False
        for line in all_lines:
            if line.startswith("## §1"):  # 前缀锚定（D-ESC-1 R forward：防他节标题引用 §1 误重开）
                in_section = True
                header_found = True
                continue
            if line.startswith("## "):
                in_section = False
                continue
            if in_section:
                section_lines.append(line)
        if not header_found:
            section_lines = all_lines  # 无 §1 头（旧格式）——fail-open 全扫
        # §1 存在但区间为空 = 合法空清单，不再回退全扫（语义区分，CTO forward #2）
        for line in section_lines:
            counters = [int(n) for n in re.findall(r"(\d+)w\+", line)]
            if counters and max(counters) >= 8 and "⚠️" in line and "CARRY" in line:
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


def push_trilc_notification(title: str, body: str) -> None:
    """POST notification to TriLC daemon (TriPilot / trilc chat clients pull it)."""
    import json as _j, os, urllib.request
    base = os.environ.get("TRILC_API_URL", "http://127.0.0.1:8711")
    try:
        req = urllib.request.Request(
            f"{base}/internal/v1/notifications",
            data=_j.dumps({"title": title, "body": body, "context": "weekly-plane-shift"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[weekly_shift] TriLC notification pushed ({resp.status})")
    except Exception as e:
        print(f"[weekly_shift] TriLC notification push failed (non-blocking): {e}")


# ── P1 改点 A/B helpers（CTO 任务书 TMV fa69fcd9d·2026-11-10 施工窗）──


def _parse_left_right_count(text: str) -> tuple[int, int]:
    """Parse `git rev-list --left-right --count` output ('L\\tR' / 'L R')."""
    parts = text.strip().split()
    if len(parts) != 2:
        raise ValueError(f"unexpected rev-list output: {text!r}")
    return int(parts[0]), int(parts[1])


def _diverge_verdict(left: int, right: int) -> str:
    """Pure classification of local-vs-bare tip counts（P1 改点 A 判据）.

    left>0 = 本地含 bare 无的提交（diverged/ahead——9c81c7ec exit-128 病灶形）
    → 拦；right>0 纯 behind 或 0/0 已齐 → 放行（pull --ff-only 留作二道闸）。
    """
    if left > 0 and right > 0:
        return "diverged"
    if left > 0:
        return "ahead"
    if right > 0:
        return "behind"
    return "synced"


def _find_repo_root(start: Path) -> Path | None:
    """Walk up from start to the nearest .git ancestor (no subprocess)."""
    for p in (start, *start.parents):
        if (p / ".git").exists():
            return p
    return None


def _preflight_bare_sync(
    repo_path: Path, remote: str = "sg-bare", branch: str = "dev"
) -> tuple[bool, str, dict]:
    """Fetch-only divergence gate before the shift chain（P1 改点 A）.

    Returns (ok_to_run, detail, readback). left>0 → (False, 告警文案, 读数)
    —调用方双址 blocking 告警 + exit 3（候裁不硬跑）；fetch/count 失败同拦
    （可观测优先·不硬跑未知态）。
    """
    readback: dict = {"remote": remote, "branch": branch}
    try:
        subprocess.run(
            ["git", "fetch", remote, branch],
            cwd=str(repo_path), check=True, capture_output=True, timeout=120,
        )
        tops = subprocess.run(
            ["git", "rev-parse", "HEAD", f"{remote}/{branch}"],
            cwd=str(repo_path), check=True, capture_output=True, text=True, timeout=30,
        ).stdout.split()
        counts = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"HEAD...{remote}/{branch}"],
            cwd=str(repo_path), check=True, capture_output=True, text=True, timeout=30,
        ).stdout
        left, right = _parse_left_right_count(counts)
    except Exception as e:  # fetch/网络/解析任一失败 = 不硬跑未知态
        readback["error"] = str(e)[:300]
        return False, f"preflight fetch/count failed: {e}", readback
    verdict = _diverge_verdict(left, right)
    readback.update({
        "left": left, "right": right, "verdict": verdict,
        "local_top": tops[0] if len(tops) > 0 else None,
        "bare_top": tops[1] if len(tops) > 1 else None,
    })
    if left > 0:
        return False, (
            f"preflight: 本地分叉 bare·候裁不硬跑 (left={left} right={right} "
            f"verdict={verdict} local={readback['local_top']} bare={readback['bare_top']})"
        ), readback
    return True, f"preflight ok (left={left} right={right} verdict={verdict})", readback


def _resolve_notify_to() -> list[str]:
    """P1 改点 B 收件人谱：WEEKLY_SHIFT_NOTIFY_TO（逗号分隔双址）优先，
    退 WEEKLY_SHIFT_SMTP_TO（兼容），均空 → []（send_notification 落 config default_to）。"""
    for key in ("WEEKLY_SHIFT_NOTIFY_TO", "WEEKLY_SHIFT_SMTP_TO"):
        addrs = [x.strip() for x in (os.environ.get(key) or "").split(",") if x.strip()]
        if addrs:
            return addrs
    return []


def _notify_blocking(
    subject: str, body: str, to: list[str], context_id: str
) -> list[dict]:
    """Canonical notify with 1 retry（P1 改点 B blocking 语义）.

    Returns failure records——空列表=已发出（重试成功亦空）；非空=重试后仍败。
    Never raises。
    """
    try:
        from runtime.cognition.notify import send_notification
    except Exception as e:
        return [{"attempt": 0, "status": "import_failed", "error": str(e)[:300]}]
    failures: list[dict] = []
    for attempt in (1, 2):
        result = send_notification(
            subject=subject, body=body, to=to,
            context_id=context_id, trigger_mode="cron",
        )
        if result.get("status") == "sent":
            return []
        failures.append({
            "attempt": attempt,
            "status": result.get("status"),
            "error": (result.get("error") or "")[:300],
        })
    return failures


def _write_shift_ade_rotating(out: Path, ade: dict) -> None:
    """Write .shift-ade.json with single-level prev rotation（CTO 裁定 a2）.

    写前已存在 → 轮转至 .shift-ade.prev.json（单级·防覆盖丢前轮）。
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        shutil.copy2(out, out.with_name(".shift-ade.prev.json"))
    out.write_text(_json.dumps(ade, ensure_ascii=False, indent=2), encoding="utf-8")


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

    # 0. preflight (P1 改点 A): fetch-only divergence gate — real runs only.
    #    勘正注①（CTO 采认 2026-11-10）: 任务书 §二① L211-213 系 push_trilc_notification
    #    死代码（main 零调用点），真告警面=_notify_shift；死代码不删（diff 最小化）·本注随卷留痕。
    #    分工表述（CTO 裁定②）: 改点 C（|| 兜底告警）=链跑路径主防线；本 preflight=手动
    #    入口拦截+链改形后纵深+分叉预检落卷可读（status=preflight-fail 轮次辨析）——非冗余。
    if args.sync:
        repo_root = _find_repo_root(root if root.is_absolute() else Path.cwd() / root)
        if repo_root is None:
            ok, detail, readback = False, (
                "preflight: repo root not found from operating-root"
            ), {"error": "no .git ancestor"}
        else:
            ok, detail, readback = _preflight_bare_sync(repo_root)
        print(f"[weekly_shift] {detail}")
        if not ok:
            ade = {
                "objectType": "ADE_SHIFT",
                "status": "preflight-fail",
                "reason": detail,
                "preflight": readback,
                "notify_failures": [],
                "dry_run": False,
                "check_time": _check_time(),
            }
            ade["notify_failures"] = _notify_blocking(
                subject=f"[TriCade] 周平面迁移 preflight 拦截 {args.from_week}→{args.to_week}",
                body="preflight: 本地分叉 sg-bare·候裁不硬跑\n"
                     + detail + "\n读数:\n" + _json.dumps(readback, ensure_ascii=False, indent=2),
                to=_resolve_notify_to(),
                context_id="weekly-plane-shift-preflight",
            )
            _write_shift_ade_rotating(
                _week_dir(root, args.to_week, args.start_date) / ".shift-ade.json", ade
            )
            print(_json.dumps(ade, ensure_ascii=False, indent=2))
            return 3

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

    # 4b. γ 二道闸（FADE-001 要点②·synthesis §二3 改判并入本阶段）: toWeek==预期周
    #     对表断言——错周静默双保险第二道（主闸=preflight 触发参数定形算周断言）。
    expected_to_week = f"W{date.fromisoformat(args.start_date).isocalendar()[1]:02d}"
    if expected_to_week != args.to_week:
        status = "fail"
        results.append({"step": "validate_week_crosscheck", "result": {
            "status": "fail",
            "reason": (f"toWeek crosscheck mismatch: got {args.to_week}, "
                       f"expected {expected_to_week} "
                       f"(ISO week of start-date {args.start_date})"),
        }})

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

    # ⑦ notify (P1 改点 B): dual-address + blocking (1 retry) — failures land in ADE.
    notify_failures: list[dict] = []
    if args.sync:
        notify_failures = _notify_shift(shift_ade)
        shift_ade["notify_failures"] = notify_failures

    if args.sync:
        _write_shift_ade_rotating(out, shift_ade)  # P1 a2: single-level prev rotation

    print(_json.dumps(shift_ade, ensure_ascii=False, indent=2))
    if notify_failures:
        return 4  # blocking: 告警发不出必须可观测（升 4 优先于迁移 fail 的 1）
    return 0 if status == "pass" else 1


def _notify_shift(shift_ade: dict) -> list[dict]:
    """Assemble weekly-shift business content and dispatch (P1 改点 B).

    Dual-address via _resolve_notify_to + blocking (1 retry). Returns failure
    records (empty = sent); empty recipient list falls back to config default_to
    inside send_notification (现役形保留)."""
    status = shift_ade.get("status", "?")

    subject = f"[TriCade] 周平面迁移完成 {shift_ade['from_week']}→{shift_ade['to_week']} ({status})"
    body_lines = [
        f"周工作平面迁移完成（TriCade 定时）",
        "",
        f"状态: {status}",
        f"迁移: {shift_ade['from_week']} → {shift_ade['to_week']}（起始 {shift_ade['start_date']}）",
        f"8w+ 升级事项: {len(shift_ade.get('escalation_8w', []))} 项",
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

    result_failures = _notify_blocking(
        subject=subject, body="\n".join(body_lines),
        to=_resolve_notify_to(), context_id="weekly-plane-shift",
    )
    print(f"[weekly_shift] notify: {'sent' if not result_failures else 'FAILED after retry'}")
    return result_failures


if __name__ == "__main__":
    sys.exit(main())