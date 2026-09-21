# 用途：cleanup-narrative.py 真源化迁移件（原 .fade/cleanup-narrative.py，原文照搬）
# 目标机：本机（M 面本地）
# 触发方式：Windows 计划任务（.fade 部署位运行中——sync.ps1 单向维护）
# 真源位：TriCompany/scripts/ops/admin/cleanup-narrative.windows.py

#!/usr/bin/env python3
"""批量清理：过时 TriMC 宿主切换叙事 + Copilot-host 专属 binding-profiles 引用
只改活体源文件（跳过含 D1c 退役注记的复合件）；逐文件报告变更。
"""
import os, re, glob

ROOT = r"D:\Code\ai\TriCompany\source-agents"
SKIP_MARKER = "本件已退役出渲染链"

# 替换规则（按优先级排列，先长后短）
REPLACEMENTS = [
    # Pattern 1: 完整 binding-profiles 引用行（含 TriMC 尾注）——CPO 已修的那款
    (
        r"你当前是源侧员工定义；当前 live 入口、support payload 与宿主阶段事实由 `TriCompany/\.github/binding-profiles/[a-z-]+\.json` 承载，不在源侧五件套内固化。这不等于 TriMC 正式宿主切换。",
        "你当前是源侧员工定义——源侧五件套为宿主无关的正身，宿主绑定事实由各宿主 binding profile 承载（不入源侧固化）。"
    ),
    # Pattern 1b: 同款但不带 TriMC 尾注的
    (
        r"你当前是源侧员工定义；当前 live 入口、support payload 与宿主阶段事实由 `TriCompany/\.github/binding-profiles/[a-z-]+\.json` 承载，不在源侧五件套内固化。",
        "你当前是源侧员工定义——源侧五件套为宿主无关的正身，宿主绑定事实由各宿主 binding profile 承载（不入源侧固化）。"
    ),
    # Pattern 1c: CEO 总助款（"TriCompany 源侧的 CEO 总助研发 agent"开头）
    (
        r"你当前是 TriCompany 源侧的 CEO 总助研发 agent；当前宿主阶段、live 入口与 support payload binding 事实由 `TriCompany/\.github/binding-profiles/[a-z-]+\.json` 承载，不在源侧五件套内固化。",
        "你当前是 TriCompany 源侧的 CEO 总助研发 agent——源侧五件套为宿主无关的正身，宿主绑定事实由各宿主 binding profile 承载（不入源侧固化）。"
    ),
    # Pattern 2: Copilot-host live 上岗 vs TriMC 宿主切换（行为护栏里的）
    (
        r"不把当前 Copilot-host live 上岗写成 TriMC 正式宿主切换",
        "不把当前宿主阶段上岗写成正式宿主切换"
    ),
    # Pattern 3: 禁止款（soul 层）
    (
        r"禁止把当前 Copilot-host 阶段写成 TriMC 正式宿主切换",
        "禁止把当前宿主阶段写成正式宿主切换"
    ),
    # Pattern 4: TriMC 宿主切换通用（不含 Copilot-host 前缀）
    (
        r"TriMC 正式宿主切换",
        "正式宿主切换"
    ),
    # Pattern 5: 层契约里的 binding 事实引用（通用化）
    (
        r"当前宿主 binding 事实由 binding profile 与 host-object manifest 承载，不在源侧五件套内固化",
        "宿主绑定事实由各宿主 binding profile 承载（不入源侧固化）"
    ),
]

changed_files = []
skipped_retired = 0

for root, dirs, files in os.walk(ROOT):
    for fname in files:
        if not fname.endswith(('.md', '.yaml', '.yml')):
            continue
        fpath = os.path.join(root, fname)
        try:
            text = open(fpath, 'r', encoding='utf-8').read()
        except:
            continue
        # 跳过退役复合件
        if SKIP_MARKER in text:
            skipped_retired += 1
            continue
        original = text
        for old_pat, new_val in REPLACEMENTS:
            text = re.sub(old_pat, new_val, text)
        if text != original:
            open(fpath, 'w', encoding='utf-8', newline='').write(text)
            rel = os.path.relpath(fpath, ROOT)
            changed_files.append(rel)
            print(f"  CHANGED: {rel}")

print(f"\n=== 汇总 ===")
print(f"变更文件: {len(changed_files)}")
print(f"跳过退役件: {skipped_retired}")
for f in changed_files:
    print(f"  {f}")
