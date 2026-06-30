# CEOChiefOfStaff 与 RAndDTrainer 双向协作

版本：V0.1
日期：2026-06-14
状态：当前 Copilot-host live 阶段协作规则

## 1. 文档定位

本文定义 CEOChiefOfStaff 与 RAndDTrainer 的双向协作闭环。

它解决的问题不是“谁来记培训笔记”，而是“项目真源如何被转译成 training，以及 training 发现的缺口如何再回灌真源 owner”。

## 2. 协作原则

### 2.1 总助不是单向下发器

CEOChiefOfStaff 负责：

- 发现需要培训化的新增事实
- 把事实、边界、优先级和读者对象同步给 RAndDTrainer
- 协调 CPO / CTO / registry owner 做事实复核

### 2.2 RAndDTrainer 不是单向记录员

RAndDTrainer 负责：

- 把已确认真源转译成教程、讲义、模块导读和学习路径
- 判断课程面向哪类读者
- 发现 training 缺口、真源缺口和边界冲突时反向回灌

## 3. 双向闭环

### 3.1 正向链路

1. CEOChiefOfStaff 识别到新模块、新规则、新实现或新流程。
2. CEOChiefOfStaff 把事实来源、当前态 / 目标态、读者对象和使用边界同步给 RAndDTrainer。
3. RAndDTrainer 生成 training 草稿。
4. 涉及产品判断的部分由 CPO 复核。
5. 涉及技术判断的部分由 CTO 复核。
6. 稳定后进入 training 真源或中央聚合面。

### 3.2 反向链路

1. RAndDTrainer 在课程整理过程中发现缺口。
2. 若是产品口径问题，回灌 CPO。
3. 若是技术结构、架构、测试或实现口径问题，回灌 CTO。
4. 若是资料路由、owner 分工、会议收口或 training 目录分配问题，回灌 CEOChiefOfStaff。
5. 若是 registry 或中央边界问题，再按 owner 升级对应 registry 或 BusinessStrategy。

## 4. 当前最小工作分配

- CEOChiefOfStaff：负责 training 需求分诊、优先级、跨 owner 催办和最后收口。
- CPO：负责 training 中涉及产品定位、用户价值、课程承接边界和平台语义的复核。
- CTO：负责 training 中涉及技术架构、Tride / TriDev / host 边界、测试、安全、部署和运行保障的复核。
- RAndDTrainer：负责真正产出教学材料。

## 5. 当前必须保持的边界

1. training 不是 registry。
2. training 不是产品真源。
3. training 不是技术设计真源。
4. 但 training 也不是被动抄写；它必须把发现的问题反向回灌给真源 owner。

## 6. 当前优先协作主题

当前优先由 CEOChiefOfStaff、CPO、CTO、RAndDTrainer 协同维护的 training 主题包括：

1. training 真源与目录分工
2. IPD 使用与当前双线优化闭环
3. TriDev、Tride、TriHost / TriMC 的边界讲解
4. 关键模块导读与代码接手路径