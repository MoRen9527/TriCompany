# TestEngineer 配套记忆

本文件是 TriCompany 源侧认知层契约，只定义 TestEngineer memory 层的用途、写入边界和运行资产落点；不记录具体阶段记忆、任务记录或运行同步摘录。

## 当前原则

- 源码侧只保留 TestEngineer 记忆层的通用规则和边界，不写具体测试任务流水、用例记录或缺陷跟踪记录。
- 当前 TestEngineer 员工实例使用 `test-engineer` employeeId。阶段性记忆写入 support employee workspace 或 runtime cognition state。
- TestEngineer 当前是源侧新增岗位和 support object payload；上岗状态由 CTO acting 管理，暂不直接向 CEO 报告。
- 稳定测试结论进入 `docs/test/` 或对应的模块 test report；测试结论不替代 source docs、registry、设计文档或中央策略裁决。
- **测试用例设计按 ISO/IEC 25010:2011 软件质量模型分层**：八特性（functional-suitability 功能适合性 / performance-efficiency 性能效率 / compatibility 兼容性 / usability 易用性 / reliability 可靠性 / security 安全性 / maintainability 可维护性 / portability 可移植性）。每条用例必须标注 `quality`（八特性之一）和 `method`（设计方法：等价类划分/因果图决策表/正交试验法/场景法/错误推测法/冒烟测试/回归测试/接口测试/恢复测试/安装卸载测试/文档测试/探索性测试/兼容性测试/可用性走查/性能基准测试/安全审计/代码检查/环境矩阵测试）。废弃 basic/boundary/exception/security 分类（CEO 认定不专业）。
- **测试集落点**：TriMetaverse 模块测试集位于 `docs/execution/e2e-test-suite.json`，已按 ISO 25010 v2.0.0 重构（commit 8a4d3b39，123 条用例）。后续测试设计全部按 ISO 25010 + 设计方法标注执行。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/test-engineer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- memory 层用于承载当前 TestEngineer 员工实例的测试上下文、阶段性判断、任务记忆和待复核测试结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 test reports、workflow 或 operating records。
