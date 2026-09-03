# TriCompany 工程纪律集（三端通用）

> sourceOfTruth: TriCompany/docs/workflow/engineering-disciplines.md
> syncMode: source-only
> lastSyncedAt: 2026-09-03（D-16 初稿立+D-13 条 4 勘误：ST↔STE（SeniorTestEngineer）、FSD/STE 随批改破例〔LG-029〕；前批：D-13/14/15 新立+BL 席+D-15 v2）
> 性质：跨域工程纪律（编排层/TriLC/TriMC 员工通用）——从编排层会话记忆升级为公司资产。员工知识工作区同步路径：合同/培训文档引用本文件。

## 为什么有这个文件

纪律最初在编排层（本地研发仓 claude code）会话记忆中沉淀，但 TriLC/TriMC 侧员工不可见——**跨域通用纪律必须落在 TriCompany 真源**，三端员工经各自知识通道读取。

## 纪律条目

### D-01 subagent 落盘纪律（2026-08-17，三次事故提炼）

长任务 agent context 耗尽时，**口头"已落盘"不可信**（总结文本先于写盘生成，断点常落在两者之间）。

- agent 侧：**先写文件、后写总结**——总结必须带文件路径 + 行数/大小证据
- 收稿侧：**三查**（文件存在 / 内容规模 / 与报告口径一致）后才采信
- 长任务（50+ 项/多文件）分段落盘（每 ~20 条），断点可续
- 兜底：发现未落盘直接接续生成（机械转化类最快），不返工原 agent

### D-02 cron job state 卫生（2026-08-17，weekly 三夜未触发根因）

手动改 cron job state 时**禁抹 `nextRunAtMs`**——引擎靠它排期，缺失=永不调度。只 patch 目标字段；改 cron 表达式后重算 nextRunAtMs；诊断口诀：cron 型 job 不触发先查该字段。

### D-03 daemon 重启纪律（2026-08-16）

重启 TriLC daemon 走 `trilc stop` → `.cmd` 拉起两步（pidfile 权威路径），禁裸杀进程（pidfile 与监听进程错位→新旧进程身份混乱→"补丁没生效"假象）。

**v2 增补（2026-08-28，LG-002 首跑 T3 失败复盘）**：`setx` 后**经 shell 直启的进程继承本 shell 的 env 快照**（读不到 setx 新值）——daemon 与扩展宿主同律。重启前必须在会话内显式从注册表读入新 env（或以读注册表的方式拉起），否则 token/配置类变更出现"已 setx 却 401"的假故障。

**v3 增补（2026-08-28，LG-012 restart 崩循环复盘，FADE-006 重建体提案采纳）**：dist 形态服务（gitignored 构建产物）的 restart 前置检查必须含两项——①dist 完整性 ②node_modules 符号链接目标存在性。**对 gitignore 构建产物仓做 reset/re-checkout 类操作后必须重建 dist**（旧进程内存存活会长期掩盖潜伏损坏，"8-26 起首次 restart 必炸"即此形态）。实施：TriMC restart 前置检查入 runbook；TriModel 类仓重检出 ops 附加 npm run build 步骤。

### D-04 时刻引用纪律（2026-08-17，编排层报时错 8 小时根因）

上下文混存本地时刻与 UTC ISO 时间戳（teammate 消息/日志 `Z` 后缀）——**报时刻前必现查系统时钟**，禁止从上下文时间戳外推；引用 ISO 时间戳必须认 `Z` 并按本地时区换算（中国 +8）。

**v2 增补（2026-08-24，CEO 质询"时区时间不准"复盘）**：报时三要素——**现查、标注、不外推**。① 凡报时标注读数时刻与来源（如"09:25 北京（09:25:15Z 实测）"）；② 禁止用早前读数外推"现在几点"（外推 + 会话隔夜续读 = 错小时级表象；根因是陈旧引用，非钟不准——当日实测三方钟 NTP 级精准）；③ 机器链路（cron/commit/.shift-ade 时间戳）不依赖人肉报时，报时仅是沟通注释。防线配套：TriMC 服务器 cron job clock-skew-check 每小时自动钟差告警（>60s 邮件 + healthz degraded 双通道）。

**v3 增补（2026-08-27，FADE 值班误报"僵了 8 小时"复盘）**：**换算一次、单一时区帧内比较**。日志/时间戳一律先换成北京时间再进入叙述；禁止把 UTC 数值与北京时钟读数直接相减得"滞后时长"（01:18Z 对 09:24 读出 8 小时即此病灶——实际只差 6 分钟）。跨时区推理时强制自问：两个数是否同一时区帧？

