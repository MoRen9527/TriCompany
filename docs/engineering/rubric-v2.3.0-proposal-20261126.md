# rubric-v2.3.0 提案稿·A 族重定义（CTO 出稿·2026-11-26）

- sourceOfTruth: 本件（TriCompany/docs/engineering/rubric-v2.3.0-proposal-20261126.md·A 族重定义提案正身）
- syncMode: write-time
- 承接: CEO 2026-11-26 逐族过 A-H 时指 A 族实质偏差（BOD 转 20:04）·CTO+CPO 联合定·BOD 确认开写（20:07）
- **状态=提案**（rubric 修订须 CEO 批·**批前不生效**）

## §一 · 偏差认定（CEO 原意 vs 现行）

**CEO 原意**：迁移前把不可变量（md5 类）做快照；迁移后对照——保证「迁移过程中」对象未被篡改（**迁移动作完整性**）。

**现行 A 族（rubric-v2.2.0·CEO 2026-11-25 批·weight 6）**：
| 字段 | 现行原文 |
|---|---|
| family_name | 迁移前基线（首拍基线） |
| reading_point | jobs.json 值面：md5 基准+nextRunAtMs+qualify/trap/RCguard 在位 |
| verdict_rule | 首拍/预演同形=与基准 md5 对表全中（含基准注） |
| special_clause | vB 基准 4f990e911c3f 有效至 PATCH 落；十阶段形基准=PATCH 后探读新值落卷替换；vB md5 与十阶段 jobs.json=全等才认定；nextRunAtMs=1794757800000（11-15 23:50 硬时钟）…… |

**三处偏差（实读锚硬）**：
1. **对象错**：查 `jobs.json`（`/srv/fleet/TriRMC/data/cron/jobs.json`·cron 调度配置·**被 PATCH 的对象**）——**非「要迁的目标周文件夹」**。**迁移对象实为 operating-records 周平面**（`docs/workflow/operating-records/2026-W47/` → `2026-W48/`·trees 目录树+各卷·双周目录本机实存已验证）。
2. **基准错**：对「形态固定值」（vB `4f990e911c3f`·换形可更新）——**非「本次迁移前的快照」**。
3. **目的错**：现=**配置漂移检测**（配置有没有变）——**非迁移动作完整性**（迁移前后同对象对照）。**后果：迁移过程中对象被篡改不可发现**。

**三守卫实称**：
- **qualify** = E 族 `qualify.json`（五断言 identity/run_dir/…·`score_engine.py` L240-241）——**A 族引用=错引**。
- **trap / RCguard** = **全仓零实现**（`grep -c "trap\|RCguard" runtime/cognition/score_engine.py` = **0**）——**rubric 引用但不存在**。

**第四偏差（CPO 定·比前三处更硬）：判据自指虚空**——**A 族判据声称了不存在的实现**（trap/RCguard 零实现·qualify 错引），即「要求的守卫在代码里不存在」→ 判据的可满足性本身不可信（非「判据松」而是「判据悬空」）。复查卷：CPO `6593c6f04`（cpo-afamily-deviation-review-20261126.md）。

## §二 · 新 A 族（v2.3.0 提案）

| 字段 | 新值 |
|---|---|
| family_id | A |
| family_name | **迁移完整性**（迁移前快照→迁移后对照） |
| reading_point | **目标周目录树全卷（`operating-records/<W>/`·trees 递归）**——迁移前逐件 `sha256_16 + size + parse_ok` 冻结为 manifest 快照；迁移后同集重算对照 |
| collection_cmd | `artifacts_manifest`（复用 E1 机制·`score_engine._artifacts_manifest`·逐件 sha256_16+size+parse_ok）+ 迁移后同集重算 |
| verdict_rule | **同对象·同集·同 hash**：①件集一致（无增无减·缺件=violation）②逐件 sha256_16 一致（差异=violation）③parse_ok 全 true。**全中=pass；任一 violation=fail** |
| weight | **6**（不变） |
| special_clause | **新基准=每次迁移前实时快照**（存 `<run_dir>/migration-pre-snapshot.json`）·**旧 vB `4f990e911c3f` 形态固定值退役**·**scope=目标周目录树全卷**（不含 jobs.json·jobs.json 属 TriRMC 调度面·其改动归 PATCH 程序自身守卫） |
| weight_note | rubric-v2.3.0（候 CEO 批）·65+35 制不变 |

