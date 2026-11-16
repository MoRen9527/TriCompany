# FADE-001 联审召集段契约与操作对表面（W2 施工件）

- sourceOfTruth: 本件（TriCompany/docs/workflow/joint-review-convene-contract.md）
- syncMode: write-time
- lastSyncedAt: 文件头时戳锚=git commit 时戳（零手打·D-47 正形）
- 架构法源: W1 架构卷 a97d76af7 §二/§三/§四（CTO 裁·三段解耦正身）
- 施工席: FSD 小全（m-fsd）·W2 评分面正位施工（COO 派工 msg 6cf048fa·2026-11-16）
- 落款: 2026-11-16T04:13:18Z 起草窗（+8=12:13:18·date 现查原值）

## §一 · 三段定位（W1§一 承接·零改写）

| 段 | 正形 | 承载 |
|---|---|---|
| 触发段 | manifest close pass 后收口段产触发件（管线内同步·r88 异步形废止） | `runtime/cognition/joint_review_trigger.py`（机械面） |
| 召集段 | 触发件落树→notify→值席拾取→逐席派工→七席会话面作答→评分卷落树 | **m-duty-cos 会话面编排（本契约=操作对表面）** |
| 回收段 | 下轮 run 消费段读评分卷→分数面判定→verdict 分叉指令面 | `runtime/cognition/joint_review_recycle.py`（机械面·禁自判） |

## §二 · 触发件契约（trigger 段产出·W1§二最小字段形）

`joint-review-trigger.json`（run_dir 必落+归属周树面双落）：

```json
{
  "trigger_version": "1.0.0",
  "loop_run_id": "shift-WW46-<ts>Z",
  "run_dir": "/var/lib/trirmc/cron/runs/<run_id>",
  "from_week": "W46", "to_week": "W47",
  "dim_a_materials":  [{"ref": "manifest.json", "sha16": "..."}, {"ref": "score.json", ...}, {"ref": "plan.json", ...}],
  "dim_b_materials":  [{"kind": "counts", "ref": "plan.json#/counts", ...}, {"kind": "ar", ...}, {"kind": "unresolved_diff", "ref": "verify.json", ...}, {"kind": "ops_commit", "hash": "..."}],
  "domain_readings":  {"machine": {...}, "duty_collection": "pending", "subjective": "pending"},
  "score_threshold": null,
  "mode": "loop-window | cron-sunday",
  "trigger_time": "<UTC ISO>"
}
```

run_state!=ok → `joint-review-trigger-skip.json`（fail-closed·联审不发起·W1§四.2）。

## §三 · 召集链操作序（值席面·m-duty-cos 执行）

1. **拾取**：notify 信到（subject=`[joint-review-trigger] <run_id>`）或树面 trigger 件巡检→读 run_dir 材料包（dim_a/dim_b 指针）。
2. **逐席派工**（七席=COS/COO/CAO/CPO/CTO/CHO/CFO·r129 席单）：SendMessage 直达各席（M-004 口径）·随信附两维度材料包指针+本契约路径+评分卷落卷要求（§四）。
3. **卷面回收**：各席会话面作答→评分卷落树 `--scores-root` 目录（W47 现役树位=`docs/workflow/operating-records/<week>/trees/fade001-loop-joint-review/scores/`）→commit 落卷直达通知值席。
4. **挂起处置**：<quorum 窗值席补召（缺席席单列·W1§四.1）——补召时限候编排定·loop 照跑不阻塞语义恒守。

## §四 · 评分卷命名与 schema 契约（每席三卷·两维度分立）

落卷位=`<scores-root>/`（§三.3 树位）·文件名契约（recycle 段硬读形）：

| 卷 | 文件名 | 形制 | schema 要点 |
|---|---|---|---|
| 维度 A | `joint-review-<SEAT>-dimA-score.json` | subjective 试卷形（rubric-firstshoot I 族判据真源） | `dim:"A"`+`seat`+`entries[]:{criterion, score(0-10 int), rationale, evidence_ref}` |
| 维度 B | `joint-review-<SEAT>-dimB-score.json` | collection 试卷形·二值制（fsd-r119c 重采正形） | `dim:"B"`+`seat`+`entries[]:{family_id(A/F/H), verdict(pass/fail), weight(int), rationale, evidence_ref}` |
| 意见卷（可选） | `joint-review-<SEAT>-improvement.json` | 改进意见面 | `seat`+`items[]`——loop_next 时=下一轮输入材料随触发件流转 |

**两维度纪律（r106 形·禁并卷禁互判）**：A/B 分立文件+各自 verdict_rule 对表；禁一卷混载两维度；禁以 B 族值面判 A 族判据（两基准禁互判同族）。schema 失配→回收段 fail-closed 拒收（零强判）·不计 quorum·挂候勘面（W1§四.3）。

## §五 · 回收段消费面（机械面·控制面拾取执行）

```
python3 -m runtime.cognition.joint_review_recycle \
    --run-dir <run_dir> --run-id <run_id> \
    --scores-root <scores-root> \
    --round <N> --max-rounds 3 --quorum 5 \
    --threshold <null=留参> \
    --tree-file <树面回写路径>
```

verdict 六态与控制面动作对表（**机械面禁自判·r101——recycle 零 POST 零 touch·动作面全归控制面**）：

| verdict | 语义 | 控制面（m-duty-cos）动作 |
|---|---|---|
| `loop_next` | 分数不足（round<3） | marker 序正形发起下一轮：touch `TRICO_LOOP_MARKER_DIR/loop-window.marker` → `POST /internal/v1/cron/jobs/weekly-plane-shift/run`（X-Internal-Token）·改进意见卷随触发件流转 |
| `converge` | 总分≥分数线 | 收敛段：关 loop 候 CEO 终认（r101 形） |
| `escalate_ruling` | 轮数上界 3 未达标 | 转候裁面禁自主续转（W1§三） |
| `pending_quorum` | 有效席<5 | 触发件挂起态标注·补召（§三.4）·loop 照跑不阻塞 |
| `pending_threshold` | 分数线未裁（null） | 挂候裁面（毕验收窗 CTO 主裁 COO 会签裁后带值回收） |
| `contract_mismatch` | 全卷失配 | 挂候勘面→FSD 修件窗走（防线不放松） |

总分口径（score_engine v2.0.0 并盘 100 形对形）：机判域实分（score.json B/C/D/E/G）+值席采集域席均（dimB pass 族 weight 和）+主观域席均（dimA entries score 和）·三域直加。

## §六 · 参数位现势（台账 676 采认·三参数三处定谳）

- 轮数上界=**3 轮**（COS 径裁·recycle `--max-rounds` 默认 3）
- quorum=**≥5/7**（COS 径裁·recycle `--quorum` 默认 5）
- 分数线=**留参**（W2 毕验收窗 CTO 主裁 COO 会签·recycle `--threshold` 缺省 null→pending_threshold——裁前禁传值面）

## 使用依据

- W1 架构卷 a97d76af7（§二契约/§三循环控制/§四降级/§五施工接口）
- COO 派工令 msg 6cf048fa·排工单 v2 dc8ce2231（护栏四族）·台账 676 ddbff5893（三参数定谳）
- 河源活体基线锚卷 fsd-w2-baseline-anchor-20261116.md（1ff86cee3·管线 25 行+通道定谳）
- 记忆锚族：机械面禁自判（r101）/两基准禁互判/M-004 派工口径/cron-job-state-hygiene
