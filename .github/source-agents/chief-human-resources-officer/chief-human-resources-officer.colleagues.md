# ChiefHumanResourcesOfficer 工作协作档案

本文件是 TriCompany 源侧认知层契约，只定义 ChiefHumanResourcesOfficer colleagues 层的用途、写入边界和运行资产落点；不记录具体人物档案或工作事项记录。

## 当前原则

- 源码侧只保留工作协作档案的通用规则和边界，不写具体人物关系、称呼偏好或事项流水。
- CHO 员工实例的具体协作关系和事项记录写入 support employee workspace 或 runtime cognition state。
- 正式岗位边界、交接流程、秘书处机制和治理规则进入 `.agent.md`、workflow 或 registry。
- 组织判断必须回链 registry、workflow 真源或明确的 CEO 输入。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-human-resources-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- colleagues 层用于承载当前 CHO 员工实例在工作层面的关系、协作偏好、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用的组织治理协作协议应晋升到 role workspace、workflow 或 `.agent.md`。