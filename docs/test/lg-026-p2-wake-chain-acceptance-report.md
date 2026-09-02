# LG-026-P2 唤醒链验收测试报告（D-15 路由测试面）

- sourceOfTruth: TriCompany/docs/test/lg-026-p2-wake-chain-acceptance-report.md
- syncMode: static（验收快照，不随代码演进改写）
- lastSyncedAt: 2026-09-02
- 执行人: ST（TestEngineer 小柯）；派工: CTO 派工令 2026-09-02T05:37Z（LG-026-P2，D-15 路由测试面）
- 验收对象: TriRLC dev `05b2d84`（批 A `8431995` 时刻Z+读侧容错 / 批 B `65352dc` 端点五件+ACL+组长接线+eventDriven / 整改 `05b2d84` escalate 强制原子版），dev ahead 5；跨仓 TriCompany `e64aa4c`（agent-core minTier，registry 收口 `e3b6167`）
- 设计依据: design §二③④ + 意见件③ + spec §8.6 + 裁示链（P1 结案 05:04Z / 批 A 核过 05:08Z / 裁甲 05:20Z / 批 B 核过+债务③裁示 05:32Z）
- 边界遵守: 只验证未改 TriRLC 源码；TriCompany 仓只读（g1 复证前后 git status 零改动）；移开复跑现场已还原（TriRLC 工作区干净）；报告落 TriCompany/docs/test/ + 证据 evidence/lg-026-p2/
- **结案裁定（CTO 2026-09-02T05:57Z 核毕，CONDITIONAL_PASS 接受，P2 结案归档）**: 盲区五裁——B1 裁「P3 强制 from=actor」（POST letters 覆盖请求体 from、escalate envelope from 改强制含取消缺省=actor、send_letter from 锁 LEAD_AGENT_ID；伪报 BOD 实证定性=代发权漏洞）；B2 无动作收档；B3 采速率上限入 P3（寄信端点 per-token 滑窗最小版超限 429）；B4 裁「P3 统一显拒」（escalate priority 非法值 400，缺省仅限未提供）+蛇形/驼峰契约 P3 统一驼峰+文档化；B5 接受现状；M12 登记观察项（P3+ 前不触，未来执行前复查须三参带声明）。门禁④定性：trimodel 网关+token 属宿主环境密钥面（env.ts:69 自证），补跑超 CTO 席无凭据可办范围——定性候 CEO 环境窗，ST 机械半实证已录关键证据，候窗补跑由 CTO 协调后另令。P3 验收令候 FD 完工另发。本件验收正文为 static 快照不改写，本行仅留痕结案态。

## 测试判断

**CONDITIONAL_PASS** —— 门禁①②③⑤全过（重测 30/30+5/5+10/10+tsc+全量 624/626 逐字吻合；端点黑盒 38 断言全绿；minTier 跨仓黑盒 15 断言全绿+g1 复证；盲区五项探边齐、全非阻塞）。唯一条件：**门禁④活模型 E2E 未执行**（模型环境不备：trimodel 网关 127.0.0.1:3333 未监听、TRIMODEL_API_TOKEN 未注入；按派工令出口单列不阻验收结论）——覆盖率缺口候 CTO 协调窗补跑；唤醒链机械面已获半实证（见门禁④节）。

## 测试策略

1. **门禁① 独立重测**：三件测试单跑（letter-store 30 / lead-tools 5 / letters-endpoints e2e 10）+ tsc + 全量回归（2 既有失败移开复跑法复证）。
2. **门禁② 端点黑盒**：独立脚本直调 createTriLCApp（port 0 + 死端口 trimodel + token 注入，非通道态），HTTP 面自写断言 ACL 四格/原子性/wake 幂等/token fail-closed/寄信重放五组。
3. **门禁③ minTier 跨仓黑盒**：TriRLC 侧 import `@tricompany/agent-core`（node_modules symlink → TriCompany packages/agent-core dist，跨仓直调实证），叠加 TriRLC 真实 registerLeadTools 注册路径，直调 getToolDefinitions；TriCompany 仓 g1 基线只读复证。
4. **门禁④ 活模型 E2E**：临时端口+真模型全链（环境不备则单列）。
5. **门禁⑤ 盲区探边**：派工令提示面五项观察实验（只探边不判级，判级建议单列）。

## 测试结果

### 门禁① 独立重测（全过）

| 项 | 派工令预期 | 实测读数 | 判定 |
| --- | --- | --- | --- |
| letter-store 单测 | 30/30 | 30/30 | ✓ |
| lead-tools 单测 | 5/5 | 5/5 | ✓ |
| 端点 e2e | 10/10 | 10/10 | ✓ |
| tsc check | 绿 | `tsc --noEmit` 无输出通过 | ✓ |
| 全量回归 | 624/626（2 既有失败） | **624 pass / 626 tests / 2 fail**（replay-flow + tui/components，与既有清单逐一吻合） | ✓ |
| 移开复跑法 | 剩余全绿 | 移开后 **624/624 全绿**，还原后 TriRLC 工作区干净 | ✓ |

