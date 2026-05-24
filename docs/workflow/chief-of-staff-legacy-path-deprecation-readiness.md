# CEOChiefOfStaff Legacy Knowledge Path Deprecation Readiness

版本：V0.1
日期：2026-04-29
状态：第二阶段验证迁移已完成；允许 deprecation label；继续冻结 archive / delete

## 1. 文档定位

本文定义 `TriCompany-copilot-host-assets/knowledge/chief-of-staff/**` 从 legacy compatibility path 进入后续 deprecation 的第一阶段验证门禁。

第一阶段已完成依赖识别、阻塞项登记和迁移准备。第二阶段已将活依赖切到员工对象路径，并把旧对象集标记为 deprecated；仍不删除旧目录，也不把旧目录归档。

## 2. 当前结论

当前结论为 `APPROVE` deprecation label、`FREEZE` archive / delete。

原因是 source runtime、support runtime published-copy、workbench fallback 与中央治理锚点已切到 `knowledge/employees/ceo-chief-of-staff/**`，readiness validation 的 `--require-ready` 模式已通过。manifest 中的 legacy compatibility 状态已从 `preserved-legacy-path` 改为 `deprecated-legacy-path`。

## 3. 可执行验证

在 `TriCompany/` 根目录执行：

```powershell
python -m runtime.cognition.chief_of_staff_legacy_path_deprecation_readiness
python -m unittest runtime.cognition.chief_of_staff_legacy_path_deprecation_validation
python -m runtime.cognition.chief_of_staff_legacy_path_shadow_gate --require-ready
python -m unittest runtime.cognition.chief_of_staff_legacy_path_shadow_gate_validation
```

如果要把 readiness 作为迁移门禁，可执行：

```powershell
python -m runtime.cognition.chief_of_staff_legacy_path_deprecation_readiness --require-ready
```

当前预期结果是 `ready-for-deprecation-label`。这代表 active blocker 已清空，但旧目录仍需至少保留一个 post-deprecation validation 周期。

补充说明：本轮最初把 shadow test 压缩在 readiness 与旧目录并行保留里，缺少显式命名的 shadow gate。现已补 `chief_of_staff_legacy_path_shadow_gate.py`，把本轮迁移重新落回“真源 -> shadow test -> 正式接管 / deprecated label”的标准流程。

## 4. 当前阻塞项

当前第一阶段扫描重点关注以下阻塞面：

- source runtime：`TriCompany/runtime/cognition/**` 中的旧路径默认目标或读取逻辑
- support runtime published-copy：`TriCompany-copilot-host-assets/runtime/cognition/**` 中的旧路径默认目标或读取逻辑
- live entry：`TriMetaverse/.github/{agents,prompts,instructions,hooks}/**` 中是否硬编码旧路径
- governance anchor：`TriMetaverse/docs/workflow/tricompany-copilot-host-assets-anchor-index.json` 中是否仍锚定旧 workbench / audit 对象

已确认第一轮阻塞曾包括：

- dispatch fallback 仍默认写入 `knowledge/chief-of-staff/audit`
- workbench 仍展示并读取 `knowledge/chief-of-staff/wiki` 语义
- closeout / audit fallback 仍默认使用 `knowledge/chief-of-staff/audit`
- schedule staging validation 默认 delivery target 仍是旧 audit
- central anchor index 仍锚定旧 workbench、approval report 与 audit pattern

第二阶段已处理：

- source runtime 与 support runtime published-copy 的默认 delivery target 已切到 `knowledge/employees/ceo-chief-of-staff/audit`
- `chief_of_staff_wiki_paths.py` 已统一指向 `knowledge/employees/ceo-chief-of-staff/{wiki,workbench,audit}`
- 新 employee workspace 已补齐旧 wiki、workbench、audit 等价对象
- central anchor index 已切到 `knowledge/employees/ceo-chief-of-staff/**`
- readiness scanner 已把 generator / README / validation 中的兼容记录识别为 non-blocking reference

## 5. 迁移准备目标

目标路径先以统一员工对象体系为准：

- `knowledge/employees/ceo-chief-of-staff/wiki/**`
- `knowledge/employees/ceo-chief-of-staff/audit/**`
- `knowledge/employees/ceo-chief-of-staff/workbench/**`

迁移准备必须先保证新路径下存在等价对象、生成逻辑和治理锚点，再修改 runtime fallback。不能只改文案或 manifest。

## 6. 进入 deprecation 的门禁

旧路径只有满足以下条件后才能标记为 deprecated：

1. readiness validation 在默认扫描下无 blocking dependencies。
2. source runtime 和 support runtime published-copy 的默认 target 都已切到新路径或显式可配置 target。
3. workbench 页面读取和链接已切到新 employee workspace。
4. central anchor index 已不再把旧路径作为当前治理锚点。
5. live `.github` 入口无旧路径硬引用。
6. `host-object-manifest.json` 和 source generation manifest 同步把旧路径状态改为 `deprecated-legacy-path`，且旧目录只读保留至少一个验证周期。

## 7. 标准流程映射

本迁移按以下三段归档：

1. 真源阶段：先在 `TriCompany/runtime/cognition/`、`TriCompany/.github/manifests/` 与模块 workflow 文档中确认员工对象路径、生成规则和 deprecation 门禁。
2. shadow test 阶段：旧 `knowledge/chief-of-staff/**` 保留，新 `knowledge/employees/ceo-chief-of-staff/**` 并行补齐对象，运行 `chief_of_staff_legacy_path_shadow_gate --require-ready` 验证等价对象、workbench 当前路径、manifest 状态和中央锚点。
3. 正式接管 / deprecated label 阶段：runtime fallback、workbench、governance anchor 使用 employee workspace；旧路径只保留为 `deprecated-legacy-path` 兼容对象，不再作为当前活路径。

## 8. 当前不做

- 不删除 `knowledge/chief-of-staff/**`。
- 不把旧路径立即改成 archive。
- 不把旧路径从 host-object manifest 中移除。
- 不把 `.tricompany-cognition/**` 当成这次 deprecation 的对象；它仍是运行态状态。