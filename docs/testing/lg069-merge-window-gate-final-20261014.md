# LG-069 合并窗序 5 门禁 · STE 终验卷（§四.6 全绿+全量对表）

- sourceOfTruth: 本件（TriCompany/docs/testing/lg069-merge-window-gate-final-20261014.md）
- syncMode: static（门禁终验读数卷·终态）
- lastSyncedAt: 2026-10-14T08:32:53+08:00（date 现查原值）
- 执行席: STE 小柯（m-ste）；令源=COO 08:19:33 LG-069 合并窗门禁预置令（序 5）+排窗令正身 §二序 5；触发=FSD 序 4 从闸毕报信号（08:31:02 落款·本席收信 hook 现戳 08:31:13 对表吻合·倒挂 11s）
- 基线卷: `docs/testing/lg069-merge-window-gate-baseline-20261014.md` @6b902a0（T0 读数+§四.6 映射抽验+执行计划）

## 一、判定（三分法）

| 判据（排窗令序 5·方案稿 §六） | 实测 | 判 |
| --- | --- | --- |
| ①基线窗首 fresh 采样（施工前） | T0=08:27:07-08:27:22 拍（**先于**序 4 毕信号 08:31）·730/730·fail=空集 | ✓ |
| ②单测门 §四.6 全绿 | 四文件定点跑 **30/30 零 fail**（23 例清单全数在内·零缺测） | ✓ |
| ③全量对表（不增不减） | T1=08:31:32-08:31:47 拍·730/730·fail 0·EXIT=0——与 T0 **逐字对表零变动** | ✓ |
| **序 5 门禁整体** | 三判据全绿·零阻塞·零非阻塞挂账 | **PASS** |

## 二、T1 终拍读数（触发后 fresh·独立验）

- 代码态三查（禁转抄独立验）：HEAD=`2e1e594fb78d44ec371c6deb676364f45976788f`（与 T0 同 hash）·分支=dev·porcelain 零 M 行——FSD 毕报「零新码同 hash」**独立复验吻合**。
- 全量：tests 730 / suites 134 / pass 730 / **fail 0** / cancelled 0 / skipped 0 / todo 0 / duration 14643ms / **EXIT=0**。
- 反证抽验：T1 log `not ok` 行=0（截断伪影家族防线）。
- §四.6 定点（power-follower+crash-handler+cron-timeout-race+cron-addjob-nextrun 四文件单跑）：**tests 30 / pass 30 / fail 0**。
- FSD 侧自测（730/730+tsc 0）与本席独立 T1 同读数——**双面互证**（FSD 毕报卷 16b2a017e）。

## 三、时序与触面如实注记

1. **本窗施工形态=验证+推送非写码**：序 1-4 四件（件A/件C/件B/从闸）已于 10-11 补窗落位先行稿（5874375/6fbde65/130133a/2e1e594），本窗 FSD 面=逐件验证+毕报；故「施工后」态与基线态同 hash——对表判据在恒定代码态下成立，语义如实分层（若窗内有新码，同法重采对表）。
2. **触面演化实锚**（FSD 知会·本席代码核验）：从闸生命周期挂接实落 `src/server/app.ts`（L122 import/L1476-1477 env 开关 TRILC_POWER_FOLLOW+startPowerFollower/L1503 shouldDispatchNewJobs 谓词/L1791-1792 healthz follower 段投影/L4940 shutdown 链 stop）——方案稿 §四字面 index.ts 系稿面表述差，实锚 app.ts 装配面；本席 §四.6 映射=测试文件面，不受影响。
3. 判定边界：本卷=**序 5 单测门禁读数面**；序 6 活体锚五项（following 镜像/hard skip/自解零残留/holding→×3 unknown+告警/三回流件正形探针）归 COO 终验逐件销（排窗令 §二序 6），本卷不代判。序 0（8713 lastReadAt 短重启）候 SDE 毕锚——活体锚⑤ staleness 传染真验依赖其毕。

## 四、使用依据

- 排窗令正身 coo-window-plan-20261014.md §二序 5/§三止损/§四派工；方案稿 cto-power-gate-phase2-plan-20261011.md §四.6/§六
- FSD 毕报信号（08:31:02）+毕报卷 TriMetaverse 16b2a017e（W41 树 fsd-merge-window-build-20261014.md）
- 基线卷 @6b902a0（T0 三查+读数+23 例映射清单）
- 活体（08:31-08:32 拍全只读）：TriRLC git rev-parse/branch/status·npm test 全量+四文件定点·app.ts grep 实锚
- 纪律：既有定性禁转抄须独立验（FSD 读数独立复验）/时刻引用先 date 现查（本文时点均原值）/先写后报/worktree 落笔/反证抽验（not ok 计数）

## 落款

- 终拍毕 08:31:47+08（现查）；本卷写毕 08:32:53+08（现查）；commit 时点见 commit 笔。
