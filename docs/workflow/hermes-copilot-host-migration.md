# TriCompany Hermes 融合与 Copilot 宿主迁移

版本：V0.1
日期：2026-04-16
状态：初版

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/hermes-copilot-host-migration.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: active-published-copy
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/hermes-copilot-host-migration.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-04-28

## 1. 文档定位

本文用于定义 TriCompany 当前阶段的 Hermes 融合与 Copilot 宿主迁移口径。

这里说的“宿主迁移”指的是把当前阶段虚拟公司在 Copilot-host 下完成 shadow-test 并进入正式接管所需的自定义资产统一收拢到 TriCompany/.github 下，而不是宣称正式宿主已经切换。

## 2. 当前成立的结论

1. TriCompany 可以先融合 Hermes 设计。
2. TriCompany 可以先承载当前阶段的 Copilot 本地正式接管宿主资产。
3. 这不等于中央战略仓迁移，也不等于正式主控宿主切换。
4. 在 TriMC 尚未进入正式宿主切换前，若要补 skill 与 cron 能力，当前应先由 Copilot 本地正式接管宿主完成试运行验证与最后一跳可用闭环。

## 3. 当前宿主资产范围

- .github/source-agents/ 下的总助与 registry agent 源侧草案
- .github/prompts/ 下的会议入口
- .github/instructions/ 下的维护规则
- .github/manifests/ 下的回迁 TriMetaverse 清单
- runtime/cognition/ 下的元认知内核原型

## 3.1 当前记忆与设置真源边界

- 项目级持久记忆、总助口吻规则、会议回填口径和当前阶段操作偏好，应优先落在当前回迁后生效的 `TriMetaverse/.github/agents/`、`TriMetaverse/.github/prompts/`、`docs/workflow/operating-records/` 与 `TriCompany-copilot-host-assets` 支撑文档中。
- `runtime/cognition/` 的后端落盘继续由 `TRICOMPANY_COGNITION_HOME` 驱动。
- VS Code / Copilot 在用户级 `globalStorage/github.copilot-chat/memory-tool` 下生成的 memory 数据只视为宿主实现缓存，不视为项目真源；若发现项目事实只存在于该处，应先回迁到仓库资产，再继续使用。

## 4. Hermes 融合范围

- soul 保持身份层
- memory、colleagues、social 保持认知资产层
- 总助本体不显式暴露底层文件感
- 元认知层采用“统一内核 + 员工私域 + 组织共享”混合结构
- 后续 recall、sync、session-end consolidate 作为 Hermes 融合层继续验证
- 后续 SkillDraft、轻量技能命中与最小 cron / 定时复杂任务能力，也作为 Hermes 融合层的后续实现与验证项

## 5. 不应写成什么

- 不应写成 TriCompany 已成为正式宿主
- 不应写成 Task Main Controller 或 Autonomy Main Controller 已迁入 TriCompany
- 不应写成生产级 Hermes 已完成接入
- 不应写成“copilot 等同于 TriMC”
- 不应写成 cron / 自动复杂任务执行器已经完整实现

## 6. 当前最小验证项

1. 总助套件是否已统一放在 TriCompany/.github 下
2. 总助本体是否避免显式底层文件感知
3. Hermes 融合分层是否已写入设计与编排文档
4. registry 是否已切换到新的路线口径
5. 执行层是否已有迁移计划、总结和验证入口

## 7. 下一步

- 先在 TriCompany 内继续稳定这套本地正式接管宿主资产
- 先让 skill 的当前阶段最后一跳在 copilot 宿主可用，再继续推进技能注册与命中链
- 先以 copilot 宿主实现总助 agent 的最小 cron / 定时复杂任务试运行能力，并保留未来迁入 TriMC 的边界
- 用 shadow-test manifest 设计回迁 TriMetaverse/.github 的安全路径
- 再让已上岗的 CPO / CTO 输出首轮产品 / 技术接管判断并接管对应真源
- 稳定后再判断哪些结论需要同步回 TriMetaverse
