## 通信正名与时刻纪律（恢复/开场基线段）

> 收编自 FSD 席手作 session 件现役有效内容（.claude/hub/full-stack-developer.session.md，2026-09-01 BOD 手作；LG-024 批 1 前置源件化——COS 施工单 2026-09-04T15:2xZ）。其余正文由合成件零剥离公式自动带入，不在本件重复。

- 通信面正名=**FD**（别名 小全/全栈开发）→ 寻址一律正名；董事会正名=**BOD**（别名 董事会）。
- 回报前 ListAgents 对名址；时刻引用先 date 现查（UTC Z 后缀 +8 换算），执行令时点须与令文交叉核对。

## FSD 实现域路由与管线命令族（域知识族·LG-028 迁入）

> D 类域知识族（LG-028 第一步②同构；内容源=FSD 实现域实战沉淀；指针两要素=目标面正名+真源路径）。

### 技术真源路由（指针）

- 技术真源顺序：`TriCompany/docs/engineering/DESIGN.md` → `metacognition-architecture.md` → `docs/registry/code-state.md` → 模块级 `docs/registry/code-state.md`（CTO 席域知识节为工程命令族主承载，实现细节路由随席）。
- 发布管线正身：`TriCompany/runtime/cognition/`（employee_source_kit / source_publish_check / employee_host_publish / host_object_generation）——协议正身 `docs/workflow/host-object-publish-flow.md`。

### 灌注/发布管线命令族（TriCompany 仓根执行）

```bash
# 五件套 validate（单席）
PYTHONPATH=D:\Code\ai\TriCompany python -m runtime.cognition.employee_source_kit validate --source-root D:\Code\ai\TriCompany --employee-id <id>
# 组件-合成件同步检查（全席）
python -m runtime.cognition.employee_source_kit check-sync --source-root D:\Code\ai\TriCompany --all
# 389 门全量回归（validation 族 discover）
python -m unittest discover -s runtime/cognition -t . -p "*_validation.py"
# 支撑面 publish（execute 真写；delegation 内嵌 publish-agents 为 dry-run）
python -m runtime.cognition.employee_host_publish --source-root D:\Code\ai\TriCompany --support-root D:\Code\ai\TriMetaverse\TriCompany-copilot-host-assets --employee <id> --execute
# spawn/session 面真写（session 面须显式 --host claude-session）
python -m runtime.cognition.source_publish_check --publish-agents --agent-execute --host claude-session --source-root D:\Code\ai\TriCompany --support-root D:\Code\ai\TriMetaverse\TriCompany-copilot-host-assets
```

### 已知坑位（实现域，2026-09-04 实勘）

- publish-agents 不带 `--host` 默认 copilot 面——session 面零行为非报错，静默陷阱。
- 写根勘定=source_root.parent（TriCompany 的 parent=D:\Code\ai 非 TriMetaverse 根）——CLI session 面写落点错位 bug 在案（D:\Code\ai\.claude\hub 幽灵目录实证 2026-09-04），修候 CTO 域；过渡期组合公式直调脚本写正根。
- agent-core contract accept 面=CONTRACT_V3_SUPPORTED_VERSIONS=['3.0','3.1']（v3.1=ceo/CTO 席 session_body 扩展形态）。
