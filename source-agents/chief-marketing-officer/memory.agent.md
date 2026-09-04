# Memory Layer Contract

## 认知层契约

- **竞品情报记忆**：竞品的关键版本更新、定价变化、市场定位调整——按时间线索引。
- **用户需求记忆**：用户访谈、反馈热力图、需求优先级排序——按产品模块分类。
- **市场趋势记忆**：行业动态、技术趋势、政策变化——按影响评估分级。
- **内容选题记忆**：内容发布日历、各渠道效果数据、选题 backlog。

## 写入边界

- 不写入未经验证的市场传闻——标注来源和可信度级别。
- 不写入产品 roadmap 的具体实现方案——那是 CPO 和 CTO 的领域。
- 市场情报标注采集日期，过期后自动降级为历史参考。

## 运行资产落点

- 市场真源：`TriCompany/docs/registry/market-state.md`（待初始化）
- 竞品情报：`TriCompany/docs/execution/competitive-intelligence/`
- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）
- 宿主 binding 事实由 binding profile 承载，不入本件
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则

- 情报原始素材与抓取记录是运行数据：写 runtime cognition 私域，不入本件；本件只留情报口径与可信度分级规则。
- 记忆层承载「哪些结论依赖哪些来源、可信度几级」的判断上下文；情报晋升为产品输入时走 CPO 域 registry。
- 增长叙事的版本演化属运行态；定稿叙事沉淀到产品/市场文档面。
- 搜索材料≠已验证结论：未核实情报只记「待验证+来源缺口」，不记结论。

## 层契约

- memory 层用于承载当前 ChiefMarketingOfficer 员工实例的阶段性上下文、待复核判断和任务连续性。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到对应正式真源。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
