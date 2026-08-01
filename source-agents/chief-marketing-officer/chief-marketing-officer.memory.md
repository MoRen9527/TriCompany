# ChiefMarketingOfficer 配套记忆

本文件是 TriCompany 源侧认知层契约，只定义 ChiefMarketingOfficer memory 层的用途、写入边界和运行资产落点；不记录具体任务流水、称呼事件或运行同步摘录。

## 当前原则

- 源码侧只保留 记忆 的通用规则和边界，不写运行消费数据。
- ChiefMarketingOfficer 员工实例的具体连续性写入宿主 employee workspace 或 runtime cognition state。
- 若某条内容经复核后成为稳定事实，应晋升到 对应 product、engineering、workflow、registry、training 或 operating record 真源。
- employee id 固定为 `chief-marketing-officer`；该 id 只用于路径和 manifest，不代表 live 已启用。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-marketing-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- memory 层用于承载当前 ChiefMarketingOfficer 员工实例的阶段性上下文、待复核判断和任务连续性。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到对应正式真源。
