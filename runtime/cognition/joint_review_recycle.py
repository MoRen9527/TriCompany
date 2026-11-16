"""FADE-001 联答回收段（W2 施工件·W1 架构卷 a97d76af7 §二.3/§三/§四 接线实现）。

业务面切片第十二段（联审族）——判「七席评分卷回收后分数面判定与分叉」。
TriRMC 下轮 run 消费段或控制面手动消费（§三回收段接线扩展·非推翻现役评分
面——score_engine/close_cli 现役模块零改动）。

**机械面禁自判（r101 定谳钉死）**：本段只读卷汇总判定产指令面——下一轮
发起（touch→POST marker 序现役通道）与收敛关 loop 动作归控制面
（m-duty-cos 值席）按 verdict 拾取执行，本段零 POST 零 touch。

两维度分立（§二.3·r106 形）：每席两份独立评分卷分立文件+各自 verdict_rule
对表——维度 A=subjective 试卷形（entries criterion/score·I 族 10 分制）·
维度 B=collection 试卷形（entries family_id/verdict 二值制）——禁并卷禁互判
（与 A 族两基准禁互判同族纪律）。材料包/评分卷/回收面全分立。

评分卷命名契约（召集段契约面配套）：
  joint-review-<seat>-dimA-score.json   维度 A 卷（subjective 形）
  joint-review-<seat>-dimB-score.json   维度 B 卷（collection 形）
  joint-review-<seat>-improvement.json  改进意见卷（可选·loop_next 轮输入材料）
席单（r129 材料）：COS/COO/CAO/CPO/CTO/CHO/CFO 七席。

schema fail-closed（§四.3）：失配卷拒收（零强判）不计 quorum·挂候勘面标注
——防线不放松。

verdict 六态：
  loop_next          分数不足（round<max）→ 控制面按 marker 序发起下一轮
  converge           分数达标 → 收敛段（关 loop 候 CEO 终认）
  escalate_ruling    轮数上界（默认 3）未达标 → 转候裁面禁自主续转
  pending_quorum     <quorum（默认 5/7）→ 触发件挂起态·loop 照跑不阻塞
  pending_threshold  分数线未裁（threshold=null 留参）→ 挂候裁面
  contract_mismatch  全部卷失配 → fail-closed 拒收挂候勘面

总分口径（score_engine v2.0.0 并盘 100 形对形）：三域直加制——机判域实分
（score.json B/C/D/E/G）+值席采集域席均（dimB pass 族 weight 和）+主观域
席均（dimA entries score 和）。

退出码：0=判定完成（含挂起态——挂起≠失败·联审与常规轮解耦另一半）；
2=落卷败（哑卷防线）。
"""

from __future__ import annotations

import argparse
import json as _json
from datetime import datetime, timezone
from pathlib import Path

RECYCLE_VERSION = "1.0.0"

SEATS = ("COS", "COO", "CAO", "CPO", "CTO", "CHO", "CFO")
_MACHINE_FAMILIES = ("B", "C", "D", "E", "G")
_DIMB_FAMILIES = ("A", "F", "H")


def _read_json(p: Path) -> dict | None:
    try:
        data = _json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001 — 不可读=失配拒收面
        return None


# ── schema fail-closed（§四.3·零强判） ─────────────────────────────


def validate_dim_a(vol: dict) -> list[str]:
    """维度 A 卷 schema 校验（subjective 试卷形）。返回缺陷列表（空=合格）。"""
    errs: list[str] = []
    if vol.get("dim") != "A":
        errs.append(f"dim!=A: {vol.get('dim')!r}")
    if not isinstance(vol.get("seat"), str) or not vol.get("seat"):
        errs.append("seat 缺")
    entries = vol.get("entries")
    if not isinstance(entries, list) or not entries:
        errs.append("entries 缺或空")
        return errs
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            errs.append(f"entries[{i}] 非对象")
            continue
        if not isinstance(e.get("criterion"), str) or not e.get("criterion"):
            errs.append(f"entries[{i}].criterion 缺")
        if not isinstance(e.get("score"), int) or not (0 <= e["score"] <= 10):
            errs.append(f"entries[{i}].score 非 0-10 int: {e.get('score')!r}")
    return errs


