# -*- coding: utf-8 -*-
# 序②b：employee_source_kit_validation 追加 fm 一致性断言（agent-body ≡ agent-frontmatter 件）
import io

p = 'runtime/cognition/employee_source_kit_validation.py'
s = io.open(p, encoding='utf-8').read()

body = s.rstrip()
old_tail = 'if __name__ == "__main__":\n    unittest.main()'
assert body.endswith(old_tail), repr(body[-80:])
body = body[: -len(old_tail)].rstrip('\n')

NEW = r'''

# ── 序②b（2026-09-15，CTO 批）：agent-body fm ≡ agent-frontmatter 件（单源对齐断言）──
# 背景：渲染器 fm 唯一来源=切源件自带 fm；fm 件为五件套独立面，二者失步=宿主
# agent 列表名/描述失配（CHO 缺 fm 致实读消失=缺陷级先例）。比较域=name/
# description/user-invocable（tools 已全司退役不比较——防「退役键回潮」误红）。

_FM_PARITY_KEYS = ("name", "description", "user-invocable")


def _fm_block(path: Path) -> dict[str, str] | None:
    """解析 md 顶部 frontmatter 段 → {key: value}；无段=None。"""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    out: dict[str, str] = {}
    for line in m.group(1).split("\n"):
        mm = re.match(r"^(\w[\w-]*):\s?(.*)$", line)
        if mm:
            out[mm.group(1)] = mm.group(2).strip().strip('"')
    return out


def _frontmatter_parity_issues(source_root: Path) -> list[str]:
    """逐席核 agent-body fm ≡ agent-frontmatter 件（三域）；返回人话差异清单。"""
    issues: list[str] = []
    for seat in iter_component_employee_ids(source_root):
        d = source_root / "source-agents" / seat
        body_fm = _fm_block(d / "agent-body.agent.md")
        fm_copy = _fm_block(d / "agent-frontmatter.agent.md")
        if body_fm is None:
            issues.append(f"{seat}: agent-body 无 frontmatter 段（渲染器 fm 唯一来源缺失）")
            continue
        if fm_copy is None:
            issues.append(f"{seat}: agent-frontmatter 件缺失或无 fm 段（应=agent-body 同值）")
            continue
        for key in _FM_PARITY_KEYS:
            if body_fm.get(key) != fm_copy.get(key):
                issues.append(f"{seat}: {key} 不一致（agent-body={body_fm.get(key)!r} vs fm 件={fm_copy.get(key)!r}）")
    return issues


class FrontmatterParityValidation(unittest.TestCase):
    def test_live_source_agents_frontmatter_parity(self) -> None:
        """实盘 14 席：agent-body fm ≡ agent-frontmatter 件（对齐后入场即绿）。"""
        repo_root = Path(__file__).resolve().parents[2]
        issues = _frontmatter_parity_issues(repo_root)
        self.assertEqual(issues, [], "\n".join(issues))

    def test_parity_checker_detects_description_drift(self) -> None:
        """反例 fixture：description 漂移必被检出（防断言摆设——正反两向都验）。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            d = source_root / "source-agents" / "parity-probe"
            d.mkdir(parents=True)
            (d / "agent-body.agent.md").write_text(
                '---\nname: Probe\ndescription: "A"\nuser-invocable: true\n---\n## 核心职责\n', encoding="utf-8"
            )
            (d / "agent-frontmatter.agent.md").write_text(
                '---\nname: Probe\ndescription: "B"\nuser-invocable: true\n---\n', encoding="utf-8"
            )
            issues = _frontmatter_parity_issues(source_root)
            self.assertTrue(any("description 不一致" in i for i in issues), issues)

    def test_parity_checker_detects_missing_body_frontmatter(self) -> None:
        """反例 fixture：agent-body 缺 fm 段（CHO 先例形态）必被检出。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "TriCompany"
            d = source_root / "source-agents" / "parity-probe2"
            d.mkdir(parents=True)
            (d / "agent-body.agent.md").write_text("## 核心职责\n\n无 fm 段。\n", encoding="utf-8")
            (d / "agent-frontmatter.agent.md").write_text(
                '---\nname: Probe2\ndescription: "X"\nuser-invocable: true\n---\n', encoding="utf-8"
            )
            issues = _frontmatter_parity_issues(source_root)
            self.assertTrue(any("无 frontmatter 段" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
'''

s = body + NEW
if "\nimport re\n" not in s and not s.startswith("import re\n"):
    s = s.replace("from __future__ import annotations\n\nimport tempfile", "from __future__ import annotations\n\nimport re\nimport tempfile", 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('appended; re-import ok:', 'import re' in s.split('class ')[0])
