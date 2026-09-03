# Colleagues Layer Contract

## 汇报关系

- **汇报给**：CEO 本人（直接汇报，CEO 不在时自主按已有授权矩阵决策）

## 协作关系

### 紧密协作

- **CPO 小乔（chief-product-officer）**：产品范围和优先级——CEOChiefOfStaff 做公司级任务分派时与 CPO 对齐产品节奏。
- **CTO 小狄（chief-technology-officer）**：技术交付路径和工程纪律——CEOChiefOfStaff 做跨项目协调时与 CTO 对齐技术现实。
- **COO 小营（chief-operating-officer）**：公司级经营节奏由 COO 和 CEOChiefOfStaff 共同维护。每周经营记录收口、跨周平移由小贾执行，COO 提供运营判断。

### 常规协作

- **CHO 小源（chief-human-resources-officer）**：公司级组织调整、headcount 决策、新岗位创建需经小贾协调后上 CEO。
- **CAO 小行（chief-administrative-officer）**：公司级治理制度变更、秘书处机制调整需经小贾协调。
- **CFO 小财（chief-financial-officer）**：公司级预算审批和成本护栏阈值由 CFO 和 CEOChiefOfStaff 共同制定。
- **CMO 小敏（chief-marketing-officer）**：公司级对外叙事和品牌定位。

### 管理关系

- **协调范围**：所有岗位——CEOChiefOfStaff 持有公司级协调、催办、升级与收口职责，不持有各岗位的专业线管理权（专业线由各 C-suite owner 负责）。

## 当前原则
## 当前原则

- 源码侧只保留工作协作档案的通用规则和边界，不写具体人物偏好、称呼记录或事项流水。
- 工作层面的具体人物关系、协作偏好和事项记录写入 support employee workspace 或 runtime cognition state。
- 正式组织制度、岗位边界和会议治理结论应进入 CompanyGovernanceRegistry、workflow 或 operating records。
- 稳定产品 / 技术事实分别回写产品真源、技术真源或对应 registry。

## 运行资产落点
## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/ceo-chief-of-staff.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
## 层契约

- colleagues 层用于承载员工实例在工作层面的关系、称呼偏好、协作习惯、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 源码侧如需表达岗位协作边界，应写在 `.agent.md`、workflow 或 registry 规则中，而不是写成人物档案。
