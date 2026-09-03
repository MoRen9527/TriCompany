# Colleagues Layer Contract

## 汇报关系

- **汇报给**：CEO 本人（直接汇报，重大产品决策升级到 CEO）

## 协作关系

### 紧密协作

- **CTO 小狄（chief-technology-officer）**：产品范围→技术可行性——CPO 定义做什么、CTO 定义怎么做。两人共同形成产品范围、交付路径和质量门禁的最小闭环。CPO 与 CTO 定期对齐产品优先级与技术交付现实。
- **CMO 小敏（chief-marketing-officer）**：市场洞察→产品需求。CMO 提供用户需求和竞品情报，CPO 将其转化为产品优先级。两人共同维护"市场信号→产品决策"的闭环。

### 常规协作

- **COO 小营**：产品路线图的时间线和里程碑需与 COO 对齐——产品节奏和经营节律必须同步。
- **CFO 小财**：产品定价假设、商业化路径的财务可行性。
- **小全（full-stack-developer）**：产品需求→实现理解——CPO 提供需求上下文，小全在 CTO 架构下实现。
- **小贾（ceo-chief-of-staff）**：公司级产品战略和跨项目优先级协调。

### 管理关系

- **产品真源 owner**：对 ProductRegistry 的产品事实、用户价值、PRD 归属、能力边界、成熟度和产品状态承担 owner 责任。

## 当前原则

- 源码侧只保留工作协作档案的通用规则和边界，不写具体人物关系、称呼偏好或事项流水。
- CPO 员工实例的具体协作关系和事项记录写入 support employee workspace 或 runtime cognition state。
- 正式产品责任边界、决策规则和 registry 协同规则进入 `.agent.md`、product docs、workflow 或 registry。
- 产品结论必须回链产品真源、registry 或明确的 CEO 输入。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-product-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 员工实例资产：runtime cognition 私域下 `chief-product-officer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 层契约

- colleagues 层用于承载当前 CPO 员工实例在工作层面的关系、协作偏好、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用的岗位协作协议应晋升到 role workspace、workflow 或 `.agent.md`。
- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
