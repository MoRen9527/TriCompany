"""agent 供给面断言探针（notice-214 款一·②preflight 供给断言族·防复发衔接）。

CTO root-cause 修复衔接面（malformed root-cause 主因=模型服务供给面败——供给
缺位未入断言族防复发·A2-2 实锚）：agent loop 一发 minimal ping（真实供给链
8710→deepseek 路由全链）——events error 面/零 delta=断言红（坏产出 fail-fast
拦截——spawn 全缺席浪费面早拦）·delta 在=绿。

preflight.check_agent_supply 调用面（·token env TRIRMC_INTERNAL_TOKEN 值面
零回显 D-46）——断言红=preflight 红不硬跑（供给缺位不烧 spawn 窗）。
"""
from __future__ import annotations

import json
import os
import urllib.request


def probe_agent_supply(endpoint: str | None = None,
                       token: str | None = None,
                       timeout_s: int = 90) -> dict:
    """agent loop 供给探针一发——返回 {ok, layer, detail}（never raises）。

    绿面判据=content_delta 非空（真实模型输出到达）；红面分层=
      call_failed（端点不可达/401 认证面）／supply_exhausted（events error
      面·fallback 全耗尽——ns4 探针实锚形）／empty_output（零 delta 零 error
      ——未知供给态·保守红）。
    """
    ep = endpoint or os.environ.get("TRICO_PLAN_AGENT_ENDPOINT",
                                    "http://localhost:8710/internal/v1/agent")
    tk = token if token is not None else os.environ.get("TRIRMC_INTERNAL_TOKEN")
    reading: dict = {"ok": False, "endpoint": ep}
    payload = {
        "systemPrompt": '只输出一个 JSON 对象：{"supply": "ok"}',
        "messages": [{"role": "user", "content": "供给探针"}],
        "maxTurns": 1,
    }
    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if tk:
            headers["X-Internal-Token"] = tk  # 值面零回显（D-46）
        req = urllib.request.Request(ep, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001 — never raises
        reading.update({"layer": "call_failed", "ok": False,
                        "reason": f"{type(e).__name__}: {str(e)[:150]}"})
        return reading
    events = result.get("events") if isinstance(result, dict) else []
    deltas = "".join(e.get("delta", "") for e in (events or [])
                     if isinstance(e, dict) and e.get("type") == "content_delta")
    if deltas.strip():
        reading.update({"ok": True, "layer": "supply_ok",
                        "delta_len": len(deltas),
                        "detail": "agent 供给链全通（模型输出到达）"})
        return reading
    errs = [str(e.get("message", ""))[:150] for e in (events or [])
            if isinstance(e, dict) and e.get("type") == "error"]
    if errs:
        reading.update({"layer": "supply_exhausted", "ok": False,
                        "reason": errs[0],
                        "note": "fallback 全耗尽形（ns4 探针实锚同型）"})
        return reading
    reading.update({"layer": "empty_output", "ok": False,
                    "reason": "零 delta 零 error（未知供给态·保守红）"})
    return reading


if __name__ == "__main__":
    r = probe_agent_supply()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    raise SystemExit(0 if r["ok"] else 2)
