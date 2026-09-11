<!-- sourceOfTruth: TriCompany/docs/test/ | syncMode: local-only | lastSyncedAt: 2026-09-11T16:07+0800 -->

# LG-035 P2 门禁交付报告 — TriModel 密钥写面/跃迁接线/build 链（STE 小柯）

- 门禁结论：**CONDITIONAL_PASS → 候转 PASS**（四裁已全部落地 TriModel 99f78ca，终读数 98/98 全绿见 §九；候 CTO 合并出 P2 PASS 终报 COS）
- 对象：TriModel commit **57d5df6**（FSD P2 交付，11 文件 635 行，实盘核验 ✓）
- 门禁件：TriModel 本席新增 `test/keys.secure.gate.test.ts`（11 用例）+`test/build.chain.gate.test.ts`（4 用例）+P1 件卫生增补（TRANS_LOG 快照协议）
- 门禁 spec：`lg-035-p2-trimodel-gate-spec.md` v0.3 终版（QA1-QC1 全闭）
- 时点：2026-09-11 15:26（预告派工）→ 15:58（本报告）

## 一、全量回归读数（全量读数纪律）

| 项 | 读数 |
|---|---|
| P2 前基线（P1 收口态） | 73/73 pass / 0 fail（串行） |
| FSD 交付卷 | 86/86（基线 73+FSD 新增 13）——本席独立复跑确认 ✓ |
| **门禁后全量** | **97/97 pass / 0 fail / 0 skip / 23 suites，~20.7s**（FSD 86+STE 门禁 11） |
| 稳定性 | 全量双跑 97/97 |
| `npm run check`（tsc） | 绿（exit 0） |
| lint 增量 | **本席门禁件 0 error**（裁定④ P2 增量零 error 纪律达标）；test 目录残余 7 error 系存量文件（FSD/先在债，按裁定挂技术债另批不混入） |
| 既有失败逐族归因 | 过程三失败事件均本席侧、零产品缺陷：①三态 401-vs-503=repo-root `.env`（dotenv 注入 TRIMODEL_ADMIN_TOKEN，键名实证）→ 三态断言改进程内 handler 实测；②跃迁记录缺席=Windows 双进程同端口瞬态（kill 未落定+重绑，flip GET 打到 lastReported=null 进程）→ 单 boot+killAndWait+新端口根治；③`statusCode`/`status` 属性乌龙一笔。**FSD 实现零缺陷击穿** |
| 运行态卫生 | 全量终跑后 keys.enc/model-transitions.jsonl/policy.json 三件全净（快照协议 ×3） |

## 二、验收锚实测（门禁预研三点）

| 锚 | 实测 | 结果 |
|---|---|---|
| ① 加密 roundtrip+损坏 fail-safe 单测族（B 核心） | KB1 密文落盘（raw 字节零明文）+masked-only 回显+overlay 覆盖 env+无读回 404+status masked-only；KB4 垃圾密文→env 回退+server 存活；KB2 bootstrap 回退链 | ✅ |
| ② A 接线跃迁触发断言（mock 通道） | A 全面降级定谳（bundle 真源 sg /srv/fleet、甲案端点不存在、乙案跨仓越权）；本地半边 transition.ts 实测：policy 翻转→GET keys→jsonl 记录 from/to/source 逐字段正确+**KB6 全文扫描：字段白名单严守+零密钥材料**（SEC-20260813-001 红线绿） | ✅ |
| ③ build 断言 | `npm run build:verify`（tsc+copy-ui+dist 断言脚本）全链绿+dist/ui/index.html 落位+编译态 UI_ROOT 可达 | ✅ |

三态鉴权（KB5，QB1 裁定）实测：进程内 handler 矩阵——未设 token=**503 disabled**（fail-closed ✓ 且不建库）/无凭据=401/凭据对=200/未知 provider=400。

## 三、发现清单（均非阻塞，候 CTO 裁）

| # | 发现 | 定性 | 候裁 |
|---|---|---|---|
| F1-P2 | ~~服务端 API 不拒掩码形态 api_key~~ **已修落地 99f78ca**：api_key/base_url 含 `*` → 400 回显污染防御（纵深第二道闸+三断言测试+套件顺序无关化） | 已闭 | 本席探针已翻转 200→400 断言，绿 |
| T-A1 | ~~model-transitions.jsonl 未入 .gitignore~~ **已修落地 99f78ca**（.gitignore 增行） | 已闭 | ✓ |
| T-C1 | ~~ci.yml Verify 步未含 dist/ui 行~~ **已修落地 99f78ca**（ci.yml 增 `test -f dist/ui/index.html` 断言） | 已闭 | ✓ |
| T-D1 | build.chain 门禁前轮一红未复现（spawnSync 偶发，多跑绿） | flaky 候选，观察项维持 | 复现再查 spawnSync timeout/shell |

