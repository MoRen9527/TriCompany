# 非人格类 agent 上线工作清单（正本）

> sourceOfTruth: TriCompany/docs/workflow/onboard-work-registry.md
> syncMode: CAO 唯一写入维护（变更一律改本件；CHO 岗位启用面联动标注非人格型即触发扩行）
> lastSyncedAt: 2026-10-15T23:40:16+08:00（date 现查·LG-083/084 并案扩附录：§六 上线自检检查单+§七 四 daemon 职责速查与 daemon 边界+§四 自检读数回写细则——CEO 23:03 指认两漏项·CEO 23:36 批并案铸条链·CTO 卷 305017229+CPO 卷 013495240/9adc7167f 素材；前账 2026-10-14T23:35:05 LG-077 初版立件）
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
- **自检读数回写（2026-10-15 增补·LG-084）**：自检/对接检查读数**回执信 body 带读数**，或**回写 progress-snapshot 同族位**（sg 现役形 `/srv/fleet/var/` 非 git 区）——「自检做了」变「自检可查」，CAO 承接时即可见自检结果，恢复态成可审计事实（D-52 自检读数回写款的形态细则面）。
- **失守信号候补接口**（CTO 面）：报到制失守信号（席位静默超阈值等）出现→启用 8713 机械探测催办；触发定义与阈值=CTO 面条目，本件不载。

## 五、附录·board 四时点 cron 重挂规格表（自 cron-rehook-spec-20261014.md 平移·内容不变）

| job | cron | 内容要点 |
| --- | --- | --- |
| 节拍转报 | `9,39 * * * *` | 读 `D:/Code/ai/TriMetaverse/docs/workflow/operating-records/<当 ISO 周目录>/trees/bod-tick/tick-latest.md` 转报 CEO；拍时戳超 12 分钟旧报上一拍并注明；token 值面禁进转报 |
| 信箱兜底巡检 | `11,41 * * * *` | date 现查落款；读 `D:/Code/ai/TriMLC/notify-mailbox.json`（顶层键=`letters`）；筛 read=false 且 target_seat∈{bod,board}；最多 5 封 latest 优先；JSON.parse→改→writeFileSync 禁文本行编辑；仅本轮已转报的落 read=true；零未读只报一行 |

- 重挂法：CronCreate 两条（recurring=true·session-only 照旧）。
- 错峰注：sg daemon 拍点=:07/:37（tick 文件生成），BOD 读点=:09/:39（+2min 错峰）；信箱=:11/:41。
- 存档出处：`TriMetaverse` 树 `bod-tick/cron-rehook-spec-20261014.md`（081c11aeb·历史冻结——本表为其制度承接正身，D-52 先立后破随批）。

## 六、附录·上线自检检查单（2026-10-15 增补·LG-083/084·CEO 23:03 指认两漏项内容面枚举）

报到承接与周期自检的**检查内容枚举**（义务条款=D-52 daemon 层对接检查款；判据数值归 CTO 面条目不入本件）：

| # | 检查项 | 判法（程序化正形） |
| --- | --- | --- |
| 1 | 快照追平 | 读 latest.json 值面断言（LG-082 试点已验证形态） |
| 2 | cron job 挂载核验 | job 清单 API 逐 job：next_run 值面+enabled=1（**禁凭 POST 201 认挂载**·F-3 家族性：受理回执≠会触发） |
| 3 | 信箱可读性 | 程序读箱断言（先验承接链通道——报到链自身依赖信箱，信箱不通=承接链死锁面） |
| 4 | 出向链状态 | outbox 三态/健康面读数断言（对接 Q2 回声流） |

- **程序化纪律**：检查单按 D-55 ①层逐步落检查脚本（断言族输出读数单），非 agent 凭记忆自述「在位」；一期清单化（agent 照单逐项跑命令贴读数）·脚本化（`onboard-daemon-check.sh` 族）归 CTO 面候排另走排程。
- **daemon 层对接检查读数**（healthz 四字段/真触发证据/next_run 在位）判法=D-52 对应款·互引不复制。

## 七、附录·四 daemon 职责速查与 daemon 边界（2026-10-15 盘点·CPO 复核卷转录·随能力演进 CAO 维护）

| daemon | 机位 | 职责要点 |
| --- | --- | --- |
| TriMLC | 8713·本机 | 信箱（notify-mailbox.json）+cron job 群；受宿主电源面约束 |
| TriMMC | 8712·sg | 7×24 mailbox+outbox+ledger「拍存判报」三链全通 |
| TriRMC | 8710·河源服务域 | mcLedger+3 jobs·R 面候选 |
| TriRLC | 8711·本机 | R 面本地+NOTIFY 出向链 |

- **daemon 不入报到制（边界写明·防机制泛化）**：D-52 类定义判据（`family: Registry`+常驻**会话**运行时实例）天然排除 daemon——daemon 是基础设施非 agent，报到信对它是伪需求；daemon 层「上线感知」正形=healthz 活性面（活体优先诊断法机械侧）。此边界防未来「daemon 也该报到」类泛化提案（机制域止于其语义面·同 Q2 红线「收推≠执行」边界逻辑）。
