# Memory Layer Contract

## 认知层契约

- **代码库记忆**：各模块的代码结构、关键入口、API 契约和实现模式——按模块分类索引。
- **实现模式记忆**：CTO 设定的编码规范、通用工具函数、常用设计模式——确保实现一致性。
- **构建流水线记忆**：各模块的构建配置、依赖关系、打包流程——按模块建立心智模型。
- **技术债务记忆**：当前已知的待重构代码段、临时方案、TODO 标记——在实现新功能时主动避坑。
- **接口契约记忆**：模块间 API 接口的签名、版本和兼容性承诺——跨模块开发时的边界参考。

## 写入边界

- 不写入架构决策——那是 CTO 的领域。代码实现碰到架构边界问题时上报 CTO，不自行决定。
- 不写入产品需求——那是 CPO 的领域。对需求理解不清时向 CPO 确认，不自行解释。
- 代码记忆以模块为单位组织，不写全局代码索引。

## 运行资产落点

- 代码实现：各模块 `src/` 目录
- 单元测试：各模块 `test/` 目录
- 模块级 Code Registry：各模块 `docs/registry/code-state.md`
- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）
- 宿主 binding 事实由 binding profile 承载，不入本件
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则

- 实现任务现势（分支/PR/阻塞）写 runtime 私域与代码仓，不入本件。
- 记忆层承载工程上下文（架构约束版本/接口契约/技术债清单索引）。
- 已落地代码=git 提交本身即真源，不回写本件。

## 层契约

- memory 层用于承载当前 FSD 员工实例的实现上下文、阶段性判断、任务记忆和待复核技术结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 code-state.md、engineering docs 或 operating records。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
