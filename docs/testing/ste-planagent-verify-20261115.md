# STE 复验卷 · plan agent 化施工（G2 GO 后验证门四门·2026-11-15）

- **seat**：STE（小柯·m-ste）·改后链验证门主责席（CTO 确认链·设计卷 §六A 四门预案）
- **施工面**：FSD 五笔（笔 4=R-HY 双读数非 commit）——a893718（笔 1·plan_scope +426 慢道分诊+agent 调用+五分类投影）/692fce4（笔 2·契约 1.1.0+agent_readings 八键）/4b7a30f（笔 3·test_plan_scope +394·16 案族）/7d090db（笔 5·shift_carry_over 头部 2→6 字段+as_posix+首测试件 7 案）
- **触发**：CTO G2 GO 15:31（提前 17:00 毕线 90min）·复验窗 15:31 起 20 分钟毕
- lastSyncedAt: 卷面时戳锚=git commit 时戳（零手打·D-47 增补款正形）

## 门 1 · 门禁独立重跑（log 落盘 .fade/ste-verify-20261115/）

| 面 | 读数 | 对表 |
|---|---|---|
| cognition 全量 | **Ran 204 tests·OK**（23.7s·ste-gate-cognition-v1 log） | 181 基线+16+7 数学闭合·与 CTO 毕报同值独立验 |
| validation 族 | **Ran 438·FAILED (failures=5, skipped=1)**（55.5s·ste-gate-validation-v1 log） | 基线闭合·五案名逐字零漂移（vs ste-gate389-v3 昨基线） |

既有失败逐族归因（独立验非转抄）：frontmatter parity（employee_source_kit）/lg024 test_6（signed piece diff）/lg025 test_1（manifest value prefix）/seats pipeline 双案（entry_level_session_body_thirteen+manifest_claude_code_targets）——五名与昨日基线逐字一致·基线既有族·非 FSD 施工新引入。

## 门 2 · 23 新案清点+值面复核

- 清点：test_plan_scope 44=28 既有+16 新（4b7a30f）·test_weekly_plane_shift 7 首件全新（7d090db）——数学闭合
- 抽 11 案值面复核（全值面断言形·非键存在性抽验）：fail-closed 四态（malformed 越值域→failed_fallback keep／low_confidence 0.4<0.6／URLError code=0 段不炸／TimeoutError call_count=1）·五族投影表（annotation 值面）·双向断言协作（M∪K=S counts）·**快道回归钉（migrate={fast-live} 零改直证）**·上界 15（call_count=15+第 16 skipped）·closeout 门·carry 三标注（值面+既有键零动）·契约键族（1.1.0+十键+结构门 []）·顶层域·笔 5 头部四字段（机械刷新时刻+继承链历史零动+CARRY 计数器 bump）

## 门 3 · 两断言组（CTO 勘正形执行）

- **组 A（plan agent 化域·reasons）**：agent_readings 八键族现役实锚（692fce4 diff 直读：tree/domain/family/confidence/reasons/source/plan_family/annotation）+五态串五案全覆盖（agent_output_malformed/agent_low_confidence/agent_call_failed/skipped_over_limit/migrate_closeout_conflict）+plan.json 留痕直证
- **组 B（rubric 判卷域·reason_codes）**：现役存活三实锚（plan_scope L775 行内键/L487 返回签名/L210 注释）——「既有字段零动」值面验真·subjective-score.json 评分窗面静态链接成立（I3 机械锚维持）

## 门 4 · 判定

**PASS**（候 CTO G3 确认链）——零阻塞零回退。

非阻塞注记：
- N1：timeout 零重试=「_call_agent 无循环实现保证」人工锚·mock 只断单树单次（上界案 call_count=15 为循环旁证·低危）
- N2：勘正面五键→现役八键（增 domain/plan_family/annotation）——判据执行按八键·设计卷组 A 文案微勘候后补

## 使用依据

- CTO G2 GO 令 15:31+验证门四门预案（设计卷 §六A·76cdf64e8 勘正形）+CTO 键名勘正 14:44（组 A/B 分拆）
- 施工笔四：a893718/692fce4/4b7a30f/7d090db（TriCompany 仓在链 HEAD=7d090db 实勘）
- 基线：昨日 cognition 181（b350f9c 面）+validation 438/5/1（ste-gate389-v3）

—— STE 小柯（m-ste）·〔commit 时戳锚〕
