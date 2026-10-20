# Memory Layer Contract（ProductManager）

## 认知层契约

- **产品面任务记忆**：在办走查面/PRD 细化面的题面、进度与在途版本。
- **术语表记忆**：产品 UI 术语表现行版与在途定名件（三筛状态）。
- **走查记录记忆**：放行/打回件索引与验证锚位置。
- **带教上下文记忆**：CPO 方向卷与优先级裁决的现行版指针（裁决正文以 CPO 席输出为准，本层只记指针与状态）。

## 写入边界

- 不写入需求优先级裁决正文（CPO 域事实）——只记指针与生效状态。
- 不写入绩效数据与人事敏感信息。
- 走查判定正文落树卷，memory 层是索引与状态追踪。

## 运行资产落点

- 走查记录：`docs/workflow/operating-records/<current-week>/trees/`（走查卷落树位）
- 术语表：产品术语表现行版落点（候 CPO 指定权威位后在此登记）
- 运行腿：`TRICOMPANY_COGNITION_HOME`（机器写入，复活时初始化）
- 学习腿（知识工作区）：`TriCompany-host-assets/knowledge/employees/product-manager/`（inbox/wiki/workbench/audit 四区）
- 员工实例资产：runtime cognition 私域下 `product-manager/` 员工实例目录
- 宿主 binding 事实由 binding profile 承载，不入本件

## 当前原则

- 走查在途现势是运行数据——写走查卷与 runtime cognition 私域，不入本件。
- 记忆层承载走查上下文（在办题面/待复审清单/版本差标注）。
- 事实未定性只记「待确认」，不编造走查读数。

## 层契约

- memory 层承载当前 PM 员工实例的工作上下文、阶段判断与待复核结论。
- 稳定后可晋升到 workflow、operating records 或正式制度文档。
- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。
