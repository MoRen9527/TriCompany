# TriCompany CEOChiefOfStaff 社交档案

本文件是 TriCompany 源侧认知层契约，只定义 CEOChiefOfStaff social 层的用途、写入边界和运行资产落点；不记录具体社交人物档案或社交事项记录。

## 当前原则

- 源码侧只保留社交档案的通用规则和边界，不写具体非正式称呼、互动偏好或轻社交流水。
- 具体社交人物档案、社交事项记录和非正式称呼偏好写入 support employee workspace 或 runtime cognition state。
- 工作事实优先进入 colleagues、workflow、operating records 或 registry，不与 social 层混写。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/ceo-chief-of-staff.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- social 层用于承载员工实例的轻社交连续性、非正式称呼、互动偏好和闲聊层面的待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 源码侧如需表达说话气质，应写在 `soul`；如需表达正式协作边界，应写在 `agent`、`colleagues` 层契约或 workflow。