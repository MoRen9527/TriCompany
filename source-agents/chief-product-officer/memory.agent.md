# Memory Layer Contract

## 认知层契约

- **产品路线图记忆**：MVP 范围、版本边界、功能优先级排序的当前状态——按版本和模块维度的索引。
- **需求池记忆**：用户需求、市场信号、CEO 输入的来源、优先级和当前处理状态——区分已验证、待验证、已拒绝。
- **竞品对比记忆**：竞品的关键功能差距、产品定位对比、能力矩阵——按模块分类。
- **产品验证记忆**：每个版本的验证指标、用户反馈、数据信号——追踪到验证闭环。
- **定价与商业化记忆**：定价假设、单位经济模型、商业化路径的当前版本和实验状态。

## 写入边界

- 不写入技术实现方案——那是 CTO 和各模块 Code Registry 的领域。
- 不写入具体用户数据或市场传闻——标注来源和可信度级别。
- 产品决策以 MVP 和当前经营实验范围为约束，不超出当前阶段商业边界扩张。

## 运行资产落点

- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME`（认知层状态与派生资产落点）

- 产品真源：`TriCompany/docs/product/PROJECT.md`、`REQUIREMENTS.md`、`STATE.md`
- 产品 Registry：`TriCompany/docs/registry/product-state.md`
- 模块级 Product Registry：各模块 `docs/registry/product-state.md`
- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）
- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-product-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则

- 源码侧只保留 CPO 记忆层的通用规则和边界，不写具体任务流水、命名记录或接管过程记录。
- 当前 CPO 员工实例的阶段性记忆写入 support employee workspace 或 runtime cognition state。
- 稳定产品结论优先回写 TriCompany 产品真源，再按需要同步到中央摘要或 support published-copy。
- 重大商业模式转向仍需 BusinessStrategy 与 CEO 裁决。

## 层契约

- memory 层用于承载当前 CPO 员工实例的产品上下文、阶段性判断、任务记忆和待复核结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 product docs、Product Registry、workflow 或 operating records。
- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
