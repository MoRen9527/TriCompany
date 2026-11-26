# 两卷架构·字段对照表（CTO 定稿·2026-11-26）

- sourceOfTruth: 本件（TriCompany/docs/engineering/two-plane-architecture-field-map.md·两卷架构字段归属正身）
- syncMode: write-time
- 承接: CEO 令 2026-11-26（fade-001 内部只做工作·不做进化·改进=任务书定·COS 树协议外部修缮）+进化施工 E1-E5（任务书 bod-taskcharter-evolution-arch-20261126.md·COS 代批）
- 草案源: TriMetaverse b6bd30cec（FSD 产出侧草案·本件定稿）

## §一 · 架构原则（CEO 定谳）

**fade-001 = 工作引擎**（十段链 + 周迁移）——**不做进化**。
- **闭环 A（迁移质量/生命周期）** = score 卷 —— fade-001 内部
- **闭环 B（进化）** = joint 卷 + 独立 evolution-charter 件 —— 外部任务书定·COS 树协议消费

**判据**：score 只留迁移质量与完整度；一切进化指标（改进/修复率/双轨/能力项）归 joint 面或独立进化任务书。

## §二 · score.json（闭环 A·迁移质量）

| 字段 | 归属 |
|---|---|
| `families`（A-H 族 state/score/weight/reasons） | 迁移质量 |
| `rubric_file` / `rubric_version` / `rubric_sha256_16` | 口径版本面 |
| `artifacts_manifest`（逐件 run_id/sha256_16/parse_ok/size） | 产物完整性 |
| `regime_check`（单一 100 制）/ `counts_check`（三面同口径） | 口径核 |
| `cost_attribution`（成本三面/stage/residual/channel_ok） | 成本面 |
| `improvement_block_ref` | **指针桩**（→joint 卷·E2 架构分离） |
| `cross_check`（两卷边界断言面·E5） | 架构分离 |
| `machine/manual/subjective_domain_weight` / `total_*` / `domain_breakdown` / `redline_caps_applied` / `verdict` / `run_state` / `check_time` | 迁移质量 |

## §三 · joint-review.json（闭环 B·进化）

| 字段 | 归属 |
|---|---|
| `faces`（七席 dimension ids + rationale）/ `seat_means` / `ab_columns` | 联审分（A/B 进化轴） |
| `improvement_block {repair{fixed_prev_pending_resolved, fixed_this_round_total, prev_pending, should_fix, whitelist, source}, improvement_rate{per_dim,total_rate}, by_seat, params{min_rate,k}, threshold{min_rate,below,below_count,note}, below_threshold, below_threshold_dims}` | **进化指标主体**（E2 迁入·E4 threshold） |
| `new_discoveries` / `inherited_pending` / `new_discoveries_anchor{count,items}` | 联审发现（下轮 plan 输入） |
| `refill {items(defer_kind/kind_by), missing, items_ok, carried_no_ref}` / `opinions_filtered_invalid` | 意见账回填 |
| `low_dim_coverage` / `evidence_check` / `seat_source` / `anchor_dimensions(read_scope)` | 联审质量 |
| `review_mode` / `opinions_total` / `comparability` | 轮次面 |

## §四 · 独立 evolution-charter 件（E3·外部）

- 落件：`<run_dir>/evolution-charter-<stamp>.json`（round_runner 写面零阻断）
- 形：`{schema_version, charter_id:"eco-<date>", approver_pending:"COS", status, items(capability/exposure 全项), aggregation{capability_items, capability_ratio}}`
- 消费：**COS 树协议**（进化任务书=独立件·非 fade-001 内部）
- charter.json 恒不含 capability 项（`charterTaskOnlyViolations()` 断言·L241/L259）

## §五 · 边界规则（E5 断言形）

1. **两卷顶层键交集**（meta 白名单 `{schema_version, run_id, check_time, round, from_week, to_week}` 外）须 = ∅。
2. **指针桩单侧**：`improvement_block_ref` 仅 score；`improvement_block` 仅 joint。
3. **断言实现** = `score_engine._cross_check_planes(run_dir, score_keys)`（score.cross_check.key_overlap / pointer）·非空=violation。

## §六 · 实现落点（代码侧索引）

| 面 | 落点 | commit |
|---|---|---|
| score 移除三块+ref 桩 | `score_engine.py` L1144 | 2acaa2a（E2） |
| joint 迁入 | `loop_joint_review_spawn.py` `_attach_improvement_block` L309/L1046 | 2acaa2a（E2） |
| threshold 独立字段 | `score_engine.py` L853-859 | 64dca6c（E4） |
| 字段级交叉断言 | `score_engine.py` `_cross_check_planes` L886/L919-920 | 3d65b4a（E5） |
| charter capability 移出 | `charter_generator.ts` L241/L259/L283/L314-323 | 4b75864（E3·TriRMC） |
| evolution-charter 落件 | `round_runner.ts` L726 | 4b75864（E3·TriRMC） |
| repair 同口径交集 | `score_engine.py` L792/L817/L820 | 0150c6b |
| kind_by 审计分离 | `score_engine.py` L801/L805 | 2a8b58f |
| 修复率 100% 机制 | `score_engine.py` L799-805 | d042515 |

## §七 · 使用依据

CEO 令 2026-11-26（fade-001 只做工作·「机制齐就点」=瞎跑）+任务书 bod-taskcharter-evolution-arch-20261126.md（COS 代批）+E1-E5 验收读数（engine 76 / charter 22 / round 65）+草案 b6bd30cec。

---
—— CTO 小狄（m-cto）·写前现查 2026-11-26T04:40Z（+0800=12:40）