def validate_dim_b(vol: dict) -> list[str]:
    """维度 B 卷 schema 校验（collection 试卷形·二值制）。"""
    errs: list[str] = []
    if vol.get("dim") != "B":
        errs.append(f"dim!=B: {vol.get('dim')!r}")
    if not isinstance(vol.get("seat"), str) or not vol.get("seat"):
        errs.append("seat 缺")
    entries = vol.get("entries")
    if not isinstance(entries, list) or not entries:
        errs.append("entries 缺或空")
        return errs
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            errs.append(f"entries[{i}] 非对象")
            continue
        if e.get("family_id") not in _DIMB_FAMILIES:
            errs.append(f"entries[{i}].family_id 非 A/F/H: {e.get('family_id')!r}")
        if e.get("verdict") not in ("pass", "fail"):
            errs.append(f"entries[{i}].verdict 非 pass/fail: {e.get('verdict')!r}")
        if not isinstance(e.get("weight"), int):
            errs.append(f"entries[{i}].weight 缺非 int")
    return errs


# ── 卷池回收 ─────────────────────────────────────────────────────


def collect_scores(scores_root: Path) -> dict:
    """七席卷池回收：present/valid/errs 分立面。返回回收读数 dict。"""
    pool: dict = {"valid": [], "absent": [], "mismatch": []}
    dim_a_pool: list[dict] = []
    dim_b_pool: list[dict] = []
    improvements: list[dict] = []
    for seat in SEATS:
        pa = scores_root / f"joint-review-{seat}-dimA-score.json"
        pb = scores_root / f"joint-review-{seat}-dimB-score.json"
        va, vb = _read_json(pa), _read_json(pb)
        if va is None and vb is None:
            pool["absent"].append(seat)
            continue
        ea = validate_dim_a(va) if va is not None else ["dimA 卷缺"]
        eb = validate_dim_b(vb) if vb is not None else ["dimB 卷缺"]
        errs = ea + [f"dimB: {m}" for m in eb]
        if errs:
            pool["mismatch"].append({"seat": seat, "errors": errs})
            continue
        pool["valid"].append(seat)
        dim_a_pool.append(va)
        dim_b_pool.append(vb)
        pi = scores_root / f"joint-review-{seat}-improvement.json"
        if pi.is_file():
            imp = _read_json(pi)
            if isinstance(imp, dict):
                improvements.append({"seat": seat, "ref": pi.name})
    pool["dim_a_pool"] = dim_a_pool
    pool["dim_b_pool"] = dim_b_pool
    pool["improvements"] = improvements
    return pool


# ── 三域分齐与判定 ───────────────────────────────────────────────


def machine_domain_score(run_dir: Path) -> tuple[int, dict]:
    """机判域实分（run_dir/score.json B/C/D/E/G 求和）。"""
    total = 0
    fams: dict = {}
    score = _read_json(Path(run_dir) / "score.json")
    if score:
        for f in (score.get("score") or {}).get("families") or []:
            if f.get("family_id") in _MACHINE_FAMILIES and isinstance(f.get("score"), int):
                total += f["score"]
                fams[f["family_id"]] = f["score"]
    return total, fams


def dim_b_domain_score(pool: list[dict]) -> float | None:
    """值席采集域席均（Σ pass 族 weight）。"""
    if not pool:
        return None
    sums = []
    for vol in pool:
        s = sum(e["weight"] for e in vol["entries"] if e["verdict"] == "pass")
        sums.append(s)
    return round(sum(sums) / len(sums), 2)


def dim_a_domain_score(pool: list[dict]) -> float | None:
    """主观域席均（Σ entries score）。"""
    if not pool:
        return None
    sums = [sum(e["score"] for e in vol["entries"]) for vol in pool]
    return round(sum(sums) / len(sums), 2)


