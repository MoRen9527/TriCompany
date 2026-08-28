# TriCompany 工程纪律集（三端通用）

> sourceOfTruth: TriCompany/docs/workflow/engineering-disciplines.md
> syncMode: source-only
> lastSyncedAt: 2026-08-27（D-08/09/10 新立，D-04 v3 增补）
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

## 维护规则

- 新纪律事故复盘后追加（格式：D-XX + 日期 + 根因一句 + 行为规则）
- 源侧为本文件；三端员工运行时经知识通道引用——不各自复制（防多真源）
