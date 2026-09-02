# LG-026-P3 推送三级验收测试报告（D-15 路由测试面）

- sourceOfTruth: TriCompany/docs/test/lg-026-p3-push-tiers-acceptance-report.md
- syncMode: static（验收快照，不随代码演进改写）
- lastSyncedAt: 2026-09-02
- 执行人: ST（TestEngineer 小柯）；派工: CTO 派工令 2026-09-02T06:37Z（LG-026-P3，D-15 路由测试面）
- 验收对象: TriRLC dev `adee963`（8 files +759/-53：R1 SSE 直推+as 补拉 / R2 上线即报 / R3 letter-sweeper 升级链 / R4 ttl 收口 / F1 from=actor / F2 priority 显拒 / F3 限流 / F4 驼峰契约+agentCount），dev ahead 6
- 设计依据: design §二④ + spec §8.6 + P2 结案裁示链（05:57Z 五裁）+ 本令五裁落法（as 收信声明语义 / sweeper 内部化 / 急件 30min 窗 / ttl 存量库不改表 / 限流不立审计表——验收按此裁对表）
- 边界遵守: 只验证未改 TriRLC 源码；时间注入法零真 sleep；TriRLC 工作区终验干净；报告+证据 evidence/lg-026-p3/
- **验收中裁定（CTO 2026-09-02T07:35Z 核毕）**: ref 急件信封自升级链**判缺陷→整改**，修法较 ST 候选扩面——sweeper **全部规则**（急件窗/重要件 8h/执行席 24h/ttl 超限的升级分支+重推分支）统一排除 refLetterId 非空件（重要件与 ttl 链升级产物同族膨胀；重推对 ref 件语义混乱；法理=升级产物入人工终裁域 §8.6，自动链单层终止，ref 件触达靠 L1/L2 既有通道）。整改归 FD（sweeper 规则排除+三用例：ref 急件 31min 不动/ref 重要件 8h 不动/ttl ref 超限不升）；rateLimitedCount 上 healthz 登记 P4 顺手件。ST 复验范围=三 FAIL 表观污染用例+ref 件全规则排除零膨胀断言，复验过则本件升 PASS 归档。状态维持 CONDITIONAL_PASS 候整改复验。

## 测试判断

**CONDITIONAL_PASS** —— 门禁①②③核心语义+⑤全过（重测 632/634 逐字吻合+移开法 632/632；端点黑盒 16 断言全绿；sweeper 时间注入 17/20，3 FAIL 全部同根=ref 自升现象非独立缺陷；盲区四项探边齐）。唯一条件项：**ref 急件信封自升级链**（盲区级真发现，升级产物无终止条件，30min/层链式膨胀实证）——非阻塞（不崩不丢数据，127.0.0.1 信任域内），但属缺陷倾向，定性（缺陷/设计权衡）与处置候 CTO 裁；裁后可升 PASS。

## 测试策略

1. **门禁① 独立重测**：三件新测试单跑（sweeper 5 / 端点 e2e 12 / 限流 1）+ tsc + 全量回归（2 既有失败移开法；SSE 拖尾 ~2min 已知悉非缺陷，移开复跑轮以 10min 上限分两次执行）。
2. **门禁② 端点黑盒新增面**：独立脚本直调 createTriLCApp——F1 伪报矩阵 / F2 显拒 / F3 限流（独立小实例 TRILC_LETTER_RATE_LIMIT=3）/ R1 活推帧无 payload / R2 ?as= 补拉。
3. **门禁③ sweeper 黑盒**：时间注入法——劫持 `Date.now` 注入偏移钟（store 时间戳走 SQLite strftime 真实墙钟不受注入影响）；每场景独立库+注入钟归零（v1 教训：场景间 offset 与真实墙钟耦合产生伪 age）。
4. **门禁④ 活模型 E2E**：双触发待命线已执行（另报），本令不重发。
5. **门禁⑤ 盲区探边**：四项提示面观察实验。

## 测试结果

### 门禁① 独立重测（全过）

