# LG-026-P1 letter-store 数据层验收测试报告（D-15 路由测试面）

- sourceOfTruth: TriCompany/docs/test/lg-026-p1-letter-store-acceptance-report.md（测试真源目录初始化首件）
- syncMode: static（验收快照，不随代码演进改写；后续变更另出报告）
- lastSyncedAt: 2026-09-02
- 执行人: ST（TestEngineer 小柯）；派工: CTO 派工令 2026-09-02T04:45Z（LG-026-P1，D-15 路由测试面）
- 验收对象: TriRLC dev `48244a2`（`fix(lg-026-p1): 严格冻结版整改——escalated 绝对终态`），含 `87fa934` 数据层落地，dev ahead 2
- 设计依据三件: `TriMetaverse/docs/execution/lg-026-business-lead-daemon-design.md` §二③ + `lg026-cto-joint-review-opinion.md` ③ + `trimlc-channel-daemon-spec.md` §8.6；终验裁示=严格冻结版（escalated 绝对终态、done 仅自 read、办结走 ref 新信封自身状态机）
- 边界遵守: 只验证未改 TriRLC 源码；复证用移开复跑法已还原（TriRLC git status 复归仅 2 个既有 untracked 目录）；发现问题未直改 FD 件，观察项单列报 CTO 裁
- **结案裁定（CTO 2026-09-02T05:04Z 核毕，三分法 APPROVE；CTO 本机独立复跑黑盒 76/76=第三方法）**: O1 结案（无风险）；O2 采双保险=读侧容错（parse 失败不炸遍历、落 raw+last_error 标记）+写入面端点 JSON schema 校验，归 P2 派工令批 A/批 B 首条；O3 维持 P3 归属（ttl 语义定时补 DDL CHECK+store 层校验一并）；O4 采 store 层 strftime 显式 Z 方案+无 Z 旧行兼容读，归 P2 批 A。O2/O4 整改落地后 P2 验收时 ST 复验闭环；P2 验收门禁 CTO 届时另发（新增端点面+ACL+wake 链验证面）。本件验收正文为 static 快照不改写，本行仅留痕结案态。

## 测试判断

**PASS** —— 三项验收门禁全过（独立重测 ✓ / 黑盒交叉验证 76 断言全绿 ✓ / 盲区观察项已探边单列 ✓），无阻塞性缺陷；4 项盲区观察全为非阻塞（O2 容错缺口 / O3 ttl 无门禁 / O4 时刻格式口径，均已给 P2 前处置建议），候 CTO 裁示。

## 测试策略

1. **门禁① 独立重测**：重跑仓内测试三件套（letter-store 单测 / tsc check / 全量回归），全量回归对 2 个既有失败用移开复跑法复证与本变更无关联。
2. **门禁② 第二方法交叉验证（黑盒）**：独立脚本直调 `createLetterStore` 公开 API（不经仓内 `test/letter-store.test.ts`），自写断言五面覆盖：seq 全局单调+重启续号 / 状态机门禁矩阵 5态×4动作全遍历含 actor 两规则 / escalate 原子性注入回滚 / ledger 留痕完整性 / sinceSeq 边界。
3. **盲区/错位观察**：对派工令提示面四项做探边实验，只记录不判级（判级建议单列供 CTO 裁）。

## 测试结果

### 门禁① 独立重测（全过）

| 项 | 派工令预期 | 实测读数 | 判定 |
| --- | --- | --- | --- |
| letter-store 单测 | 25/25 | 25/25（`node --import tsx --test test/letter-store.test.ts`） | ✓ |
| tsc check | 绿 | `tsc -p tsconfig.json --noEmit` 无输出通过 | ✓ |
| 全量回归 | 603/605（2 既有失败） | **604 pass / 606 tests / 2 fail**（复跑两轮读数稳定） | ✓（差 1 已溯源，见下） |
| 移开复跑法 | 剩余全绿 | 移开 2 既有失败文件后 **604/604 全绿**，还原后 TriRLC 工作区干净 | ✓ 与本变更无关 |

- **2 个既有失败身份**：`test/integration/replay-flow.test.ts`、`test/tui/components.test.ts`——与派工令既有失败清单逐一吻合。
- **603/605 vs 604/606 差 1 溯源（实查非推断）**：`git show 87fa934:test/letter-store.test.ts` 用例数=24，`48244a2`=25（48244a2 提交补「ref 信封走自身主链办结 done」用例 +1）；CTO 基线读数（04:41Z 裁示）取自 87fa934 时刻，48244a2（04:45Z 提交）后全量自然 +1。无异常。

### 门禁② 黑盒交叉验证（76 断言 PASS / 0 FAIL，exit=0）

脚本与全文读数：`TriCompany/docs/test/evidence/lg-026-p1/blackbox.ts` + `blackbox-result.log`（另从证据目录复跑一轮复证同读数）。

