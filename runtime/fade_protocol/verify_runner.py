"""Verify 断言 runner 骨架（N-D3 件①·通用骨架）。

职责：写入后回读的断言执行框架——断言清单装载形/三种断言运行形
（存在性/格式合规/非空）/失败上报形。断言集=实例个性化件（由实例配置
载入，本骨架零实例知识）。
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

# 断言类型注册形（运行形三原语；扩展=注册新运行形，不改 runner）
_ASSERTION_RUNNERS: Dict[str, Callable[[Dict], Tuple[bool, str]]] = {}


def register_assertion(kind: str, runner: Callable[[Dict], Tuple[bool, str]]) -> None:
    """装载形扩展点：注册自定义断言运行形（实例侧扩展通道）。"""
    _ASSERTION_RUNNERS[kind] = runner


def load_assertions(spec: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """断言清单装载形：校验清单形态（kind 必填/参数体随 kind），返回规范化清单。"""
    normalized: List[Dict[str, Any]] = []
    for i, item in enumerate(spec or []):
        if not isinstance(item, dict) or not item.get("kind"):
            raise ValueError("assertion #{}: missing 'kind'".format(i))
        normalized.append({**item, "_index": i})
    return normalized


def _run_exists(item: Dict[str, Any]) -> Tuple[bool, str]:
    import os
    target = item.get("target", "")
    ok = bool(target) and os.path.exists(target)
    return ok, "exists: {}".format(target or "<missing target>")


def _run_non_empty(item: Dict[str, Any]) -> Tuple[bool, str]:
    value = item.get("value")
    ok = isinstance(value, str) and value.strip() != ""
    return ok, "non-empty check on '{}'".format(item.get("label", "value"))


def _run_format(item: Dict[str, Any]) -> Tuple[bool, str]:
    value = str(item.get("value", ""))
    pattern = item.get("pattern", "")
    if not pattern:
        return False, "format assertion missing 'pattern'"
    ok = re.search(pattern, value) is not None
    return ok, "format match [{}] against {} chars".format(pattern, len(value))


_ASSERTION_RUNNERS.update({"exists": _run_exists, "non-empty": _run_non_empty, "format": _run_format})


def run_verify(assertions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """回读执行：逐条跑断言清单，产出失败上报形（逐条结果+汇总）。

    失败不上抛（上报形=逐条结果记录；调用方据 summary 决定段位处置）。
    """
    results: List[Dict[str, Any]] = []
    failures = 0
    for item in load_assertions(assertions):
        kind = item["kind"]
        runner = _ASSERTION_RUNNERS.get(kind)
        if runner is None:
            ok, detail = False, "unknown assertion kind: {}".format(kind)
        else:
            try:
                ok, detail = runner(item)
            except Exception as err:  # 运行形异常=断言失败（不炸 runner）
                ok, detail = False, "runner exception: {}".format(err)
        if not ok:
            failures += 1
        results.append({"index": item["_index"], "kind": kind, "ok": ok, "detail": detail})
    return {"total": len(results), "failed": failures, "passed": len(results) - failures, "results": results}
