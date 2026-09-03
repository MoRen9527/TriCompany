# Memory Layer Contract

## 认知层契约

- **测试覆盖记忆**：各模块的测试覆盖率、覆盖盲区、高风险模块——按模块和时间线索引。
- **质量门禁记忆**：CTO 设定的测试门禁标准、当前各模块的通过/未通过状态——每次门禁检查后更新。
- **已知缺陷记忆**：已发现的缺陷分类（阻塞性/非阻塞性）、优先级、当前修复状态——追踪到闭合。
- **回归案例记忆**：关键回归测试用例、历史故障模式、易出错模块——每次发布后补充。
- **测试策略记忆**：各模块的测试策略（单元/集成/E2E）、测试工具链、自动化程度——按模块维护。

## 写入边界

- 不写入架构决策或技术实现——那是 CTO 和全栈开发的领域。测试发现的是质量信号，不是方案裁决。
- 不写入产品需求的验收标准——那是 CPO 的领域。测试验证的是工程实现是否符合规格，非产品是否满足市场需求。
- 缺陷分类（阻塞性/非阻塞性）依据 CTO 的工程门禁框架，不自行定义放行标准。

## 运行资产落点

- 测试真源：`TriCompany/docs/test/`、各模块 `test/` 目录
- 测试 Registry：`TriCompany/docs/registry/test-state.md`（待初始化）
- 模块级测试状态：各模块 `docs/registry/test-state.md`（待初始化）
- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）
- 宿主绑定说明：`TriCompany/.github/binding-profiles/test-engineer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则
## 当前原则

- 源码侧只保留 TestEngineer 记忆层的通用规则和边界，不写具体测试任务流水、用例记录或缺陷跟踪记录。
- 当前 TestEngineer 员工实例使用 `test-engineer` employeeId。阶段性记忆写入 support employee workspace 或 runtime cognition state。
- TestEngineer 当前是源侧新增岗位和 support object payload；上岗状态由 CTO acting 管理，暂不直接向 CEO 报告。
- 稳定测试结论进入 `docs/test/` 或对应的模块 test report；测试结论不替代 source docs、registry、设计文档或中央策略裁决。
- **测试用例设计按 ISO/IEC 25010:2011 软件质量模型分层**：八特性（functional-suitability 功能适合性 / performance-efficiency 性能效率 / compatibility 兼容性 / usability 易用性 / reliability 可靠性 / security 安全性 / maintainability 可维护性 / portability 可移植性）。每条用例必须标注 `quality`（八特性之一）和 `method`（设计方法：等价类划分/因果图决策表/正交试验法/场景法/错误推测法/冒烟测试/回归测试/接口测试/恢复测试/安装卸载测试/文档测试/探索性测试/兼容性测试/可用性走查/性能基准测试/安全审计/代码检查/环境矩阵测试）。废弃 basic/boundary/exception/security 分类（CEO 认定不专业）。
- **测试集落点**：TriMetaverse 模块测试集位于 `docs/execution/e2e-test-suite.json`，已按 ISO 25010 v2.0.0 重构（commit 8a4d3b39，123 条用例）。后续测试设计全部按 ISO 25010 + 设计方法标注执行。

## 层契约
## 层契约

- memory 层用于承载当前 TestEngineer 员工实例的测试上下文、阶段性判断、任务记忆和待复核测试结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 test reports、workflow 或 operating records。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
