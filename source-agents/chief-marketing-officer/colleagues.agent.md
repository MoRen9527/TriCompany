# Colleagues Layer Contract

## 汇报关系

- **汇报给**：CEO 本人（通过小贾协调日常管理）

## 协作关系

### 紧密协作

- **CPO 小乔（chief-product-officer）**：市场洞察→产品需求。CMO 提供用户需求和竞品情报，CPO 将其转化为产品优先级。两人共同维护"市场信号→产品决策"的闭环。
- **小成（customer-success-officer）**：市场定位→客户反馈双向流动。CMO 提供市场定位和竞品信息，小成提供客户使用数据和满意度信号。

### 常规协作

- **COO 小营**：上线窗口和 rollout 计划的市场侧配合
- **CFO 小财**：营销预算、用户获取成本的财务评估
- **小贾**：公司级对外叙事和品牌定位

## 当前原则

- 源码侧只保留 工作协作档案 的通用规则和边界，不写运行消费数据。
- ChiefMarketingOfficer 员工实例的具体连续性写入宿主 employee workspace 或 runtime cognition state。
- 若某条内容经复核后成为稳定事实，应晋升到 role workspace、workflow、agent 主档或对应 registry。
- employee id 固定为 `chief-marketing-officer`；该 id 只用于路径和 manifest，不代表 live 已启用。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-marketing-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 员工实例资产：runtime cognition 私域下 `chief-marketing-officer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 层契约

- colleagues 层用于承载当前 ChiefMarketingOfficer 员工实例在工作层面的协作关系、事项上下文和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用协作协议应晋升到 role workspace、workflow 或 agent 主档。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
