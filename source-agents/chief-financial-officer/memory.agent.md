# Memory Layer Contract

## 认知层契约

- **预算记忆**：各项目的预算分配、已执行金额、剩余额度——按项目和时间线追踪。
- **成本护栏记忆**：成本异常预警阈值、触发条件、当前是否有活跃的预警信号。
- **盈利检查记忆**：各产品的单位经济模型、盈亏状态、盈利路径时间线。
- **财务风险记忆**：现金流、burn rate、runway——按周更新趋势。

## 写入边界

- 不写入具体的 API 调用费用或 token 级别成本——那是工程团队的粒度，CFO 关注项目级和公司级预算。
- 不替代各岗位的采购决策——CFO 设定预算边界和审批门槛，具体采购由岗位 owner 在边界内自主决定。
- 财务记忆不替代正式的会计系统——这是经营决策辅助层，不是法定财务报告。

## 运行资产落点

- 财务真源：`TriCompany/docs/registry/finance-state.md`（待初始化）
- 预算记录：`TriCompany/docs/execution/budget-records/`
- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）
- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-financial-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则

- 源码侧只保留 记忆 的通用规则和边界，不写运行消费数据。
- ChiefFinancialOfficer 员工实例的具体连续性写入宿主 employee workspace 或 runtime cognition state。
- 若某条内容经复核后成为稳定事实，应晋升到 对应 product、engineering、workflow、registry、training 或 operating record 真源。
- employee id 固定为 `chief-financial-officer`；该 id 只用于路径和 manifest，不代表 live 已启用。

## 层契约

- memory 层用于承载当前 ChiefFinancialOfficer 员工实例的阶段性上下文、待复核判断和任务连续性。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到对应正式真源。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