| 面 | 断言数 | 关键结论 |
| --- | --- | --- |
| A. seq 全局单调+重启续号 | 8 | 首信 seq=1、严格 +1 步长（跨发送人/收件人）、关开 factory 两轮重验 MAX 续号、{1..5} 无重复无空洞 |
| B. 状态机门禁矩阵 5态×4动作 | 20+10 | 20 格全遍历与严格冻结版期望矩阵逐一吻合（escalated/done 两终态 8 格全 DENY；done 仅自 read）；actor 两规则：deliver 拒非 leader ×4（含空串）、read 拒非收件人 ×4（**组长代标被拒实证**）；escalate/done 无 store 层 actor 白名单=设计如此（store.ts:254-258 注释载明终裁升级权在 COS） |
| C. escalate 原子性 | 20 | 三路注入全回滚无中间态（非法 priority / 重复 letterId / ghost+未冻结 ref）：原信状态不变+seq 无空洞+ledger 无残留+无半行；成功路径冻结+新信封同事务、seq 连续 +1；附加自引用注入（新信封 letterId=原信 id）回滚解冻 ✓ |
| D. ledger 留痕完整性 | 9 | 全流转 4 行 send→deliver→read→done、actor 序列正确、id 严格递增、at 全非空；escalate 双信轨迹（原信 send+escalate / 新信封 send 起）；sinceId 增量读 ✓；recordRetry 不入台账（留痕在 retries/last_error 字段，设计如此） |
| E. sinceSeq 边界 | 8 | 0→全量 / 负数→全量 / 中段→恰为后继 seq / =max→0 / 超界→0 / 恒升序 / 与 status+to 组合过滤 ✓ / 缺省 undefined 无过滤 |

### 盲区/错位观察项（四项，均非阻塞；处置建议候 CTO 裁）

探边脚本与全文读数：`evidence/lg-026-p1/blindspot.ts` + `blindspot-result.log`。

**O1 `"from"` 引号列名查询边界——无风险**：参数化查询对 `O'Brien`、注入形态值（`x'); DROP TABLE letters;--`）精确过滤且表存活；裸 SQL 引号列返回键名无引号（`["from","to"]`），`rowToLetter` 映射正确；from=to 同值双过滤正常。

**O2 payload 非 JSON 容错——容错缺口（非阻塞）**：正常写入路径 roundtrip 全一致（9 型矩阵含 undefined→null 归一）。但 `rowToLetter`（store.ts:145）`JSON.parse` 无 try-catch：外部/手工写坏的 payload 使 `getLetter` 单读抛 SyntaxError，且 **`listLetters` 全表读连带抛错——一封坏信毒化整个收信列表/积压重放面**；仅过滤不命中坏信才幸免。当前写入面全走 `JSON.stringify` 不会产生坏数据，故非阻塞；P2 信箱端点接线前建议裁：读侧容错（跳坏信留痕）或维持 fail-fast + 读写权限收紧承诺。

**O3 ttl 类型边界——store 层无校验+DDL 无 CHECK（非阻塞）**：0/负数/浮点照收；字符串 `'abc'` 静默落库且读回 typeof 漂移为 string（types 标 `number | null` 仅编译期）；布尔 true 与 >2^53 数被 node:sqlite 绑定层拒（fail-fast）。ttl 到期语义 P2/P3 才定——届时若依赖正整数需补门禁（store 层校验或 CHECK 约束），现记录在案。

**O4 `datetime('now')` 时区口径 vs UTC 纪律——值 UTC、格式非纪律格式（非阻塞）**：
- 值域实证为 UTC（与 JS UTC 时钟差 <1s）；letterId 前缀（`genLetterId` 用 `getUTC*`）与 createdAt 日期段两 UTC 源一致。
- **格式错位实证**：SQLite 给 `2026-09-02 04:57:21`（空格分隔无 Z），非 UTC 纪律的 `YYYY-MM-DDTHH:MM:SSZ`；JS `new Date(createdAt)` 会按**本地时区**解析——实测读数偏 -8 小时（O4d）。ledger.at 同格式。
- P2 消费侧接线前建议裁：读侧显式 UTC 解读（`replace(' ','T')+'Z'`）或 store 层改 `strftime('%Y-%m-%dT%H:%M:%SZ','now')` 一劳永逸。

## 质量门禁评估

| 派工令门禁 | 结果 |
| --- | --- |
| ① 独立重测（25/25 + tsc + 全量回归 603/605 基线） | ✓ 全过（606/604 差 1 已实查溯源=48244a2 补用例） |
| ② 第二方法交叉验证（黑盒五面） | ✓ 76 断言 PASS / 0 FAIL + 证据目录复跑复证同读数 |
| ③ 盲区/错位观察项单列 | ✓ 四项探边完毕、两条实质发现（O2/O4）+两条记录项（O3/O1 无风险）单列候裁 |
| 严格冻结版终验裁示对表 | ✓ escalated 绝对终态（升后全拒含 done）、done 仅自 read、办结走 ref 新信封自身状态机（黑盒 B/C 面实证） |
| 边界（只验证不改源码） | ✓ TriRLC 工作区还原干净，未触 FD 件 |

**三分法：PASS**。无阻塞性缺陷；O2/O3/O4 三项非阻塞观察已带处置建议，不构成拒收项，是否列入 P2 前整改清单候 CTO 裁示。

## 使用依据

- 验收对象：TriRLC dev `48244a2`（源码 `src/letter-store/store.ts` 368 行 / `types.ts` 71 行 / `test/letter-store.test.ts` 352 行 25 用例）
- 设计依据三件：见文首；严格冻结版口径以 `48244a2` 提交文与 types.ts:8-10 注释为准
- 证据六件：`TriCompany/docs/test/evidence/lg-026-p1/`（blackbox.ts / blindspot.ts / blackbox-result.log / blindspot-result.log / fullreg-run1.log / fullreg-run2-moved-aside.log）
- 复现命令：单测 `node --import tsx --test test/letter-store.test.ts`；全量 `npm test`；黑盒 `npx tsx <evidence>/blackbox.ts`（于 TriRLC 根执行）
- 避峰已知悉：LG-025 M0 09-05/08，本验收无冲突
