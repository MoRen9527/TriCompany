<!-- sourceOfTruth: TriCompany/docs/testing/ | syncMode: local-only | lastSyncedAt: 2026-09-11T21:25+0800 -->

# LG-035 UI 重设计门禁 Spec — STE 预备版 v0.1

- 状态：**预备**（CTO 21:19 预研三点；正式实例化候 FSD 回稿）
- spec 正身：TriModel docs/execution/88ecedd2（**磁盘现未found——FSD 在飞嫌疑**，落库随批对表；本骨架据 CTO 令文三点+COS 定稿五断言先行）
- UI 现势：3333 静态单页 vanilla（1fb16a1 后含三子栏：栏头三态/候选池 masked+眼睛/当前使用只读单选器）

## 一、P2 secure 端点退役改写（410）

| 原用例 | 退役后对表 |
|---|---|
| KB5-a/b/c 三态（PUT/status 503/401/200） | **410 Gone + 人话指引断言**：响应体含指引文案（指向卡片条目 key 通道；禁内部术语——410 body 文案规格候 spec 正身/FSD 契约） |
| KB1 密文落盘 | 迁移：卡片条目 api_key at-rest 永密文断言（trimmc-card.ts AES-256-GCM 逐条目语义，1fb16a1 已实现——GET 端点明文水合仅 COS 通道，门禁断言落盘文件零明文） |
| KB2 overlay 优先 | 迁移：卡片 key 语义下的解析序断言（keys.enc→卡片条目过渡期并存语义候 FSD 契约） |
| KB3 masked 拒 | 已由卡片 PUT 前置实现（含 * 拒，1fb16a1+三断言）——本席对表断言保留转卡片端点 |
| KB4 fail-safe | 迁移：卡片读损坏→回落+warn 绝不 crash 同族断言 |
| KB6 零泄漏扫描 | **SEC 不回退族全保留**：transitions 白名单扫描/卡片文件零明文扫描/admin 三态族（迁移到卡片端点同构复用） |

## 二、jsdom 首启五断言（COS 定稿）

选型勘定：**jsdom devDep（约 3MB，装批候 FSD/CTO 签）**。判据=能断言真实渲染 DOM：五断言全落 jsdom 能力边界内（class/hidden 属性/disabled/selectedOptions/click 派发/全文本扫描）；轻量 DOM mock 否决（断言的是 mock 非 UI，违反判据）。能力边界如实注记：jsdom 无真实渲染层——布局/截图类不覆盖（Playwright 真浏览器案已在 COS 盘点档，候后续批）。

| # | 断言 | jsdom 实现点 |
|---|---|---|
| U-UI1 | 无令牌态=连接设置自动展开+引导可见+数据面板禁用 | section hidden/class 态+引导文案 textContent+面板 disabled 属性 |
| U-UI2 | 令牌保存→自动重拉 | click 派发→断言 fetch 调用发生（stub 全局 fetch 记录调用） |
| U-UI3 | 下拉有值 | options 长度+值集合对 model-catalog 五名 |
| U-UI4 | 提交可达 | 提交 click→PUT 请求发出断言（fetch stub 捕获 URL/method/body） |
| U-UI5 | TriMMC 卡片区域通道+结构词汇零出现 | document.body.textContent 全扫描（含 JS 运行时注入——真 DOM 优势） |

## 三、三遍走查清单（v3 §7）进门禁

- **可自动化子集**→checklist 断言进门禁件（设计符合=DOM 结构断言复用 §二；任务流=U-UI2/4 行为链；破坏流=错误态渲染断言——410/401 文案与禁用态）。
- **非作者手测硬门**：登记为 declared-manual 清单（视觉/交互手感/真实浏览器项），**COS 预走查首用**——本席门禁报告单列 manual 清单与自动化覆盖边界，不越权代签。

## 四、开放问题（候 FSD 回稿/spec 正身落盘）

| # | 问题 |
|---|---|
| Q1 | spec 正身 88ecedd2 落盘对表（当前磁盘未found） |
| Q2 | 410 响应体人话指引文案规格 |
| Q3 | keys.enc→卡片 key 过渡期并存语义（KB2 迁移断言依据） |
| Q4 | jsdom devDep 装批签发 |
| Q5 | 卡片端点三件路径/schema 细节（1fb16a1 已有代码可预读，回稿后以终稿为准） |

## 五、维护规则

FSD 回稿后升执行态（Q 表闭合+骨架实例化 test/ui.redesign.gate.test.ts+keys.secure.gate 退役改写）；SEC 不回退族任何批次不裁撤。
