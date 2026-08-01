# TriCompany CEOChiefOfStaff 配套记忆

本文件是 TriCompany 源侧认知层契约，只定义 CEOChiefOfStaff memory 层的用途、写入边界和运行资产落点；不记录具体阶段记忆、任务记录或运行同步摘录。

## 当前原则

- 源码侧只保留通用记忆管理规则、边界说明和迁移约束。
- 具体员工阶段记忆、任务上下文、命名记录和运行同步摘录写入 support employee workspace 或 runtime cognition state。
- 已稳定且需要成为项目事实的内容，按文档纪律回写 `docs/`、`docs/registry/` 或 operating records，不反向堆回本文件。
- `soul` 属于身份气质层，不与普通记忆混写。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/ceo-chief-of-staff.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 共享 / 审计运行态：`TRICOMPANY_COGNITION_HOME` 或 `.tricompany-cognition/org/shared.md`、`.tricompany-cognition/org/audit.md`

## 层契约

- memory 层用于承载员工实例的阶段性记忆、任务上下文、运行同步摘录和待复核判断。
- 这些内容默认属于 employee 私域或 current-host support payload，不属于 TriCompany 源码真源。
- 当记忆内容沉淀为稳定事实时，应升级到对应产品、技术、workflow、registry 或 operating record 文档。