### 门禁② 端点黑盒交叉验证（38 断言 PASS / 0 FAIL，exit=0）

脚本+读数：`evidence/lg-026-p2/endpoints-blackbox.ts` + `endpoints-blackbox-result.log`。

- **G1 token fail-closed（6 断言）**：信件五端点无 token 全 401 + 错 token 401——全局门先于端点族。
- **G2 寄信/seq/重放（7）**：POST 寄信 201 返回 letter_id+seq_no（蛇形手工构造）；seq 全局单调 1→2→3；since_seq 0/中段/超界三态 ✓；box=in 收信箱 to 过滤+缺 to 400。
- **G3 ACL 四格矩阵（13）**：白名单外（bob）×有 envelope → 403+台账 escalate_denied 留痕+原信仍 pending；白名单外×无 envelope → 仍 403（ACL 先于 envelope 校验）+留痕；白名单内（COS、组长各验）×无 envelope → 400 invalid_envelope 且不触库（原信 pending+台账无残留）；白名单内×有 envelope → 200 返回 original+envelope 双件。
- **G4 escalate 强制原子版（10）**：原信 escalated+新信封 pending+refLetterId=原信+新封 seq>原信；冻结后 deliver/read/escalate/done 全 409；台账原信恰 send+escalate 两行、新信封 send 起；不存在信 404。
- **G5 wake（4）**：202+woken:true；连发幂等同 202；非通道态无组长注册空转无害；寄信内联 wake 无副作用。
- 过程记录：首轮 37/38，唯一 FAIL 为**断言侧字段名笔误**（GET 响应透传 store 驼峰 seqNo，断言写蛇形 seq_no）——修正后 38/38；引出「同 API 面两种字段风格」观察（见 B4c 邻接口径，报 CTO 作契约一致性备忘）。

### 门禁③ minTier 跨仓黑盒（15 断言 PASS / 0 FAIL + g1 复证）

脚本+读数：`evidence/lg-026-p2/mintier-blackbox.ts` + `mintier-blackbox-result.log`。

- **组长清单（真实 registerLeadTools 路径）**：heartbeat 清单恰五工具且名单精确匹配 [letter_list_pending, letter_deliver, letter_escalate, send_letter, ledger_read]；无 file 系八件、无 shell_exec、无 task；subagent/coordinator 清单不可见；main 可见；无参全量=5。
- **缺省行为不变（g1-1 口径）**：无声明自定义工具查表无→main 缺省（subagent/heartbeat 不可见、main 可见，default-safe 实证）；表内名（read_file）无声明照表分派。
- **显式声明优先（g1-2 口径）**：声明 subagent 覆盖 main 缺省；声明 heartbeat 对 heartbeat 可见/subagent 不可见（组长面声明语义重现）。
- **TriCompany 仓 g1 只读复证**：tools-min-tier-declaration 2/2 pass，前后 git status 零改动。
- **M12 观察项（单列报 CTO）**：二参 `canUseTool('letter_deliver','heartbeat')` 导出面（无声明上下文）走查表→main 缺省→**拒**；现执行路径 loop.ts 不逐工具复查（清单即权限边界）故无实害，但若未来任何执行面引入二参复查需带声明上下文（canUseToolDeclared 三参），备忘防回归。

### 门禁④ 活模型 E2E——单列候 CTO 协调窗（不阻验收结论）

- **环境缺口（实测）**：trimodel 网关 127.0.0.1:3333 未监听（netstat 无行+curl 000）；本会话 TRIMODEL_API_TOKEN 未注入。
- **机械面半实证（通道态临时实例日志，`blindspot-result.log` B2e 段）**：TRILC_CHANNEL_MODE=1 实例 `[trilc] lead agent registered (channel mode): 组长` + `heartbeat runner started (2 agents)`；寄信入件后组长 agentLoop **真被唤醒起跑**（trimodel-client STREAM msgs=2→msgs=5 两轮、fallback 链 19 模型遍历）——「入件即醒→eventDriven 单 turn」机械链路通；仅 keys fetch failed（chat 模型全链调用失败）止于模型面。全链真跑（寄信→组长醒→letter_deliver 真投→台账留痕）候 CTO 协调窗补跑。

### 门禁⑤ 盲区探边（五项，19 条观察；结论均非阻塞，判级建议候 CTO 裁）

脚本+读数：`evidence/lg-026-p2/blindspot.ts` + `blindspot-result.log`（B5c 修正复验 `b5c-fix.ts`）。

**B1 envelope from 缺省=actor 的自报伪造面——审计自报一致性面（非权限提升）**：实证 actor='组长' 显式伪报 envelope.from='BOD' → 新信封 from 落 'BOD'、新信封台账 send 行 actor='BOD'，与原信 escalate 行真实 actor='组长' 背离。ACL 仍拦白名单外（非提权）；属 token 信任域内「信封显示寄信人 vs 实际操作人」可背离。建议 P3 写信面统一 from=actor 不可覆盖，或 from≠actor 时补第二留痕字段。

