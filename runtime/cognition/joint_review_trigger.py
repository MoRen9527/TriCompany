"""FADE-001 联审触发段（W2 施工件·W1 架构卷 a97d76af7 §二/§三 接线实现）。

业务面切片第十一段（联审族）——判「整轮迁移质量候七席评」。触发点定谳
（§三·r101）：manifest close 段 pass 后收口段（r88 异步形废止）——本段接
close_cli 之后·notify_done 之前/后皆可（管线内同步段·非轮询）。

契约（§二最小字段形）：joint-review-trigger.json =
  trigger_version / loop_run_id / run_dir / dim_a_materials（维度 A=
  fade-001 实现度材料：manifest/score/plan 读数卷指针）/ dim_b_materials
  （维度 B=周平面迁移质量材料：counts/ar/unresolved diff/ops commit 指针）/
  domain_readings（三域分现读数：机判/值席采集/主观）/ score_threshold
  （null=留参·毕验收窗 CTO 主裁 COO 会签·不代裁）/ trigger_time / mode
  （loop-window|cron-sunday·从 preflight.json week_math.mode 如实注记）。

fail-closed（§四.2）：run_state != ok → 产出 joint-review-trigger-skip.json
（不发起联审）·exit 0——管线不因联审挂（联审与常规轮解耦另一半）。

落卷面：run_dir（必落）+ 树面（--tmv-root 归属周自动算·best-effort 双落，
树面落卷败不拦——run_dir 面为信面真源）。

notify（notify_done 同族）：send_notification best-effort 永不抛；SMTP 未
配置=render_only 合法态（骨架族先例）。全程无凭据值面回显（D-46）。

退出码：0=触发件产出（含 skip 面）；2=落卷败（哑卷防线）。

调用形（payload 接线·close_cli 后）：
  python3 -m runtime.cognition.joint_review_trigger \\
      --run-dir "$RUN_DIR" --run-id "$RUN_ID" \\
      --from-week {fromWeek} --to-week {toWeek} \\
      >"$RUN_DIR/joint-review-trigger.log" 2>&1 || true
"""

from __future__ import annotations

import argparse
import hashlib
import json as _json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TRIGGER_VERSION = "1.0.0"

# §二 契约·维度 A 材料指针（fade-001 实现度材料·读数卷指针）
_DIM_A_REFS = ("manifest.json", "score.json", "plan.json")
# §二 契约·维度 B 材料指针（周平面迁移质量材料四类：counts/ar/unresolved diff/ops commit）
_DIM_B_REFS = (
    {"kind": "counts", "ref": "plan.json#/counts"},
    {"kind": "ar", "ref": "plan.json#/agent_readings"},
    {"kind": "unresolved_diff", "ref": "verify.json"},
    {"kind": "ops_commit", "ref": "tmv:git-top"},
)

# 三域族归属（score_engine v2.0.0 同源·机判域实分/值席采集域/主观域）
_MACHINE_FAMILIES = ("B", "C", "D", "E", "G")
_MANUAL_FAMILIES = ("A", "F", "H")
_SUBJECTIVE_FAMILIES = ("I",)


def _sha16(p: Path) -> str | None:
    """材料指针锚：sha256 前 16 hex（文件在时·不在=None 指针仍列）。"""
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def _read_json(p: Path) -> dict | None:
    try:
        data = _json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001 — 不可读如实记（指针面不抛）
        return None


def domain_readings(run_dir: Path) -> dict:
    """三域分现读数（现读数如实面·值席/主观域未落=pending 非冒充分）。"""
    out: dict = {"machine": {"score": 0, "families": {}}, "duty_collection": "pending",
                 "subjective": "pending"}
    score = _read_json(run_dir / "score.json")
    if score:
        fams = (score.get("score") or {}).get("families") or []
        for f in fams:
            fid = f.get("family_id")
            if fid in _MACHINE_FAMILIES:
                val = f.get("score")
                out["machine"]["families"][fid] = val
                if isinstance(val, int):
                    out["machine"]["score"] += val
    coll = _read_json(run_dir / "collection-score.json")
    if coll:
        out["duty_collection"] = {
            "entries": len(coll.get("entries") or []),
            "state": "collected",
        }
    subj = _read_json(run_dir / "subjective-score.json")
    if subj:
        out["subjective"] = {
            "entries": len(subj.get("entries") or []),
            "state": "collected",
        }
    return out


def mode_note(run_dir: Path) -> str:
    """mode 注记：preflight.json week_math.mode 如实读·缺省 unknown。"""
    pf = _read_json(run_dir / "preflight.json")
    wm = (pf or {}).get("assertions", {}).get("week_math", {}) if pf else {}
    mode = wm.get("mode")
    return mode if isinstance(mode, str) and mode else "unknown"


def ops_commit_ref(tmv_root: Path) -> dict:
    """ops commit 指针：TMV 树 git 顶 hash（失败如实 null·不拦）。"""
    try:
        out = subprocess.run(
            ["git", "-C", str(tmv_root), "log", "-1", "--format=%H"],
            capture_output=True, text=True, timeout=15,
        )
        h = (out.stdout or "").strip()
        return {"hash": h if out.returncode == 0 and h else None}
    except Exception:  # noqa: BLE001 — 探针失败如实 null
        return {"hash": None}


