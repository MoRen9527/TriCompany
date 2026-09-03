# Memory Layer Contract

## 认知层契约

- **技术架构记忆**：项目整体架构、模块间依赖关系、技术债务分布——按模块和时间线索引。
- **交付路径记忆**：当前 MVP 的技术实现顺序、里程碑、阻塞项——与 CPO 的产品路线图对齐。
- **代码质量记忆**：各模块的代码成熟度、已知缺陷、性能瓶颈——由 Code Registry 承载，memory 层做状态索引。
- **工程门禁记忆**：构建流水线状态、测试覆盖率阈值、发布 readiness 检查点——按模块追踪。
- **技术选型记忆**：技术栈的当前选择、替代方案评估、升级路径——标注决策依据和时间。

## 写入边界

- 不写入产品需求排序——那是 CPO 的领域。
- 不写入具体实现代码——代码本身在模块 `src/` 目录中，CTO memory 层是架构级记忆。
- 技术决策记录标注依据（Code Registry、实验数据或架构评审结论），不标注个人偏好。

## 运行资产落点

- 技术真源：`TriCompany/docs/engineering/DESIGN.md`、`STATE.md`、`ROADMAP.md`
- 代码 Registry：`TriCompany/docs/registry/code-state.md`
- 模块级 Code Registry：各模块 `docs/registry/code-state.md`
- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）
- 宿主 binding 事实由 binding profile 承载，不入本件
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则

- 构建态、测试读数、发布窗口倒计时是运行数据——写 runtime cognition 私域与 engineering 工作面，不入本件。
- 记忆层承载工程判断上下文（门禁在途变更/验证矩阵版本/回滚预案索引）。
- 已定稿技术结论晋升 docs/engineering。
- 验证不足只记「候验证+缺口」，不记 production-ready。

## 层契约

- memory 层用于承载当前 CTO 员工实例的技术上下文、阶段性判断、任务记忆和待复核结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 engineering docs、Code Registry、workflow 或 operating records。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
