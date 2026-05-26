# TriCompany

TriCompany 是三元宇宙体系里的赛博公司研发仓，同时也是当前阶段用于承载赛博公司 Hermes 融合设计与 Copilot 试运行宿主资产的仓库。

它单独维护 git、单独提交。当前职责不是承担中央战略，也不是宣称已经成为正式运行宿主，而是先把“赛博公司怎么设计、怎么融合 Hermes、怎么把当前阶段 Copilot 宿主资产收拢到 .github”沉淀成可复用资产。

## 当前定位

- 研发赛博公司的产品文档、技术设计、registry、workflow、execution 和 training 六层基线
- 孵化融合 Hermes 的总助 agent 与相关编排
- 承载当前阶段放在 .github 下的 Copilot 试运行宿主资产
- 承接当前 Copilot-host live 阶段已经上岗的 CPO / CTO，并继续为更高成熟度宿主验证做准备

## 当前状态

- 当前为 V0.1 初版基线仓
- 已建立首版产品、技术、registry、workflow、执行层和 training 文档骨架
- 已建立首版 TriCompany 总助 agent 套件与会议 prompt
- 当前已转向“先在 TriCompany 融合 Hermes，再完成 .github 下 Copilot 宿主迁移”的路线
- 已把 Hermes 核心 memory 编排代码冻结到 vendor/reference，并开始搭建 runtime/cognition 原型骨架
- 当前阶段的宿主资产属于试运行承载，不等于正式宿主切换
- CPO / CTO 已在当前 Copilot-host live 入口上岗，并已补齐 TriCompany 源侧五件套与 role / employee support object payload；这不等于 TriMC 正式宿主切换

## 目录约定

- docs/product/: 产品真源
- docs/engineering/: 技术真源
- docs/registry/: 模块级产品 / 代码状态
- docs/workflow/: 赛博公司研发编排、Hermes 融合与会议机制
- docs/execution/: 执行层阶段文档
- docs/training/: 赛博公司岗位、模块、代码和流程培训材料
- vendor/reference/: Hermes 冻结参考副本
- runtime/cognition/: 元认知运行时原型
- .github/source-agents/: 赛博公司源侧 agent 定义、员工五件套与 registry 发布源；TriCompany 不再使用 `.github/agents` 作为 agent discovery 面
- .github/binding-profiles/: 员工 source/support/live 绑定状态
- .github/instructions/: 总助套件维护规则
- .github/manifests/: 回迁 TriMetaverse 的宿主资产清单
- .github/prompts/: 会议开始 / 结束等专用入口

## 与 TriMetaverse 的关系

- TriMetaverse 继续承担中央战略、模块边界和正式宿主地位判断
- TriCompany 当前负责赛博公司研发、Hermes 融合和 Copilot 试运行宿主资产
- 形成稳定结论后，再同步回 TriMetaverse 的 Product Registry、Code Registry 和相关制度文档

## 当前下一步

1. 在 TriCompany 内继续把 Hermes 融进总助分层与编排
2. 把当前阶段 Copilot 宿主资产统一收拢并稳定在 TriCompany/.github
3. 让 CPO 与 CTO 接手产品 / 技术真源的持续优化，共同优化 TriCompany 与整个 TriMetaverse 项目
