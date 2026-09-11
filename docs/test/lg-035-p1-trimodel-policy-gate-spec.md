<!-- sourceOfTruth: TriCompany/docs/test/ | syncMode: local-only | lastSyncedAt: 2026-09-11T14:05+0800 -->

# LG-035 P1 门禁 Spec — TriModel policy 策略面（STE 小柯 预备版 v0.1）

- 状态：**预备**（正式开工候 FSD 回稿；本 spec 为门禁骨架，接口细节候 FSD 交付后由 CTO 补充裁决）
- 派工源：CTO 令 2026-09-11 13:58+0800（预告派工，实施=FSD 并行进行中）
- 对象仓：`D:/Code/ai/TriModel`（v0.2.0，node:test + tsx，node v22.21.1）
- daemon 消费方：`D:/Code/ai/TriRLC/src/config/key-cache.ts`（锚③基座）

## 一、范围与验收锚

对象：TriModel P1 增量四件——policy 策略面、`/v1/config/policy` 读写、`/v1/config/keys` 的 `default_model` 策略化、`/ui` 静态页。

CTO 验收锚三条 → 测试化：

| 锚 | 令文 | 门禁测试化 |
|---|---|---|
| ① | UI 可配置策略（PUT roundtrip） | E2E：PUT `/v1/config/policy` → GET 回读逐字段一致；`/ui` 页可达且 200 |
| ② | 策略生效后 GET `/v1/config/keys` 的 `default_model` 按窗切换（断言对 17:59 deepseek / 18:01 glm，或等价 mock 时点） | L1 单元边界族 + L3 E2E 等价时点法（见 §四，不真实等待墙钟） |
| ③ | daemon 轮询实测拉新值（TriMLC 或 TriRLC key-cache 真轮询，或 mock 轮询断言注明） | 双档：Tier M mock 轮询（CI 默认，注明）+ Tier R 真链路（交付验证跑一次），见 §五 |

## 二、P1 前基线读数（2026-09-11 14:00+0800，FSD 落码前锚定）

- `npm test`：**31/31 pass / 0 fail / 8 suites**（duration ~0.9s，exit 0）
- `npm run check`（tsc --noEmit）：**exit 0 零错误**
- 现有测试文件：`test/client.test.ts`、`test/relay-sandbox.test.ts`、`test/usage.test.ts`（另有 `_probe_tmp.ts` 临时探针残留，非 .test.ts 不入 glob——观察项，非本席清理域）
- 归因基线意义：**基线零失败** → P1 交付后全量回归中任何 fail 均为新引入，逐个归因到 P1 改动，无既有失败族需豁免。

## 三、现势代码事实（门禁设计依据，2026-09-11 勘）

1. **`src/api/keys.ts:28` `DEFAULT_MODEL` 为模块级常量**（import 时冻结，`env TRIMODEL_DEFAULT_MODEL ?? 'tmv-deepseek-v4-pro'`）→ 策略化必须改逐请求求值。**门禁捕获的缺陷形态：PUT 策略后 GET 仍返回旧值（常量未解冻）**。
2. **`src/server.ts` 请求处理器只收集 headers 不读 body** → PUT 带 JSON 体需 FSD 新增 body 读取。**E2E PUT roundtrip 天然兜住此缺失**。
3. `src/api/routes.ts` 现有 4 路由（/health、/v1/models、/v1/config/keys、POST /v1/config/keys/refresh），404 fallback；`/v1/config/policy`、`/ui` 均未存在（与 policy 零命中一致——FSD 未落盘）。
4. 鉴权现状：keys 面 Bearer `TRIMODEL_API_TOKEN`，未配置/不匹配 → 401。policy 面鉴权模型候 FSD 契约（骨架按继承 keys 面设计）。
5. TriRLC key-cache（锚③机制，`key-cache.ts`）：`initKeyCache` 启动即拉一次 → 随机 stagger 0-60s 后起定时器 → 间隔=服务端下发 `refresh_interval_s`（默认 900s）→ `doRefresh` 更新缓存并触发 `onKeyCacheUpdated` 回调；`applyKeyCacheToEnvironment` 将 `defaultModel` 落 `env.TRIMODEL_DEFAULT_MODEL`。**注意：POST `/v1/config/keys/refresh` 仅服务端重读 env，不构成向客户端的推送通道，不能当锚③依据。**

