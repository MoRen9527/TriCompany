# TriCompany Training

版本：V0.1
日期：2026-04-29
状态：项目培训目录初版

## 定位

本目录当前用于承载 `TriCompany` 模块自己的 training 内容，当前由 `RAndDTrainer` 负责产出。

培训内容的目标是把 `TriCompany` 模块、其与当前宿主 / 发布链 / 治理链的关系讲到目标受众能够理解、学习和复述，同时保留到真源文档和源码位置的回链。

`RAndDTrainer` 是当前唯一已启用的 Trainer，使用 `rd-trainer` 作为 canonical 文件名、employeeId 和 support object id。本目录当前优先承载 `TriCompany` 模块的研发 onboarding、技术 enablement、模块导读、代码导读和技术学习路径。

销售、运维、运营、人力行政、市场、产品等培训方向与技术研发培训差异很大，未来应分别启用对应专项培训师，不把这些职责混入当前 `RAndDTrainer`。培训学院产品能力与课程运行能力则应由与 `TriCompany` 同级的 `TriTraining` 模块承接，而不是继续堆在 `TriCompany/docs/training/`。

培训内容不是项目真源本身；遇到冲突时，以对应模块的 `AGENTS.md`、`README.md`、`docs/product`、`docs/engineering`、`docs/workflow`、`docs/registry` 和源码为准。`TriTraining` 模块启用后，其 training 真源应进入 `TriTraining/docs/training/`；宿主侧如需发布副本，应按真源发布链进入 `TriTraining-copilot-host-assets`，而不是反向回写 `TriCompany/docs/training/`。

## 当前培训入口

- [Project Onboarding For Beginners](project-onboarding-for-beginners.md)
- [Virtual Company Module Employee Onboarding And Enablement Flow](chief-human-resources-officer-enablement-training.md)
- [IPD Usage Guide](ipd-usage-guide.md)
- [IPD CLI 与代码工作流程教程（小白版）](ipd-cli-and-code-workflow-beginner-course.md)
- [从 CEO Demand 到 Discovery 的产品与代码教程（小白版）](ceo-demand-to-discovery-beginner-course.md)
- [IPD 双线优化与 Merge 流程教程](ipd-dual-track-optimization-and-merge-flow.md)
- [项目真源文档同步 FADE 教程](project-source-document-sync-fade-tutorial.md)
- [FADE 小白教程（零基础入门）](fade-beginner-course.md)
- [FADE 产品版教程（使用方操作指南）](fade-product-guide.md)
- [FADE 代码深潜（研发实现地图）](fade-code-deep-dive.md)
- [FADE-002 发布域四版教程（小白/产品/代码/深度研究，2026-09-05）](fade-002/README.md)
- [FADE-001 周平面维护四版教程（小白/产品/代码/深度研究，2026-09-05）](fade-001/README.md)
- [Training 真源与目录分工](training-source-and-directory-allocation.md)
- [CEOChiefOfStaff 与 RAndDTrainer 双向协作](ceo-chief-of-staff-and-rd-trainer-collaboration.md)
- [Engineering Course Teaching Pattern](engineering-course-teaching-pattern.md)
- [Employee Source Kit CLI Course](LearningToPractice/CLI/employee-source-kit-cli-course.md)
- [Employee Source Kit CLI Lab Manual](LearningToPractice/CLI/employee-source-kit-cli-lab-manual.md)

## 维护规则

- 新模块、新设计、新实现和新治理规则出现后，先由 CEOChiefOfStaff 同步给 RAndDTrainer。
- RAndDTrainer 负责把同步内容改写成渐进式技术教程、模块导读、代码导读和术语解释。
- RAndDTrainer 在课程整理过程中发现真源缺口、培训断层、边界冲突或 owner 待确认项时，必须反向回灌 CEOChiefOfStaff，并按内容类型拉 CPO / CTO / 对应 registry 复核。
- RAndDTrainer 组织教程时应优先按项目大图、模块图谱、全局流程、模块内部流程、代码结构和接手路径讲解，不按操作者的临时问题生硬拆条。
- RAndDTrainer 讲研发技术课程时，默认复用“结果 -> 价值 -> 理论/协议 -> MVP 全流程 -> 原理拆解 -> 增量实现 -> 完整实现 -> 生产级考虑 -> 心智模型总结”的统一骨架。
- 当 `integrated-product-development-flow.md`、`platform-product-mainline-cutover.md`、`ipd-company-baseline-checklist.md` 或 `IPD-20260612-WORKFLOW-002` 改变 IPD case 分工、Gate A/B/C 目标、replay / 产品主线消费口径时，必须同轮检查 [IPD CLI 与代码工作流程教程（小白版）](ipd-cli-and-code-workflow-beginner-course.md) 与 [IPD Usage Guide](ipd-usage-guide.md)，避免 training 真源继续保留旧说法。
- 当前 CPO、CTO 已可分别同步产品功能、技术架构和工程流程培训输入；其他职能培训师待未来独立启用。
- 培训内容必须明确区分已实现、草案中、待验证、待初始化。
- 培训内容不得替代 registry、设计文档、代码真源或中央策略裁决。

## 待补培训主题

- TriCompany 赛博公司研发仓
- role / employee knowledge workspace
- 产品和研发新员工全局 onboarding / enablement 技术培训
- 赛博公司模块的新员工入职与启用流程
- ~~当前 Copilot-host 支撑包和 live 宿主入口~~（已补齐 2026-08-19：见 `../TriTraining/docs/training/employee-host-publish-chain-beginners-guide.md`，六环全链路白话课，含已实现/规划中区分）
- ChiefHumanResourcesOfficer 作为新员工启用案例
- TriMC、TriLC、Tripilot、Tristaciss、Triavatar 等模块导读
- runtime/cognition 代码导读
