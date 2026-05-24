# TriCompany CEOChiefOfStaff 工作协作档案

本文件是 TriCompany 源侧认知层契约，只定义 CEOChiefOfStaff colleagues 层的用途、写入边界和运行资产落点；不记录具体人物档案或工作事项记录。

## 当前原则

- 源码侧只保留工作协作档案的通用规则和边界，不写具体人物偏好、称呼记录或事项流水。
- 工作层面的具体人物关系、协作偏好和事项记录写入 support employee workspace 或 runtime cognition state。
- 正式组织制度、岗位边界和会议治理结论应进入 CompanyGovernanceRegistry、workflow 或 operating records。
- 稳定产品 / 技术事实分别回写产品真源、技术真源或对应 registry。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/ceo-chief-of-staff.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- colleagues 层用于承载员工实例在工作层面的关系、称呼偏好、协作习惯、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 源码侧如需表达岗位协作边界，应写在 `.agent.md`、workflow 或 registry 规则中，而不是写成人物档案。