<!-- sourceOfTruth: TriCompany/docs/test/ | syncMode: local-only | lastSyncedAt: 2026-09-11T14:45+0800 -->

# LG-035 P1 门禁交付报告 — TriModel policy 策略面（STE 小柯）

- 门禁结论：**CONDITIONAL_PASS**（无阻塞性缺陷，覆盖充分；三项非阻塞候 CTO 确认后可转 PASS，见 §四）
- 对象：TriModel commit **8e9b6c9**（FSD 交付，8 文件与 CTO 令文清单逐项一致，实盘核验 ✓）
- 门禁件：TriModel commit **462453f**（`test/policy.gate.evaluation.test.ts` + `test/policy.gate.e2e.test.ts`，492 行）
- 门禁 spec：`lg-035-p1-trimodel-policy-gate-spec.md` v0.4（执行态）
- 时点：2026-09-11 14:15（开工令）→ 14:45（本报告），全链当日闭环

## 一、全量回归读数（全量读数纪律）

| 项 | 读数 |
|---|---|
| P1 前基线 | 31/31 pass / 0 fail（npm test，node v22.21.1） |
| FSD 交付卷 | 48/48（基线 31 + FSD 新增 17，CTO 转述；本席独立复跑确认） |
| **门禁后全量** | **73/73 pass / 0 fail / 0 skip / 17 suites，~11.7s**（FSD 48 + STE 门禁 25） |
| 稳定性 | 全量三连跑（14:38/14:41/14:47）均 73/73 |
| `npm run check`（tsc --noEmit） | 绿（exit 0） |
| eslint（门禁件） | **0 error**（46 warnings 均 no-floating-promises 类，与全仓既有风格一致；全仓先在债 11 error/219 warnings 系基线遗留，非本席引入，未处置） |
| 既有失败逐族归因 | 基线与交付卷零失败族。过程中出现过 **3 fail 事件一宗**：根因=本席 e2e 与 daemon-poll 两文件在 node --test 并行执行下互抢 repo-root policy.json（daemon-poll init 拉到 e2e R1 写入值 + e2e R1 重启遇 daemon-poll after 清库）——**本席自竞争，非 P1 实现缺陷**；修复=两文件合并单生命周期，修复后三连绿 |
| 运行态卫生 | 测试后 repo-root policy.json=缺席（快照协议生效），无残留 |

## 二、验收锚三条实测

| 锚 | 实测 | 结果 |
|---|---|---|
| ① UI 可配置策略（PUT roundtrip） | E2E：PUT→GET 回读一致；`/ui` 200+text/html+页面内容断言；穿越探针（raw `../` 与 `%2e%2e`）403/404 无泄漏 | ✅ |
| ② 按窗切换（17:59/18:01 或等价时点） | L1 边界族独立复测（start 含/end 不含、跨午夜四点、构造 UTC 瞬时映射上海墙钟）+ E2E「窗含/不含 now」双轮 PUT-GET 翻转等价法（契约允许口径，未真实等墙钟） | ✅ |
| ③ daemon 轮询拉新值 | **真链达成**：真 TriModel server（interval=1s）+ 真 TriRLC `key-cache.ts`（子进程跨仓加载）+ 真 HTTP 轮询——双向实测（策略翻转→daemon 拉新并 `applyKeyCacheToEnvironment` 落 env；空集复位→daemon 拉回 env default）。stub 两处注明：stagger `Math.random→0`、S3 明文+tmp dataDir。spec 定义 Tier M/R 之上，Tier R 语义等价达成（原排程候窗项就此销） | ✅ |

## 三、门禁覆盖明细（25 件）

- **L1 evaluation（10）**：U3 [start,end) 定谳边界、U5-U8 跨午夜四点、U9 优先级、U10 数组序、U11 无策略回退、U14 时区构造瞬时三件（18:00 缝/午夜缝/非上海时区跳过）、U15 fail-safe（坏 JSON/坏 shape/缺席/目录路径四路不抛+savePolicy 原子性）。
- **L3 E2E（15）**：锚③-a init、P4 netstat 回退护栏、T1 keys 鉴权不受 Q6 影响、P3 空态、P4 无鉴权 PUT、锚② 翻转、锚③-b daemon 拉新、P7 空集 PUT、锚③-c daemon 拉回、U12 API 400、F1 探针、T8 UI+穿越、F2 探针、L3-R1 重启持久、P6 旧路由回归。

