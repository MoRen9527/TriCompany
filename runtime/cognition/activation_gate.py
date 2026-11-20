"""FADE-001 D6 写面·激活判据件（挡位边·cto-d6d7-activation-ns9-survey-20261120
§二.4 件形定谳照铸零改形·WO-D6D7-20261120 §四形 A 派工面）。

业务面（§一 三层判据族总纲）：挡位边=值席手动形态→自动挡形态（run 挡）
一次性切换——与轮转边（D1 EXIT≥95 程序自动边）/质量边（D5 retry<90）零交叠
零分支：两件零消费对方产物·激活判据件不判 EXIT·EXIT 判据不判挡位。

判读面纯函数定谳（§二.4）：状态采集位在调用面（值席/runner 起跑前采集
A1-A4 状态喂入参）——件内零跨仓读零文件读·纯 stdlib·零写面（判读面
白盒零写面断言钉）。

激活判据条目族（§二.3 四条·全兑现→自动挡生效）：
  A1 改造线锚：D1-D5 划项（plan-list 划项状态·调用面采集布尔）；
  A2 白盒面：D 线新铸案族全绿+全树零新增红（判读基准=零新增红非全绿——
     既有 12 红面 3f+9e=预存环境面如实定谳禁全绿冒充·IDENTICAL 形承）；
  A3 护栏面：四护栏常位验证锚齐（与 D7 共享验证读数·单向引用非环——
     D6=引用位读 D7 验证锚结论·未齐=blocked·真实交点位）；
  A4 语义面：两态等价性锚在卷+铁律域零触维持。

防死锁自指豁免（§二.2 机械面）：checks schema 白名单=A1-A4+轮面可选键——
D6 自身毕/D7 毕/S5 毕条目键出白名单=ValueError 拒（判据含自身则死锁·
D7=起跑前置门反向非激活判据·S5 义融 ns9 首轮知情停点双承载）。

知情停点语义面（§三·D6=语义面·执行面=runner 消费接线 D7 窗族随铸零夹带）：
  首轮=ns9 起跑窗 runner 活体第一轮·完整性边界=close 段毕+verdict 面；
  首轮毕→first_round_pending=stop+呈报载荷拟稿入出参（阻塞停非知会续跑
  §三.1 四理由链·放行一次非逐轮放行）；
  放行令消费（§三.3）：停点解除=令面非时面——release_ref（authority_ref
  CEO 一手令面）在=解除语义+ref 记录；无 ref=拒绝 fail-closed（§二 CEO
  切换权同族·知会非批·COO 位=宣告知会收位非批门位 §四）。

切换宣告（§四.3）：A1-A4 全兑现→switch_announce 载荷拟稿入出参（宣告=
呈报面动作·消费位=值席/runner 呈报链·非码面分支）。

契约两分（D4 同构承）：契约面 ValueError fail-fast（checks 非 dict/白名单
外键/必填键缺/值面非布尔——try 外）；运行面 never raises 保守 dict（try 内
——值面奇异对象布尔化炸等）。零密值零敏感面（D-46）·现役件零触碰。
"""

from __future__ import annotations

import json as _json

ACTIVATION_GATE_VERSION = "1.0.0"

# A1-A4 必填键（§二.3 条目族定谳——值面布尔·采集位在调用面）
_REQUIRED_KEYS = (
    "A1_d1_d5_done",            # 改造线锚：D1-D5 划项
    "A2_whitebox_zero_new_red",  # 白盒面：案族全绿+零新增红（判读基准）
    "A3_guard_anchors_ok",      # 护栏面：四护栏常位验证锚齐（D7 共享读数引用位）
    "A4_equivalence_and_zero_touch",  # 语义面：等价性锚在卷+铁律零触
)
# 轮面可选键（§三 停点语义面·零填=零停点面）
_OPTIONAL_KEYS = (
    "first_round_complete",     # 首轮毕（close 段毕+verdict 面·调用面采集）
    "release_ref",              # 放行令 authority_ref（CEO 一手令面·停点解除）
    "round_reading",            # 轮面读数槽位（close_verdict/score_total/
                                # retry_count/exit_reading·入停点载荷拟稿）
)
_SCHEMA_KEYS = frozenset(_REQUIRED_KEYS + _OPTIONAL_KEYS)
# 防死锁禁入条目（§二.2 自指豁免·白名单拒即 ValueError——机械面零豁口）
_FORBIDDEN_TOKENS = ("d6", "d7", "s5", "activation_gate_done")

ITEM_LABELS = {
    "A1_d1_d5_done": "A1 改造线锚（D1-D5 划项·plan-list 事实源）",
    "A2_whitebox_zero_new_red": "A2 白盒面（案族全绿+全树零新增红·IDENTICAL 形）",
    "A3_guard_anchors_ok": "A3 护栏面（四护栏常位验证锚齐·D7 共享读数单向引用）",
    "A4_equivalence_and_zero_touch": "A4 语义面（两态等价性锚在卷+铁律域零触）",
}