## 四、测试矩阵

### L1 单元 — evaluatePolicy 边界族（门禁核心件）

可测性前置要求（候 FSD 接口谈判点）：**evaluatePolicy 须接受可注入时钟（now 参数）**；若实现硬编码 `Date.now()` 则边界族不可测，须要求改造。

| # | 用例 | 输入 | 预期 |
|---|---|---|---|
| U1 | 窗内命中 | 单窗 [18:00, 22:00)→glm，now=20:00 | glm |
| U2 | 切换点前 | 同窗，now=17:59 | 非该窗 model（deepseek，锚②断言对前半） |
| U3 | 切换点归属 | 同窗，now=18:00 | 按契约定死并显式断言（骨架按 [start, end) 假设=glm；FSD 契约确认项 Q3） |
| U4 | 切换点后 | 同窗，now=18:01 | glm（锚②断言对后半） |
| U5 | 跨午夜窗·窗内深夜 | 窗 [22:00, 06:00)→glm，now=23:30 | glm |
| U6 | 跨午夜窗·窗内凌晨 | 同窗，now=00:30 | glm |
| U7 | 跨午夜窗·末边界 | 同窗，now=05:59 | glm |
| U8 | 跨午夜窗·出窗 | 同窗，now=06:00 | 非 glm |
| U9 | 双窗重叠优先级 | 窗A [18:00,22:00)→glm 优先级1，窗B [20:00,23:00)→deepseek 优先级5，now=21:00 | deepseek（高优先级胜） |
| U10 | 优先级相等确定性 | 两同优先级重叠窗 | 契约定义行为并断言（拒绝配置 or 稳定序——Q4） |
| U11 | 无策略向后兼容 | 空策略集 | 回退现行行为：`env TRIMODEL_DEFAULT_MODEL`，缺省 `tmv-deepseek-v4-pro` |
| U12 | 畸形时间串 | start="25:00" 等 | 契约定义（倾向 evaluate 防御性跳过该窗+PUT 层 400 拒收，Q4） |
| U13 | start==end / 非跨午夜逆序窗 | [18:00,18:00)、[20:00,10:00) 且无跨午夜语义 | 契约定义（Q4） |
| U14 | 时区语义 | 同一 now 两种时区表达 | 契约钉死窗口时间基准（本地 or UTC）后断言（Q2——跨午夜用例必须先钉此时区才有效） |

### L2 API 契约（in-process dispatch 级）

- P1 PUT 合法 policy → 2xx；GET `/v1/config/policy` 回读逐字段一致（roundtrip，锚① API 半边）
- P2 PUT 畸形 policy → 4xx 拒收（具体码候契约 Q4），拒收后 GET 维持原策略（拒收不半写）
- P3 GET policy 无策略时形态（空集 200 or 404——Q5）
- P4 鉴权：无/错 token → 401（按继承 keys 面假设，Q6）
- P5 策略化生效点：PUT 含 now 的窗 → GET `/v1/config/keys` `default_model` 即变（同进程内，无需等轮询）——**捕获缺陷形态 1（常量冻结）**
- P6 无策略时 GET keys 的 default_model 与 P1 前基线行为逐字段一致（向后兼容回归护栏）

### L3 E2E 冒烟（真 HTTP server，锚①②载体）

步骤骨架：随机高位端口+测试 token 起 server → `/health` 200 → PUT policy（窗含 now → glm）→ GET keys 断言 `default_model==glm` → 反向 PUT（窗不含 now）→ GET 断言回退基线值 → GET `/ui` 断言 200 + content-type text/html → teardown。

- 锚②「17:59/18:01」等价实现：**不真实等待墙钟**，以「窗含 now / 窗不含 now」两轮 PUT-GET roundtrip 等价覆盖时点切换语义，测试报告注明等价性（CTO 令文已预留「或等价 mock 时点」口径）。真实 17:59→18:01 墙钟观察不进自动化门禁（不可 CI 化），如 CTO 要求人工真时点观察另立验证窗。
- 捕获缺陷形态 2：PUT 无响应/挂起（body 未读取）。

### 锚③ daemon 轮询（双档）

