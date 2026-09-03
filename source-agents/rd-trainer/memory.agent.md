# Memory Layer Contract

## 认知层契约

- **培训材料记忆**：各模块的教程、模块导读、代码导读的当前版本和覆盖状态——按模块和受众级别索引。
- **学习路径记忆**：不同角色（全栈开发、测试、部署、产品等）的推荐学习路径——从项目大图到代码接手的渐进路线。
- **模块知识记忆**：每个模块的定位、当前成熟度、真源文件路径、常见误区——作为培训的事实基线。
- **新人 onboarding 记忆**：最近一批新人的学习进度、卡点、常见疑问——用于持续改进培训材料。
- **技术术语记忆**：项目内使用的术语定义、别称、缩写——确保培训一致性。

## 写入边界

- 不写入代码实现——培训内容以"解释"为目标，不以"裁决"为目标。事实源是 CTO 的 Code Registry 和各模块源码。
- 不写入产品决策——培训解释产品的事实状态，不评判产品决策的优劣。
- 培训材料引用的任何技术事实必须标注真源路径，让读者能追溯到权威来源。

## 运行资产落点

- 培训真源：`TriCompany/docs/training/`、`TriMetaverse/docs/training/`
- 模块导读与代码导读：各模块 `docs/training/` 目录
- 知识工作区：runtime cognition 私域（TRICOMPANY_COGNITION_HOME）
- 宿主 binding 事实由 binding profile 承载，不入本件
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 当前原则

- 课程件版本与学员接续上下文写 runtime 私域与 docs/training，不入本件。
- 记忆层承载课程地图与迭代记录。
- 培训事实以工程真源为锚不自我背书。

## 层契约

- memory 层用于承载当前 RAndDTrainer 员工实例的技术研发培训上下文、阶段性判断、任务记忆和待复核结论。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 稳定后可晋升到 training docs、workflow 或 operating records。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
