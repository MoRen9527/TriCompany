# TriCompany 技术路线图

版本：V0.2
日期：2026-08-07
状态：新增 ADE 全生命周期实施路线

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/engineering/ROADMAP.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/engineering/ROADMAP.md
- supportSyncRule: 仅在成批发布或当前宿主重新显式依赖时追平 support 副本
- lastSyncedAt: 2026-08-07

## Wave 0：文档与 agent 骨架

- 建立 docs/product、docs/engineering、docs/registry、docs/workflow、docs/execution
- 建立 TriCompany registry agent
- 建立总助 agent 套件与会议 prompt

## Wave 1：Hermes 融合与 Copilot 宿主迁移

- 继续细化 soul、memory、colleagues、social 的分工
- 把“agent 不显式暴露底层文件”的约束写稳
- 把当前阶段 Copilot 宿主资产统一收拢到 TriCompany/.github
- 收口研发阶段的总助编排文档与 Hermes 融合清单

## Wave 2：TriCompany 内部验证与收口

- 测试会议入口、记忆分层表达、registry 路由和迁移清单
- 收口冻结项、待验证项和后续正式宿主所需缺口

## Wave 3：CPO / CTO 接管产品与技术真源

- CPO 接手产品文档与产品 registry
- CTO 接手技术设计、技术状态与 Hermes / 宿主接入
- 两者共同优化 TriCompany 资产结构

## Wave 4：跨仓同步与持续扩展

- 让更多岗位逐步进入研发与验证闭环
- 评估哪些稳定资产需要同步回 TriMetaverse
- 评估是否需要新增 runtime 代码、自动化脚本或测试资产

## Wave 5：ADE 全生命周期

当前裁决：保留一套 ADE 协议，提供 `runtime-owned-durable` 与 `agent-owned-interactive` 两个 profile；当前项目真源同步只完成 DCE，不写成完整 ADE 已落地。

CPO / CTO 对 TriLC 代码审计后追加裁决：完整 ADE 开工 `FREEZE`，先完成 P0 事实基线修复，再推进单项目、单定义、TriLC 单写主的 `runtime-owned-durable` MVP。

实施顺序：

1. 在 `@trimetaverse/agent-core` 落共享 ADE contracts、完整 orchestrator、Skill/DCE/Close runtime 与测试向量。
2. 优先复用 TriLC 已有类 Claude Code Agent loop、SkillTool、permissions、cron、HITL 和本地工具，完成首个 SQLite 本地域 ADE Host。
3. TriMC 使用同一共享 runtime 补 PostgreSQL、webhook/CI、服务端 Signal 和集群 worker adapter，达到行为 parity。
4. 通过 `homeDomain / writeAuthority / authorityEpoch / version` 实现双域同步和显式 authority 转移，禁止双活写入。
5. 由 TriCompany Trees v0.4 公司协议投影 ADE run，各项目只维护实例 adapter。
6. 完成 chaos、幂等、跨会话恢复、人工审批、投影重建和生产部署门禁。

详细设计：

- [ADE 生命周期行业模式联审](ade-lifecycle-industry-review.md)
- [ADE 与 TriLC 当前实现差距评估](ade-trilc-current-gap-assessment.md)
- [ADE 全生命周期实现蓝图](ade-full-lifecycle-implementation-plan.md)
- [TriLC / TriMC 共享 Runtime Parity 决策](trilc-trimc-runtime-parity.md)

进入实现前置条件：CEO 确认首期 local-first 范围、完成 TriLC P0 基线、CAO 对 Trees v0.4 公司真源补签，并以 `project-source-doc-sync@1.0.0` 作为首个 ADE definition。
