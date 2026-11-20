"""FADE-001 D3 层 2·COS 进化判决门（cto-gate-interface-ruling-20261120 §二 层 2
同构仿形新实现·仿形非改现役件）。

业务面（cto-round-programming-design §一C 定谳）：COS 收集 7 席意见综合评估＋看
双分数（7 席联审均分+fade-001 内部分）→COS 给进化/不进化判决（不投票制）——
判决程序面承载=cos-score.json 扩展形（cos 终判行+eviction_decision: evolve|hold
+rationale+双分数引用）——round_runner 读判决文件驱动（事件源双轨并读形）。

真值源=prev run_dir/cos-score.json：
  {eviction_decision: "evolve"|"hold", rationale, joint_review_avg_score,
   fade001_internal_score, decided_at, ...}——字段面施工选定形（§一C 只定
  「eviction_decision+rationale+双分数引用」语义·具体键名候 CTO 终审定谳）。

四态值域（A=check_ceo_ruling 同构承·结构同形/值域自语义）：
  skip               → ok=True（runs_root 缺/目录缺/无已跑轮·可选 gate 向后
                       兼容同款——旧宿主/单测面零波及）
  awaiting-decision  → ok=False（卷缺席/坏卷/坏值=保守拦·fail-closed 挂起；
                       >72h→escalated 升级催办 notify（never-raises 同款·
                       挂起保持不自行推进）
  evolve             → ok=True（本轮判卷毕·迭代放行——与层 1 continue AND
                       门并读=迭代放行·§一C debug 支双事件门）
  hold               → ok=False（COS 判本轮不进化·判止面——非 job 停用语义，
                       权属分立 §一C：COS=「本轮判卷后进不进」·CEO=「态切不切」
                       ——消费面投影退出码时 hold→5 判止族·与层 1 terminated
                       同表但不写 job 停用知会——job 停用面=CEO 令专权域）

prev 候选解析=check_ceo_ruling 同构三件：preflight.json size>0（F2 空壳排除
ns4 首拍实锚）+close.json 在（F3 完整轮语义 ns4 第二拍实锚·残拍排除）+
pf mtime 最新（本轮自身 run_dir 零 preflight 产物=自然排除）。

退出码映射（消费面约定·与 preflight 族同表语义）：evolve→0（放行）/
awaiting-decision→4（挂起）·hold→5（判止）——本函数只落 dict·退出码由
消费面（round_runner/层 3 探针）自行投影。

单值源注：72h 阈值显式承 preflight._ESCALATE_AFTER_H（import 单值源·零复制
常量防两处漂移）；升级收件面承 TRICO_RULING_ESCALATE_TO 同款 env（升级收件
单值面·零新键）。

与层 1 AND 门并读（裁卷 §二）：AND 消费位=round_runner while 体（§一C.135
debug 支双事件 AND 门）+层 3 生产探针投影（gate_probe_production.py）——
preflight.py 现役件零触碰（本件=独立新文件·零集成零现役行为面变更·零活体
daemon 触面）。

幂等/防重：落卷知会面=cos_decision_probe.py（.done 同款·本函数零知会防重
面——催办 notify 每探测拍可重复=与层 1 同构承）。

never raises：探测面全异常路径保守返回 dict（零阻宿·白盒案补承）。
"""

from __future__ import annotations

import json as _json
import os
from datetime import datetime, timezone
from pathlib import Path

from runtime.cognition.preflight import _ESCALATE_AFTER_H

COS_DECISION_GATE_VERSION = "1.0.0"

# 判决二值域（§一C 程序面承载·eviction_decision 键值）
EVOLUTION_DECISIONS = ("evolve", "hold")


