# 非人格类 agent 上线工作清单（正本）

> sourceOfTruth: TriCompany/docs/workflow/onboard-work-registry.md
> syncMode: CAO 唯一写入维护（变更一律改本件；CHO 岗位启用面联动标注非人格型即触发扩行）
> lastSyncedAt: 2026-10-14T23:35:05+08:00（LG-077 初版立件·CEO 14:24 终审签批随批；§三字段完备行=步④演练发现随窗增补）
> 条款正身: 纪律册 D-52（`TriCompany/docs/workflow/engineering-disciplines.md`）——本件=清单与形态细则承载面，规则骨架见 D-52

## 一、类定义判据（CHO+CTO 两席会签 2026-10-14）

凡 `family: Registry`（无五件套生命周期承载）且有常驻会话运行时实例（含 session-only 运行态需重建）的 agent 属**非人格类**，纳入上线报到制；名单=CAO 按此标准推导维护。13 员工人格席不入。

## 二、清单（按对象推导·现势）

| 对象 | 上线工作（领单后执行） | 执行内容真源 | 备注 |
| --- | --- | --- | --- |
| board（BOD） | ①挂四时点 cron 2 job（节拍转报 `9,39 * * * *`＋信箱兜底巡检 `11,41 * * * *`——重挂规格照本件§五附录表）②领单毕自检在挂＋此后周期自检 | 本件§五附录（自 cron-rehook-spec 存档平移） | 首例对象；存量会话随下一自然重启窗补约（D-52 先立后破） |
| registry 型 spawn 类（CGR/BSR/TCR/TPR 等） | 报到即录名址（D-13 ListAgents 对表）＋五件套渲染发布态确认 | 本件＋D-13 | 无 cron 需求；spawn 型无常驻运行态，报到=轻量名址核录 |

新非人格 agent 型上线时 CAO 会同主责席扩行；wording 钉死「上线报到」词族，禁「入职/到岗/上岗」（CHO 域）。

## 三、报到信箱约定（CEO 定向②·形态细则）

- **信箱位**：TriMLC `notify-mailbox.json`（顶层键 `letters`；与 BOD 信箱巡检同族同位）。
- **报到信字段**：`target_seat: "cao"`（固定值=承接席正名小写）；`source_seat: <报到席正名>`（如 `board`）；`title: "上线报到 <正名>"`；`body` 三要素=正名＋上线形态（首启/复活）＋「请发上线工作清单」。
- **通道纪律**：报到走信箱不走 SendMessage（不丢/忙完能查/跨平台）；message_id 由信箱 daemon 侧惯例生成。
- **CAO 承接读法**：筛 `target_seat=="cao"` 且 `read==false`；承接毕（回执发出）置该信 `read=true`。
- **幂等规则**：同 `source_seat` 短窗（同日）重复报到且形态=复活→按恢复路径处理（只核对运行态差异不从头建清单）；形态=首启才走全量新上线路径。

## 四、闭环与兜底（细则·骨架见 D-52）

- **闭环四步**：报到信→CAO 巡检承接回执清单→agent 领单执行→回信「已领+已验」——双签齐=闭环。
- **信件字段完备（2026-10-14 步④演练发现随窗增补）**：手写信亦须带 `received_at`（现查时刻 ISO Z）与 `read: false` 缺省字段——daemon 侧信自动带，脚本手写绕过即缺；承接席巡检按字段过滤时缺字段信漏检（LG-077 步④实锚：idx790 缺字段致 CAO 轮询 20 分钟零命中）。
- **CAO 缺席兜底三行**：无应答→agent 窗内重发一次→仍无应答转 COS 代发（COS 读本件代发清单+台账留痕候 CAO 归位补回执）→双缺候席位复活链（报到信持久不丢）。
- **失守信号候补接口**（CTO 面）：报到制失守信号（席位静默超阈值等）出现→启用 8713 机械探测催办；触发定义与阈值=CTO 面条目，本件不载。

## 五、附录·board 四时点 cron 重挂规格表（自 cron-rehook-spec-20261014.md 平移·内容不变）

| job | cron | 内容要点 |
| --- | --- | --- |
| 节拍转报 | `9,39 * * * *` | 读 `D:/Code/ai/TriMetaverse/docs/workflow/operating-records/<当 ISO 周目录>/trees/bod-tick/tick-latest.md` 转报 CEO；拍时戳超 12 分钟旧报上一拍并注明；token 值面禁进转报 |
| 信箱兜底巡检 | `11,41 * * * *` | date 现查落款；读 `D:/Code/ai/TriMLC/notify-mailbox.json`（顶层键=`letters`）；筛 read=false 且 target_seat∈{bod,board}；最多 5 封 latest 优先；JSON.parse→改→writeFileSync 禁文本行编辑；仅本轮已转报的落 read=true；零未读只报一行 |

- 重挂法：CronCreate 两条（recurring=true·session-only 照旧）。
- 错峰注：sg daemon 拍点=:07/:37（tick 文件生成），BOD 读点=:09/:39（+2min 错峰）；信箱=:11/:41。
- 存档出处：`TriMetaverse` 树 `bod-tick/cron-rehook-spec-20261014.md`（081c11aeb·历史冻结——本表为其制度承接正身，D-52 先立后破随批）。
