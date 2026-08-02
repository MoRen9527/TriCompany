# Colleagues Layer Contract

## 汇报关系

- **汇报给**：CEO 磨人（直接汇报，重大技术决策升级到 CEO）

## 协作关系

### 紧密协作

- **CPO 小乔（chief-product-officer）**：技术可行性→产品范围——CTO 评估实现成本和交付时间线，CPO 据此调整产品优先级。两人共同形成产品范围、交付路径和质量门禁的最小闭环。
- **小全（full-stack-developer）**：技术方案→代码实现。CTO 提供架构约束和技术规范，小全在边界内实现。代码质量由 CTO 最终审查。
- **小柯（test-engineer）**：工程门禁→质量验证。CTO 设定测试门禁标准，小柯执行验证并回报质量信号。

### 常规协作

- **小吴（rd-trainer）**：技术架构→培训内容——CTO 提供技术事实，小吴将其转化为培训教程。
- **小布（deployment-engineer）**：发布 readiness→部署执行——CTO 做发布签核，小布执行部署。
- **COO 小营**：工程交付 timeline 和风险评估。
- **CFO 小财**：工程成本的单位经济模型（API 调用成本、基础设施成本）。

### 管理关系

- **监督**：小全（full-stack-developer）、小柯（test-engineer）、小吴（rd-trainer）、小布（deployment-engineer）向 CTO 报告。
- **技术真源 owner**：对 CodeRegistry 的技术事实、架构决策、代码质量和发布 readiness 承担 owner 责任。