def decide(pool: dict, run_dir: Path, threshold: float | None,
           round_no: int, max_rounds: int, quorum: int) -> tuple[str, dict]:
    """分数面判定→verdict 六态分叉（纯判定面·零执行动作）。"""
    detail: dict = {}
    if not pool["valid"] and pool["mismatch"]:
        return "contract_mismatch", {"mismatch": pool["mismatch"]}
    if len(pool["valid"]) < quorum:
        return "pending_quorum", {
            "valid_seats": pool["valid"], "absent": pool["absent"],
            "quorum_required": quorum,
            "mismatch_sidelined": [m["seat"] for m in pool["mismatch"]],
            "note": "触发件挂起态·loop 照跑不阻塞（W1§四.1）",
        }
    mscore, mfams = machine_domain_score(run_dir)
    bscore = dim_b_domain_score(pool["dim_b_pool"])
    ascore = dim_a_domain_score(pool["dim_a_pool"])
    domains = {"machine": mscore, "duty_collection_dimB": bscore,
               "subjective_dimA": ascore}
    detail["domains"] = domains
    detail["machine_families"] = mfams
    if threshold is None:
        return "pending_threshold", {
            **detail,
            "note": "分数线接口位=null 留参（W1§二·毕验收窗 CTO 主裁 COO 会签）·挂候裁面",
        }
    parts = [mscore] + [v for v in (bscore, ascore) if isinstance(v, (int, float))]
    total = round(sum(parts), 2)
    detail["total"] = total
    detail["threshold"] = threshold
    if total >= threshold:
        return "converge", {
            **detail,
            "action_directive": "收敛段：关 loop 候 CEO 终认（控制面执行·r101 形）",
        }
    if round_no >= max_rounds:
        return "escalate_ruling", {
            **detail,
            "action_directive": f"轮数上界 {max_rounds} 未达标·转候裁面禁自主续转（W1§三）",
        }
    return "loop_next", {
        **detail,
        "action_directive": (
            "控制面按 marker 序正形发起下一轮 loop"
            "（touch TRICO_LOOP_MARKER_DIR/loop-window.marker → "
            "POST /internal/v1/cron/jobs/weekly-plane-shift/run·X-Internal-Token）"
            "·改进意见卷=下一轮输入材料随触发件流转（W1§三）"),
        "improvement_refs": pool["improvements"],
    }


def run_recycle(args: argparse.Namespace) -> tuple[int, dict]:
    """回收段主入口：(exit_code, 输出卷)。挂起态 exit 0（解耦语义）。"""
    run_dir = Path(args.run_dir)
    scores_root = Path(args.scores_root)
    pool = collect_scores(scores_root)
    verdict, detail = decide(
        pool, run_dir, args.threshold, args.round, args.max_rounds, args.quorum)
    out = {
        "recycle_version": RECYCLE_VERSION,
        "run_id": args.run_id,
        "round": args.round,
        "max_rounds": args.max_rounds,
        "quorum_required": args.quorum,
        "verdict": verdict,
        "valid_seats": pool["valid"],
        "absent_seats": pool["absent"],
        "mismatch": pool["mismatch"],
        **detail,
        "check_time": datetime.now(timezone.utc).isoformat(),
    }
    text = _json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "joint-review-recycle.json").write_text(text, encoding="utf-8")
        tree_target = Path(args.tree_file) if args.tree_file else None
        if tree_target is not None:
            tree_target.parent.mkdir(parents=True, exist_ok=True)
            tree_target.write_text(text, encoding="utf-8")
            out["_landed_tree"] = str(tree_target)
    except Exception as e:  # noqa: BLE001 — 哑卷防线
        out["write_error"] = f"{type(e).__name__}: {e}"
        return 2, out
    return 0, out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 联答回收段（W2·W1§二.3/§三/§四 接线）")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--scores-root", required=True,
                   help="七席评分卷落树目录（召集段契约面配套）")
    p.add_argument("--round", type=int, required=True, help="本轮号（1 起）")
    p.add_argument("--max-rounds", type=int, default=3,
                   help="轮数上界（COS 台账 676 采认 3 轮径裁）")
    p.add_argument("--quorum", type=int, default=5,
                   help="有效席判定线（W1§四.1 ≥5/7 径裁）")
    p.add_argument("--threshold", type=float, default=None,
                   help="分数线（null=留参·毕验收窗裁前禁传值面）")
    p.add_argument("--tree-file", default=None,
                   help="树面回写路径（可选·best-effort 双落）")
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    exit_code, out = run_recycle(args)
    print(_json.dumps(out, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
