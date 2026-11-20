"""D3 层 3·生产探针薄适配件（cto-gate-interface-ruling §二 层 3·骨架 B
gate_probe_fn 注入形为准——生产探针=本件）。

校准②（裁卷 §二定谳·零复写）：B 签名保持 ``gate_probe_fn() -> str`` 注入形
（骨架 31 案白盒零改动）——本适配件内做 dict→str 投影；detail/age/escalated
审计面留探针 stderr log（不进 Skill report·零混 stdout json 面）。

AND 门（§一C.135 debug 支双事件门）：ceo-ruling ∧ cos-evolution-decision——
投影合成规则（施工选定形·候 CTO 终审如实注）：
  判止优先：层 1 terminated 或 层 2 hold            → "terminate"
  挂起次之：层 1 awaiting-ruling 或 层 2 awaiting-decision → "absent"
  双 skip（零候选轮·校准①映射表 skip→absent 承）   → "absent"
    ——首轮面=round_runner 开轮令域（§一C debug=CEO 候批）非轮间门域·如实注
  skip 中性门（ok=True 向后兼容）+另一门有效态      → 另一门决定
  层 1 continue ∧ 层 2 evolve                       → "continue"
  任一门 raise → "absent" fail-closed（骨架 run_review try/except 已承探针崩
    →absent·本件再自承一层双保险）

Skill 本体零改动：score_skill.run_review 签名/GATE_STATES/verdict 族全零触
——接线=调用方（round_runner/部署窗 main 注入位）传本件 production_gate_probe。

runs_root 供给：参数直传 > env TRICO_PREV_RUNS_ROOT（probe 族同款缺省面）。
零密值零敏感面（D-46）·never raises（恒返 str·异常面=absent 挂起态）。
"""

from __future__ import annotations

import os
import sys

GATE_PROBE_PRODUCTION_VERSION = "1.0.0"

RUNS_ROOT_DEFAULT = "/var/lib/trirmc/cron/runs"

# 判止态族（层 1/层 2 各自语义名→B 面 terminate 投影）
_TERMINATE_STATES = frozenset({"terminated", "hold"})
# 挂起态族（ok=False fail-closed·任一门挂起→absent 不放行）
_PENDING_STATES = frozenset({"awaiting-ruling", "awaiting-decision"})


def production_gate_probe(
    runs_root: str | None = None,
    now_ts=None,
    *,
    ceo_fn=None,
    cos_fn=None,
) -> str:
    """层 3 生产探针——层 1/层 2 双门 dict→AND→B 三值 str 投影。

    ceo_fn/cos_fn=测试注入参（白盒零 mock 直注入·生产零注入走延迟 import
    单值源真件）——注入形家族语言（spawn_fn 同款精神）。
    """
    if runs_root is None:
        runs_root = os.environ.get("TRICO_PREV_RUNS_ROOT", RUNS_ROOT_DEFAULT)
    # 延迟 import 只在零注入分支走（单值源真件）——注入形（白盒/骨架树镜像面）
    # 零触发真 import（骨架树无 preflight/cos_decision_gate 零炸）。
    if ceo_fn is None:
        try:
            from runtime.cognition.preflight import check_ceo_ruling as ceo_fn
        except Exception as e:  # noqa: BLE001 — 供给面缺=absent fail-closed
            _audit_log(f"layer1 import failed: {type(e).__name__}: {e}")
            return "absent"
    if cos_fn is None:
        try:
            from runtime.cognition.cos_decision_gate import check_cos_decision as cos_fn
        except Exception as e:  # noqa: BLE001 — 同上双保险
            _audit_log(f"layer2 import failed: {type(e).__name__}: {e}")
            return "absent"

    try:
        ceo = ceo_fn(runs_root, now_ts)
    except Exception as e:  # noqa: BLE001 — 层 1 崩=absent fail-closed
        _audit_log(f"layer1 crashed: {type(e).__name__}: {e}")
        return "absent"
    try:
        cos = cos_fn(runs_root, now_ts)
    except Exception as e:  # noqa: BLE001 — 层 2 崩=absent fail-closed
        _audit_log(f"layer2 crashed: {type(e).__name__}: {e}")
        return "absent"

    s1 = str(ceo.get("state", ""))
    s2 = str(cos.get("state", ""))
    _audit_log(
        f"l1={s1}(ok={ceo.get('ok')}) l2={s2}(ok={cos.get('ok')})"
        f" prev={ceo.get('prev_run_dir')}/{cos.get('prev_run_dir')}"
        f" age={ceo.get('prev_run_age_h')}/{cos.get('prev_run_age_h')}"
        f" esc={ceo.get('escalated', False)}/{cos.get('escalated', False)}"
    )

    # AND 投影（判止 > 挂起 > skip 中性 > 放行）
    if s1 in _TERMINATE_STATES or s2 in _TERMINATE_STATES:
        return "terminate"
    if s1 in _PENDING_STATES or s2 in _PENDING_STATES:
        return "absent"  # 挂起态（ok=False）任一门在=挂起不放行
    if s1 == "skip" and s2 == "skip":
        return "absent"  # 双 skip（校准①映射表承·首轮面=开轮令域非本门域）
    if s1 == "skip":  # skip 中性门+层 2 有效态
        return "continue" if s2 == "evolve" else "absent"
    if s2 == "skip":  # skip 中性门+层 1 有效态
        return "continue" if s1 == "continue" else "absent"
    # 双有效态：continue ∧ evolve 才放行（余态保守 absent）
    return "continue" if (s1 == "continue" and s2 == "evolve") else "absent"


def _audit_log(line: str) -> None:
    """探针审计 log（校准②承：detail/age/escalated 面→stderr·不混 stdout）。"""
    try:
        print(f"[gate-probe] {line}", file=sys.stderr, flush=True)
    except Exception:  # noqa: BLE001 — 审计面零炸投影
        pass
