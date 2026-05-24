# RAndDTrainer 配套记忆

本文件是 TriCompany 源侧认知层契约，只定义 RAndDTrainer memory 层的用途、写入边界和运行资产落点；不记录具体阶段记忆、任务记录或运行同步摘录。

## 当前原则

- 源码侧只保留 RAndDTrainer 记忆层的通用规则和边界，不写具体任务流水、命名记录或教程更新记录。
- 当前 RAndDTrainer 员工实例使用 `rd-trainer` employeeId；`project-trainer` 仅作为历史兼容 alias。阶段性记忆写入 support employee workspace 或 runtime cognition state。
- RAndDTrainer 当前仍是源侧新增岗位和 support object payload，不代表已经发布为 live agent。
- 稳定培训内容进入 `docs/training/`；培训内容不替代 source docs、registry、设计文档或中央策略裁决。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/rd-trainer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- memory 层用于承载当前 RAndDTrainer 员工实例的技术研发培训上下文、阶段性判断、任务记忆和待复核结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 training docs、workflow 或 operating records。
