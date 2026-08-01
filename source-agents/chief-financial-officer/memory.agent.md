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
- Employee workspace：`TriCompany-copilot-host-assets/knowledge/employees/chief-financial-officer/`
