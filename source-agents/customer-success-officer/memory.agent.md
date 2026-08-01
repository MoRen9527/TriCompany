# Memory Layer Contract

## 认知层契约

- **客户关系记忆**：每个客户的 onboarding 时间线、关键里程碑、最近互动日期和内容摘要。
- **客户健康度指标**：活跃度评分、使用频率、功能采用率、满意度趋势——由 runtime cognition state 维护，源侧仅定义 schema。
- **反馈闭环追踪**：每条客户反馈的处理状态（pending→routed→responded→resolved）、路由目标和响应时效。

## 写入边界

- 不写入客户个人隐私信息（姓名、联系方式等由 CRM 系统承载）。
- 不写入未经验证的客户行为推断——只记录可观测的事实和指标。
- 记忆层不替代 CRM——只记录对客户成功运营决策有影响的认知状态。

## 运行资产落点

- 客户成功记忆：`TriCompany-copilot-host-assets/knowledge/employees/customer-success-officer/`
- 客户健康度状态：由 runtime cognition state 在 employee workspace 中维护
