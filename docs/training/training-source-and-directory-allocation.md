# Training 真源与目录分工

版本：V0.1
日期：2026-06-14
状态：按 CEOChiefOfStaff、CPO、CTO、RAndDTrainer 当前共识整理

## 1. 文档定位

本文用于明确当前 training 内容应分别落在哪一层，避免把模块 training 面、中央 training 聚合面、模块 training 包和宿主侧发布副本混成一层。

本文不替代模块产品真源、技术真源或中央策略裁决；它只定义 training 文档的承接位置与 owner 分工。

## 2. 当前共识

当前按六个落点理解：

1. 各模块自己的 `docs/training/`
2. `TriCompany/docs/training/`
3. `TriTraining/docs/training/`
4. `TriMetaverse/docs/training/`
5. `TriMetaverse/docs/training/<module-pack>/`
6. `<Module>-copilot-host-assets/docs/training/`（仅在宿主侧需要 published copy 时）

其中 `TriCompany/docs/training/` 和 `TriTraining/docs/training/` 仍然属于模块自己的 training 面，只是因为当前讨论重点单独列出；第 6 层只在宿主侧确实需要 published copy 时启用，不自动成为模块真源。

## 3. 各层职责

### 3.1 模块自己的 `docs/training/`

每个模块都可以有自己的 `docs/training/` 六件套 training 面。

它负责：

- 该模块自己的研发培训
- 模块导读
- 模块内部流程讲解
- 代码接手路径
- 面向该模块维护者的 onboarding

它不负责：

- 代替中央 training 聚合
- 代替培训学院模块课程包
- 代替产品 / registry / engineering 真源

### 3.2 `TriCompany/docs/training/`

这是 `TriCompany` 模块自己的 training 面，当前由 `RAndDTrainer` 负责产出。

它负责：

- `TriCompany` 模块研发培训
- `TriCompany` 模块的 IPD 使用教程
- `TriCompany` 模块里的 source -> publish -> live -> runtime 一类链路教程
- 当前 `RAndDTrainer` 负责的讲义骨架、渐进式课程组织和模块导读
- 面向 `TriCompany` 维护者和协作者的 onboarding

它不负责：

- 充当中央 training 根目录
- 代替其他模块自己的 training 真源
- 直接承担培训学院平台的软件功能、前后端承接或宿主发布副本

### 3.3 `TriMetaverse/docs/training/`

这是中央 training 聚合面。

它负责：

- 中央索引
- training 目录治理
- 已成型 training 包的聚合入口
- 跨模块课程包的中央承接

它不负责：

- 代替 `TriCompany/docs/training/` 写 trainer 原稿
- 代替模块自己的 `docs/training/` 做模块内部 training 真源

### 3.4 `TriMetaverse/docs/training/tricompany/`

这是 `TriCompany` 模块 training 包。

它负责讲：

- 为什么需要 TriCompany
- 员工 source -> publish -> live -> runtime -> governance 链路
- 赛博公司模块的研发与治理训练内容

### 3.5 `TriTraining/docs/training/`

这是 `TriTraining` 模块自己的 training 面。

它负责讲：

- `TriTraining` 模块自己的培训内容
- lesson / lab contract
- 课程图谱与课程体系
- 培训学院模块内部流程、实现边界和与 `TriAvatar` / `TriStaciss` 的协作方式

当前如果仍出现“Phase A / Web 优先切片 / 分阶段落地”这类表述，只描述培训学院当前的落地节奏，不代表 `TriTraining` 只是临时目录或未来要改名的候选模块。

`TriTraining` 应作为与 `TriCompany`、`TriAvatar`、`TriStaciss` 同级的软件模块承接培训学院主实现；其 training 真源应进入 `TriTraining/docs/training/`。培训学院完成落地后，主要实现应归 `TriTraining` 主承载；`TriAvatar` 与 `TriStaciss` 分别配合前端入口、后端 / API / 沙箱等协作面，以降低模块耦合，而不是反向替代 `TriTraining` 成为主实现归属。

`TriTraining` 是否在当前阶段直接成为培训学院 training 真源产生面，以及其产品 / 技术边界如何收口，应由 `CPO` 和 `CTO` 联合决定。宿主侧是否需要生成 `TriTraining-copilot-host-assets/docs/training/` 这类 published copy，也应由 `CPO` 和 `CTO` 评估后决定；如决定需要，再按真源发布链发布，而不是让 `TriCompany` 或 `TriMetaverse/docs/training/` 兼任宿主支撑包。

### 3.6 `TriMetaverse/docs/training/tritraining/`

这是中央 training 聚合面下的 `TriTraining` 模块 training 包。

它与同级的 `TriMetaverse/docs/training/tricompany/` 作用相同：

- 作为中央索引下的模块 training 包入口
- 承接已经成型、可集中阅读的模块 training 内容
- 帮助中央 training 面按模块分发导读入口

它不负责：

- 代替 `TriTraining/docs/training/` 成为模块 training 真源
- 代替宿主侧发布副本
- 获得比 `tricompany/` 更多的额外平台职责

`TriMetaverse/docs/training/tritraining/` 是否继续保留详细正文，还是裁成只保留模块入口与索引，也应由 `CPO` 和 `CTO` 评估后决定。

### 3.7 `<Module>-copilot-host-assets/docs/training/`

这是宿主侧按真源发布链生成的 training published copy。

它负责：

- 承接宿主运行面确实需要的 training 发布副本
- 保留与模块 training 真源对应的 published copy
- 服务当前宿主入口、runbook 或 support object 消费场景

它不负责：

- 反向代替模块自己的 `docs/training/` 成为真源
- 代替中央 `TriMetaverse/docs/training/` 聚合面
- 在没有宿主需求时强行生成一套重复目录

## 4. Owner 分工

- CPO：定义培训学院模块产品边界、课程承接边界和 training 与产品真源的关系。
- CTO：定义 training 与技术架构、模块承载和工程实现之间的边界。
- RAndDTrainer：把已确认真源转译成课程、讲义、导读和学习路径。
- CEOChiefOfStaff：负责收口、分诊、协调与催办，不长期代写 training 文档。

## 5. 当前执行规则

1. 新 training 内容先判断属于哪个模块。
2. 属于模块内部研发培训，先落该模块自己的 `docs/training/`。
3. 属于 `TriCompany` 模块 training 内容，先落 `TriCompany/docs/training/`；当前该模块的 Trainer 只有 `RAndDTrainer`。
4. 属于 `TriTraining` 模块 training 内容，先落 `TriTraining/docs/training/`；其是否作为当前 training 真源产生面，由 `CPO` / `CTO` 决定。
5. 宿主侧是否需要 published copy，由 `CPO` / `CTO` 评估后决定；如决定需要，再按真源发布链进入对应 host assets，例如 `TriTraining-copilot-host-assets`。
6. 需要中央聚合展示时，再进入 `TriMetaverse/docs/training/`。
7. 进入中央聚合后，`TriMetaverse/docs/training/tricompany/` 与 `TriMetaverse/docs/training/tritraining/` 只承担同级模块 training 包职责，不额外承担真源或宿主功能；其中 `tritraining/` 是否继续保留详细正文，还是只保留模块入口与索引，由 `CPO` / `CTO` 评估后决定。

## 6. 不这样做会出现什么问题

如果不分层，至少会出现三类混乱：

1. 把 trainer 原稿误写成中央课程真源。
2. 把模块 training 包误写成培训学院产品真源。
3. 把中央 training 聚合面误写成模块 source truth。
4. 把宿主侧 published copy 和模块 training 真源混成同一个目录。

当前目录分工的目标，就是避免这三类混写。
