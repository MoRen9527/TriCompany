# ChiefMarketingOfficer 工作协作档案

本文件是 TriCompany 源侧认知层契约，只定义 ChiefMarketingOfficer colleagues 层的用途、写入边界和运行资产落点；不记录具体人物关系、称呼偏好或事项流水。

## 当前原则

- 源码侧只保留 工作协作档案 的通用规则和边界，不写运行消费数据。
- ChiefMarketingOfficer 员工实例的具体连续性写入宿主 employee workspace 或 runtime cognition state。
- 若某条内容经复核后成为稳定事实，应晋升到 role workspace、workflow、agent 主档或对应 registry。
- employee id 固定为 `chief-marketing-officer`；该 id 只用于路径和 manifest，不代表 live 已启用。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-marketing-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- colleagues 层用于承载当前 ChiefMarketingOfficer 员工实例在工作层面的协作关系、事项上下文和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用协作协议应晋升到 role workspace、workflow 或 agent 主档。
