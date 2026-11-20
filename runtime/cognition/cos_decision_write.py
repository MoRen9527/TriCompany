"""FADE-001 D4 写面·COS 综合裁判接口（cto-d4-cosreferee-interface-survey-20261120
§一.4 签名定谳照铸零改形·WO-D4-20261120 §四 派工面）。

业务面（§一C 定谳语义）：COS 收集 7 席意见综合评估＋看双分数→COS 给
evolve|hold 判决（不投票制）——本件=判决落卷唯一写面（终局事件源）。

六键 schema（§一.2 定谳·键名通用化形 A=internal_score+instance）：
  {eviction_decision: evolve|hold, rationale, joint_review_avg_score,
   internal_score, instance, decided_at}——其余键=写面自由扩展区（读面零依赖）。

三定谳伴生语义（§一.4·零改形照铸）：
  1. 落卷位=本轮 run_dir/cos-score.json——写本轮非写 prev（读面 candidates[-1]
     pf mtime 最新完整轮=下轮开时的 prev——本轮落卷→下轮本轮变 prev→链条闭合
     =防自吞判决正形）；
  2. 原子写=tmp+os.replace 同目录（零半卷面——读面坏卷保守拦已兜底·写面自持
     原子=零制造坏卷）；
  3. 防重默认拒覆写=decided 卷在（eviction_decision 有效二值）→默认拒绝
     （判决=终局事件源·零静默覆写）——勘正重判=显式 overwrite=True+勘正理由
     并入 rationale（调用方义务）——覆写溯源=卷面 overwritten/previous_decided_at
     两扩展键（施工选定形·自由扩展区·值席线 B-7 数据处置联动审计面）候终审。

校验两分（施工选定形·如实注）：
  参数契约面（编程错误）=raise ValueError fail-fast（二值域出域/空串/非数值——
  白盒锚「二值域出域 ValueError 案」定谳承）；
  运行面（IO/意外）=never raises 保守返 {ok: False, ...}（门族同构承·零阻宿）。

读面配套=cos_decision_gate.py（D3 交付·本窗随勘 internal_score 单行+docstring
——勘面卷 §一.3 承）。意见窗机制面=勘面卷 §二定谳在卷（码面候生产并发编排
窗·零本窗施工面）。

零密值零敏感面（D-46）·preflight 现役件零触碰（独立新件）。
"""

from __future__ import annotations

import json as _json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

COS_DECISION_WRITE_VERSION = "1.0.0"

EVOLUTION_DECISIONS = ("evolve", "hold")

SCORE_FILE = "cos-score.json"


def write_cos_decision(
    run_dir: str | Path,
    eviction_decision: str,
    rationale: str,
    joint_review_avg_score: float,
    internal_score: float,
    instance: str,
    decided_at: str | None = None,
    overwrite: bool = False,
) -> dict:
    """COS 进化判决落卷（写面唯一接口·§一.4 定谳照铸）。

    参数校验=契约面 raise ValueError（fail-fast）；运行面异常=never raises
    保守返 dict（{ok: False, reason, ...}）。
    """
    # ── 参数契约面校验（fail-fast·白盒锚定谳承） ──────────────────────
    decision = str(eviction_decision).strip().lower()
    if decision not in EVOLUTION_DECISIONS:
        raise ValueError(
            f"eviction_decision={eviction_decision!r} 非二值域 {EVOLUTION_DECISIONS}"
            "（出域拒·判决终局事件源零出域值入卷）")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("rationale 空串/非字串面拒（零空卷·综合评估理由必付）")
    if instance is None or not str(instance).strip():
        raise ValueError("instance 空串拒（实例身份入卷 evidence 面·§一.1 形 A）")
    for name, val in (("joint_review_avg_score", joint_review_avg_score),
                      ("internal_score", internal_score)):
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ValueError(f"{name}={val!r} 非数值面拒（bool⊂int 陷阱同族）")

    try:
        rd = Path(run_dir)
        target = rd / SCORE_FILE
        rd.mkdir(parents=True, exist_ok=True)

        # ── 防重（三伴生③：decided 卷在=终局事件源·默认拒覆写） ──────
        previous_decided_at = None
        if target.is_file():
            prev_state = _read_prev_decision(target)
            if prev_state in EVOLUTION_DECISIONS and not overwrite:
                return {
                    "ok": False,
                    "state": "already_decided",
                    "path": str(target),
                    "reason": (
                        "cos-score.json already decided（判决=终局事件源·防重"
                        "默认拒覆写——勘正重判=显式 overwrite=True+勘正理由入 "
                        "rationale·值席线 B-7 数据处置联动）"),
                }
            if prev_state in EVOLUTION_DECISIONS:
                previous_decided_at = _read_prev_field(target, "decided_at")

        # ── 落卷时点（None=函数内 date 现查 UTC ISO8601·D-47 面） ─────
        if decided_at is None:
            decided_at = datetime.now(timezone.utc).isoformat()

        payload = {
            "eviction_decision": decision,
            "rationale": rationale,
            "joint_review_avg_score": joint_review_avg_score,
            "internal_score": internal_score,
            "instance": str(instance).strip(),
            "decided_at": decided_at,
        }
        if previous_decided_at is not None:
            payload["overwritten"] = True
            payload["previous_decided_at"] = previous_decided_at

        # ── 原子写（三伴生②：tmp+os.replace 同目录·零半卷） ──────────
        fd, tmp_path = tempfile.mkstemp(dir=str(rd), prefix=".cos-score-",
                                        suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                _json.dump(payload, f, ensure_ascii=False, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, target)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        return {
            "ok": True,
            "path": str(target),
            "decided_at": decided_at,
            "eviction_decision": decision,
            "instance": payload["instance"],
            "overwritten": previous_decided_at is not None,
        }
    except ValueError:
        raise  # 契约面透传（fail-fast 语义面）
    except Exception as e:  # noqa: BLE001 — 运行面 never raises（门族同构承）
        return {"ok": False, "reason": f"write failed: {type(e).__name__}: {e}"[:200],
                "path": str(Path(run_dir) / SCORE_FILE)}


def _read_prev_decision(target: Path) -> str | None:
    """读既有卷判定键（防重判据用·坏卷/缺键=非 decided 卷→None 可覆写）。"""
    try:
        raw = _json.loads(target.read_text(encoding="utf-8"))
        d = str(raw.get("eviction_decision", "")).strip().lower()
        return d if d in EVOLUTION_DECISIONS else None
    except Exception:  # noqa: BLE001 — 坏卷=非 decided 卷（可覆写·零静默面注）
        return None


def _read_prev_field(target: Path, field: str):
    try:
        return _json.loads(target.read_text(encoding="utf-8")).get(field)
    except Exception:  # noqa: BLE001 — 溯源面零炸
        return None
