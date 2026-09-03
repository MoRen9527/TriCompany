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
- 宿主绑定说明：`TriCompany/.github/binding-profiles/full-stack-developer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则
## 当前原则

- 源码侧只保留 FullStackDeveloper 记忆层的通用规则和边界，不写具体编码任务流水、实现记录或技术债务跟踪记录。
- 当前 FullStackDeveloper 员工实例使用 `full-stack-developer` employeeId。阶段性记忆写入 support employee workspace 或 runtime cognition state。
- FullStackDeveloper 当前是源侧新增岗位和 support object payload；上岗状态由 CTO 管理，向 CTO 小狄报告。
- 稳定实现结论进入对应模块的 code-state.md 或 engineering docs；实现结论不替代 source docs、registry、设计文档或中央策略裁决。

## 层契约
## 层契约

- memory 层用于承载当前 FullStackDeveloper 员工实例的实现上下文、阶段性判断、任务记忆和待复核技术结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 code-state.md、engineering docs 或 operating records。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
