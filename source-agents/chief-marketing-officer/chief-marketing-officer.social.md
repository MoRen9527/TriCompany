# ChiefMarketingOfficer 社交档案

本文件是 TriCompany 源侧认知层契约，只定义 ChiefMarketingOfficer social 层的用途、写入边界和运行资产落点；不记录具体非正式称呼、互动偏好或轻社交流水。

## 当前原则

- 源码侧只保留 社交档案 的通用规则和边界，不写运行消费数据。
- ChiefMarketingOfficer 员工实例的具体连续性写入宿主 employee workspace 或 runtime cognition state。
- 若某条内容经复核后成为稳定事实，应晋升到 colleagues、workflow 或正式协作规则。
- employee id 固定为 `chief-marketing-officer`；该 id 只用于路径和 manifest，不代表 live 已启用。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-marketing-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- social 层用于承载当前 ChiefMarketingOfficer 员工实例的轻社交连续性、非正式互动偏好和闲聊层面的待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 如果某条社交偏好变成稳定协作要求，应经复核后晋升。
