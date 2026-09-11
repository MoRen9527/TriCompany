<!-- sourceOfTruth: TriCompany/docs/test/ | syncMode: local-only | lastSyncedAt: 2026-09-11T15:30+0800 -->

# LG-035 P2 门禁 Spec — TriModel 密钥写面/跃迁接线/build 链（STE 小柯 预备版 v0.1）

- 状态：**预备**（预告派工 CTO 2026-09-11 15:26+0800；正式开工候 FSD 回稿接口）
- 对象仓：`D:/Code/ai/TriModel`（P1 终态 HEAD=11b8ebc）
- 三工作流：A=策略跃迁→MMC/RMC bundle 接线（先勘拓扑，可能降级勘验报告）；B=密钥写面 keys.enc；C=build 链 copy 步骤+dist/ui 存在断言

## 一、P2 前基线（2026-09-11 15:27+0800 现查）

- P1 收口态全量：**73/73 pass / 0 fail / 0 skip**（串行，`--test-concurrency=1` 已固化）——即 P2 前基线，交付后任何红=新引入逐个归因
- 门禁件在库：`test/policy.gate.*.test.ts` 25 件（P1 资产，P2 交付须回归不红）
- P2 接缝现势：`keys.enc`/`secure` 在 src 零命中（FSD 未落盘）；`UI_ROOT` 指向 `dist/ui`（编译态）而 `build=tsc` 不 copy ui/——C 工作流接缝实锤

## 二、拓扑勘验（A 工作流）

| 端 | 位置 | 现势 |
|---|---|---|
| 生成端 | TriRLC `src/company/sync-bundle.ts` | 五维 bundle（company/model/keys/employees/project）纯函数；I/O 链在 `init-sync.ts` |
| 接收端 | TriMMC `src/config-sync/`（apply.ts / default-model.ts / types.ts） | 契约双端同构；**`default-model.ts` 已存在**=策略跃迁维度的现成落点 |
| RMC 端 | TriRMC `packages/`（仅 agent-core） | **未见 bundle 消费者**——A 若涉及 RMC 侧，接线面尚缺 |

**密钥纪律（SEC-20260813-001，A×B 交叉护栏）**：bundle schema 递归拒绝 `api_key/apiKey/secret/token` 非空字符串字段（任意深度）；keys 维白名单仅 `provider/ready/fingerprint/baseUrl`；密钥材料零传输只有指纹（SHA-256 前 8 位）。**若 P2-A 接线=true，跃迁触发的 bundle 写门禁必断言不泄漏密钥材料**（尤其 B 落地 keys.enc 后，跃迁链若触及 keys 维）。

**A 降级判据（候选，候 CTO 裁）**：MMC 侧 `default-model.ts` 现成+生成端纯函数现成 → MMC 向接线可行性高；RMC 侧无消费者 → 若 FSD 回稿确认 RMC 接线超出本批，A 降级为勘验报告（本节即勘验底稿）。

## 三、B 工作流门禁单测族（核心）

复用参照：TriRLC `src/config/key-encryptor.ts`（AES-256-GCM+PBKDF2 机器指纹，S2 存储）——TriModel 侧自研或跨仓复用候 FSD 契约。

| # | 用例族 | 断言要点 |
|---|---|---|
| KB1 | 加密 roundtrip | PUT secure 合法密钥 → 落盘 keys.enc **密文形态**（明文材料不得出现在磁盘文件字节中）→ 读回解密 → GET keys 反映新值 |
| KB2 | 覆盖优先 .env | keys.enc 与 .env 同时存在时的优先序（候契约 QB2）：逐请求求值语义对齐 P1 default_model 模式 |
| KB3 | UI masked 只写 | masked 值（如 `sk-ab****`）回写不得覆盖真实密钥（把掩码当真值落盘=污染）；masked 展示不回传全量材料 |
| KB4 | 损坏 fail-safe | keys.enc 坏 JSON/坏密文/缺文件 → 回落 env + warn + **绝不 crash**（对表 policy.json loadPolicy 同款模式） |
| KB5 | 鉴权面 | 密钥写面鉴权模型候裁（QB1）——**密钥写面系 P1 三候裁域之一转正，鉴权强度门禁从紧预期** |
| KB6 | A×B 交叉 | 若 A 接线=true：跃迁→bundle 写后对 bundle 全文递归扫密钥材料字段=零命中+keys 维仅白名单字段+指纹形态合法 |

