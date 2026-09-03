# LG-025 顺手窗接纳项——D-16 三面管控 × publish_check 纳门域对表注记

- sourceOfTruth: TriCompany/docs/test/evidence/lg-025-m0e-graft/lg-025-d16-vs-publish-check-gate-note.md
- syncMode: evidence（对表快照，2026-09-03 顺手窗）
- lastSyncedAt: 2026-09-03
- 用途：D-16 状态行「FADE 发布链控死+publish_check 纳门=分段闸下批 2 放行前置」的门域对表注记；FSD 小全执行，交 CTO 核验收
- 对象：D-16 条款真源=`TriCompany/docs/workflow/engineering-disciplines.md` §D-16（LG-028 立法）；publish_check 门源=`TriCompany/runtime/cognition/source_publish_check.py`（--publish-agents/--project-docs/--check 族 CLI，2026-09-03 d78e5d5 前版本面）

## 一、publish_check 现有门清单（纳门域 A 面）

| 门族 | CLI 面 | 覆盖内容 |
| --- | --- | --- |
| 副本同步检查 | `--check` / `--sync`（B3，live-entry 保护） | 源↔支撑面文件 out_of_sync/in_sync/gap 报告 |
| agent 发布 | `--publish-agents` / `--agent-execute` | manifest liveEntries 资格过滤（status/kind/--employees）；多宿主渲染（HOST_RENDER_REGISTRY：copilot=.github/agents、claude=.claude/agents、claude-session=.claude/hub）；protected target；hash identical-skip；tools 白名单+剔除审计；sourceFiles preflight 存在性门（M0d R1-R5 返工面）；派生身份标记 |
| project 真源文档同步 | `--project-docs` / `--project-docs-execute` | manifest 驱动 4 条目（tricompany-central-summary / dynamic-task-tree-protocol / **trimetaverse-claude-md-copy→CLAUDE.md** / trimetaverse-agents-md-copy→AGENTS.md）+ 文档元信息头 metadata 检查 |
| ADE 终态门 | `--close`/`--verdict`/`--run-id`/`--score` 族 | §2.5 终态门 CLOSED、run-id 贯穿、Score CLI |
| watch 族 | `--event-watch`/`--watch`/`--auto-sync` | 事件监视/自动同步（audit/state 配套） |

## 二、对表：D-16 三面管控 × publish_check 门

| D-16 管控点 | D-16 指定通道 | publish_check 对应门 | 对表结论 |
| --- | --- | --- | --- |
| CLAUDE.md 客观结构面（GID-05 真源） | FADE-002 双条目（编排平面在册） | `--project-docs`（条目 trimetaverse-claude-md-copy，source=GID-05 真源文件，target=CLAUDE.md）+ metadata 检查 | 已纳；真写需 `--project-docs-execute` 显式门 |
| session 面（.claude/hub/*.session.md） | claude-session 渲染条目（LG-023 在册/LG-024 在飞） | `--publish-agents` host=claude-session：sessionBody 渲染、无 frontmatter、CLAUDE_SESSION_DERIVED_MARKER 尾注、protected_prefix=.claude/hub/、未声明 sessionBody 零行为 | 已纳；真写门 `--agent-execute` 未开（delegation dry-run） |
| spawn 面（.claude/agents+.github/agents） | source_publish_check --publish-agents（D-07 通道） | copilot/claude 双 host 渲染：frontmatter 字段序、tools PascalCase 映射+白名单（映射域外=error 不落盘）、剔除清单审计（dropped_tools）、protected target、派生标记、sourceFiles preflight | 已纳；真写门同 `--agent-execute` |
| 禁人工直改（违手改=hash 不一致→下次 publish 覆盖+审计留痕） | D-07 处置三面通用化 | before/after hash + identical-skip + action 分类（updated 留痕）+ ADE 报告 | 已纳（检查面）；覆盖动作待真写门开 |
| 无第三形态（spawn/session 同规则两渲染目标） | LG-023 S6 定案 | HOST_RENDER_REGISTRY 三 host 注册表单源多模板（加宿主=注册表加条目，管线零改动） | 已纳 |
| ADE 分段闸（D-16 状态行「批 2 放行前置」） | 分段闸 | `--close`/`--verdict`/run-id/Score CLI 终态门 | 已纳 |
| 内容×席/宿主映射（GID 条目，三环收口：内容 owner 提交→索引 owner 收口写入→MEMORY.md 指针行） | governance-memory-index（索引 owner 流程） | **无**（源码检索零命中 governance-memory-index/GID 引用） | **域外缺口①**：索引收口=CAO 治理流程门，非 publish_check 代码门域——候索引 owner 验证面认账 |
| GID 条目 platforms 全键强制声明（裁⑦ CPO 条款） | 同索引 GID 条目条款 | **无**（源码检索零命中 platforms 校验） | **域外缺口②**：无对应校验门——候选扩展缝：project-docs metadata 门增 platforms 键查，或由索引 owner 收口流程把关（CTO 裁定） |

## 三、注记结论

1. **纳门域已覆盖**：D-16 三约束面（CLAUDE.md/session/spawn）的发布、渲染、覆盖与审计通道在 publish_check 现有门内均有对应——面 1 经 `--project-docs`，面 2/3 经 `--publish-agents` 双 host 渲染（含 claude-session 特化），违手改处置经 hash/action 审计。
2. **真写门状态**：检查门全绿可跑（本次 employee_host_publish execute 委托 publish-agents：total=18 identical=5 would_sync=0 errors=0）；真写门 `--agent-execute` / `--project-docs-execute` 未开——「publish_check 纳门」当下含义=检查门纳门，与 D-16 存量手作件「管线化/退役路径销账、销账前维持 interim」前置一致。
3. **两域外缺口**（非 publish_check 代码门域，不影响纳门判据，候认账面）：① GID 内容×席映射收口（索引 owner 三环流程）；② GID 条目 platforms 全键声明无校验门（扩展缝=project-docs metadata 门或索引收口流程二选一，CTO 裁定）。

## 四、对表证据锚

- source_publish_check.py：argparse 门面（行 2964-3206）；HOST_RENDER_REGISTRY（行 174-226）；保护位/白名单（行 153-171）；project doc manifest 条目（TriCompany/.github/manifests/project-source-doc-sync-manifest.json，4 条目含 GID-05→CLAUDE.md 同步条）
- D-16 条款：engineering-disciplines.md 行 133-165（含管线并轨表行 147-155、状态行行 165）
- 本批实证：employee_host_publish execute pass errors=0（2026-09-03T15:26Z）；TriMetaverse 2bd6c228 / TriCompany 02caeea
