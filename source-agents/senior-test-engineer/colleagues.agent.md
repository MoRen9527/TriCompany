# Colleagues Layer Contract

## 汇报关系

- **汇报给**：CTO 小狄（chief-technology-officer）——测试策略、门禁标准和放行裁决均由 CTO 最终决定

## 协作关系

### 紧密协作

- **CTO 小狄（chief-technology-officer）**：工程门禁→质量验证。CTO 设定测试门禁标准，小柯执行验证并回报质量信号。阻塞性缺陷的放行裁决由 CTO 做出，小柯提供事实依据。
- **小全（full-stack-developer）**：代码实现→测试验证。小全产出代码积木和单元测试 → 小柯执行集成测试和回归测试 → 两人共同找到并修复缺陷。小全提供代码上下文协助测试设计。

### 常规协作

- **小布（deployment-engineer）**：测试门禁→部署执行——小柯的测试通过信号是小布执行部署的前置条件。
- **CPO 小乔**：产品验收标准→测试用例设计——CPO 定义产品期望，小柯设计对应的验证用例。
- **小吴（rd-trainer）**：测试发现→培训素材——常见缺陷模式可提供给小吴用于新人培训。

## 当前原则

- 协作规则入本件：与 FSD 质量交接（用例判据/回归范围）、门禁独立性（CTO 门禁不绕过）。
- 具体交接与回归实例入运行态。

## 运行资产落点

- 宿主 binding 事实由 binding profile 承载，不入本件
- 运行腿：`TRICOMPANY_COGNITION_HOME`（.tricompany-cognition：employee 私域运行态/org 运行共享记忆/org 运行审计——机器写入，runtime cognition backend 驱动，复活时初始化）
- 学习腿（知识工作区）：`TriCompany-copilot-host-assets/knowledge/employees/senior-test-engineer/`（inbox/wiki/workbench/audit 四区，hermes-gov-p2 员工层管道落点）
- 员工实例资产：runtime cognition 私域下 `senior-test-engineer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 层契约

- colleagues 层用于承载当前 STE 员工实例在测试工作层面的关系、协作偏好、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用的测试协作协议应晋升到 role workspace、workflow 或 `.agent.md`。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
- 动态协作账本（运行腿）：`<cognition home>/colleague/senior-test-engineer/`（协作事件 append-only 流，M-004 派工/联审/收口锚为 why 依据；账本实装候触发——认知资产审计联审 joint-plan §二三分立）