def check_cos_decision(runs_root: str | None, now_ts: datetime | None = None) -> dict:
    """COS 进化判决门（层 2·check_ceo_ruling 同构仿形）——读上轮 run_dir
    cos-score.json 四态。

    与层 1 差异面（零复写防漂移·如实注）：
      - 真值源文件=cos-score.json（非 ceo-ruling.json）
      - 判定键=eviction_decision 二值域 evolve|hold（非 decision continue|terminate）
      - 挂起态名=awaiting-decision（非 awaiting-ruling——判决主体=COS 非 CEO）
      - 72h 阈值/候选解析/保守拦/never-raises 催办=全同构承
    """
    reading: dict = {"ok": True, "state": "skip", "detail": ""}
    if not runs_root:
        reading["detail"] = "no runs_root（可选 gate 缺省 skip·向后兼容）"
        return reading
    root = Path(runs_root)
    if not root.is_dir():
        reading["detail"] = f"runs_root not found: {root}（skip 注）"
        return reading
    candidates = []
    for d in root.iterdir():
        pf = d / "preflight.json"
        close = d / "close.json"
        if (d.is_dir() and pf.is_file() and pf.stat().st_size > 0
                and close.is_file()):
            # 空壳排除（F2）+残拍排除（F3）语义=check_ceo_ruling 同构承
            # （零复写：排除判据三件同款·注释面锚 preflight.py 同段）。
            try:
                candidates.append((pf.stat().st_mtime, d))
            except OSError:
                continue
    if not candidates:
        reading["detail"] = "no previous run（首拍/空 runs·skip 注）"
        return reading
    candidates.sort()
    prev_dir = candidates[-1][1]
    reading["prev_run_dir"] = prev_dir.name
    score_path = prev_dir / "cos-score.json"
    if not score_path.is_file():
        reading["state"] = "awaiting-decision"
        reading["ok"] = False
        age_h = None
        if now_ts is None:
            now_ts = datetime.now(timezone.utc)
        try:
            mtime = datetime.fromtimestamp(candidates[-1][0], tz=timezone.utc)
            age_h = round((now_ts - mtime).total_seconds() / 3600, 1)
        except (OSError, ValueError, OverflowError):
            pass
        reading["prev_run_age_h"] = age_h
        reading["detail"] = (
            f"cos-score.json absent in {prev_dir.name}（awaiting-decision·"
            "fail-closed 无判决不进下轮·cron 下窗再探）"
        )
        if age_h is not None and age_h > _ESCALATE_AFTER_H:
            reading["escalated"] = True
            reading["detail"] += f"·{age_h}h>{_ESCALATE_AFTER_H}h 升级催办 notify（挂起保持不自行推进）"
            reading["escalate_notify_failures"] = _escalate_notify(
                prev_dir.name, age_h)
        return reading
    try:
        score = _json.loads(score_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — 判决卷坏=保守拦（不硬跑）
        reading["state"] = "awaiting-decision"
        reading["ok"] = False
        reading["detail"] = f"cos-score.json unparsable: {e}（保守拦·候 COS 勘正）"
        return reading
    decision = str(score.get("eviction_decision", "")).strip().lower()
    reading["rationale"] = score.get("rationale")
    reading["decided_at"] = score.get("decided_at")
    reading["scores"] = {
        "joint_review_avg_score": score.get("joint_review_avg_score"),
        "fade001_internal_score": score.get("fade001_internal_score"),
    }
    if decision == "evolve":
        reading["state"] = "evolve"
        reading["ok"] = True
        reading["detail"] = (
            f"eviction_decision=evolve（{prev_dir.name}·本轮判卷毕迭代放行"
            "——层 1 continue AND 门并读=迭代放行）"
        )
        return reading
    if decision == "hold":
        reading["state"] = "hold"
        reading["ok"] = False
        reading["detail"] = (
            f"eviction_decision=hold（{prev_dir.name}·COS 判本轮不进化——"
            "判止面非 job 停用语义·权属分立 §一C）"
        )
        return reading
    reading["state"] = "awaiting-decision"
    reading["ok"] = False
    reading["detail"] = f"eviction_decision={decision!r} 非二值域（保守拦·候 COS 勘正）"
    return reading


def _escalate_notify(prev_run: str, age_h: float) -> list[dict]:
    """72h 升级催办（never-raises·check_ceo_ruling 同构承）——失败如实落
    failures 列表零炸段。"""
    try:
        from runtime.cognition.weekly_plane_shift import _notify_blocking
        to = [x.strip() for x in (os.environ.get(
            "TRICO_RULING_ESCALATE_TO", "").split(",")) if x.strip()]
        failures = _notify_blocking(
            subject="[cos-gate] cos-score 判决缺席超 3 天升级催办",
            body=f"上轮 run={prev_run} cos-score.json 缺席 "
                 f"{age_h}h（>{_ESCALATE_AFTER_H}h）——层 2 判决门 "
                 "awaiting-decision 挂起保持·候 COS 综合评估判决落卷"
                 "（eviction_decision: evolve|hold+rationale+双分数引用）",
            to=to, context_id=f"cos-decision-escalate-{prev_run}",
        )
        return failures
    except Exception as e:  # noqa: BLE001 — 催办面零炸段
        return [{"status": "escalate_path_failed", "error": str(e)[:200]}]


if __name__ == "__main__":  # pragma: no cover — 直跑探针面（审计用·零退出码表语义）
    import argparse
    import sys

    p = argparse.ArgumentParser(description="层 2 COS 进化判决门直跑探针")
    p.add_argument("--runs-root", required=True)
    args = p.parse_args()
    r = check_cos_decision(args.runs_root)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — 老宿主维持默认
        pass
    print(_json.dumps(r, ensure_ascii=False, indent=2))
