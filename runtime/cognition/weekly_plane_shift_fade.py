"""weekly_plane_shift_fade — FADE 化参数动态化 wrapper（a 级施工件·2026-10-18）

SDE 席 a 级件（CEO 11:32:57 预裁开工授权·BOD 转达·建议卷 8ac615631 §三）：
  - 新增 wrapper 不覆写现役入口 weekly_plane_shift.py（零操作回滚锚）
  - 自动计算 --from/--to/--start-date（ISO 周口径·默认=触发时刻算次周）
  - 周界口径做成开关 --boundary next|current（候裁点④·14:00 评审裁后改默认即可）
  - sync 形跑毕生成 FADE 收口 brief（brief+checkpoint+resumePoint）落 to 周 reports/
  - 通知默认抑制（--notify 才发·影子跑零噪音）

用法:
  python -m runtime.cognition.weekly_plane_shift_fade --operating-root <abs> [--sync]
      [--ref-date YYYY-MM-DD] [--boundary next|current] [--notify] [透传参数...]

参数计算口径:
  - boundary=next（默认）: from=ref 所在 ISO 周, to=次周, start_date=次周周一
  - boundary=current:      from=上周, to=ref 所在周, start_date=本周一（补偿形）
  - ref 默认=当前 Asia/Shanghai 日期（job 触发时刻=周日 23:00 → from=当周, to=次周）
  - W 号两位化（W01 形）——一月起 W1-W9 周与历史单双形差异候勘注记（现役 W32+ 无歧义）
"""

from __future__ import annotations

import argparse
import json as _json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Asia/Shanghai")
except Exception:  # zoneinfo 不可用回退固定 +8
    _TZ = timezone(timedelta(hours=8))


def compute_shift_params(ref: date, boundary: str = "next") -> dict:
    """ISO 周口径参数计算（触发时刻算次周=默认·候裁点④开关位）。"""
    iso = ref.isocalendar()
    if boundary == "next":
        from_y, from_w = iso[0], iso[1]
        this_monday = date.fromisocalendar(from_y, from_w, 1)
        to_y, to_w = (this_monday + timedelta(days=7)).isocalendar()[0:2]
    elif boundary == "current":
        this_monday = date.fromisocalendar(iso[0], iso[1], 1)
        prev = this_monday - timedelta(days=7)
        from_y, from_w = prev.isocalendar()[0:2]
        to_y, to_w = iso[0], iso[1]
    else:
        raise ValueError(f"unknown boundary: {boundary}")
    start = date.fromisocalendar(to_y, to_w, 1)
    return {
        "from_week": f"W{from_w:02d}",
        "to_week": f"W{to_w:02d}",
        "start_date": start.isoformat(),
        "boundary": boundary,
        "ref_date": ref.isoformat(),
    }


def _write_closeout_brief(root: Path, params: dict) -> Path | None:
    """FADE 收口 brief（brief+checkpoint+resumePoint）落 to 周 reports/。

    artifactCommit 形注记：影子跑=本地产物未入 git（N/A）；生产拍 git 链在
    job command 层，SHA 回填链候 b 级接线（建议卷 §三 b 级）。
    """
    to_dir = root / f"{params['start_date'][:4]}-{params['to_week']}"
    ade_path = to_dir / ".shift-ade.json"
    if not ade_path.exists():
        print(f"[fade_wrapper] brief skipped: no {ade_path}")
        return None
    ade = _json.loads(ade_path.read_text(encoding="utf-8"))
    reports = to_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    brief_path = reports / f"shift-closeout-{ts}.md"
    steps_line = "；".join(
        f"{s.get('step')}={s.get('result', {}).get('status', '?')}" for s in ade.get("steps", [])
    )
    lines = [
        "# 周平面迁移收口 brief（FADE a 级形·wrapper 生成）",
        "",
        f"- from/to: {ade.get('from_week')}→{ade.get('to_week')}（起始 {ade.get('start_date')}）",
        f"- status: {ade.get('status')}（dry_run={ade.get('dry_run')}）",
        f"- steps: {steps_line}",
        f"- escalation_8w: {len(ade.get('escalation_8w', []))} 项",
        f"- checkpoint: {ade_path}（check_time={ade.get('check_time')}）",
        "- artifactCommit: N/A（影子跑=本地产物未入 git；生产拍 commit/push 在 job command 层·SHA 回填候 b 级）",
        "- resumePoint: 生产形下步=job command git add/commit/push；异常回看 checkpoint ADE JSON steps 段失败步",
        f"- 周界口径: {params['boundary']}（ref={params['ref_date']}·候裁点④ 14:00 评审裁）",
        "- 执行件: TriCompany runtime/cognition/weekly_plane_shift_fade.py（a 级 wrapper·现役入口零改动）",
    ]
    brief_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[fade_wrapper] brief: {brief_path}")
    return brief_path


def main() -> int:
    p = argparse.ArgumentParser(description="FADE weekly plane shift wrapper (param auto)")
    p.add_argument("--operating-root", default="docs/workflow/operating-records")
    p.add_argument("--sync", action="store_true", default=False)
    p.add_argument("--ref-date", default=None, help="YYYY-MM-DD（默认=当前 Asia/Shanghai 日期）")
    p.add_argument("--boundary", default="next", choices=["next", "current"],
                   help="周界口径（候裁点④·默认 next=触发时刻算次周）")
    p.add_argument("--notify", action="store_true", default=False,
                   help="启用迁移完成通知（默认抑制·影子跑零噪音）")
    args, passthrough = p.parse_known_args()

    if args.ref_date:
        ref = date.fromisoformat(args.ref_date)
    else:
        ref = datetime.now(_TZ).date()

    params = compute_shift_params(ref, args.boundary)
    print("[fade_wrapper] params=" + _json.dumps(params, ensure_ascii=False))

    # 复用现役 CLI（import 注入 argv·零复制零覆写）
    from runtime.cognition import weekly_plane_shift as impl

    if not args.notify:
        impl._notify_shift = lambda ade: print("[fade_wrapper] notify suppressed (default)")
    sys.argv = [
        "weekly_plane_shift",
        "--from", params["from_week"],
        "--to", params["to_week"],
        "--start-date", params["start_date"],
        "--operating-root", args.operating_root,
    ] + (["--sync"] if args.sync else []) + passthrough
    rc = impl.main()

    if args.sync:
        _write_closeout_brief(Path(args.operating_root), params)
    print(f"[fade_wrapper] impl rc={rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
