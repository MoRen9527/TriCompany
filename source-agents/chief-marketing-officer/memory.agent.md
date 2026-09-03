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
- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-marketing-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则
## 当前原则

- 源码侧只保留 记忆 的通用规则和边界，不写运行消费数据。
- ChiefMarketingOfficer 员工实例的具体连续性写入宿主 employee workspace 或 runtime cognition state。
- 若某条内容经复核后成为稳定事实，应晋升到 对应 product、engineering、workflow、registry、training 或 operating record 真源。
- employee id 固定为 `chief-marketing-officer`；该 id 只用于路径和 manifest，不代表 live 已启用。

## 层契约
## 层契约

- memory 层用于承载当前 ChiefMarketingOfficer 员工实例的阶段性上下文、待复核判断和任务连续性。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到对应正式真源。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
