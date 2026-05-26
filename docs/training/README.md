# TriCompany Training

版本：V0.1
日期：2026-04-29
状态：项目培训目录初版

## 定位

本目录当前用于承载 RAndDTrainer 输出的技术研发培训内容。

培训内容的目标是把 TriMetaverse、TriCompany 和相关模块讲到目标受众能够理解、学习和复述，同时保留到真源文档和源码位置的回链。

RAndDTrainer 是技术研发培训师，当前使用 `rd-trainer` 作为 canonical 文件名、employeeId 和 support object id。本目录当前优先承载研发 onboarding、技术 enablement、模块导读、代码导读和技术学习路径。

销售、运维、运营、人力行政、市场、产品等培训方向与技术研发培训差异很大，未来应分别启用对应专项培训师，不把这些职责混入当前 RAndDTrainer。

培训内容不是项目真源本身；遇到冲突时，以对应模块的 AGENTS.md、README.md、docs/product、docs/engineering、docs/workflow、docs/registry 和源码为准。

## 当前培训入口

- [Project Onboarding For Beginners](project-onboarding-for-beginners.md)
- [Virtual Company Module Employee Onboarding And Enablement Flow](chief-human-resources-officer-enablement-training.md)
- [IPD Usage Guide](ipd-usage-guide.md)

## 维护规则

- 新模块、新设计、新实现和新治理规则出现后，先由 CEOChiefOfStaff 同步给 RAndDTrainer。
- RAndDTrainer 负责把同步内容改写成渐进式技术教程、模块导读、代码导读和术语解释。
- RAndDTrainer 组织教程时应优先按项目大图、模块图谱、全局流程、模块内部流程、代码结构和接手路径讲解，不按操作者的临时问题生硬拆条。
- 当前 CPO、CTO 已可分别同步产品功能、技术架构和工程流程培训输入；其他职能培训师待未来独立启用。
- 培训内容必须明确区分已实现、草案中、待验证、待初始化。
- 培训内容不得替代 registry、设计文档、代码真源或中央策略裁决。

## 待补培训主题

- TriMetaverse 中央真源和模块边界
- TriCompany 虚拟公司研发仓
- CEOChiefOfStaff 与 RAndDTrainer 的协作方式
- role / employee knowledge workspace
- 产品和研发新员工全局 onboarding / enablement 技术培训
- 虚拟公司模块的新员工入职与启用流程
- 当前 Copilot-host 支撑包和 live 宿主入口
- ChiefHumanResourcesOfficer 作为新员工启用案例
- TriMC、TriLC、Tripilot、Tristaciss、Triavatar 等模块导读
- runtime/cognition 代码导读
