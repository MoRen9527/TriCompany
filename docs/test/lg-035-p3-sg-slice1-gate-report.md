<!-- sourceOfTruth: TriCompany/docs/test/ | syncMode: local-only | lastSyncedAt: 2026-09-11T17:20+0800 -->

# LG-035 P3-sg 切片 1 门禁交付报告 — 3334 轻改写转发器（STE 小柯）

- 门禁结论：**PASS（门禁口径内）**——CTO 六点全实测绿、零产品缺陷；唯一覆盖缺口=真 Node18 实测（已按 17:08 令文预案接受静态+标注，sg 冒烟补）
- 对象：TriModel commit **8c9ce45**（5 文件 605 行，实盘核验 ✓）
- 门禁件：`test/proxy.gate.test.ts`（7 用例，进程内双服务器+mock 上游捕获）
- 时点：2026-09-11 17:08（开工令）→ 17:20（本报告）

## 一、全量回归读数

| 项 | 读数 |
|---|---|
| P3 前基线（P2 收口态） | 98/98 pass / 0 fail（串行） |
| FSD 交付卷 | 113/113（+15）——本席独立复跑确认 ✓ |
| **门禁后全量** | **120/120 pass / 0 fail / 23→? suites，双跑稳定**（FSD 113+STE 门禁 7） |
| `npm run check` / lint | 绿 / 本席门禁件 0 error |
| 既有失败归因 | 过程 1 宗确定性失败=**本席门禁件自身类型错误打翻 build:verify**（tsconfig include 含 test/**，build 的 tsc 编译测试文件——类型门禁进 build 的特性即脆性，本席自纠）；另 1 宗=门禁件首版把 deepseek 路由指向真实 api.deepseek.com（哨兵键 401 拒、无实害）——已修为双路由全 mock+baseUrl=mock 断言防回归。**FSD 实现零缺陷击穿** |
| 运行态卫生 | policy.json 快照协议生效，终态净 |

## 二、六点对表实测

| # | CTO 门禁要点 | 实测 | 结果 |
|---|---|---|---|
| ① | 3333 零触碰=结构保证 | git 实证：diff 5 文件无 `src/server.ts`（stat 清单锁证）；运行时隔离：proxy 端口上 `/v1/config/keys` → 405（配置面路由不存在）；`serve:proxy` 独立入口默认 3334≠3333 | ✅ |
| ② | 映射路由四案+两 502 防御 | 纯函数四案：tmv-deepseek→deepseek 端点+DS key+tmv- 剥壳 / tmv-glm→bigmodel+GLM key / 未匹配→no-upstream-route / 匹配缺 key→no-api-key；**最长前缀序断言**（tmv-deepseek 优先于裸 deepseek）；E2E 级：未匹配→502 且 **mock 上游零请求**（不发错 key 到错端点的直接证据）；bad-json→400 | ✅ |
| ③ | SSE 逐字节不碎 | 3 分片×300ms 间隔 mock SSE：客户端收到字节序列逐位一致+分片≥2 未坍缩+**首字节到达早于上游发毕 >150ms（非缓冲时序证明）**+content-length 缺席（真流式） | ✅ |
| ④ | 转发保真 deep-compare | 上游捕获侧逐字段比对：仅 model 改写（tmv- 剥壳）其余字段 deep-equal；x-api-key/authorization 服务端注入=env 哨兵值；anthropic-version 透传；任意客户端 header/connection 不转发；**上游响应的 auth 头不回漏客户端** | ✅ |
| ⑤ | 缺口探针透传保真 | 未知路由 405 形态稳定（error+hint）；观测环 recent_rewrites 字段白名单严守（at/from/to/matched_schedule_id/upstream_prefix）零密钥材料；health 零键值（仅 env 变量名+key_configured 布尔） | ✅ |
| ⑥ | Node18 兼容 | 静态断言：engines === '>=18.20.0' + serve:proxy 入口存在 + 双文件 import 白名单（node:http/https/url/path）+ Node20-only 令牌扫描零命中。**真 18 实测候 sg 冒烟**（本机 nvm 无 18 且 nvm-windows 全局切换危及在飞 13 席 node 进程，按令文预案静态+标注） | ✅（静态档） |

## 三、发现清单

| # | 发现 | 定性 | 处置 |
|---|---|---|---|
| — | **产品面零发现**——FSD 切片 1 实现六点全过 | — | — |
| T-P3-1 | 本席门禁件首版曾把 deepseek 路由指向真实 api.deepseek.com（哨兵键、401 拒、无实害）——转发器类测试必须双路由全 mock | 本席测试卫生，已自纠（baseUrl=mock 断言固化） | 闭 |
| T-P3-2 | build 链编译 test/**（tsconfig include）：测试文件类型错即打翻 build:verify——类型门禁进 build 的特性亦脆性 | 观察（不动，记录在案） | 维持 |
| T-D1 | P2 期 build 门禁 flaky 观察本轮未复现（上轮两败已定性为本件类型错非 flaky） | 观察 | 维持 |

## 四、覆盖缺口如实声明

1. **真 Node18 运行时执行未测**（静态档，sg 冒烟候）——engines 下限 18.20 与 node:https 流式在 18 的实测归 sg 部署窗。
2. GLM anthropic-compat 端点真值（open.bigmodel.cn/api/anthropic）候 sg 实勘（源码注释已标注切片 2 部署窗核对）——本门禁以 env override mock 覆盖。
3. CC 真实客户端（claude code）端到端行为未测——本门禁以协议级请求模拟，真 CC 联调归 sg 部署窗冒烟。

## 五、使用依据

- TriModel：commit 8c9ce45（实盘核验）、门禁件（本席 commit）、`npm test`/`npm run check`/`npx eslint` 现跑读数（2026-09-11 17:08-17:19）
- 令源：CTO 17:08 开工令（六点对表+Node18 预案）；CEO 16:51 开工令（FSD 令文转述）
- 前序：P1/P2 门禁报告（同目录）