| 项 | 预期 | 实测 | 判定 |
| --- | --- | --- | --- |
| letter-sweeper 单测 | 5/5 | 5/5 | ✓ |
| 端点 e2e | 12/12 | 12/12 | ✓ |
| 限流测试 | 1/1 | 1/1 | ✓ |
| tsc check | 绿 | 通过 | ✓ |
| 全量回归 | 632/634 | **632 pass / 634 tests / 2 fail**（replay-flow + tui/components，既有失败清单吻合） | ✓ |
| 移开复跑法 | 剩余全绿 | **632/632 全绿**，现场还原 | ✓ |

### 门禁② 端点黑盒新增面（16 断言 PASS / 0 FAIL，exit=0）

证据：`evidence/lg-026-p3/p3-endpoints-blackbox.ts` + `endpoints-blackbox-result.log`。

- **F1 伪报矩阵（6）**：寄信 body.from 伪报被 actor 覆盖（201 且信封 from=actor）；缺 actor 400 invalid_actor；escalate envelope.from 伪报（≠actor）400 / 缺 400 / =actor 200。
- **F2 显拒（2）**：envelope.priority 提供非法（'紧急'）400 invalid_priority；未提供 200 且新信封缺省 '急件'。
- **R1/R2 SSE（5）**：R2 连接即补拉首帧=delivered 积压信 letter_inbox；补拉帧不含 payload 键；R1 连接期间新信活推帧；活推帧字段恰七枚摘要 [event, letterId, seqNo, from, to, priority, status]（无 payload）。
- **F3 限流（3）**：独立实例 limit=3——前 3 封 201 / 第 4-5 封 429 rate_limited；GET 端点不受限流影响。

### 门禁③ sweeper 黑盒——时间注入法（17 PASS / 3 FAIL，exit=1）

证据：`evidence/lg-026-p3/p3-sweeper-blackbox.ts` + `sweeper-blackbox-result.log`。

- **① C-suite 4h 链（核心全过）**：3h 不动 → 4h+ rePush（rescued=1、retries=1、wake 触发、状态仍 delivered）→ 8h+ 自动升级（原信 escalated 冻结 + ref 信封 to=COS/priority=急件/escalatedBy 含 auto-sweep）。
- **② 执行席 24h 同构**：5h 不动断言 ✓ → 24h+ rePush → 48h+ 升级 → ref 同构。
- **③ 急件 30min 保护窗**：29min 窗内不动 → 31min 过窗即升；retries=0 全程（零等待语义=不走重推链，CTO 裁示口径吻合）；pending 急件过窗同样升。
- **④ ttl 到期链**：到期 rePush ×3（retries 1→2→3=maxRetries，wake 恰 3 次）→ retries>=3 escalate。
- **⑤ 终态不动**：已读件任意时刻零动作。
- **3 个 FAIL 同根定性**：全部为 **ref 急件信封自升现象**在同场景的表观（sweeper 急件规则把 escalate 产物当普通急件扫描再升级）——非独立缺陷，现象本体单列盲区节候裁。核心阈值/重推/原子升/窗口/ttl 链语义 17 断言全过。

### 门禁⑤ 盲区探边（四项+一项跨引，12 观察项）

证据：`evidence/lg-026-p3/p3-blindspot.ts` + `blindspot-result.log`。

**① pushLetterEvent 广播调用点事务一致性（重点探——通过）**：源码级三调用点（POST letters / state / escalate 双推）全在 store API 返回后（内部 BEGIN/COMMIT 完成才返回）——无事务内推帧路径；黑盒实证：失败 escalate（400，库未触）零状态帧、成功推帧 status 与库终态一致（推的是已提交数据）。**未提交数据风险不存在。**

**② 同席 as 多连接并发注册（通过）**：同席两 stream 连接并发在册，寄信后两连接各收同一帧（Set<res> 广播语义）；连接断开 cleanup 双挂（req+res close）。

**③ 30min 宽限与 4h 阈值边界叠压（无叠压面+真叠压点定位）**：同信单 priority 无叠压——重要件 @30min 零动作（不被急件窗误伤）、急件 @4h 不进重要件链（priority 隔离实证）。真实叠压点=急件 ref 产物回灌急件规则（见下项）。

