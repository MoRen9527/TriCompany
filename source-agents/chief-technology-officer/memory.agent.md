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
- Employee workspace：`TriCompany-copilot-host-assets/knowledge/employees/chief-technology-officer/`
