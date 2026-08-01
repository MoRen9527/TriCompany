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
- Employee workspace：`TriCompany-copilot-host-assets/knowledge/employees/chief-marketing-officer/`
