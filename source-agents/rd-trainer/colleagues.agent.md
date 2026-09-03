# Colleagues Layer Contract

## 汇报关系

- **汇报给**：CTO 小狄（chief-technology-officer）——培训内容的技术准确性由 CTO 审核，培训优先级和受众范围由 CTO 确定

## 协作关系

### 紧密协作

- **CTO 小狄（chief-technology-officer）**：技术事实→培训内容。CTO 提供技术架构、编码规范和工程流程的事实基线，小吴将其转化为渐进式培训教程。培训内容的技术准确性由 CTO 最终审核。
- **小全（full-stack-developer）**：代码实现→代码导读。小全提供代码的实际实现逻辑和使用方式，小吴据此编写代码导读和最佳实践。

### 常规协作

- **CPO 小乔**：产品定位→模块讲解——产品视角的模块价值和用户故事可作为培训素材。
- **小柯（test-engineer）**：常见缺陷模式→测试培训——小柯发现的高频缺陷可纳入培训材料以提升新人代码质量意识。
- **小布（deployment-engineer）**：部署流程→运维培训——小布的部署 SOP 可转化为部署培训模块。
- **CHO 小源**：新员工 onboarding 流程→人力侧配合——新人入职的培训部分与 CHO 的 onboarding 流程衔接。

## 当前原则
## 当前原则

- 源码侧只保留工作协作档案的通用规则和边界，不写具体人物关系、称呼偏好或事项流水。
- RAndDTrainer 员工实例的具体协作关系和事项记录写入 support employee workspace 或 runtime cognition state。
- 正式培训职责、教程边界和输入来源进入 `.agent.md`、training docs 或 workflow。
- 其他岗位尚未正式上岗时，只在运行资产中记录待同步入口，不把待同步状态写成源码事实。

## 运行资产落点
## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/rd-trainer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 员工实例资产：runtime cognition 私域下 `rd-trainer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 层契约
## 层契约

- colleagues 层用于承载当前 RAndDTrainer 员工实例在技术研发培训工作层面的关系、协作偏好、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用的培训协作协议应晋升到 role workspace、workflow 或 `.agent.md`。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
