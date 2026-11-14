"""FADE-001 阶段 10: 结论与动作段骨架（fsd-ten-stage-tech-collab §三路线框架）。

业务面切片第十段——判「结论到达人」。ζ 缝隙闭合面：成功/失败双向 notify 路由
（复用 P1 notify.py 现役形·send_notification best-effort 永不抛）：
  ok     → 结论通知（COS 到达反馈·成功面）
  failed → 失败告警（文案必带 run id·PM 契约定谳）
  stale  → 悬空 run 报告（未走完即断面·如实告知）

骨架形边界（预演形·COS 裁决 B）：路由骨架+notify_done.json 落卷；
ζ 实锚（notify 失败重试语义定性+成功反馈可达实证）候首拍后窗（生产形判读）。

退出码：0=notify 路由完成（含 render_only 降级态——SMTP 未配置=骨架合法态）；
  2=notify_done.json 落卷败（哑卷防线）。notify 本身永不拦（best-effort 契约）。
"""

from __future__ import annotations

import argparse
import json as _json
from datetime import datetime, timezone
from pathlib import Path

NOTIFY_DONE_VERSION = "1.0.0"
# 结论路由映射（run_state → 收件面·COS 单址对表 close_skill.notify_target）
_ROUTE = {
    "ok": ("结论通知", "成功面·COS 到达反馈"),
    "failed": ("失败告警", "告警面·文案必带 run id"),
    "stale": ("悬空 run 报告", "未走完即断面·如实告知"),
}


def route_conclusion(run_state: str) -> tuple[str, str]:
    """run_state → (subject_prefix, note)。未知态=如实降级 unknown 面（fail-closed 方向）。"""
    if run_state in _ROUTE:
        return _ROUTE[run_state]
    return ("run 结论未知态", f"run_state={run_state!r} 非三态（如实降级）")


def _notify_to_chain(cli_value: str) -> list[str]:
    """收件人缺省链（发现 27 对齐形·CTO 派工 2026-11-14·CEO 点名项）：

    CLI 传参优先，缺省链对齐迁移器 `_resolve_notify_to` env 双址谱（precedence
    同源——P1 改点 B 收件人谱单一真源·shift_notify_fail 先例形）：CLI 逗号分隔
    值 → WEEKLY_SHIFT_NOTIFY_TO（逗号分隔双址）→ WEEKLY_SHIFT_SMTP_TO（兼容）
    → []（send_notification 落 config default_to）。
    """
    cli_addrs = [x.strip() for x in (cli_value or "").split(",") if x.strip()]
    if cli_addrs:
        return cli_addrs
    from runtime.cognition.weekly_plane_shift import _resolve_notify_to

    return _resolve_notify_to()


def run_notify_done(args: argparse.Namespace) -> tuple[int, dict]:
    """结论路由并返回 (exit_code, notify_done dict)。notify best-effort 永不拦。"""
    manifest_path = Path(args.run_dir) / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = _json.loads(manifest_path.read_text(encoding="utf-8"))
            run_state = str(manifest.get("run_state", "unknown"))
        except Exception:  # noqa: BLE001 — manifest 不可读=如实降级（终点记录缺位面）
            run_state = "unknown"
    else:
        run_state = "unknown"

    subject_prefix, note = route_conclusion(run_state)
    run_id = args.run_id
    result: dict | None = None
    if not args.dry_run_only:
        try:
            from runtime.cognition.notify import send_notification

            result = send_notification(
                subject=f"[FADE-001] {subject_prefix} run={run_id}",
                body=(
                    f"FADE-001 run 结论\nrun_id: {run_id}\nrun_state: {run_state}\n"
                    f"from_week: {args.from_week} → to_week: {args.to_week}\n"
                    f"说明: {note}\n（段产物见 run dir manifest.json）"
                ),
                to=_notify_to_chain(args.notify_to),
                context_id=run_id,  # PM 契约：run id 全链主键
                trigger_mode="cron",
            )
        except Exception as e:  # noqa: BLE001 — send_notification 契约=永不抛·此为兜底
            result = {"status": "email_failed", "note": f"{type(e).__name__}: {e}"}

    done: dict = {
        "notify_done_version": NOTIFY_DONE_VERSION,
        "run_id": run_id,
        "from_week": args.from_week,
        "to_week": args.to_week,
        "run_state": run_state,
        "route": {"subject_prefix": subject_prefix, "note": note},
        "notify_result": result or {"status": "render_only", "note": "dry_run_only: no send"},
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    return 0, done


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 10 结论与动作（notify·骨架形）")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--run-id", default="")
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--notify-to", default="", help="收件人（缺省=notify.py config default_to）")
    p.add_argument(
        "--dry-run-only", action="store_true",
        help="仅落卷不发信（沙箱/演练面·生产 payload 不传）",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    exit_code, done = run_notify_done(args)
    out = _json.dumps(done, ensure_ascii=False, indent=2)
    run_dir = Path(args.run_dir)
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "notify_done.json").write_text(out + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 哑卷防线同族
        print(f"notify_done.json write failed: {type(e).__name__}: {e}", flush=True)
        return 2
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
