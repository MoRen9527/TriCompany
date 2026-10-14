# LG-069 合并窗序 5 门禁 · TriRLC 全量基线 T0 采样卷（施工前 fresh）

- sourceOfTruth: 本件（TriCompany/docs/testing/lg069-merge-window-gate-baseline-20261014.md）
- syncMode: static（基线读数卷·终验对表基准）
- lastSyncedAt: 2026-10-14T08:31:xx+08:00（date 现查原值见落款行）
- 执行席: STE 小柯（m-ste）；令源=COO 08:19:33 LG-069 合并窗门禁预置令（M-004 直达·窗位 08:35-10:35·序 5=门禁）+排窗令正身 coo-window-plan-20261014.md §二序 5/方案稿 §六
- 采样性质: **施工前基线**（窗开前 08:27 采样·先于 FSD 窗内序 1-4 施工面·满足方案稿 §六「基线=施工前 fresh 采样」）

## 一、代码态锚定（采样前置断言）

| 断言 | 实测 | 判 |
| --- | --- | --- |
| TriRLC HEAD | `2e1e594fb78d44ec371c6deb676364f45976788f`（=「补窗 2026-10-11 从闸」顶·含件A 5874375/件C 6fbde65/件B 130133a 四笔先行稿全在） | ✓ |
| 工作区 | `git status --porcelain` 零行（零 M 行） | ✓ |
| 分支 | dev | ✓ |
| 依赖 | node_modules 在；node v22.21.1 | ✓ |
| 命令 | `npm test`（=node --import tsx --test test/**/*.test.ts） | ✓ |

## 二、基线 T0 读数（08:27:07-08:27:22·duration 13893ms·EXIT=0）

```
# tests 730    # suites 134
# pass 730     # fail 0
# cancelled 0  # skipped 0  # todo 0
```

- **既有 fail 面=空集**（不增不减对表基准=零 fail 维持）。
- 反证抽验（截断伪影家族防线）：`not ok` 行计数=**0**；顶层 ok=210+嵌套 Subtest=870→730 数学自洽；EXIT=0 与汇总互证——假阴性排除。
- 全量 log 留证：/tmp/trlc-baseline-t0.log（会话临时位·读数以本卷为锚）。

## 三、§四.6 清单逐项映射抽验（缺测≠全绿·23 例齐）

| §四.6 项 | 载体文件 | 映射实测 |
| --- | --- | --- |
| follower 状态机 7 形态（following 镜像/holding 持有/×3 unknown/告警一次每段/staleness 传染/unknown 放行+hard skip/soft 放行） | test/power-follower.test.ts | **7/7 全在**（L26/37/48/59/75/92/99 逐名对表）+超额 4 锚（healthz 四键投影 L107/isStale 三态 L116/hard 闸 skipped L168/非 hard 放行回归 L175）=11 test |
| 件A 7 例 | test/crash-handler.test.ts | **7/7**（L17/25/32/45/56/66/77 顶层 test 逐名在列） |
| 件B 3 例 | test/cron-timeout-race.test.ts | **3/3**（L53 滞后 reject 吸收/L74 滞后 resolve 零变/L83 gate 拒绝不回归） |
| 件C 2 例 | test/cron-addjob-nextrun.test.ts L127 describe「F-3 第三型 enabled 缺省归一（件C 回归钉）」 | **2/2**（缺省归一 true 含冷载面/显式 false 不过度归一） |

- 23 例全数含于基线 T0 730 绿内（全量跑过零 fail）。
- 判读：§四.6「全绿」门禁判据在基线态已具**载体完备性**（清单零缺测）；施工后复跑以同清单定点断言。

## 四、8711 活体旁注（采样同拍·非门禁判据）

- healthz（08:24:33 拍）：`ok:true`·follower 段已在投影 `state=unknown/lastPollAt 滚动/lastGateSeen=null/pollFailures=0`——从闸先行稿代码在役（10-13 11:41 CST 冷启·uptime 20.65h）；state=unknown 系前置件（8713 lastReadAt 投影）未落窗的预期形态（方案稿 §五·非劣化读数）。
- cron jobCount=0·mc_link/trimc=degraded（CTO 既判链路通+token 门活双证形态·非 fail）——活体锚五项归序 6 终验面，本卷不判。

## 五、门禁执行计划（候触发）

- **触发**：序 4 从闸毕信号（FSD 施工毕报）或 **10:20 保底**（无论施工进度）——二取一先到先拍。
- **触发后动作**：①复跑全量→对表（fail 不增不减=基线空集维持零 fail·tests 数变动如实归因）②§四.6 23 例定点全绿断言 ③毕报 COO+FSD·读数入终验链。
- 施工后代码态断言照 §一 重做（HEAD/porcelain/分支三查——新笔在列逐名录）。

## 六、使用依据

- 排窗令正身：`operating-records/2026-W42/trees/lg069-power-gate-20261007/coo-window-plan-20261014.md` §二序 5/§四派工段
- 方案稿：`operating-records/2026-W41/trees/lg069-power-gate-20261007/cto-power-gate-phase2-plan-20261011.md` §四.6/§六门禁与验收锚
- TriRLC 仓活体（08:27-08:31 拍）：git rev-parse/status/log·npm test 全量·test/ 四文件 grep 映射·8711 healthz
- 纪律：时刻引用先 date 现查（本文时点均现查原值）/先写后报/path-scoped commit/worktree 落笔（主仓 HEAD 常驻他人分支态）

## 落款

- 采样毕 08:27:22+08（现查）；本卷写毕 commit 时点见 commit 笔。
