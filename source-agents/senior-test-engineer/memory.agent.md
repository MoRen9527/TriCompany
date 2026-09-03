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
- 宿主 binding 事实由 binding profile 承载，不入本件
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则

- 测试套件与门禁读数写 runtime 私域与 docs/test，不入本件。
- 记忆层承载门禁矩阵与用例策略版本。
- 已稳定质量结论晋升 docs/test 验收报告。

## 层契约

- memory 层用于承载当前 STE 员工实例的测试上下文、阶段性判断、任务记忆和待复核测试结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 test reports、workflow 或 operating records。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