**三守卫退役**：
- `qualify`：语义已在 **E 族**（五断言）·**不迁入 A**（避免双面重复）。
- `trap` / `RCguard`：**零实现·表述退役**（历史「形态固定值」时代残留）。

## §三 · 差异影响

| 面 | 影响 |
|---|---|
| 迁移事故可见性 | **新增**——迁移前后 hash 对照使「迁移中对象被篡改」可发现（现无） |
| jobs.json 面 | **移出 A 族**——其漂移检测归 PATCH/调度面自身守卫（不在迁移完整性范围） |
| 实现成本 | **零新造**——复用 E1 `artifacts_manifest`（逐件 sha256_16+size+parse_ok·commit ff5d2ab） |
| 既有轮次 | A 族旧判（v2.2.0）**已落卷数据不改**（历史叙事冻结）·新判自 rubric 批后生效 |

## §四 · 进程面（生效与点火）

- **rubric 批前不生效**：r49 若点火，A 族仍按 v2.2.0 旧判（或标「候选新判·待批」）。
- **点火仍候 CEO**（无 CEO 批任务书=零点火·照役）。
- 批后首轮=新 A 族首个实锚轮（建议 r49 或其后首轮）。

## §五 · 会签与批面

- **CTO 出稿**（本件·技术侧）
- **CPO 会签 = 已毕（2026-11-26·CPO 卷 6593c6f04）**：产品语义面一句=**A 族重定义不改变产品语义、PRD 无需改**——「迁移完整性本就是 fade-001 的核心产品承诺（记录随周封存·活随人带走+迁移中不失真），重定义只是让判据回归承诺本身；属判据修正非产品变更」·CPO 联署确认。
- **CEO 批**（rubric 修订须 CEO 批·rubric-v2.2.0 是 CEO 批的）

## §五之二 · 产品面约束（CPO 会签附带·一并载）

1. **完整性读数对内可见可复算**：**drift 告警须入周读数/评审卷证据面**（与 CPO cpo-2 需求承载完整性证据形衔接）——**对客户可见=候对外产品面**（现无客户面·登记 later·不阻塞本提案）。
2. **过渡期标注**：**rubric 批前 A 族分数按「判据缺陷」标注**（rubric_defect 先例）——**不洗白不扣席**。

## §六 · 实读锚

| 锚 | 值/位置 |
|---|---|
| jobs.json 现 md5 | `bb07f8f9764d42e94aeb8af10bbdbde3`（BOD 2026-11-26 20:04 读数） |
| jobs.json 采集实现 | `score_engine.py` `_collect_a` L333-360（读 jobs.json·md5 全串·jobs 计数） |
| qualify 实现 | `score_engine.py` L240-241（E 族·`_read_stage(run_dir,"qualify.json")`） |
| trap/RCguard | `grep -c` = 0（全仓零实现） |
| 迁移对象实存 | `TriMetaverse/docs/workflow/operating-records/2026-W47/` + `2026-W48/`（本机双周） |
| artifacts_manifest 机制 | `score_engine.py` `_artifacts_manifest`（sha256_16/size/parse_ok·commit ecf6c03→50d3b55→ff5d2ab E1 加固） |

## §七 · 使用依据

CEO 令（BOD 转 20:04 A 族复查）+BOD 確認开写（20:07）+rubric-v2.2.0 原文（`runtime/cognition/rubric-firstshoot.json` family A）+实读锚六条。

---
—— CTO 小狄（m-cto）·写前现查 2026-11-26T12:07Z（+0800=20:07）
