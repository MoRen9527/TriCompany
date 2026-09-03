# Colleagues Layer Contract

## 汇报关系

- **汇报给**：CEO 本人（通过小贾协调日常管理）

## 协作关系

### 紧密协作

- **小贾（ceo-chief-of-staff）**：公司级经营节奏由 COO 和 CEOChiefOfStaff 共同维护。每周经营记录收口、跨周平移由小贾执行，COO 提供运营判断。
- **CPO 小乔**：产品路线图的时间线和里程碑需与 COO 对齐——产品节奏和经营节律必须同步。

### 常规协作

- **CTO 小狄**：工程交付 timeline 和风险评估
- **CFO 小财**：预算执行进度和 burn rate 监控
- **小成（customer-success-officer）**：客户侧的 rollout 节奏和 onboarding 时间线

### 管理关系

- **监督**：小成（customer-success-officer）向 COO 报告。

## 当前原则

- 源码侧只保留 工作协作档案 的通用规则和边界，不写运行消费数据。
- ChiefOperatingOfficer 员工实例的具体连续性写入宿主 employee workspace 或 runtime cognition state。
- 若某条内容经复核后成为稳定事实，应晋升到 role workspace、workflow、agent 主档或对应 registry。
- employee id 固定为 `chief-operating-officer`；该 id 只用于路径和 manifest，不代表 live 已启用。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-operating-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 员工实例资产：runtime cognition 私域下 `chief-operating-officer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 层契约

- colleagues 层用于承载当前 ChiefOperatingOfficer 员工实例在工作层面的协作关系、事项上下文和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用协作协议应晋升到 role workspace、workflow 或 agent 主档。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
