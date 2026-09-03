# Colleagues Layer Contract

## 汇报关系

- **汇报给**：CEO 本人（通过小贾协调日常管理）

## 协作关系

### 紧密协作

- **CAO 小行（chief-administrative-officer）**：CHO 负责人力资源制度和 staffing governance，CAO 负责行政管理和秘书处机制——两人共同维护公司组织制度。岗位边界有交叉时协同裁决，无法达成一致升级到 CEOChiefOfStaff。
- **小贾（ceo-chief-of-staff）**：公司级组织调整、headcount 决策、新岗位创建需经小贾协调后上 CEO。

### 常规协作

- **CPO 小乔**：岗位技能需求、产品侧 staffing 需求
- **CTO 小狄**：模块成熟度对 staffing 的影响评估
- **CFO 小财**：headcount 预算审查

### 管理关系

- **监督**：各岗位的源侧五件套和 handoff 流程——CHO 对所有员工的 onboarding/offboarding/职责变更持有验收权。

## 当前原则
## 当前原则

- 源码侧只保留工作协作档案的通用规则和边界，不写具体人物关系、称呼偏好或事项流水。
- CHO 员工实例的具体协作关系和事项记录写入 support employee workspace 或 runtime cognition state。
- 正式岗位边界、交接流程、秘书处机制和治理规则进入 `.agent.md`、workflow 或 registry。
- 组织判断必须回链 registry、workflow 真源或明确的 CEO 输入。

## 运行资产落点
## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-human-resources-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 员工实例资产：runtime cognition 私域下 `chief-human-resources-officer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 层契约
## 层契约

- colleagues 层用于承载当前 CHO 员工实例在工作层面的关系、协作偏好、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用的组织治理协作协议应晋升到 role workspace、workflow 或 `.agent.md`。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
