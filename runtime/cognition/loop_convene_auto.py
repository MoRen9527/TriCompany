"""联审召集自动段自动化脚本面（V2-2·基于 V2-1 loop_convene 交付谱系）。

全链自动段：trigger convene_mode 读 → dimB 初判（机判可验族草卷）→ 召集件
渲染（七席信箱 dispatch payload 形）→ convene staging 落位（run_dir/convene/
面·控制面 m-duty-cos 值守拾取发送——本脚本零直接投递零 POST）。

manual 形对照（过渡形对照跑面）：convene_mode=manual → 零召集件产出·输出
值守 SOP 对照读数（召集动作归值席值守循环 SOP 面）——新旧两形读数并出供
对照跑（过渡形=新旧召集形对照读数）。

隔离纪律（§六 v2）：TC 面脚本·零触河源·零触第 11 轮在途链与已验收现役链；
dry=全链渲染零落位（预演面）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from runtime.cognition.loop_convene import (
    build_convene_letters,
    dimb_initial_judge,
    read_convene_mode,
)


def run_auto_segment(run_dir: Path, trigger_dir: Optional[Path] = None,
                     dry: bool = False) -> Dict[str, Any]:
    """联审召集自动段主步：mode 门→dimB 初判→召集件渲染→staging 落位。

    返回读数卷（mode/letters/dimb/landed/compare——对照跑读数面）。
    """
    run_dir = Path(run_dir)
    trigger_dir = Path(trigger_dir) if trigger_dir else run_dir
    mode, warn = read_convene_mode(trigger_dir)

    dimb = dimb_initial_judge(run_dir)
    # mode 门控：manual=值守循环 SOP 召集形（零自动件产出）；auto=召集件渲染。
    letters = (build_convene_letters(
        run_dir.name, 0, dimb.get("verdict", "unknown"),
        {"entries": len(dimb.get("entries", []))}) if mode == "auto" else [])

    landed: List[str] = []
    compare: Dict[str, Any] = {}
    if mode == "auto":
        if not dry:
            stage = run_dir / "convene"
            stage.mkdir(parents=True, exist_ok=True)
            (stage / "convene-letters.json").write_text(
                json.dumps(letters, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (stage / "dimb-initial.json").write_text(
                json.dumps(dimb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            landed.append(str(stage / "convene-letters.json"))
            landed.append(str(stage / "dimb-initial.json"))
        compare = {"form": "auto", "letters": len(letters), "dimb_entries": len(dimb.get("entries", [])),
                   "staged": bool(landed) and not dry}
    else:
        # manual 形对照读数（过渡形对照跑面）：召集动作=值守循环 SOP 面（值席手
        # 动召集·零自动件产出）——读数并出供新旧形对照跑。
        compare = {"form": "manual", "note": "值守循环 SOP 召集形（零自动件产出·对照跑读数面）"}

    return {"mode": mode, "warn": warn, "letters": letters, "dimb": dimb,
            "landed": landed, "compare": compare,
            "readings": {"letters_count": len(letters),
                         "dimb_entries": len(dimb.get("entries", []))}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="联审召集自动段自动化脚本面（V2-2）")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--trigger-dir", default=None)
    parser.add_argument("--dry", action="store_true", help="dry 预演：全链渲染零落位")
    args = parser.parse_args(argv)
    out = run_auto_segment(Path(args.run_dir), Path(args.trigger_dir) if args.trigger_dir else None, args.dry)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