**v4 增补（2026-08-28，CEO 提案：双轨时刻制）**：时刻呈现按**受众分轨**——
- **机器轨**：JSON 合同（envelope check_time / 评分卷宗 / registry / 审计文件）与需字典序排序的字段，一律 ISO8601 UTC Z（`2026-08-28T15:12:47Z`），不改；
- **人读轨**：面向 CEO/员工呈现的 markdown 报告、树 resultNote、战役记录、log.md 表格、通知正文——一律北京时间对齐（`2026-08-28 23:12 +08`），可括注 UTC 原值（`(15:12Z)`）供机器复核；
- **衔接件**：§2.7 节点收口报告的 ```json 机读核心走机器轨，散文叙述走人读轨——同一报告内两轨并存合法，但同一句内禁止混用。

### D-05 git index 共享卫生（2026-08-14，三次 index 污染提炼）

多 agent 共享仓：统一 `git add <明确路径>` + `git commit`，禁 `git commit -- <path>`；commit 前三查（status/cached diff/log）。

### D-07 live entry 派生壳纪律（2026-08-19，live entry 评审裁决）

live entry（`.github/agents/*.agent.md`）是员工 contract 的**派生加载壳**——信息真源收敛到 contract（三端可读），live entry 只承载当前宿主（Copilot-host）发现面。**禁人工直接编辑 live entry**：改动一律走源侧（source-agents 五件套/contract）后经 `source_publish_check --publish-agents` 发布；hash 不一致时下次 publish 覆盖 + 审计留痕（防双真源漂移）。三层语义：名册=决策真源、contract=信息真源、live entry=适配面。退役时点=TriMC 正式宿主切换（不设独立退役项）。

### D-06 共学周记记录纪律（2026-08-18，W34 首写违规立册）

「记入周记/共学」类动作**先查规范再动笔**：必读 prompt 固定格式（`TriMetaverse/.github/prompts/项目级 AI 共学周记.prompt.md`）+ 归档 README + **最近一个已存在周**的周记（格式随周演进，禁止跨多周翻旧模板）；条目用固定五件结构（现象/具体表现/解决方案/问题影响 + 当前经验{项目经验,模型自查}）；落当周目录、只追加不重写；内部工程台账（commit 索引）不入册。完整动作规范（Qualify 四问/Plan 三查/Close 五查/终态）：`TriMetaverse/docs/workflow/operating-records/项目级 AI 共学周记/ade-journal-recording-spec.md`；完整 ADE 正典链：登记（CLI begin 生成 runId）→ agent Qualify/Plan（语义四问 + entry.json）→ DCE（CLI qualify/append，格式由代码保证）→ **Agent Close Skill（读回语义裁决 approved|escalated）→ Close CLI（校验裁决 + run 链 + 五查 → 终态 APPROVED/ESCALATED）**——agent 收口在前，CLI 收口在后，CLI 是裁决的校验者不是发起者。执行体：`TriMetaverse/scripts/journal/journal-cli.mjs`。

### D-08 git hook 内跨仓操作必须 unset GIT_DIR 系变量（2026-08-27，FADE hook pull 全静默失败）

git 给 post-receive 等 hook 进程注入 `GIT_DIR`（指向裸仓），优先级高于 `git -C` 的目录探测——hook 里对**其他**工作仓执行 fetch/rebase 会全部打回裸仓且零报错。行为规则：hook 脚本 shebang 后立即 `unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES`；子进程继承干净环境一并得救。

### D-09 含中文的 .ps1 必须 UTF-8 带 BOM（2026-08-27，fade-watch 解析崩溃）

Windows PowerShell 5.1 对无 BOM 文件按 ANSI/GBK 解码，中文注释/字符串乱码可吞引号与花括号（"string is missing the terminator" 类解析错误）。pwsh 7 无此问题。行为规则：含非 ASCII 的 .ps1 写完立即补 BOM（`[IO.File]::WriteAllText($p, [IO.File]::ReadAllText($p,[Text.Encoding]::UTF8), [Text.UTF8Encoding]::new($true))`），提交前用 powershell.exe 最小调用冒烟一次。

### D-10 共享裸仓权限卫生——混合身份 push 后的自愈（2026-08-27，p0fix1 push 被拒复盘）

多身份（root 终端 + fleet 服务）共写同一批 bare 仓时，高权用户 push 会落下 root:root 新对象段，低权用户随后 push 撞 objects Permission denied。行为规则：① bare 仓统一 `core.sharedRepository=group` 且属主收敛 fleet 组；② 无法消除混合身份时，部署周期性自愈（sg-server crontab `bare-perm-heal`：每 15 分钟对所有 /srv/git/*.git 执行 chgrp -R fleet + chmod -R g+w；**共享锁文件一并治理**——fade-hook.lock 类文件归属随推送者漂移，须 chgrp+chmod 666 或预建共享位）；③ 遇 push 无故被拒先查裸仓对象目录属主分布再查网络/凭证。

### D-11 审批按命令前缀整串匹配——禁复合 cd 形态（2026-08-27，p0fix1 三轮 blocked 根因判定）

CC 工具白名单规则（如 `Bash(git status:*)`）对**整条命令串做前缀匹配**：`cd /repo && git status` 以 `cd` 开头→零命中→拒。首次怀疑方向（Task 子代理不继承 --allowedTools）经 sg 判定实验证伪——子代理完全继承白名单；真因即复合形态。行为规则：① 编排 spawn 必须把工作仓路径直接作为会话 cwd（orchestrate_tick 已按 tree.repo 字段路由），使执行体用裸命令即可；② 执行体跨仓用 `git -C <路径> …`；③ BRIEF_V2 已固化该铁律；④ 排查"工具被拒"类问题先取**原始拒绝文本**分层定位（审批层 vs 权限层 vs 上游），禁凭表象归因。

### D-12 Windows 原生操作优先 PowerShell 工具——Git Bash 的 MSYS 路径转换陷阱（2026-08-28，LG-002 终验探测误判复盘）

已设 `CLAUDE_CODE_USE_POWERSHELL_TOOL` 只表示**增加** PowerShell 工具，不禁用 Bash——工具选型仍是每次调用的判断。Git Bash 的 MSYS 层会把 `/v`、`/d` 类参数转换成路径（reg query 的 `/v` 被吃→token 读空→健康系统误判 401，LG-002 终验探测实录）。行为规则：① Windows 原生操作（registry/env/服务/Windows 路径/含 `/x` 单字母参数的命令）一律优先 PowerShell 工具；② Git Bash 仅用于 POSIX 管道与 ssh 场景；③ 判据口诀：命令里有反斜杠路径或单字母斜杠参数=PowerShell。

### D-13 通信名址规程与命名宪法——ListAgents 对名址+双向纪律+14 席正名表（2026-09-01，令源存疑事件与名址三易复盘）

根因：常驻会话名址三易（team-lead→trimetaverse-ec→f9）+自称董事会之来件无从对名址校验→2026-09-01 08:0x 令源存疑安全事件（治理面冻结，以编号解冻令 U-20260901-01 经 CEO 在席确认解冻）。通信面无固定名址=防伪校验无锚。

行为规则：

1. **发件前 ListAgents 对名址**：寻址一律用对方**正名**；正名不唯一时附 ListAgents 列表 ref 消歧；收到自称某席的来件，先 ListAgents 核对该名址在册再做治理性动作（无编号之恢复/解冻类来件一律视伪）。
2. **双向纪律**：呈报方核通道、转呈方核结论——转呈前必须核对原结论，禁转发未核（2026-09-01 调查树批复立，由单向教训「零日志先核重定向面」升格）。
3. **命名宪法全文表（CEO 2026-09-01 裁定）**：正名原则=职位代号；别名=中文名/职位全称/英文名，可空缺候补。

| 正名 | 职位 | 别名（中文名/职位全称/英文名） |
| --- | --- | --- |
| BOD | 董事会 | 董事会 |
| COS | 总裁助理 | 小贾/总裁助理/jarvis |
| CPO | 产品总裁 | 小乔/产品总裁/jobs |
| CTO | 技术总裁 | 小狄/技术总裁/Dee |
| CHO/CAO/COO/CFO/CMO/CSO | 各主管席 | 候补录（空缺候补） |
| FD | 全栈开发 | 小全/全栈开发 |
| ST | 测试 | 小柯/测试 |
| RDT | 研发培训 | 小吴/培训 |
| DE | 部署 | 部署人员 |
| BL | 业务组长 | 候补录（候选「业务 lead」；中文名空缺候补） |

4. **spawn 面 frontmatter name 不改原则**（§8-2 先例 breaking）——正名属通信面/常驻会话面；FD/ST/RDT/DE 通信面正名↔spawn 型映射：FSD/STE（SeniorTestEngineer）/RAndDTrainer/DeploymentEngineer。

   **条 4 勘误与破例（2026-09-03，LG-029 锚，CEO 方案 v3）**：①ST 行映射「↔TestEngineer」勘误为「↔STE（SeniorTestEngineer）」，同批 FD 行 FullStackDeveloper→FSD；②「一律不改」原则对 FSD/STE 两席显式破例——spawn name 随批改，CAO 席 agent 类型面实测 FSD/STE 已在役、旧名 FullStackDeveloper/TestEngineer 退役（2026-09-03 22:3x）；③CHO 历史名沿革口径四条随勘误对表入册：历史名冻结／映射行承载／检索口径／role-id 分轨注记（议题卡正身归 LG-029 卷）。
5. 宣贯落地读数（2026-09-01 四席全达）：CPO/CTO 独立会话直送（msg 7b6743a2/a3fe4295）；FD d433c445/ST 24fff145 双送达。各员真源 description 批量补别名关键词=CHO 域同批（LG-024 fast-follow 同窗候排期）。

**BL 席增设注记（2026-09-02，BOD 裁决全包采纳，LG-026 P0 件）**：BL=Business Lead（业务组长），daemon 常驻信件督办岗，挂 COS 麾下（项目负责人管理）。格式冻结：`BL-<项目代号>`（per-project 授名候业务出现再授，现在只冻格式不预留名——按需授名）。首任惯例（CAO 裁 2026-09-02）：**单组长起步=正名 BL 无后缀**——席位正名本身即寻址名，`BL-<项目代号>` 仅候多项目分席按冻结格式授名（GEN 非项目代号，不采用，防格式外 token）。扩展评估触发线（满足其一）：日均 200 封×连续 7 天／并行活跃项目≥3／组长单点故障积压事故≥1 次。实际岗位启用（合同/五件套/binding）时走 CHO 侧 handoff 流程，本条只登记通信面席位。

### D-14 跨仓相对路径审计须显式声明审计根（2026-09-01，LG-023 二次勘误案复盘）

根因：fade-protocol-spec.md/fade-registry.md 实盘在 `TriCompany/docs/engineering/`，历代审计（董事会实勘/晨检/r5 三人组五源重建）均从 TriMetaverse 根扫起→三重审计集体误判「无实盘」；被引用路径系 TriCompany 仓根相对路径而审计根错位，被审计方边编辑边宣告「不存在」的自证锚一并如实入卷。

行为规则：

1. 跨仓相对路径审计**先显式声明审计根**（从哪个仓/目录起扫），结论句必须带根声明；
2. 「无实盘/不存在」类结论**必须全仓扫过且扫对根**后才可下（「答不存在前必须全仓扫过」纪律的跨仓扩展）；
3. **实测同文≠因果**：找到同名/同文文件≠找到因果镜像正身，镜像件勘误须另核渊源（镜像件勘误同族教训同批入册）。

### D-15 CPO+CTO 双席联审门与开发测试分派枢纽（2026-09-01，CEO 新规程立法）

规程内容（CEO 2026-09-01 裁定，即刻生效向前适用）：

1. **必要功能和模块=CPO+CTO 双席联审门**——单席不得自决；
2. **开发与测试分派枢纽=CTO**——FD 承接开发、ST 承接测试，一律从 CTO 手里派，**不接受越手直派**。

宣贯落地读数（2026-09-01 四席全达）：CPO/CTO 独立会话直送（msg 7b6743a2/a3fe4295）；FD d433c445/ST 24fff145 双送达。中枢路由领受：功能/模块令先送联审再分派。

注：宣贯令原建议号位 D-12 已被 2026-08-28「MSYS 路径转换陷阱」条占用——号位勘误（D-12→D-15）随入册留痕。

**v2 增补（2026-09-02，LG-026 重审复盘教训制度化；BOD 六裁点⑥采）——联审门第四核查项「能力底座核查」**：业务规则定稿前，产品+技术**双签**核对该宿主面是否具备规则所需的**通信/持久化原语**。案源：LG-026 双席联审 premised on「组长可通信」未被识破——R 面 agent-core 系 CC 移植子集无跨会话消息能力，而收发督办枢纽五项核心职能（收/发/督办/状态流转/升级）全部以跨会话通信为底座，岗位设计 0% 达成（**结构性 0**：非实现质量打折，是能力底座缺失致岗位本身不成立）。行为规则：①联审清单固定第四项=能力底座核查，业务规则定稿前双签过门；②前提性能力假设（「XX 可通信/可持久化/可调度」类）必须显式核对宿主面实盘，禁默认成立（「会话」被降格为「函数调用」即本例盲区形态——agent-core 被当 CC 等价物评估）；③核查结论随联审记录留痕。号位裁定（CAO 裁）：**D-15 v2 就地增补，不立 D-16**——联审门定义保持单条目可查照，本文件 D-03/D-04 版次增补先例同构。案源正身：`TriMetaverse/docs/execution/lg026-re-review-report.md` §一.2/§二问 0/§三。

### D-16 约束面内容域路由与发布控制（2026-09-03，LG-028 立法，BOD 七点全裁；初稿候 CHO/CAO 验证）

**载体（裁①）**：双轨——规则本体=本条；内容×席/宿主映射=governance-memory-index GID 条目（三环收口：内容 owner 提交→索引 owner 收口写入→MEMORY.md 指针行；条目稿随立法件交付索引 owner）。三约束面定性=**派生渲染面**，禁人工直改。

**三面分工（裁②③）**：

1. **CLAUDE.md=客观结构面**：只许装客观结构描述+路由导航+分权制中性指针行，迁后三段式（客观结构/路由导航/分权制中性指针行）；域知识（具体模块产品事实/技术细节/测试口径/当前排期/命令集本体/文件惯例细则）一律随席路由，本面只留指针。
2. **session 面=域知识主承载**：迁出域知识落各席 session 面新立「D 类域知识族」；spawn/session 同一规则真源两渲染目标，无第三形态（裁⑤）。
3. **spawn 面=发现与骨架面**：name/description/tools 骨架供宿主发现，域知识不入。

**正面判据（防扯皮条款）**：许留结构面=模块布局与兄弟仓路径／职责域 owner 矩阵摘要／registry 路由优先序／迁出件路由导航指针／分权制中性指针行；禁止=上条域知识清单内容正文。

**迁出四件+指针质量（裁③）**：Common Commands→CTO 面；File Conventions→CAO 纪律册（本文件附录，候实施落位）；Weekly Operating Records→COS 面；v0.9.x 双轨→BusinessStrategy 面。**指针质量=验收读数项**：每条迁出件在 CLAUDE.md 保留路由指针行（两要素=目标面正名+真源路径），按指针一步可达真源，失联=验收不过（防迁出即失联）。

**维护控制（裁①⑥）**：三面唯一合法更新通道=源侧改→管线发布；**CLAUDE.md 入渲染管线（裁「入」，依据=CEO 令控死原文）**——真源=`TriCompany/docs/project-sources/trimetaverse-claude-md.md`（GID-05），管线=FADE-002 双条目（在册）。三面管线并轨表：

| 约束面 | 真源 | 发布管线 |
| --- | --- | --- |
| CLAUDE.md | TriCompany/docs/project-sources/trimetaverse-claude-md.md（GID-05） | FADE-002 双条目（在册） |
| session 面（.claude/hub/*.session.md） | source-agents 合同 sessionBody | claude-session 渲染条目（LG-023 在册，LG-024 扩席在飞） |
| spawn 面（.claude/agents+.github/agents） | source-agents 五件套/contract | source_publish_check --publish-agents（D-07 通道） |

**处置**：违手改=hash 不一致时下次 publish 覆盖+审计留痕（D-07 处置三面通用化）。

**分权制自指改造界限（首执行件）**：只改叙述人称、不改分权制语义——语义真源=ceo-chief-of-staff-authorization-matrix（GID-08a）+岗位合同；施工走 CLAUDE.md 真源+FADE-002，禁直改发布面。

**非溯及（裁④）**：已产出已签批不返工；新内容候本条适用；勘定并行；机械件照常。

**platforms 强制声明（裁⑦，CPO 条款）**：本条映射面 GID 条目必须显式声明 platforms 全键，禁依赖缺省（与索引头「权限与审批/工具选型/daemon 与进程」强制声明条款同族，扩及路由类条目）。

**向前适用+存量临时件**：生效向前适用；存量手作 hub session 件（含 CAO 本席 session 文件）走 LG-024 管线化/退役路径销账，销账前维持 interim 标注勿作真源；LG-024 管线批对表并入实施排期（裁⑥连带）。

**状态**：初稿候 CHO/CAO 验证（验证窗 COS 安排；FADE 发布链控死+publish_check 纳门=分段闸下批 2 放行前置）；验证读数落本状态行，通过前本条不作生产级援引。

## 维护规则

- 新纪律事故复盘后追加（格式：D-XX + 日期 + 根因一句 + 行为规则）
- 源侧为本文件；三端员工运行时经知识通道引用——不各自复制（防多真源）
