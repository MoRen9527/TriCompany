"""联审召集自动段自动化脚本面（V2-2 基座+v3 投递面·P0 registry 化 orchestrator）。

全链自动段：trigger convene_mode 读 → deliver_via 门控 → dimB 初判（机判可验
族草卷）→ 召集件渲染（七席信箱 dispatch payload 形）→ 投递/落位。

P0 registry 化（BOD 托转 138·CEO 门已开+CTO 门禁首闸绿 d54bda7af）：投递执行
面正身=delivery_plugins.py（DeliveryPlugin 契约 v1+REGISTRY 三键）——本模块=
orchestrator（mode 门控/初判/召集件渲染/插件调用）。核函数经 re-export 面保持
现名可 import（backward-compat·现有白盒 import 面零改）。

deliver_via 三形（方案卷 §3.1·零行为变）：
  · legacy-staging（缺省）：convene staging 落位（run_dir/convene/ 双件族·控制面
    m-duty-cos 值守拾取发送——零直接投递零 POST）——缺省零行为漂移
  · patch-runner（v3 主形）：--patch overlay 注入 fsd-adopt-runner 插件
  · cli-adopt（兜底形）：rc.2 原生 CLI `--session-id` adopt 直用（stdin `-` 形）

manual 形对照：convene_mode=manual → 零召集件产出零投递·输出值守 SOP 对照读数。

隔离纪律（§六 v2 照走+v3）：TC 面脚本·dry=全链渲染零落位零子进程（预演面）；
投递两形仅 deliver_via 显式声明时触 dsh 面（缺省=legacy 零 dsh 触）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── backward-compat re-export 面（现名照旧可 import·白盒 import 面零改） ──
from runtime.cognition.delivery_plugins import (  # noqa: F401
    DEFAULT_DELIVER_VIA,
    REGISTRY,
    VALID_DELIVER_VIA,
    CliAdoptPlugin,
    DeliveryPlugin,
    LegacyStagingPlugin,
    PatchRunnerPlugin,
    build_patch_runner_overlay,
    is_session_id_form,
    read_deliver_via,
    run_deliver,
    seat_session_id,
)
from runtime.cognition.loop_convene import (
    build_convene_letters,
    dimb_initial_judge,
    read_convene_mode,
)

__all__ = [
    "DEFAULT_DELIVER_VIA", "REGISTRY", "VALID_DELIVER_VIA",
    "DeliveryPlugin", "LegacyStagingPlugin", "PatchRunnerPlugin", "CliAdoptPlugin",
    "build_patch_runner_overlay", "is_session_id_form", "read_deliver_via",
    "run_deliver", "seat_session_id",
    "run_auto_segment", "main",
]


def run_auto_segment(run_dir: Path, trigger_dir: Optional[Path] = None,
                     dry: bool = False,
                     deliver_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """联审召集自动段主步：mode 门→deliver_via 门→dimB 初判→召集件渲染→插件投递/落位。

    返回读数卷（mode/deliver_via/letters/dimb/landed/delivery/compare/readings
    八键——P0 byte-level 对照面·形状零改）。
    """
    run_dir = Path(run_dir)
    trigger_dir = Path(trigger_dir) if trigger_dir else run_dir
    mode, warn = read_convene_mode(trigger_dir)
    deliver_via, dv_warn = read_deliver_via(trigger_dir)
    warns = [w for w in (warn, dv_warn) if w]

    dimb = dimb_initial_judge(run_dir)
    # mode 门控：manual=值守循环 SOP 召集形（零自动件产出零投递）；auto=召集件渲染。
    letters = (build_convene_letters(
        run_dir.name, 0, dimb.get("verdict", "unknown"),
        {"entries": len(dimb.get("entries", []))}) if mode == "auto" else [])

    delivery: Dict[str, Any] = {}
    landed: List[str] = []
    compare: Dict[str, Any] = {}
    if mode == "auto":
        # P0 registry 形：投递/落位=插件 apply（legacy=staging 落位·读数形状零改）
        delivery = run_deliver(run_dir, letters, deliver_via, deliver_config, dry)
        landed = list(delivery.get("landed", []))
        compare = {"form": "auto", "letters": len(letters), "dimb_entries": len(dimb.get("entries", [])),
                   "staged": bool(landed) and not dry}
    else:
        # manual 形对照读数（过渡形对照跑面）：召集动作=值守循环 SOP 面（值席手
        # 动召集·零自动件产出零投递）——读数并出供新旧形对照跑。
        compare = {"form": "manual", "note": "值守循环 SOP 召集形（零自动件产出·对照跑读数面）"}

    return {"mode": mode, "warn": warns, "deliver_via": deliver_via, "letters": letters,
            "dimb": dimb, "landed": landed, "delivery": delivery,
            "compare": compare,
            "readings": {"letters_count": len(letters),
                         "dimb_entries": len(dimb.get("entries", []))}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="联审召集自动段自动化脚本面（V2-2+v3 投递面·P0 registry 化）")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--trigger-dir", default=None)
    parser.add_argument("--dry", action="store_true", help="dry 预演：全链渲染零落位零子进程")
    parser.add_argument("--deliver-config", default=None,
                        help="deliver_via 投递配置 JSON（dsh_bin/dsh_home/dsh_install_anchor[/runner_path]）")
    args = parser.parse_args(argv)
    deliver_config = json.loads(args.deliver_config) if args.deliver_config else None
    out = run_auto_segment(Path(args.run_dir), Path(args.trigger_dir) if args.trigger_dir else None,
                           args.dry, deliver_config)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