**Tier M（CI 默认，断言注明 mock）**：测试内建 mock config-plane（可控 `default_model` 序列 + `refresh_interval_s: 1`）→ 真 TriRLC `initKeyCache(mockUrl, tmpDataDir, token)` → stagger 规避（stub `Math.random`→0；不可 stub 则 90s 超时窗）→ 观察点=`onKeyCacheUpdated` 回调携带新 `defaultModel`，并断言 `applyKeyCacheToEnvironment` 后 `env.TRIMODEL_DEFAULT_MODEL` 更新 → `stopKeyCache` 清理 + tmp 目录清理。**报告与断言消息注明「mock 轮询」性质。**

**Tier R（真链路，交付验证手动跑一次）**：真 TriModel server（`TRIMODEL_KEY_REFRESH_INTERVAL_S=2`）+ 真 `initKeyCache` 指向它，其余同 Tier M，90s 超时窗容忍 stagger。落读数进交付报告。

dataDir 一律用 `fs.mkdtemp` 临时目录，禁触真 daemon `keys.json`。

## 五、交付时全量回归计划（全量读数纪律）

1. TriModel：`npm test` 全量 + `npm run check`，报四项读数（total/pass/fail/skip）+ 逐失败归因（基线零失败 → 全部归因 P1）。
2. TriRLC：`npm test` 全量读数（TriRLC 侧 key-cache 既有测试是否受 P1 影响的回归面；TriRLC 基线在 FSD 交付时先取再跑，避免跨仓漂移误归因）。
3. E2E 冒烟 + Tier R 真轮询读数单列。
4. 结论按三分法：PASS / CONDITIONAL_PASS（列非阻塞缺口）/ FAIL（阻塞性缺陷），报 CTO 裁决。

## 六、开放问题清单（候 FSD 接口，CTO 可补裁决）

| # | 问题 | 影响用例 |
|---|---|---|
| Q1 | evaluatePolicy 模块路径与签名（含 now 可注入？） | 全部 L1 |
| Q2 | 窗口时间基准时区（本地/UTC） | U5-U8、U14 |
| Q3 | 18:00 切换点边界归属（[start,end) 假设？） | U3、锚② |
| Q4 | 优先级相等/畸形策略/逆序窗的处理（拒收 or 定义序） | U10、U12、U13、P2 |
| Q5 | GET policy 无策略形态 | P3 |
| Q6 | policy 端点鉴权模型（继承 keys Bearer？） | P4 |
| Q7 | policy 持久化介质与重启语义（内存 or 落盘；重启后策略是否存活） | L3 增补重启用例 |

## 七、骨架落位策略

骨架测试代码（evaluatePolicy 边界族 + E2E 冒烟）**暂不落 `TriModel/test/`**——现在落盘会被 `npm test` glob（`test/**/*.test.ts`）拾取且 import 不存在的 policy 模块直接污染 FSD 的红绿信号。骨架随本 spec §八交付，候 FSD 接口定签名后落位改后缀生效。

## 八、Drop-in 骨架代码（候接口实例化）

```ts
// TriModel/test/policy.evaluation.test.ts（骨架——Q1 签名定后落位）
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
// TODO(Q1): import { evaluatePolicy } from '../src/policy.js';

// TODO(Q1): 依 FSD 契约实例化 PolicyShape 构造器与 evaluatePolicy 签名
// 用例映射：U1-U14 见本 spec §四 L1 表，逐条落 it()；
// 边界三点半径：17:59 / 18:00 / 18:01；跨午夜四点：23:30 / 00:30 / 05:59 / 06:00。
```

```ts
// TriModel/test/policy.e2e.smoke.test.ts（骨架——L3 步骤已定，候 /v1/config/policy 与 /ui 落盘）
// 步骤：spawn server(RANDOM_PORT, test-token) → health → PUT policy(含now窗→glm)
//   → GET keys 断言 default_model==glm → PUT 反向窗 → GET 断言回退 → GET /ui 200+html → teardown
// 锚③ Tier M 骨架独立文件 policy.daemon-poll.test.ts（mock config-plane + initKeyCache + onKeyCacheUpdated 观察点）
```

## 九、维护规则

- 本 spec 状态字段随门禁进展更新（预备→执行→收口）；FSD 交付后由 STE 实例化骨架并补 Q1-Q7 裁决读数。
- 全量读数与收口结论落 TriCompany/docs/test/ 交付件，报 CTO 工程门禁裁决。
