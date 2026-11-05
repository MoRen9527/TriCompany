# STE 验证卷 · source_publish_check 升 gate 形回归验证（FSD 施工交接验证）· 2026-11-05

- sourceOfTruth: 本卷（TriCompany/docs/testing/source-publish-gate-ste-verify-20261105.md）
- syncMode: static（验证读数卷·D-15 留痕）
- lastSyncedAt: 2026-11-05 14:24:33+08（date 现查原值·D-47 正形）
- 执行席: STE 小柯（m-ste）；令源=FSD 交接知会（m-fsd·11-05 14:09Z+8·CTO 路由注记「STE 回归验证候排——建议小柯现窗顺手段」·非派工形态·按排窗废止新制顺序推进接令）；对象=TriCompany **7f55fe4**（gate 施工 commit·现顶）·TMV **65e675fde**（FSD 毕报落卷·在链·顶=f29e7d855 CTO APPROVE 裁定）

## 一、判定

**PASS**（三分法·CTO 确认链）——双锚断言毕+四项读数独立复跑全对平+既有失败 4 件第二方法基线实证（非转抄）+语义翻转面独立活体 22/22 全绿；零阻塞性缺陷·零施工引入失败。一环境噪声如实录（§四）。本席不独立放行·判定呈 CTO。

## 二、独立复跑读数（与 FSD 自测面逐项对表）

| 项 | FSD 报 | STE 独立复跑 | 判 |
| --- | --- | --- | --- |
| PublishGateTests | 10/10 OK | **10/10 OK**（7.07s·rc=0） | ✓ |
| employee_host_publish_validation | 5/5 OK | **5/5 OK**（0.76s·rc=0） | ✓ |
| source_publish_check_validation | 194 tests / 2 失败 | **194 tests / 2 失败**（18.24s）·两件=SeatsPipelineValidation（`test_entry_level_session_body_thirteen_in_place` sessionBody 席位漂移 product-manager 多出+`test_manifest_claude_code_targets_complete` 登记数 15!=14） | ✓ 逐名对平 §五 归因 |
| 全量 discover（`*_validation.py`） | 420 tests / 4 failures / 1 skip | **420 tests / 4 failures / 1 skipped**（42.98s） | ✓ 三读数精确对平 |
| 全量 4 失败件名单 | frontmatter_parity / lg025_manifest_value_prefix / SeatsPipeline 两件 | `test_live_source_agents_frontmatter_parity`（employee_source_kit）/ `test_1_manifest_value_prefix_form`（lg025_m0d）/ SeatsPipeline 两件（同上） | ✓ 逐名剥齐全对平 |
| 代码态 | TriCompany 7f55fe4 / TMV 65e675fde | TriCompany 顶=7f55fe4 ✓·TMV 65e675fde 在链 ✓（porcelain 残留两笔非本域如实录：hub-ledger-governance.md 改动+P3 探针文档 untracked·不触 runtime/cognition 面） | ✓ hash 级 |

### 既有失败「既有」定性——第二方法独立实证（禁转抄纪律）

基线 worktree（施工前顶 **3feadc1**）复跑同 4 失败件 = **4/4 同炸**：

| 件 | 基线读数 |
| --- | --- |
| frontmatter_parity | 炸（senior-deployment-engineer name 一致性漂移——同族席位谱漂移） |
| lg025_manifest_value_prefix | 炸（14 != 13 role-agent sourceFiles 席位谱漂移） |
| SeatsPipeline sessionBody | 炸（同 product-manager 漂移） |
| SeatsPipeline claudeCodeTargets | 炸（15 != 14） |

**四件全为席位谱活体漂移族·施工前已在——零施工引入实锤**（与 FSD §五 stash 基线归因独立互证·第二方法=worktree 基线复跑非 stash 形）。技术债⑧口径成立：A4 治本段（席位变更流程补项·候 CHO）落位前每窗全量回归需重新分拣归因。

## 三、语义翻转面独立活体验证（裸 --publish-agents 默认 gate·本窗核心注意点）

**自建 temp fixture 独立脚本**（非仓内·零借测试 helper·`%TEMP%/ste-gate-verify-20261105.py`·显式时戳 env 控制 commit 时序）——五案 22 断言 **22/22 全绿**：