## 四、门禁外知悉项（CTO 通报对表）

- ADMIN_TOKEN 生产值=运维面未配置期，503 即预期态——与门禁 fail-closed 实测语义一致 ✓
- UI 无自动 E2E（手测步骤在 FSD 卷）——本席未覆盖 UI 交互面，如实声明

## 五、覆盖缺口如实声明

1. UI 密钥页签交互（masked 展示/只写）无自动化——手测域（FSD 卷），与上条同源。
2. keys.enc 跨机解密失败路径（GCM auth fail=机器迁移场景）以损坏密文同路径覆盖，未做真双机实验。
3. A 面 bundle 生成端消费（TriRLC 读 transitions 末条）系 P3 提案域，本批不测。
4. U14 时区盲区 sg 复跑候办（P1 遗留）继续有效——P2 门禁件同 beneficiario。

## 六、过程教训（本席侧，沿 P1 台账延续）

1. **dotenv 注入盲区**：repo-root `.env` 经 dotenv（override:false）注入子进程，env 删不净——凡「缺省态」断言涉及 .env 可定义的变量，一律进程内 handler 实测或显式 env 钉值。
2. **Windows 双进程同端口瞬态**：kill 未落定+SO_REUSEADDR 重绑可致请求跨进程漂移——boot 前等 exit 事件、每 boot 新端口。
3. **运行态文件清单随批次增长**：policy.json→keys.enc/model-transitions.jsonl，门禁件快照协议须同步扩（本席 P1 件漏 TRANS_LOG 已自纠——P2 过程失败③之一）。

## 七、收尾增补终验（commit 8cce59a，2026-09-11 15:58 CEO 增补：UI 密钥框眼睛切换）

- **实盘核验**：8cce59a 在库，UI-only（1 文件 10 行，端点零变更 ✓）。
- **两步手测位源级核验**：①默认掩码态=`k-key` input `type="password"`（ui/index.html:63）✓；②点击明文态=`k-eye` onclick 切 type password↔text+👁/🚫 图标互换（:145-149）✓。**交互点击级未由本席执行**（本会话无浏览器），仍在 FSD 卷手测步骤内——如实声明。
- **合规边界核验**：存量密钥展示路径零变更（status 页签保持尾 4 位 masked、无读回路径；diff 范围内无 status 渲染改动）✓。
- **回归**：全量 97/97 复跑绿（post-8cce59a）+运行态三件净 ✓。

## 八、使用依据

- TriModel：commit 57d5df6（FSD P2 交付）、8cce59a（CEO 增补 UI 眼睛切换）、99f78ca（四裁收尾）、本席门禁件 commit、`npm test`/`npm run check`/`npx eslint` 现跑读数（2026-09-11 15:40-16:06）
- 令源：CTO 15:26 预告派工+15:31 四裁+15:40 交付通报+15:58 增补通报+16:04 收尾通报；CEO 三裁 B 方案（FSD 令文转述）
- spec：`lg-035-p2-trimodel-gate-spec.md` v0.3 终版

## 九、四裁收尾终读数（2026-09-11 16:06+0800）

| 项 | 收尾落地（99f78ca） | 本席对表 |
|---|---|---|
| F1-P2 掩码第二道闸 | api_key/base_url 含 `*` → 400 回显污染防御 | 门禁探针 200→400 翻转+非存储断言，绿 |
| T-A1 gitignore | model-transitions.jsonl 入 .gitignore | ✓ |
| T-C1 ci.yml | Verify 步增 `test -f dist/ui/index.html` | ✓ |
| T-D1 flaky | 观察维持 | 复现再查 |

**终读数**：99f78ca+门禁件翻转后全量 **98/98 pass / 0 fail**（与 CTO 预期一致）；tsc 绿；门禁件 lint 0 error。FSD 顺带修套件间 keystore 耦合（独立路径顺序无关化）——测试基建健壮性增量，本席复跑确认。

**结论**：四裁全落+终读数全绿，候 CTO 据本节出 P2 PASS 终报 COS。

- TriModel：commit 57d5df6（实盘核验）、门禁件与 P1 件卫生增补（本席 commit）、`npm test`/`npm run check`/`npx eslint` 现跑读数（2026-09-11 15:40-15:57）
- 令源：CTO 15:26 预告派工+15:31 四裁+15:40 交付通报；CEO 三裁 B 方案（FSD 令文转述）
- spec：`lg-035-p2-trimodel-gate-spec.md` v0.3 终版