def check_activation(checks: dict) -> dict:
    """激活判据判读面（§二.4 照铸）——纯函数零写面·状态采集位在调用面。

    出参：gate=ready|blocked+items 逐条读数+unmet 未兑现明细+
    first_round_pending 停点语义面+switch_announce 切换宣告载荷拟稿。
    契约面 ValueError fail-fast；运行面 never raises 保守 dict。
    """
    # ── 契约面校验（fail-fast·try 外·D4 校验两分同构） ───────────────
    if not isinstance(checks, dict):
        raise ValueError(
            f"checks={type(checks).__name__} 非 dict 面（schema 拒·判读面入参契约）")
    for key in checks:
        k = str(key)
        if k not in _SCHEMA_KEYS:
            low = k.lower()
            if any(tok in low for tok in _FORBIDDEN_TOKENS):
                raise ValueError(
                    f"checks 键 {k!r} 含防死锁禁入条目（D6 自身/D7/S5 零入激活判据清单"
                    "——自指豁免 §二.2·白名单拒）")
            raise ValueError(
                f"checks 键 {k!r} 出 schema 白名单（拒·防死锁机械面·"
                f"白名单={sorted(_SCHEMA_KEYS)}）")
    for key in _REQUIRED_KEYS:
        if key not in checks:
            raise ValueError(f"checks 必填键缺: {key}（A1-A4 四条目族全喂面·schema 契约）")
    for key in _SCHEMA_KEYS:
        if key in checks and key != "round_reading" and key != "release_ref" \
                and not isinstance(checks[key], bool):
            raise ValueError(f"checks[{key!r}] 非布尔面（{type(checks[key]).__name__}·"
                             "判读条目值面契约）")

    # ── 运行面（never raises·纯判读零写面） ─────────────────────────
    result: dict = {
        "ok": False,
        "gate": "blocked",
        "gate_version": ACTIVATION_GATE_VERSION,
        "items": {},
        "unmet": [],
        "first_round_pending": None,
        "switch_announce": None,
    }
    try:
        unmet: list[str] = []
        for key in _REQUIRED_KEYS:
            val = checks[key]
            result["items"][key] = {
                "label": ITEM_LABELS[key],
                "ok": val,
            }
            if not val:
                unmet.append(key)
        result["unmet"] = unmet

        if unmet:
            result["gate"] = "blocked"
            result["detail"] = (
                f"激活判据未全兑现（unmet={unmet}）——fail-closed 门闭零激活"
                "（A3 未齐=D6/D7 真实交点位·验证读数候 D7 施工窗活体面）")
            return result

        # ── 全兑现→自动挡生效（程序面即切 §四.1 兑现形） ─────────────
        result["ok"] = True
        result["gate"] = "ready"
        result["detail"] = (
            "A1-A4 全兑现→自动挡生效（挡位边程序面即切·轮转边/质量边照 D1/D5 "
            "各守各域）——switch_announce 呈 COO 知会（宣告知会位非批门·§四定谳）")
        result["switch_announce"] = {
            "announce": "fade-001 自动挡已生效（激活判据 A1-A4 全兑现·程序面即切）",
            "notify_target": "COO",
            "nature": "宣告知会（非批门·候=呈报知会非候回执·§四.1 歧义消解承）",
        }

        # ── 首轮知情停点语义面（§三.4·语义面 D6/执行面 D7 分工如实注） ──
        if checks.get("first_round_complete"):
            release_ref = checks.get("release_ref")
            reading = checks.get("round_reading")
            if isinstance(release_ref, str) and release_ref.strip():
                pending = {
                    "state": "released",
                    "authority_ref": release_ref.strip(),
                    "note": "停点解除=令面非时面（放行一次非逐轮放行·二轮起全自动）",
                }
            else:
                pending = {
                    "state": "stop",
                    "authority_ref": None,
                    "note": "首轮毕阻塞停（§三.1 四理由链·候 CEO 一手令知情放行——"
                            "放行令消费位=令面 authority_ref·无 ref=拒绝 fail-closed）",
                }
            pending["brief"] = {
                "summary": "fade-001 ns9 首轮跑毕·挂起候您一眼知情（自动挡首轮知情停点）",
                "close_verdict": (reading or {}).get("close_verdict")
                if isinstance(reading, dict) else None,
                "score_total": (reading or {}).get("score_total")
                if isinstance(reading, dict) else None,
                "retry_count": (reading or {}).get("retry_count")
                if isinstance(reading, dict) else None,
                "exit_reading": (reading or {}).get("exit_reading")
                if isinstance(reading, dict) else None,
            }
            result["first_round_pending"] = pending
        return result
    except Exception as e:  # noqa: BLE001 — never raises（门族同构承）
        return {"ok": False, "gate": "blocked", "gate_version": ACTIVATION_GATE_VERSION,
                "detail": f"activation gate failed: {type(e).__name__}: {e}"[:200],
                "items": {}, "unmet": [], "first_round_pending": None,
                "switch_announce": None}


def render_activation_payload(result: dict) -> str:
    """激活判读结果 JSON 序列化面（直跑 CLI/呈报链消费便利面·零写面）。"""
    return _json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="FADE-001 D6 激活判据件（挡位边·纯判读面）")
    p.add_argument("--checks-json", required=True,
                   help="A1-A4 状态 JSON（调用面采集后喂入）")
    a = p.parse_args()
    print(render_activation_payload(check_activation(_json.loads(a.checks_json))))
