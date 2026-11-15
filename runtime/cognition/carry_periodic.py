"""carry_periodic 入迁移器机制（线 3 施工令·周期滚动族搬运机制·白名单扩窗框架）。

机制面：白名单驱动的周期滚动族搬运——清单条目（path_pattern 模板+mode）按
from-week 树 glob 取源，机械搬运至 to-week 正形目录（copy 模式=整文件平移）。
扩窗框架：清单=JSON 文件面（entries 增删=扩窗，零代码变更）；清单内容=实例
个性化面（线 1 卷定谳填入；本批交付=机制+空清单骨架）。

边界：cron schedule 零触碰；零 payload 人工触；搬运=机械复制非语义迁移
（内容 owner 席后处理）；源缺失=合法跳过记读数（不造替身）。
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_WHITELIST = Path(__file__).parent / "carry_periodic_whitelist.json"


def load_whitelist(path: Path) -> Dict[str, Any]:
    """清单装载形：JSON 面读取+形态校验（entries 缺=空清单合法）。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("whitelist entries must be a list")
    for e in entries:
        if not isinstance(e, dict) or not e.get("path_pattern"):
            raise ValueError("whitelist entry missing 'path_pattern'")
    return {"version": data.get("version", "1.0"), "entries": entries}


def carry_periodic_step(operating_root: Path, params: Dict[str, Any],
                        whitelist: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """搬运机制主步：逐白名单条目 glob from-week 源→机械搬运 to-week 正形目录。

    模板替换面：条目 path_pattern 支持 {from_week}/{to_week}/{year} 令牌
    （year=params['start_date'][:4]）；目的路径=to_dir 正形（year-W）。
    返回 (读数列表, 错误列表)。
    """
    from_week = params["from_week"]
    to_week = params["to_week"]
    year = str(params.get("start_date", ""))[:4]
    to_dir = operating_root / f"{year}-{to_week}"
    to_dir.mkdir(parents=True, exist_ok=True)
    readings: List[Dict[str, Any]] = []
    errors: List[str] = []
    for entry in whitelist.get("entries", []):
        pattern = entry.get("path_pattern", "")
        mode = entry.get("mode", "copy")
        substituted = pattern.format(from_week=from_week, to_week=to_week, year=year)
        # 源寻址：从周正形目录（year-W）优先——pattern 内 {from_week} 周段在 from_dir
        # 下剥除（防二次拼接）；裸 from_week 目录兼容面（跨年 from_dir 缺席时
        # operating_root.glob(f"*/{rel}") 三段命中形·STE 修正案）；根 glob 兜底。
        from_dir = operating_root / f"{year}-{from_week}"
        rel = substituted
        prefix = f"{from_week}/"
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
        found: List[Tuple[Path, Path]] = []
        for p in sorted(from_dir.glob(rel)):
            found.append((p, p.relative_to(from_dir)))
        if not found:
            for p in sorted(operating_root.glob(f"*/{rel}")):
                rp = p.relative_to(operating_root)
                found.append((p, Path(*rp.parts[1:])))  # 剥首周段目录
        if not found:
            # 三路兜底（STE 第二修转办）：绝对形 pattern（{year}-{from_week}/... 全路径
            # 合法模板用法）——substituted 首段=year-W 周段，剥首段后落位子结构
            # （与二路剥首段形同构一致）。
            for p in sorted(operating_root.glob(substituted)):
                rp = p.relative_to(operating_root)
                found.append((p, Path(*rp.parts[1:])))
        if not found:
            readings.append({"pattern": substituted, "mode": mode, "carried": 0,
                             "note": "源缺失（合法跳过）"})
            continue
        carried = 0
        for src, src_rel in found:
            try:
                dst = to_dir / src_rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
                carried += 1
            except Exception as err:
                errors.append("{} copy failed: {}".format(src, err))
        readings.append({"pattern": substituted, "mode": mode, "carried": carried})
    return readings, errors
