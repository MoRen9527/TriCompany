# Memory Layer Contract

源侧认知层契约（CSO 合并件形态席；boundary marker 按本件实文承载）。

## 认知层契约

- **客户关系记忆**：每个客户的 onboarding 时间线、关键里程碑、最近互动日期和内容摘要。
- **客户健康度指标**：活跃度评分、使用频率、功能采用率、满意度趋势——由 runtime cognition state 维护，源侧仅定义 schema。
- **反馈闭环追踪**：每条客户反馈的处理状态（pending→routed→responded→resolved）、路由目标和响应时效。

## 写入边界

- 不写入客户个人隐私信息（姓名、联系方式等由 CRM 系统承载）。
- 不写入未经验证的客户行为推断——只记录可观测的事实和指标。
- 记忆层不替代 CRM——只记录对客户成功运营决策有影响的认知状态。

## 当前原则

- 源码侧只保留记忆层的通用规则和边界，不写运行消费数据。
- 客户成功运营决策相关的认知状态按下方落点分流，不混记录。

## 运行资产落点

- 学习腿（客户成功记忆）：`TriCompany-copilot-host-assets/knowledge/employees/customer-success-officer/`（inbox/wiki/workbench/audit 四区，hermes-gov-p2 员工层管道落点）
- 运行腿：`TRICOMPANY_COGNITION_HOME`（.tricompany-cognition：employee 私域运行态/org 运行共享记忆/org 运行审计——机器写入，runtime cognition backend 驱动，复活时初始化）
- 客户健康度状态：由 runtime cognition state 在 employee workspace 中维护

## 层契约

- 记忆层不替代 CRM——只记录对客户成功运营决策有影响的认知状态。
- employee id 固定为 `customer-success-officer`；该 id 只用于路径和 manifest，不代表 live 已启用。
