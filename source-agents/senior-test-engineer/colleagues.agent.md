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
## 当前原则

- 源码侧只保留工作协作档案的通用规则和边界，不写具体人物关系、称呼偏好或事项流水。
- STE 员工实例的具体协作关系和事项记录写入 support employee workspace 或 runtime cognition state。
- 正式测试职责、质量门禁和输入来源进入 `.agent.md`、test docs 或 workflow。
- STE 当前由 CTO acting 管理；正式向 CTO 报告，与 CTO 共同维护工程门禁。
- 其他岗位尚未正式上岗时，只在运行资产中记录待同步入口，不把待同步状态写成源码事实。

## 运行资产落点
## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/senior-test-engineer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 员工实例资产：runtime cognition 私域下 `senior-test-engineer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 层契约
## 层契约

- colleagues 层用于承载当前 STE 员工实例在测试工作层面的关系、协作偏好、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用的测试协作协议应晋升到 role workspace、workflow 或 `.agent.md`。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
