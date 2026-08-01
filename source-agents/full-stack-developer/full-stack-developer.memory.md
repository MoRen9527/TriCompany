# FullStackDeveloper 配套记忆

本文件是 TriCompany 源侧认知层契约，只定义 FullStackDeveloper memory 层的用途、写入边界和运行资产落点；不记录具体阶段记忆、任务记录或运行同步摘录。

## 当前原则

- 源码侧只保留 FullStackDeveloper 记忆层的通用规则和边界，不写具体编码任务流水、实现记录或技术债务跟踪记录。
- 当前 FullStackDeveloper 员工实例使用 `full-stack-developer` employeeId。阶段性记忆写入 support employee workspace 或 runtime cognition state。
- FullStackDeveloper 当前是源侧新增岗位和 support object payload；上岗状态由 CTO 管理，向 CTO 小狄报告。
- 稳定实现结论进入对应模块的 code-state.md 或 engineering docs；实现结论不替代 source docs、registry、设计文档或中央策略裁决。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/full-stack-developer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- memory 层用于承载当前 FullStackDeveloper 员工实例的实现上下文、阶段性判断、任务记忆和待复核技术结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 code-state.md、engineering docs 或 operating records。
