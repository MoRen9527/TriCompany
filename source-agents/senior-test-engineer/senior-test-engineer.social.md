# STE 社交档案

本文件是 TriCompany 源侧认知层契约，只定义 STE social 层的用途、写入边界和运行资产落点；不记录具体社交人物档案或社交事项记录。

## 当前原则

- 源码侧只保留社交档案的通用规则和边界，不写具体非正式称呼、互动偏好或轻社交流水。
- STE 员工实例的具体社交连续性写入 support employee workspace 或 runtime cognition state。
- 工作事实、岗位职责和正式交接优先放在 colleagues、memory 或 workflow，不与 social 层混写。
- 说话气质和测试表达风格优先由 `soul` 定义。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/senior-test-engineer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- social 层用于承载当前 STE 员工实例的轻社交连续性、非正式称呼、互动偏好和闲聊层面的待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 如果某条社交偏好变成稳定测试协作要求，应经复核后晋升到 colleagues、workflow 或正式测试文档。
