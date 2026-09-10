#!/usr/bin/env python3
"""LG-033 mc_link/mc_peer 晨检断言（BOD 强制令 2026-09-08；接线值守面）。

对 TriRLC(8711, peer=trirmc)/TriMLC(8713, peer=trimmc) healthz 做接线双断言：
- mc_peer 错值 → 接线告警（exit 2，升级级——面归属错乱）；
- mc_link != connected → 状态告警（exit 1，分报级——连接态波动）；
- 旧 trimc 字段双写过渡期兼容读（mc_link 缺位时回退 trimc）；
  正名（BOD 派单 2026-09-10）：trimc=TriMC 时代遗留 wire 名，语义=对 TriMMC
  上游链路态（现役 TRIMC_BASE_URL=sg 8710），与 TriRMC（fleet 值班面）无关；
- TriMLC 段增 trimlc 自识别串核（service 字段）。

用法：python -m runtime.cognition.mc_link_check [--base8711 URL] [--base8713 URL]
模拟触发实测：--mock-json '<healthz json>'（单面注入，测试用）。
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request

EXIT_OK = 0
EXIT_STATE = 1   # link 断（状态告警，分报）
EXIT_PEER = 2    # peer 错（接线告警，升级）

CHECKS = [
    {"name": "TriRLC", "default_base": "http://127.0.0.1:8711", "expect_peer": "trirmc", "expect_service": None},
    {"name": "TriMLC", "default_base": "http://127.0.0.1:8713", "expect_peer": "trimmc", "expect_service": "trimlc"},
]


def fetch_healthz(base: str, timeout: float = 8.0) -> dict:
    with urllib.request.urlopen(f"{base.rstrip('/')}/healthz", timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_face(name: str, health: dict, expect_peer: str, expect_service: str | None) -> tuple[int, list[str]]:
    """单面双断言。返回 (exit 码, 读数行列表)。peer 错优先于 link 断。"""
    lines: list[str] = []
    code = EXIT_OK

    # TriMLC 段自识别串核
    if expect_service is not None:
        service = health.get("service")
        if service != expect_service:
            code = max(code, EXIT_PEER)
            lines.append(f"[{name}] 接线告警: service={service!r} 期望 {expect_service!r}（自识别串错=面归属错乱）")
        else:
            lines.append(f"[{name}] service={service} ✓")

    # mc_link/mc_peer 双断言（旧 trimc 兼容读：mc_link 缺位回退 trimc；
    # trimc=遗留 wire 名，语义=mc_link→TriMMC 链路态，非 TriRMC）
    peer = health.get("mc_peer")
    link = health.get("mc_link", health.get("trimc"))
    if peer != expect_peer:
        code = max(code, EXIT_PEER)
        lines.append(f"[{name}] 接线告警: mc_peer={peer!r} 期望 {expect_peer!r}（升级级）")
    else:
        lines.append(f"[{name}] mc_peer={peer} ✓")
    if link != "connected":
        code = max(code, EXIT_STATE)
        lines.append(f"[{name}] 状态告警: mc_link={link!r} ≠ connected（分报级）")
    else:
        lines.append(f"[{name}] mc_link=connected ✓")
    legacy = health.get("trimc")
    if legacy is not None:
        lines.append(f"[{name}] trimc={legacy}（双写过渡期兼容读；遗留名，语义=mc_link→TriMMC，非 TriRMC）")
    return code, lines


def main() -> int:
    parser = argparse.ArgumentParser(description="mc_link/mc_peer 晨检断言（LG-033 接线值守）")
    parser.add_argument("--base8711", default=CHECKS[0]["default_base"])
    parser.add_argument("--base8713", default=CHECKS[1]["default_base"])
    parser.add_argument("--mock-json", help="模拟注入 healthz JSON（单面实测用，跳过网络）")
    args = parser.parse_args()

    worst = EXIT_OK
    all_lines: list[str] = []

    if args.mock_json:
        # 模拟触发实测：注入 JSON 对两面判读（peer 错→2 优先验证）
        health = json.loads(args.mock_json)
        code, lines = check_face("Mock", health, health.get("expect_peer", "trirmc"), None)
        worst = max(worst, code)
        all_lines.extend(lines)
    else:
        bases = {CHECKS[0]["name"]: args.base8711, CHECKS[1]["name"]: args.base8713}
        for check in CHECKS:
            try:
                health = fetch_healthz(bases[check["name"]])
            except Exception as exc:
                worst = max(worst, EXIT_STATE)
                all_lines.append(f"[{check['name']}] 状态告警: healthz 不可达 {exc}（分报级）")
                continue
            code, lines = check_face(check["name"], health, check["expect_peer"], check["expect_service"])
            worst = max(worst, code)
            all_lines.extend(lines)

    for line in all_lines:
        print(line)
    verdict = {EXIT_OK: "OK", EXIT_STATE: "STATE-ALERT", EXIT_PEER: "PEER-ALERT(升级)"}[worst]
    print(f"mc_link_check verdict={verdict} (exit={worst})")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
