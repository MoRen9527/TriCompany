# TestEngineer 配套记忆

本文件是 TriCompany 源侧认知层契约，只定义 TestEngineer memory 层的用途、写入边界和运行资产落点；不记录具体阶段记忆、任务记录或运行同步摘录。

## 当前原则

- 源码侧只保留 TestEngineer 记忆层的通用规则和边界，不写具体测试任务流水、用例记录或缺陷跟踪记录。
- 当前 TestEngineer 员工实例使用 `test-engineer` employeeId。阶段性记忆写入 support employee workspace 或 runtime cognition state。
- TestEngineer 当前是源侧新增岗位和 support object payload；上岗状态由 CTO acting 管理，暂不直接向 CEO 报告。
- 稳定测试结论进入 `docs/test/` 或对应的模块 test report；测试结论不替代 source docs、registry、设计文档或中央策略裁决。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/test-engineer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- memory 层用于承载当前 TestEngineer 员工实例的测试上下文、阶段性判断、任务记忆和待复核测试结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 test reports、workflow 或 operating records。