**④ 限流计数器内存态（重启清零实证）**：进程内 Map（app.ts:1310）——两实例计数独立互不串扰；实例重启后同 60s 窗内首封即 201（清零实证）；滑窗 60s 自然恢复同构语义。定性：内存态=设计现状（CTO 裁接受不立审计表）；重启清零可被攻击者借以重置窗口，127.0.0.1+token 信任域内可接受。

**⑤ ref 急件信封自升级链（盲区级真发现，候 CTO 裁）**：sweeper 急件规则（listLetters priority='急件'，status pending/delivered）**未排除 refLetterId 非空的升级产物**——实证链：原始急件 31min 过窗升级 → ref 信封（急件，to=COS，pending）→ 再 31min 后 sweep 把 ref 信封又升级（escalated=1，ref2 生成 to=COS）→ 无终止条件，30min/层链式膨胀（收件方未办结时每 ~30min+5min 扫描周期产生一层新信）。影响面含 sweeper 自动升级与组长 letter_escalate 的全部急件产物。非阻塞（不崩不丢数据、人工可断、信任域内），缺陷倾向明显；修法候选（FD 面）：急件规则排除 `refLetterId IS NOT NULL` 件（升级链终止于人工 COS），或排除 escalatedBy 含 auto-sweep 的产物。**另附错位备忘**：rateLimitedCount 注释称「healthz 可观测」但计数未上 healthz（注释与实现出入，P3+ 顺手件）；限流留痕仅 console（CTO 裁已接受）。

## 质量门禁评估

| 派工令门禁 | 结果 |
| --- | --- |
| ① 独立重测 | ✓ 全过（632/634 逐字吻合+移开法+三件单跑+tsc） |
| ② 端点黑盒新增面 | ✓ 16 断言全绿（F1 矩阵/F2 显拒/F3 429/R1 无 payload/R2 补拉） |
| ③ sweeper 黑盒 | ✓ 核心 17 断言全过；3 FAIL 同根=ref 自升现象（单列候裁非独立缺陷） |
| ④ 活模型 E2E | 不重发（双触发线已执行另报：机械面全通+第三型阻塞 TriModel dist 定性） |
| ⑤ 盲区探边 | ✓ 四项齐+ref 自升真发现单列 |
| 五裁落法对表 | ✓ as 收信声明语义（?as= 断言合规）/ sweeper 内部化（未入 cron CRUD）/ 急件 30min 窗（窗内不动过窗即升）/ ttl 存量不改表（应用层校验+新建库 CHECK 双保险实证：ttl<=0 写入 invalid_ttl 拒）/ 限流不立审计表（console+计数收档） |
| 边界 | ✓ 只验证不改源码，工作区干净 |

**三分法：CONDITIONAL_PASS**。四门禁核心全过、无阻塞性缺陷；条件项=ref 急件信封自升级链（缺陷倾向候裁定性：若 CTO 判缺陷→P3+ 整改后复验闭环；若判可接受权衡→记已知边界升 PASS）。

## 使用依据

- 验收对象：TriRLC dev `adee963`（letter-sweeper.ts 188 行新建 / app.ts P3 段：pushLetterEvent+限流+端点改造 / store.ts ttl CHECK+应用层校验+priority 过滤 / heartbeat-runner agentCount）
- 证据八件：`TriCompany/docs/test/evidence/lg-026-p3/`（p3-endpoints-blackbox.ts+log / p3-sweeper-blackbox.ts+log / p3-blindspot.ts+log / fullreg-run1.log / fullreg-run2-moved-aside.log）
- 复现命令：`npx tsx <evidence>/<script>.ts`（于 TriRLC 根执行；sweeper 脚本为时间注入版 v2）
- 关联线：门禁④活模型 E2E 补跑已另报（机械面全通+第三型阻塞=TriModel dist 旧构建定性，候 triage）
- 避峰照旧：LG-025 M0 09-05/08 无冲突