## 四、发现清单（均非阻塞，候 CTO 裁）

| # | 发现 | 定性 | 候裁选项 |
|---|---|---|---|
| F1 | **零长窗 [18:00,18:00) PUT 200 入库**（spec U13 预期 400）——`validatePolicyShape` 不拒、`evaluatePolicy` 永不命中 | 行为无害（永不命中、不影响生效面），spec-impl 分歧 | 修实现（PUT 400）或修 spec（承认合法零长窗语义）；门禁断言现钉观测值，裁决后单边翻转即红 |
| F2 | **413 路径不可达**：>1MB body 被 `req.destroy()` 直接断连（实测 ECONNRESET，无任何 HTTP 状态码）；`readRawBody` 标记的 `statusCode:413` 无消费方 | 防御功能在（内存有界、请求被拒），但 commit message 宣称的「413 防御」观测不到，客户端拿到的是连接重置非 413 | catch 块消费 `err.statusCode` 或 destroy 前先写 413；或接受现状并在文档改口 |
| F3 | Q5 空策略 GET 形态与裁决字面有差：实现返回 `object+policy{version,schedules}+effective`（env-default 预览对象，含 evaluated_at），裁决字面为 `effective:null` | 「200+空数组非 404」精神完全满足，effective 预览信息量更大 | CTO ack 字面偏差接受现状，或令 FSD 对齐字面 |
| T1 | **测试基建**：node --test 默认并行跑文件，repo-root policy.json 存在跨文件竞争——本席两文件已合并根治自竞争；**残余 FSD `policy.test.ts` backward-compat 用例读方竞争窗口**（实测三连绿未触发，窗口小但非零） | 测试基建风险，非产品缺陷 | 建议 `package.json` test 脚本加 `--test-concurrency=1`（一行，串行代价 ~10s），或 FSD backward-compat 用例加同款快照协议——候 CTO/FSD 裁 |

## 五、覆盖缺口如实声明

1. **U14 宿主污染检测上限**：本机时区 UTC+8 与 Asia/Shanghai 同相，若实现误读宿主墙钟本机测不出；已用构造 UTC 瞬时映射断言尽力覆盖，**跨宿主增强建议 sg 侧复跑一次门禁件**（零改动，`npm test` 即可）。
2. 真实 17:59→18:01 墙钟观察未自动化（等价时点法覆盖，CTO 令文允许口径）；如需人工真时点观察另立验证窗。
3. 锚③为「真 server+真 key-cache 模块+真 HTTP」链路；完整 TriRLC daemon 进程级（initKeyCache 在真实 daemon 启动路径中的接线）验证候窗，本验证未触及 daemon 进程装配面。
4. 三候裁域（强断/密钥写面/sg 暴露）FSD 未触、本门禁未测——与令文口径一致。

## 六、门禁结论

**CONDITIONAL_PASS**：锚三条全部实测通过、全量 73/73 三连绿、无阻塞性缺陷、三候裁域未越界；F1/F2/F3/T1 四项非阻塞候 CTO 裁决后转 PASS。质量读数以本报告与 TriModel commit 462453f 为锚。

## 七、使用依据

- TriModel：commit 8e9b6c9（实盘 `git show` 核验）、commit 462453f（门禁件）、`npm test`/`npm run check`/`npx eslint` 现跑读数（2026-09-11 14:16-14:47）
- TriRLC：`src/config/key-cache.ts` 实读（锚③机制）
- CTO 令：13:58 派工 / 14:07+14:09+14:15 三轮裁决 / FSD 交付通报
- spec：`lg-035-p1-trimodel-policy-gate-spec.md` v0.4（本席维护，Q1-Q7 全闭）
