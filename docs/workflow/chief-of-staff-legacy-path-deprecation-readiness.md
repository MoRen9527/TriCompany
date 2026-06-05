# CEOChiefOfStaff Legacy Knowledge Path Deprecation Readiness

版本：V0.1
日期：2026-04-29
状态：post-deprecation closeout 已完成；旧目录已退役并删除

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/chief-of-staff-legacy-path-deprecation-readiness.md
- publishedFrom: 当前文件（audit record）
- syncMode: audit-record
- publishTier: audit-record
- lastSyncedAt: 2026-06-04

## 1. 文档定位

本文记录 `TriCompany-copilot-host-assets/knowledge/chief-of-staff/**` 从 legacy compatibility path 进入 deprecation、完成 closeout 并最终退役删除的全过程。

第一阶段已完成依赖识别、阻塞项登记和迁移准备。第二阶段已将活依赖切到员工对象路径，并把旧对象集标记为 deprecated。当前 closeout 已完成：legacy inbox 历史文件已并入 `knowledge/employees/ceo-chief-of-staff/inbox/`，旧目录已从 support payload、manifest 与 binding profile 中退役删除。

## 2. 当前结论

当前结论为 `APPROVE` closeout、`REMOVE` legacy directory。

原因是 source runtime、support runtime published-copy、workbench fallback 与中央治理锚点已切到 `knowledge/employees/ceo-chief-of-staff/**`，readiness validation 的 `--require-ready` 模式已通过，且 closeout 时已把唯一遗留的 inbox 历史文件迁入 employee workspace。manifest 与 binding profile 已不再登记 `knowledge/chief-of-staff/**`。

## 3. 可执行验证

在 `TriCompany/` 根目录执行过：

```powershell
python -m runtime.cognition.employee_host_publish --source-root . --support-root ..\TriMetaverse\TriCompany-copilot-host-assets --employee ceo-chief-of-staff
python -m unittest runtime.cognition.role_employee_workspace_validation
python -m unittest runtime.cognition.rd_trainer_host_object_generation_validation
```

当前最终结果是：旧路径已退役删除，不再需要单独的 readiness / shadow gate 验证脚本。

## 4. 已完成的收口项

- source runtime、support runtime published-copy、workbench fallback 与中央治理锚点都已切到 `knowledge/employees/ceo-chief-of-staff/**`
- 旧 legacy inbox 的历史文件已迁入 `knowledge/employees/ceo-chief-of-staff/inbox/`
- source / support manifest 与 employee binding profile 已移除 `knowledge/chief-of-staff/**`
- 当前总助 support payload 只剩 role / employee workspace 两条对象路径

## 5. 当前有效对象路径

目标路径先以统一员工对象体系为准：

- `knowledge/employees/ceo-chief-of-staff/wiki/**`
- `knowledge/employees/ceo-chief-of-staff/audit/**`
- `knowledge/employees/ceo-chief-of-staff/workbench/**`

当前总助 support payload 只保留统一员工对象路径；不得再把 `knowledge/chief-of-staff/**` 恢复成活目录、fallback 或治理锚点。

## 6. closeout 判定

旧路径在满足以下条件后已被删除：

1. readiness validation 在默认扫描下无 blocking dependencies。
2. source runtime 和 support runtime published-copy 的默认 target 都已切到新路径或显式可配置 target。
3. workbench 页面读取和链接已切到新 employee workspace。
4. central anchor index 已不再把旧路径作为当前治理锚点。
5. live `.github` 入口无旧路径硬引用。
6. `host-object-manifest.json`、source generation manifest 与 employee binding profile 都不再登记旧路径。
7. 旧目录中唯一未并入 employee workspace 的 inbox 历史文件已完成迁移。

## 7. 收口结果

本迁移按以下三段归档：

1. 真源阶段：确认员工对象路径、生成规则和 deprecation 门禁。
2. deprecation 阶段：runtime fallback、workbench、governance anchor 使用 employee workspace；旧路径降为兼容对象。
3. closeout 阶段：迁移剩余 inbox 历史文件，移除 manifest / binding profile 中的旧路径，并删除 support 侧 legacy 目录。

## 8. 当前不再做

- 不恢复 `knowledge/chief-of-staff/**`。
- 不再为旧路径保留单独 manifest、binding profile 或 shadow gate。
- 不把 `.tricompany-cognition/**` 当成这次 deprecation 的对象；它仍是运行态状态。