## 四、C 工作流门禁

1. **build copy 步骤**：`npm run build` 后 `dist/ui/index.html` 存在（copy 步骤进 build 脚本）；编译态 `UI_ROOT` 解析路径实跑可达。
2. **CI 断言**：`.github/workflows/ci.yml`「Verify dist integrity」步增 `dist/ui/index.html` 断言行（现缺——已勘）。
3. **CI 触发面观察（如实报，非本席修域）**：CI 仅触发 main push/PR，现分支 dev 不触发；**CI lint 门禁当前即红**（11 先在 errors + 269 warnings 超 `--max-warnings 200` 阈值，其中 46 warnings 系本席门禁件与全仓同风格所致）——P2-C 落地时 lint 健康度需 CTO/FSD 一并裁决（eslint config 豁免 test 或修先在债）。

## 五、P1 教训沿用（固化项）

1. **串行已固化**：`--test-concurrency=1` 在 package.json，P2 新测试文件自然继承；涉及 repo-root 运行态文件（keys.enc 同 policy.json 性质）的新门禁件仍维持**单文件单生命周期+快照恢复协议**。
2. **基线先行**：FSD 回稿后、落码前重取基线读数（现 73/73 为锚），交付后逐失败归因。
3. **骨架避红绿污染**：P2 门禁骨架**暂不落 `TriModel/test/`**（会被 glob 拾取且 import 不存在模块直接红）——drop-in 骨架随本 spec，候接口落位。

## 六、开放问题清单（候 FSD 回稿/CTO 裁）

| # | 问题 | 影响用例 |
|---|---|---|
| QA1 | A 接线=true/降级勘验报告的判定；跃迁定义（PUT 时点？窗口翻转时点？两者？） | KB6、bundle 写断言 |
| QA2 | bundle 通道形态（写盘路径/watch 文件/直接调 TriRLC 生成端？）mock 断言的注入点 | ② 跃迁一次写断言 |
| QB1 | 密钥写面鉴权模型（admin token？仍 loopback 无鉴权？）——P1 候裁域转正 | KB5 全族 |
| QB2 | keys.enc 覆盖优先序（vs .env，vs env vars）；读取时机（启动一次/逐请求） | KB2 |
| QB3 | 加密方案与密钥派生（AES-256-GCM+机器指纹对表 TriRLC？独立 passphrase/env master key？） | KB1/KB4 |
| QB4 | UI masked 语义（掩码回写拒绝 or 忽略 or 透传真实值？） | KB3 |
| QB5 | keys.enc 落点与 gitignore（repo root 同 policy.json？） | KB1/KB4 环境隔离 |
| QC1 | C 的 copy 步骤落点（package.json build 串 or ci.yml 步内） | §四 |

## 七、Drop-in 骨架占位（候 QB1-QB5 实例化）

```
TriModel/test/keys.enc.gate.test.ts        — KB1-KB5（tmp 目录隔离，禁触 repo-root）
TriModel/test/policy.transition.bundle.test.ts — QA1/QA2 mock 通道一次写断言+KB6 密钥泄漏扫描
CI 断言行（ci.yml Verify dist integrity）   — test -f dist/ui/index.html
```

## 八、维护规则

本 spec 随 FSD 回稿升版（Q 表闭合→执行态）；交付门禁报告落 `lg-035-p2-trimodel-gate-report.md`。
