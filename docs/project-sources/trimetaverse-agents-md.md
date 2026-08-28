<!-- GOVERNANCE: 本文件真源在 TriCompany/docs/project-sources/，项目侧副本经 FADE-002 发布域管线（project-source-doc-sync-manifest）字节发布，禁直接修改项目侧——变更一律改真源后走管线发布。 -->

# TriMetaverse Agent Rules

## Agent Families

- `Registry Agents` 是无人格资料中枢，只负责事实、状态、边界、索引和记忆。
- `Role Agents` 是有人格岗位执行体，只负责经营判断、推进和协同。

## Central Strategy Registry

- `BusinessStrategy` 是整个三元宇宙的中央 `Strategy Registry`。
- 遇到以下问题时，必须先咨询 `BusinessStrategy`：
  - 代码所在项目说明（本次为TriMetaverse）查白皮书（tmv-whitepaper.md）
  - 总商业模式、模块商业模式（如有）、当前商业模式实验、阶段与商业目标映射
  - 模块边界变化、模块优先级、模块是否参与某条商业路径
  - 整体架构设计查询`arch-storage-migration.md`文件(融合了商业模式和价值流转设计)。
  - 公司级治理规范、文档规范、命名规范、管理流程、规则记录等应查询公司级 `CompanyGovernanceRegistry`。
  - 公司级 GitHub 仓库治理规则查询 `docs/github-repo-governance.md`文件。
  - 具体模块的内容应深入模块查询 `Business Strategy Registry`、`Product Registry`、`Code Registry`
  - 项目级整体说明查询project.md
  - 赛博公司内容查询tricompany.md
  - TriMetaverse仓说明查询README.md
  - 模块架构和功能说明查询 `docs/三元宇宙架构与模块说明.md`。
  - TriMetaverse GitHub App + Copilot 协同落地查看`github-app-copilot-rollout-v1.md`。

## Registry Convention

- 模块商业模式资料 agent 统一命名为 `<Module>BusinessStrategyRegistry`。
- 模块产品资料 agent 统一命名为 `<Module>ProductRegistry`。
- 模块代码资料 agent 统一命名为 `<Module>CodeRegistry`。
- 公司级公司治理资料 agent 固定命名为 `CompanyGovernanceRegistry`。
- 当模块已建立 `docs/registry/business-state.md` 时，该文件是同模块 `product-state.md` 与 `code-state.md` 的业务上游约束；若中央 `BusinessStrategy` 与模块 business registry 冲突，先以中央边界裁决为准。
- 在模块级 registry agent 尚未落地前，先使用该模块根目录的 `AGENTS.md`、`README.md`、设计文档和源代码树，并显式报告资料缺口。

## Architecture Routing

- 涉及 `TriMetaverse/reference/`、开源吸收链、模块 `vendor/` 布局与“最小版先跑通”的项目级说明，统一查看 `docs/三元宇宙架构与模块说明.md` 中的“TriMetaverse reference说明”。
- 如开源吸收动作会引入新的长期主模块或改变既有模块边界，必须先咨询 `BusinessStrategy`；在中央真源口径更新前，不得把边界变化写成既成事实。

## Source Of Truth Order

1. `tmv-whitepaper.md`
2. `project.md`
3. `tricompany.md`
4. `docs/三元宇宙架构与模块说明.md`
5. `docs/workflow/tricompany-agent-roles.md`
6. `docs/registry/*.md`

说明：`docs/三元宇宙架构与模块说明.md` 用于承接项目级架构说明、模块说明与 `reference` 层口径，不替代白皮书、`project.md` 或 `tricompany.md`；`docs/registry/*.md` 是工作型登记层，也不替代上面的真源文档。出现冲突时以上游真源为准。

- 项目级持久偏好、会议回填口径、宿主资产边界和运营事实必须落在仓库文件中；Copilot `memory-tool` 的 user/session/repo scope 只视为宿主侧缓存或临时辅助，不视为项目真源。

## Update Discipline

- 只有在用户明确要求“记录”或“更新”或总助（小贾）工作收口时，registry 文档才允许被修改。
- 默认先解释事实、指出来源，再给出下一步应查询的 registry 或文档。
- 对低成熟模块必须如实标记为“占位 / 待初始化 / 当前无代码”，禁止虚构进度。

## Task Tree Orchestration

Copilot CLI 默认 agent 与 Trees 协议协同，实现跨岗位自动编排。

**CLI agent 只做机器级动作：检测、调用、流转、报告。不创建节点，不做收口检查。**
节点创建和运维是 `CEOChiefOfStaff`（小贾）的职责——见 `TriCompany/docs/workflow/ceo-chief-of-staff-maintenance-rules.md`。

### 机器级规则

1. **每次收到用户消息时**，检查 SQL 活跃任务树（`task_trees.status='active'`）
2. **找到 `status='in_progress'` 的节点**，按 `seq` 最小优先
3. **根据 `agent` 字段自动调用**对应的 employee agent：
   - `ChiefProductOfficer` → `task(agent_type='ChiefProductOfficer')`
   - `ChiefTechnologyOfficer` → `task(agent_type='ChiefTechnologyOfficer')`
   - `FullStackDeveloper` → `task(agent_type='FullStackDeveloper')`
   - `TestEngineer` → `task(agent_type='TestEngineer')`
   - `CEOChiefOfStaff` → 默认 agent 自行处理
   - 未知 agent → 报告并 fallback 到 `CEOChiefOfStaff`
   - 员工级 agent 有需要升级的，应上报归属领导（当前阶段：小全、小柯归属 CTO）
   - C-Level 级 agent 有需要决策的升级到 `CEOChiefOfStaff` 决策
   - C-Level 间分歧无法达成一致时，联合升级至总助，由总助决定是否需要 CEO 裁决
   - 总助（小贾）有需要决策的升级到 `CEO` 决策(在对话中等待CEO回复，未来可以设计短信提示等方式)。
4. **传递上下文**：task prompt 包含节点的 `action`、`delivery`、上游节点交付物路径
5. **节点完成后**：
   - 更新节点状态：`in_progress → done`
   - 如果 `next_agent` 已指定 → 调用该 agent（不创建新节点——节点由总助预建）
   - 如果 `next_agent` 指定但对应节点不存在 → 报告"待总助创建节点: `<tree-id> → <next_agent>`"，不静默
   - 如果 `next_agent = NULL` → 报告"需路由评估"
6. **引用协议**：状态枚举定义见 `ceo-chief-of-staff.instructions.md`；TriMetaverse 项目摘要见 `docs/workflow/dynamic-task-tree-protocol.md`，公司级完整协议见 `../TriCompany/docs/workflow/dynamic-task-tree-protocol.md`