| 案 | 构造 | 断言结果 | 对表 |
| --- | --- | --- | --- |
| V1 gate-block | 发布面手工值 baseline 后单文件 commit（MANUAL_TS 新于源 BASE_TS）→ 裸 `--publish-agents` | rc≠0 fail-closed·mode=gate·status=fail·**gate_blocked=1**·gate.enforced=True·reason=**gate_target_newer_than_source**·手工值原样在盘（零覆写） | =FSD VERIFY-1 ✓ |
| V2 flag 降级 | 同 drift 形+`--agent-dry-run` | rc=0·mode=dry-run·dry_run=True·零写盘 | =FSD VERIFY-2 ✓ |
| V2b env 降级 | 同 drift 形+env `SOURCE_PUBLISH_CHECK_MODE=dry-run` | rc=0·mode=dry-run·零写盘 | 降级双通道第二通道补验（FSD 三验证含 flag 形·env 形测试族有·活体独立再证） |
| V3 allow 真写 | 发布面 stale 值 baseline·源侧演进 commit（EVO_TS 最晚）→ 裸 `--publish-agents` | rc=0·mode=gate·status=pass·gate_blocked=0·**updated=1**·**allowed_drift=1**·live 内容带源侧 payload | =FSD VERIFY-3 ✓ |
| V4 互斥 | `--agent-dry-run`+`--agent-execute` 同传 | **rc=2**（互斥错·RC2） | resolve 层单点收口语义活体实证 |

CLI 文案面核验：`--publish-agents` help="**Default mode is GATE (CEO 裁③ 2026-11-05)** … fail-closed"；`--agent-dry-run`="explicit downgrade … no writes, no gate enforcement … mutually exclusive with --agent-execute"——语义翻转在文案面成立。

**方向判据四规则活体覆盖**：发布面新于真源→block（V1）/源侧演进→allow（V3）/显式降级→零写盘（V2/V2b）/互斥 RC2（V4）。dirty 形与 fail-closed 无 git 信息形由 PublishGateTests 10/10 覆盖（复跑绿·本席活体未重复构造）。

## 四、非阻塞观察项（如实录）

1. **Windows GBK stderr 解码炸噪声**：PublishGateTests 复跑中一笔 subprocess reader thread UnicodeDecodeError（0xb2 GBK 字节·utf-8 母进程）——测试自身 OK 不判缺陷；与 FSD §五 注记同族（施工中 gate 提示文案汉字已改全英文·截断伪影家族在案）。环境性·候窗勘。
2. **fixture 施工两坑（本席自踩·防复发记）**：①manifest `sourceFiles` 键名=**下划线形**（`agent_body`/`agent_frontmatter`）·值路径=连字符文件名——键名连字符形 → preflight `source_files_missing:agent_body` 假阴性（errors=1 而 gate_blocked=0·gate 判定未达）；②drift fixture 时序=target 手工值须 baseline commit **后** seed 再单文件 commit（baseline 前写入=nothing to commit rc=1）。两坑均为 fixture 构造面非产品缺陷·gate 判定本体行为正确。

## 五、使用依据

- FSD 毕报卷 `fsd-gate-closure.md`（TMV 65e675fde 系·三验证读数+§五 stash 归因锚）；CTO 裁定卷（TMV f29e7d855·APPROVE）
- TriCompany 活体：顶 7f55fe4 双锚断言+四项读数独立复跑+基线 worktree 3feadc1 复跑 4/4+CLI --help 文案面+独立活体脚本 22/22（读数以本卷为锚·脚本=temp 会话临时位）
- 纪律：FSD 自测≠STE 验证（独立复跑）/既有定性禁转抄（第二方法 worktree 基线实证）/验证输出禁截断关键行（首轮 fixture 假阴性靠完整 JSON dump 抓获）/时刻引用先 date 现查/先写后报/判定不独立放行（CTO 确认链）

## 落款

- 验证窗 14:13-14:24+08（现查锚 14:13:28/14:24:33）；本卷写毕 14:24:33+08；commit 时点见 commit 笔。