**B2 eventDriven 与 cron 面并发唤醒竞态——无真竞态，防重面实证**：node:sqlite 同步 API+JS 单线程，无真并发写竞态；「并发」8 路 deliver 同一信 → 恰 1 ok / 7 illegal_transition（唯一投递执行者防重面）；并发 8 路寄信 seq 2..9 无重复无抛错；通道态组长注册在场时寄信×5 内联唤醒+wake 洪泛×10 → 全 202+healthz 200 稳定。

**B3 payload 恶意指令 prompt injection 残余面——结构性提示面风险，缓解在位**：恶意 payload（指令伪装/role_override）落库为纯数据不执行；白名单五工具后无 shell/file 逃逸面；残余=诱导组长滥用 letter_escalate（升级链疲劳）与 send_letter（组长名义群发）。缓解在位：systemPrompt 形式复核约束+终裁升级权 COS 人工闸+minTier 清单。结构性风险无法根除，P3 可考虑升级速率上限/群发限额。

**B4 端点 priority 非法值静默归急件——同族口径不一致（吞错）**：实证寄信端点 priority='紧急' → 400 invalid_priority 显拒；escalate 端点 envelope.priority='紧急' → 200 且新信封静默落 '急件'（app.ts 三元缺省）。实害低（升级链语义=急件合理），建议统一为显拒 400 或文档化缺省。邻接口径备忘：寄信响应蛇形 letter_id/seq_no（手工构造）vs 查询/流转响应透传 store 驼峰——同一 API 面两种字段风格，P3 文档化契约定型。

**B5 CHECK 约束兜底——在位（含一处设计现状记录）**：letters.priority/status 两枚 CHECK 拒非法值实证；ledger.letter_id 外键兜底（ghost 信拒）；ledger.action 无 CHECK（合法信存在时任意 action 字符串可写）=设计现状（escalate_denied 等经 appendLedger 内部原语写入，无外部写面；token 内直库写不在威胁模型）。

## 质量门禁评估

| 派工令门禁 | 结果 |
| --- | --- |
| ① 独立重测 | ✓ 全过（624/626 逐字吻合预期+移开法复证+现场还原） |
| ② 端点黑盒 | ✓ 38 断言全绿（ACL 四格/原子性/wake 幂等/fail-closed/重放） |
| ③ minTier 跨仓黑盒 | ✓ 15 断言全绿+g1 只读复证+TriCompany 零改动 |
| ④ 活模型 E2E | △ 单列候协调窗（环境不备；机械面半实证；派工令出口不阻结论） |
| ⑤ 盲区探边 | ✓ 五项齐，19 条观察，全非阻塞，判级建议候裁 |
| 边界（只验证不改源码/TriCompany 只读） | ✓ 两仓工作区终验干净 |

**三分法：CONDITIONAL_PASS**。四门禁全过、无阻塞性缺陷；条件项=门禁④活模型面覆盖率缺口（候 CTO 协调窗补跑后可升 PASS）。观察项判级建议：B1/B3/B4+M12 单列候裁（B4 邻接口径统一或文档化建议 P3 批内定夺；B1/B3 缓解在位可后置 P3；M12 为防回归备忘）；B2/B5 无行动项。

## 使用依据

- 验收对象：TriRLC dev `05b2d84`（diff 基线 48244a2..05b2d84：store.ts 批 A O4 strftime-Z+normalizeTs / O2 读侧容错、批 B LEAD_AGENT_ID+ESCALATE_ACTOR_ALLOWLIST+appendLedger、lead-tools.ts 140 行五工具 minTier:'heartbeat'、heartbeat-runner eventDriven、app.ts 端点五件 4164-4360+组长注册 4602-4630+强制原子版 4299-4330）；TriCompany `e64aa4c`（permissions.ts canUseToolDeclared / tools.ts RegisterOptions.minTier）
- 证据九件：`TriCompany/docs/test/evidence/lg-026-p2/`（endpoints-blackbox.ts+log / mintier-blackbox.ts+log / blindspot.ts+log / fullreg-run1.log / fullreg-run2-moved-aside.log / b5c-fix.ts）
- 复现命令：三件单跑 `node --import tsx --test test/<file>.test.ts`；全量 `npm test`；黑盒三脚本 `npx tsx <evidence>/<script>.ts`（于 TriRLC 根执行；mintier 需脚本目录 node_modules junction → TriRLC node_modules/@tricompany/agent-core）
- 噪音记录：盲区脚本同进程双实例引发全局 registry shell_exec 覆盖警告（脚本环境噪音，非产品缺陷——单实例部署形态只注册一次，组长清单纯度由干净进程 M1-M3 证明）；contract-resolver 对 ceo-chief-of-staff contract v3.1 unsupported 提示（TriCompany 合同版本超前 TriRLC parser，与验收对象无关，转告项）
- 避峰照旧：LG-025 M0 09-05/08 无冲突
