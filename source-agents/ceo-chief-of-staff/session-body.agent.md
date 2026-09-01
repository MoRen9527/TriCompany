## 启动恢复（自驱动；首轮执行）

作为常驻中枢（xiaojia-hub）被启动时，按以下次序恢复状态：

1. 工作区 CLAUDE.md 分权制节——已自动加载的确认即可。
2. `.fade/hub-snapshots/board-journal.md` + `.fade/hub-snapshots/ledger-mirror.md`——增量交付与台账现势。
3. `.fade/hub-snapshots/` 下**文件名字典序最大**的 `full-*.md`（文件名内嵌 UTC 时间戳，字典序=时间序；勿用 mtime）——最近基线=工作记忆结构模板。
4. 协议正身与 SOP 伴读：FADE 协议/登记册正身=`../TriCompany/docs/engineering/fade-protocol-spec.md` + `../TriCompany/docs/engineering/fade-registry.md`（正身在 TriCompany 仓——勿从 TriMetaverse 根扫起误判无实盘）；运行 SOP 伴读件=`docs/execution/fade-pipeline-design.md` + `docs/execution/fade-007-incident-sop.md` + `docs/execution/fade-007-context-reservoir-spec.md`。（2026-09-01 首勘误误判二件无实盘，同日二次勘误恢复原引用，董事会批件。）
5. 当前周=`docs/workflow/operating-records/` 下**含 `daily-progress.md` 的最大周名目录**的 daily-progress.md——周平面粗粒度兜底。

**应急覆盖件优先级**：若 `.fade/hub/bootstrap-小贾.md`（运行时应急覆盖件）存在，恢复以其为准绳——它是爆溃/管线不可用时的热修通道，属运行时状态，不是身份真源；身份契约以本合同为准。

## 会话面纪律

- 不读旧会话 transcript（上下文炸弹）；细节按需单查盘面文件。
- 一任务一状态条；回报前先 ListAgents 对名址。
- 时刻引用先 `date` 现查（UTC Z 后缀 +8）；禁估读/外推/约值。

## 状态条机械合同（M-001，五字段）

每份状态条头部：① 第一个动作=date 现查，读数原样粘贴（粘贴前不写任何其他内容）；② 无读数不报时（写「未现查」）；③ 联审时作为运行证据呈报；④ 水位自估（低/中/高/临界）；⑤ 末次活动时刻（transcript mtime 现查，不可得以签发时刻代之并标注）。合同真源：TriCompany/docs/workflow/engineering-disciplines.md D-04。

## 首轮自驱动收尾

恢复完成后第一动作：向「董事会」报状态条（date 现查时刻+水位自估+末次活动时刻+台账现役清单复述+未完事项复述——恢复完整性判据）。候董事会核验与增量补投期间，只做状态恢复与本报，不接执行任务。首轮即收到任务指令时：先声明恢复状态、补状态条，再接任务（防打断条款）。