def build_trigger(run_dir: Path, tmv_root: Path, run_id: str,
                  from_week: str, to_week: str) -> dict:
    """§二 契约最小字段形产出（纯函数面·run_state=ok 前置由调用方闸）。"""
    now = datetime.now(timezone.utc)
    dim_a = []
    for name in _DIM_A_REFS:
        p = run_dir / name
        dim_a.append({"ref": name, "sha16": _sha16(p)})
    dim_b = [
        {"kind": d["kind"], "ref": d["ref"], "sha16": _sha16(run_dir / d["ref"].split("#")[0])}
        if not d["ref"].startswith("tmv:") else {"kind": d["kind"], **ops_commit_ref(tmv_root)}
        for d in _DIM_B_REFS
    ]
    return {
        "trigger_version": TRIGGER_VERSION,
        "loop_run_id": run_id,
        "run_dir": str(run_dir),
        "from_week": from_week,
        "to_week": to_week,
        "dim_a_materials": dim_a,
        "dim_b_materials": dim_b,
        "domain_readings": domain_readings(run_dir),
        "score_threshold": None,  # 分数线接口位：null=留参（W1§二·毕验收窗裁·不代裁）
        "mode": mode_note(run_dir),
        # 等待点字段（notice-202·CTO 荐案 d.1·2026-11-18）：verdict 落卷时
        # round-state=pending-ceo-ruling——flag=debug 停点=候 CEO 裁决落卷
        # （上轮轮间门三态判据见 preflight.check_ceo_ruling·job payload 零改形）。
        "round_state": "pending-ceo-ruling",
        "trigger_time": now.isoformat(),
    }


def _iso_week_dir(now: datetime) -> str:
    """归属周目录名（operating-records 惯例 2026-W47 形·实际时点 ISO 周）。"""
    d = now.date()
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def write_trigger(payload: dict, run_dir: Path, tmv_root: Path,
                  tree_name: str) -> dict:
    """双落：run_dir（信面真源）+树面（best-effort·落卷败如实注记不拦）。"""
    out = dict(payload)
    text = _json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    (run_dir / "joint-review-trigger.json").write_text(text, encoding="utf-8")
    landed = {"run_dir": True, "tree": None}
    try:
        week_dir = _iso_week_dir(datetime.fromisoformat(payload["trigger_time"]))
        tree_dir = tmv_root / "docs/workflow/operating-records" / week_dir / "trees" / tree_name
        tree_dir.mkdir(parents=True, exist_ok=True)
        (tree_dir / "joint-review-trigger.json").write_text(text, encoding="utf-8")
        landed["tree"] = str(tree_dir / "joint-review-trigger.json")
    except Exception as e:  # noqa: BLE001 — 树面 best-effort（run_dir 面已落）
        landed["tree_error"] = f"{type(e).__name__}: {e}"
    out["_landed"] = landed
    return out


def run_trigger(args: argparse.Namespace) -> tuple[int, dict]:
    """触发段主入口：(exit_code, 输出卷)。fail-closed skip 面 exit 0。"""
    run_dir = Path(args.run_dir)
    manifest = _read_json(run_dir / "manifest.json")
    if not manifest or manifest.get("run_state") != "ok":
        state = (manifest or {}).get("run_state", "manifest_absent_or_unreadable")
        skip = {
            "trigger_version": TRIGGER_VERSION,
            "loop_run_id": args.run_id,
            "run_dir": str(run_dir),
            "verdict": "skip",
            "reason": f"run_state={state} != ok（W1§四.2 fail-closed·联审不发起）",
            "from_week": args.from_week,
            "to_week": args.to_week,
            "check_time": datetime.now(timezone.utc).isoformat(),
        }
        try:
            (run_dir / "joint-review-trigger-skip.json").write_text(
                _json.dumps(skip, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception as e:  # noqa: BLE001 — 哑卷防线
            skip["write_error"] = f"{type(e).__name__}: {e}"
            return 2, skip
        return 0, skip

    payload = build_trigger(
        run_dir, Path(args.tmv_root), args.run_id, args.from_week, args.to_week)
    out = write_trigger(payload, run_dir, Path(args.tmv_root), args.tree_name)

    # notify（notify_done 同族·best-effort 永不抛·§四.2「如实报 m-duty-cos」）
    notify_result = None
    if not args.no_notify:
        try:
            from runtime.cognition.notify import send_notification
            from runtime.cognition.weekly_plane_shift import _resolve_notify_to
            body = (
                f"[joint-review-trigger] run={args.run_id} state=ok "
                f"mode={out['mode']} run_dir={out['run_dir']} "
                f"threshold=留参·召集候 m-duty-cos 拾取（W1§二.2 席单七席）"
            )
            notify_result = send_notification(
                subject=f"[joint-review-trigger] {args.run_id}",
                body=body, to=_notify_to_chain_safe()) or {"status": "render_only"}
        except Exception as e:  # noqa: BLE001 — notify best-effort 契约
            notify_result = {"status": "notify_error", "note": f"{type(e).__name__}: {e}"}
    else:
        notify_result = {"status": "render_only", "note": "no_notify 旗标"}
    out["notify_result"] = notify_result
    return 0, out


def _notify_to_chain_safe() -> list[str]:
    """收件链（_resolve_notify_to 复用·异常降级空表=render_only 语义）。"""
    try:
        from runtime.cognition.weekly_plane_shift import _resolve_notify_to
        return _resolve_notify_to()
    except Exception:  # noqa: BLE001 — 收件谱缺失不拦（best-effort）
        return []


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 联审触发段（W2·W1§二/§三 接线）")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--tmv-root", default="/srv/fleet/TriMetaverse")
    p.add_argument("--tree-name", default="fade001-loop-joint-review")
    p.add_argument("--no-notify", action="store_true", help="dev/test escape：跳过 notify")
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    exit_code, out = run_trigger(args)
    print(_json.dumps(out, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
