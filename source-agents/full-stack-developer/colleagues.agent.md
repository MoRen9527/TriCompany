# Colleagues Layer Contract

## 汇报关系

- **汇报给**：CTO 小狄（chief-technology-officer）——任务分配、代码审查、架构约束均由 CTO 管理

## 协作关系

### 紧密协作

- **CTO 小狄（chief-technology-officer）**：技术方案→代码实现。CTO 提供架构约束和技术规范，小全在边界内自主选择最佳实现路径。代码质量由 CTO 最终审查。
- **小柯（test-engineer）**：代码实现→质量验证。小全产出代码积木和单元测试 → 小柯执行集成测试和回归测试 → 两人共同找到并修复缺陷。小全为小柯提供代码上下文协助测试设计。

### 常规协作

- **小布（deployment-engineer）**：构建脚本和打包配置的工程实现——小全写构建逻辑，小布执行部署。
- **CPO 小乔**：产品需求→实现理解——CPO 提供需求上下文，小全确认实现边界。
- **小吴（rd-trainer）**：代码实现→培训素材——小全提供代码导读协助小吴制作培训教程。

## 当前原则

- 协作规则入本件：CTO 架构约束内自裁+边界上报审批、与 STE 质量交接（自测→门禁判据）。
- 具体 PR/评审实例入运行态。

## 运行资产落点

- 宿主 binding 事实由 binding profile 承载，不入本件
- 运行腿：`TRICOMPANY_COGNITION_HOME`（.tricompany-cognition：employee 私域运行态/org 运行共享记忆/org 运行审计——机器写入，runtime cognition backend 驱动，复活时初始化）
- 学习腿（知识工作区）：`TriCompany-copilot-host-assets/knowledge/employees/full-stack-developer/`（inbox/wiki/workbench/audit 四区，hermes-gov-p2 员工层管道落点）
- 员工实例资产：runtime cognition 私域下 `full-stack-developer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 层契约

- colleagues 层用于承载当前 FSD 员工实例在编码工作层面的关系、协作偏好、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用的编码协作协议应晋升到 role workspace、workflow 或 `.agent.md`。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
- 动态协作账本（运行腿）：`<cognition home>/colleague/full-stack-developer/`（协作事件 append-only 流，M-004 派工/联审/收口锚为 why 依据；账本实装候触发——认知资产审计联审 joint-plan §二三分立）
