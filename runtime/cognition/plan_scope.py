"""FADE-001 阶段 3: plan skill 迁移范围预审段（fsd-ten-stage-tech-collab-20261113 §二·CTO 裁① APPROVE）。

业务面切片第三段（与 preflight「该不该跑」/qualify「有没有资格跑」零重叠探针零复检）——
判「迁什么不迁什么」。语义锚（CPO 件 C）：「这是一周的记录，还是这一周的活——
记录随周封存·活随人带走」。

三分类（机械判据·§二.8 实盘勘定修正版；1.1.0 agent 化施工后=plan.json 契约族
  原样冻结——树域快道直出+慢道 agent 五分类投影回填）：
  migrate    — 在途树（活随人带走）→清单候选面。预演形=零动手候审；
               生产形=清单驱动 OP index 元数据层搬家（文件树本体原地封存——
               现役 migrate_weekly_plane 动作域=index 层·weekly_plane.py L231-311 白盒实锚）。
  keep       — 全 close/记录面（记录随周封存·原地留档）——degrade 链终态=保守 keep。
  carry_over — unresolved-items §1 现役区 CARRY 行（两形正则·带状态去向）。

agent 判断面（1.1.0·CTO 设计定稿卷 2026-11-15 §一+栏 A 裁决卷 4a6c9c0c2 §二/§三
  +联审增补附款 c398d7b0b §四·CEO 14:26:37 三点裁决「首拍前改后链上拍」）：
  快道零改——classify_dir 机械判据一字不动（证据链完整树直出·回归钉）。
  慢道三入集——证据冲突（status/expiry 判向不同）/degrade 默认 keep/expired——
  agent 语义判断（POST /internal/v1/agent·8710 现役路由实勘正形·60s 零重试·
  fail-closed keep 零炸段）。五分类枚举（COS 清单卷 §一：carry_periodic/
  new_week_templated/weekly_selfbuild/active_tree_ongoing/one_shot）→契约三族
  投影（栏 A 裁决 §二·契约冻结）：carry_periodic→migrate·余四族→keep+语义标注。
  护栏三件：结构守门（family 值域/conf 界/reasons 非空·违=fail-closed keep）/
  置信门槛 0.6（低置信保守 keep）/双向断言照走（M∪K=S 含 agent 判定树·断言权在
  脚本）。机械门：慢道树数上界 15（超出 skipped_over_limit）+migrate_closeout_
  conflict（投影 migrate∧树含 closeout 形文件名→降 keep 候人工）。
  顶层文件判断域（栏 A 裁决①笔 1 扩）——周目录顶层 is_file 实扫+合并单次 agent
  判断·纯读数面零触三清单（M∪K=S 域=trees/ 不变·verify strict 对表域不破）。
  未完树计数判据（栏 A 裁决⑥·判据面非闸面）：active_tree_ongoing>2→readings
  reasons 如实尾注（W43 §五 纪律界·不拦停不改判）。

判据要点（§二.8 四发现实锚）：
  1. 全集 S={from_week}/trees/ 全条目（目录+散文件混装形）——OP index 与实盘脱节是
     现势常态（W46 activeTrees=0 vs 实盘 20+），index 只作旁证对表层（index_drift 读数）。
  2. 目录 degrade 链：tree-op.json status → authorization.json expiry → 默认 keep
     （漏迁毒于误封存——verify 对表+carry_over 面+生产形候审三兜底）。
  3. CARRY id 两形：`CARRY-YYYYMMDD-NNN`（日期形·实盘 CARRY-20260728-004）|
     `CARRY-NNN`（纯数字形·现役 shift_carry_over L103 域）——现役纯数字正则对日期形
     漏匹配（缺陷候选已登记候 CTO 裁），本模块判据面兼容两形。
  4. 散文件（.md 单件）默认 keep 原地封存。

双向枚举断言（STE 锚②·CPO 三标准之一；表述勘正 2026-11-14 review 日·发现 32
  CTO 裁词照录）：**M∪K=S（trees 域双向断言·零遗漏 ∧ 两两交=∅ 零重叠）∧ C 独立解析
  （unresolved-items 域·带状态去向·不进 S 断言）**——S 定义=trees/ 全条目（判据要点 1），
  CARRY 行域=unresolved-items 文件不同域不在 S 内（原稿「∪C=S」字面永假=表述含混；
  实现面 bidirectional_check 一向如此·本勘正仅 docstring 零行为）。违即 exit 2 拦。
  替身禁令（STE 锚⑤·S51 三向）：目录缺失/不可读/结构门毒化=
  exit 2 FAIL-EXPECTED——禁造替身清单（空 keep 全集形=最毒替身·双向断言会假绿）。

退出码（preflight/qualify 同族）：0 全过 → 交棒（DCE 照单执行）；
  2 = 范围拦（双向断言违/扫描败/结构门毒化）→ 本拍不执行（plan.json 带 verdict=fail 落卷）。

输出：单份 JSON 到 stdout（bash 重定向落 $RUN_DIR/plan.json·CPO 对接点②命名族）——
plan_version(1.1.0) / run_id / from_week / to_week / migrate[] / keep[] /
carry_over[]（行含三标注 source/dest/pending_reason） / counts /
bidirectional_ok / index_drift / other_unresolved_count /
agent_readings[]（1.1.0 增补·审计面：{tree, domain: tree|top_level, family 原值,
confidence, reasons, source: fast_path|agent|failed_fallback, plan_family
投影后族, annotation 语义标注}——值守读卷即审 agent 判断质量；
1.2.0 WP1/2/3 增补：rationale 判读理由+evidence_ref 证据引用（判读留痕三件套·
零 null 面 fail-closed）+disposition 去向四选一（migrate/keep/carry/pending_ledger
·WP2 活件对账）+pending_review 候裁态}） / reconciliation{}（WP2 counts↔readings
对账读数） / fallback_governance{}（WP3 兜底治理：批次/慢道序/候裁分支/失败率告警） /
check_time。
既有字段（1.0.0 形）零动——verify/dce/score/close 消费面零波及（close 面 verdict
单键只读实勘 2026-11-15·extra keys 容忍族）。

调用形（payload vC 接入点·候部署窗·今晚零生产触）：
  cd /srv/fleet/TriCompany && python3 -m runtime.cognition.plan_scope \\
      --from-week W46 --to-week W47 --run-dir "$RUN_DIR" \\
      --operating-root /srv/fleet/TriMetaverse/docs/workflow/operating-records
"""

from __future__ import annotations

import argparse
import json as _json
import os
import re
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

PLAN_VERSION = "1.2.0"  # WP1/2/3 兜底治理施工升版（2026-11-18·minor：既有字段零动
#   +agent_readings 增 rationale/evidence_ref/disposition 字段族+counts.top_level
#   +reconciliation/fallback_governance 区块——WP1 判读留痕/WP2 活件对账/WP3 兜底治理
#   ·notice-185 施工序·拆解任务书获批面）

# ── agent 慢道判断面常量（plan agent 化施工·CTO 设计定稿卷 2026-11-15 §一 +
#    联审增补附款三条 c398d7b0b §四——快道 classify_dir 零改·慢道三入集形态；
#    WP3 兜底治理增补 2026-11-18：批次拆分/一次重试/失败率告警三面） ──

AGENT_TIMEOUT_S = 60        # 单树超时（WP3 增补：重试面一次见下·总时长由批次上界保险丝承载）
AGENT_RETRY_MAX = 1         # WP3 兜底治理·重试分支：瞬时失败（call_failed/malformed）
                            # 一次重试面（拆解任务书获批改形——原「零重试」刚性退役，
                            # 段总时长保险丝=批次数上界·低置信案不重试=语义已出候裁面）
AGENT_BATCH_SIZE = 15       # WP3 批次拆分（CFO 15 件/批案·原附款①单批界退役为批内规模）
AGENT_BATCH_MAX = 3         # WP3 批数上界（段时长保险丝·3×15=45 件总界）
AGENT_SLOW_PATH_LIMIT = AGENT_BATCH_SIZE * AGENT_BATCH_MAX  # 慢道总界·超出
                            # skipped_over_limit fail-closed keep（附款①语义保留·
                            # 界值随批次拆分扩为 45——超界读数如实非替身）
AGENT_CONFIDENCE_FLOOR = 0.6  # 护栏 2：低置信保守 keep（误封存可候审·误迁移不可逆）
AGENT_FALLBACK_ALERT_RATE = 0.20  # WP3 fast_path（agent 慢道判断面）失败率阈值：
                            # failed_fallback/慢道判断总数 >20%→_notify_blocking
                            # 转人工（WP4 通知链承·cho/cto >20% 案）
# 8710 现役路由实勘正形（TriRMC src/server/app.ts L506·startsWith 前缀匹配；
# 设计卷草案 /internal/v1/agent-run 非现役名·实勘裁正 2026-11-15）
_AGENT_ENDPOINT_DEFAULT = "http://localhost:8710/internal/v1/agent"
_CLOSEOUT_HINT = "closeout"  # 附款②：树内含 closeout 形文件名→migrate 判定降级门
_AGENT_SYSTEM_PROMPT = (
    "你是周平面迁移范围预审的语义判断器。输入是一棵工作树的证据面 JSON。"
    "锚：「这是一周的记录，还是这一周的活——记录随周封存·活随人带走」。"
    "family 五枚举（COS 清单卷 §一）："
    "carry_periodic=周期滚动件（每周必续·迁移面——OP index/unresolved-items/"
    "demand-pool/daily-progress 族）；"
    "new_week_templated=新周新件（周后缀参数化·内容 owner 席立——cfo-quota-daily/"
    "scoring-ledger 族）；"
    "weekly_selfbuild=周期自建树（tick/巡查/运行面·新周自建预期态非缺口）；"
    "active_tree_ongoing=跨周续作活树（不迁文件·挂账台账线跨周承接·周未完树≤1~2 纪律界）；"
    "one_shot=一次性毕报/评审/定稿/法证卷（历史冻结·git 可溯）。"
    "只输出一个 JSON 对象，无其他文字："
    '{"family": "carry_periodic"|"new_week_templated"|"weekly_selfbuild"|'
    '"active_tree_ongoing"|"one_shot", "confidence": <0.0-1.0>, '
    '"reasons": "<一句话依据>"}'
)
_AGENT_SYSTEM_PROMPT_TOP = (
    "你是周平面迁移范围预审的语义判断器。输入是 operating 周目录顶层文件清单 JSON"
    "（name+size_bytes· trees/ 目录域之外的顶层文件域）。"
    "对清单中每一件输出 family 五枚举判断（同树域枚举：carry_periodic 周期滚动件/"
    "new_week_templated 新周新件/weekly_selfbuild 周期自建/active_tree_ongoing 跨周活树/"
    "one_shot 一次性件）。只输出一个 JSON 对象，无其他文字："
    '{"files": [{"name": "<原样回填>", "family": <五枚举之一>, '
    '"confidence": <0.0-1.0>, "reasons": "<一句话依据>"}...]}'
)
# 五分类→契约三族投影（栏 A 裁决卷 §二·契约冻结）：carry_periodic→migrate·
# 其余四族→keep+语义标注（agent_readings 载原值+标注·三清单/verify 对表域零波及）
_AGENT_FAMILY_ANNOTATION = {
    "new_week_templated": "expected_absent",
    "weekly_selfbuild": "selfbuild_expected",
    "active_tree_ongoing": "ongoing_ledger_handover",
    "one_shot": "one_shot_frozen",
}

# CARRY id 两形（§二.8③·日期形实盘在役+纯数字形现役域）
_CARRY_ID_RE = re.compile(r"^\s*\|\s*`(CARRY-\d{8}-\d+|CARRY-\d+)`\s*\|")
# 树内未过期授权=在途标记（authorization.json expiry 面秒级 epoch 或 ISO）
_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")
# tree-op.json status → keep 终态集（其余非空值=在途 migrate）
_KEEP_STATUS = {"done", "closed", "retired", "cancelled"}


# ── 分类器（degrade 链·§二.8④） ──────────────────────────────────────────


def _parse_expiry(value: str) -> datetime | None:
    """authorization expiry 面解析（ISO 8601 或 epoch 毫秒·解析败=None=视为在途保守拦）。"""
    v = value.strip()
    if v.isdigit():
        try:
            return datetime.fromtimestamp(int(v) / 1000, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    if _ISO_TS_RE.match(v):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def classify_dir(tree: Path, now: datetime) -> tuple[str, list[str]]:
    """目录分类 degrade 链：tree-op.json status → authorization expiry → keep。"""
    # 1) tree-op.json status 面（若有）
    top = tree / "tree-op.json"
    if top.is_file():
        try:
            data = _json.loads(top.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — 坏 tree-op=结构信号丢失→降级继续链（不炸不替）
            data = None
        if isinstance(data, dict):
            status = str(data.get("status", "")).strip().lower()
            if status in _KEEP_STATUS:
                return "keep", ["tree_op_status:" + status]
            if status:
                return "migrate", ["tree_op_status:" + status]
    # 2) authorization.json expiry 面（若有·未过期=在途活授权）
    auth = tree / "authorization.json"
    if auth.is_file():
        try:
            adata = _json.loads(auth.read_text(encoding="utf-8"))
            expiry_raw = str(
                (adata.get("expiry") if isinstance(adata, dict) else None) or ""
            )
        except Exception:  # noqa: BLE001 — 坏 authorization=同降级
            expiry_raw = ""
        if expiry_raw:
            exp = _parse_expiry(expiry_raw)
            # 发现 30（CTO 派工 2026-11-14·八项之 5）：reason 码拆两态——
            # authorization_active=exp>now 确证活授权 / authorization_unparsable=
            # 过期解析不可得保守在途。原合一码 authorization_active_or_unparsable
            # 系判读歧义源（mount-gate 亲历误判）·分类行为不变（两态同 migrate）。
            if exp is None:
                return "migrate", ["authorization_unparsable"]
            if exp > now:
                return "migrate", ["authorization_active"]
            return "keep", ["authorization_expired"]
    # 3) 默认 keep（保守·漏迁毒于误封存——verify 对表+carry_over+候审三兜底）
    return "keep", ["no_active_markers_default_keep"]


def scan_trees(week_dir: Path, now: datetime) -> tuple[dict[str, list[str]] | None, str | None]:
    """全集扫描（目录+散文件两类）——返回 {name: (category 附 reason)} 或 (None, err)。

    替身禁令：week_dir 缺失/不可读=FAIL-EXPECTED（返回 err 非空清单替身）。
    """
    if not week_dir.is_dir():
        return None, f"trees dir not found: {week_dir}（NOT_FOUND·不造替身）"
    entries: dict[str, list[str]] = {}
    try:
        children = sorted(week_dir.iterdir(), key=lambda p: p.name)
    except Exception as e:  # noqa: BLE001 — 扫描异常同拦
        return None, f"trees dir unreadable: {type(e).__name__}: {e}（不造替身）"
    for child in children:
        name = child.name
        if child.is_dir():
            cat, reasons = classify_dir(child, now)
        else:
            cat, reasons = "keep", ["scatter_file_archive"]
        entries[name] = [cat] + reasons  # [category, *reason_codes]
    return entries, None


# ── carry_over 解析（两形正则·状态去向面） ────────────────────────────────


def parse_carry_rows(unresolved_path: Path) -> tuple[list[dict], int, str | None]:
    """unresolved-items §1 现役区 CARRY 行解析（两形）——返回 (rows, other_count, err)。

    other_count=非 CARRY 前缀的 unresolved 行数（REGR-/BUG- 等·读数如实面不进清单——
    与现役 shift_carry_over bump 域同域）。文件缺失=合法空集（carry 面缺失是迁移器
    carry_over 步的域·非 plan 拦点）。
    """
    if not unresolved_path.is_file():
        return [], 0, None  # 合法空集+读数面
    try:
        text = unresolved_path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 读败=扫描异常族（替身禁令）
        return [], 0, f"unresolved-items unreadable: {type(e).__name__}: {e}"
    rows: list[dict] = []
    other = 0
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        m = _CARRY_ID_RE.match(line)
        if m:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            carry_id = m.group(1)
            # 状态去向面（行内词面归类·CPO 三标准之三 carry_over 带状态去向）
            joined = " ".join(cells)
            if "frozen" in joined.lower() or "冻结" in joined:
                status_to = "frozen"
            elif "已修" in joined or "销账" in joined:
                status_to = "closed"
            else:
                status_to = "pending_review"
            # 三标注（联审增补附款·carry 行审计面增补·既有键零动）：
            # source（来源）/dest（候选去向显式字段）/pending_reason（待定原因）
            pending_reason = {
                "frozen": "冻结挂账（行内 frozen/冻结 词面）",
                "closed": "已销账存照（行内 已修/销账 词面）",
                "pending_review": "状态判读未定（行内无冻结/已修词面·候人工复核）",
            }[status_to]
            rows.append({
                "carry_id": carry_id,
                "cells": cells[:6],  # 截断防超长行进卷
                "status_to": status_to,
                "source": "unresolved-items §1 现役区",
                "dest": status_to,
                "pending_reason": pending_reason,
            })
        elif re.match(r"^\s*\|\s*`?[A-Z]{3,}-", line):
            other += 1
    return rows, other, None


# ── 双向枚举断言（STE 锚②） ───────────────────────────────────────────────


def bidirectional_check(
    entries: dict[str, list[str]], migrate: list[str], keep: list[str]
) -> tuple[bool, list[str]]:
    """M∪K=S（零遗漏）∧ M∩K=∅（零重叠）——违例明细返回（替身禁令配套）。"""
    violations: list[str] = []
    mset, kset = set(migrate), set(keep)
    covered = mset | kset
    all_names = set(entries.keys())
    uncovered = sorted(all_names - covered)
    if uncovered:
        violations.append(f"uncovered(漏): {uncovered}")
    overlap = sorted(mset & kset)
    if overlap:
        violations.append(f"overlap(重): {overlap}")
    phantom = sorted(covered - all_names)
    if phantom:
        violations.append(f"phantom(清单外幽灵): {phantom}")
    return (not violations), violations


# ── index 旁证对表层（§二.8①·index_drift 读数） ──────────────────────────


def index_drift(week_dir: Path, migrate_count: int) -> dict:
    """OP index activeTrees/doneTrees vs 实盘 migrate 数对表——旁证读数·读败不拦。"""
    drift: dict = {}
    try:
        ops = sorted(week_dir.glob("OP-*.json"))
        if not ops:
            return {"note": "no OP index found（旁证缺位·不拦）"}
        # 妆容劫持防族规（PM §四/STE §三.4）：取最新禁字典序——mtime 序正形
        latest = max(ops, key=lambda p: p.stat().st_mtime)
        data = _json.loads(latest.read_text(encoding="utf-8"))
        drift["index_file"] = latest.name
        drift["index_activeTrees"] = len(data.get("activeTrees", []))
        drift["index_doneTreesThisWeek"] = len(data.get("doneTreesThisWeek", []))
        drift["plan_migrate"] = migrate_count
        drift["note"] = (
            "index 与实盘脱节为现势常态（W46 实锚 activeTrees=0 vs 实盘 20+）——"
            "旁证读数非分类基准"
        )
    except Exception as e:  # noqa: BLE001 — 旁证层读败如实注记不拦
        drift["error"] = f"{type(e).__name__}: {e}"
    return drift


# ── agent 慢道判断面（设计定稿卷 §一·快道 classify_dir 本体零改的伴生面） ────


def _collect_evidence(tree: Path, now: datetime) -> dict:
    """双判向证据收集（分诊底座·与 classify_dir 同证据源·零行为面）。

    status_dir/expiry_dir 各自的机械判向与 classify_dir 短路链同值：
    status∈KEEP→keep / status 非空→migrate / expiry unparsable|active→migrate /
    expired→keep / 缺失→None。
    """
    ev: dict = {"status_dir": None, "expiry_dir": None,
                "status_raw": None, "expiry_raw": None}
    top = tree / "tree-op.json"
    if top.is_file():
        try:
            data = _json.loads(top.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — 坏 tree-op=结构信号丢失（同 classify_dir 降级形）
            data = None
        if isinstance(data, dict):
            status = str(data.get("status", "")).strip().lower()
            ev["status_raw"] = status or None
            if status in _KEEP_STATUS:
                ev["status_dir"] = "keep"
            elif status:
                ev["status_dir"] = "migrate"
    auth = tree / "authorization.json"
    if auth.is_file():
        try:
            adata = _json.loads(auth.read_text(encoding="utf-8"))
            expiry_raw = str(
                (adata.get("expiry") if isinstance(adata, dict) else None) or ""
            )
        except Exception:  # noqa: BLE001 — 坏 authorization 同降级
            expiry_raw = ""
        ev["expiry_raw"] = expiry_raw or None
        if expiry_raw:
            exp = _parse_expiry(expiry_raw)
            if exp is None or exp > now:
                ev["expiry_dir"] = "migrate"  # unparsable 保守在途 / active 活授权
            else:
                ev["expiry_dir"] = "keep"     # expired
    return ev


def _is_slow_path(ev: dict) -> bool:
    """慢道入集判据（设计卷 §一.1 慢道 a/b 两形态）：

    a) 证据冲突——status 与 expiry 判向不同（现役短路链被 status 优先掩盖·双判向
       并检才可见）；b) degrade 走默认 keep——缺 tree-op（或坏/空 status）且无活
    授权（无 expiry / 已过期）。其余（单证据确证面）=快道·现役判零改直出。
    """
    sd, ed = ev["status_dir"], ev["expiry_dir"]
    if sd is not None and ed is not None and sd != ed:
        return True
    if sd is None and ed in (None, "keep"):
        return True
    return False


def _tree_brief(tree: Path, max_bytes: int = 2048) -> str:
    """目录内容摘要 ≤2KB（README 首段/文件清单）——agent 语义判断输入面。"""
    lines: list[str] = []
    try:
        names = sorted(p.name for p in tree.iterdir())
    except Exception:  # noqa: BLE001 — 清单读败=空 brief（brief 是旁证非判据·不拦）
        names = []
    readme = next((n for n in names if n.lower().startswith("readme")), None)
    if readme:
        try:
            head = (tree / readme).read_text(encoding="utf-8", errors="replace")
            lines.append(f"README[{readme}] 首段: " + head.split("\n\n", 1)[0][:600])
        except Exception:  # noqa: BLE001 — README 读败跳过不拦
            pass
    if names:
        lines.append(
            "文件清单: " + ", ".join(names[:30]) + ("…" if len(names) > 30 else "")
        )
    brief = "\n".join(lines)
    return brief.encode("utf-8")[:max_bytes].decode("utf-8", errors="replace")


def _tree_has_closeout(tree: Path) -> bool:
    """附款②探测：树含 closeout 形文件名（顶层·大小写不敏感）→migrate 降级门。"""
    try:
        return any(_CLOSEOUT_HINT in p.name.lower() for p in tree.iterdir())
    except Exception:  # noqa: BLE001 — 探测败=门不触发（keep 向保守·误放毒于误拦的反向面此处取宽）
        return False


def _call_agent(payload: dict, endpoint: str, token: str | None) -> dict:
    """进程内 HTTP→8710 agent loop（POST /internal/v1/agent·60s 零重试）。

    调用方 except 全族（URLError/TimeoutError/HTTPError/JSONDecodeError）
    fail-closed——设计 §一.2 硬约束：段不炸·plan.json 照落卷。
    """
    body = _json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Internal-Token"] = token  # TRIRMC_INTERNAL_TOKEN·值面零回显（D-46）
    req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=AGENT_TIMEOUT_S) as resp:
        return _json.loads(resp.read().decode("utf-8"))


def _extract_agent_text(result: dict) -> str | None:
    """agent loop events 响应→文本宽松提取。

    勘修线①定谳修复（2026-10-20·T3 preview unparseable 15 根因）：引擎文本信道=
    content_delta 事件族（键=delta，loop.ts:164/257）——判定 JSON 经此通道分段
    发出；旧提取键（text/content/message）不含 delta→逆序命中最后一个
    tool_result 的 content（工具裸输出非判定文）→判卷解析必败=unparseable 全族。

    修复形=delta 串联主路径（按事件序拼接全部 content_delta 文本=完整判定文）；
    旧键逆序兼容路径保留（旧事件族兼容）。
    """
    events = result.get("events") if isinstance(result, dict) else None
    if not isinstance(events, list):
        return None
    deltas: list[str] = []
    for ev in events:
        if (isinstance(ev, dict) and ev.get("type") == "content_delta"
                and isinstance(ev.get("delta"), str) and ev["delta"].strip()):
            deltas.append(ev["delta"])
    if deltas:
        return "".join(deltas)
    for ev in reversed(events):
        if isinstance(ev, dict):
            for key in ("text", "content", "message"):
                v = ev.get(key)
                if isinstance(v, str) and v.strip():
                    return v
    return None


def _parse_agent_verdict(text: str) -> dict | None:
    """agent 文本→{family,confidence,reasons}：直解→败则截 {...} 段再解。

    None=malformed（守门面 fail-closed 入口）。
    """
    candidates = [text]
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        candidates.append(m.group(0))
    for cand in candidates:
        try:
            out = _json.loads(cand)
        except Exception:  # noqa: BLE001 — 逐候选试解
            continue
        if isinstance(out, dict):
            return out
    return None


_AGENT_FAMILY_ENUM = (
    "carry_periodic", "new_week_templated", "weekly_selfbuild",
    "active_tree_ongoing", "one_shot",
)


def _validate_agent_output(out: dict) -> tuple[bool, str | None]:
    """结构守门（设计卷 §一.3 护栏 1）：family 五枚举值域/confidence float[0,1]/reasons 非空。"""
    if out.get("family") not in _AGENT_FAMILY_ENUM:
        return False, "family out of enum"
    conf = out.get("confidence")
    if (not isinstance(conf, (int, float)) or isinstance(conf, bool)
            or not (0.0 <= conf <= 1.0)):
        return False, "confidence not float[0,1]"
    if not str(out.get("reasons", "")).strip():
        return False, "reasons empty"
    return True, None


def _project_agent_family(family: str, to_week: str) -> tuple[str, str]:
    """五分类→契约三族投影（栏 A 裁决卷 §二·契约冻结）：carry_periodic→migrate·
    其余四族→keep+语义标注。

    WP1 判读留痕改形（2026-11-18·零 null 面）：migrate 案显式迁移语义标注
    （migrate_carry_periodic）——annotation 恒非空 str（返回形 str|None→str·
    投影枚举扩时漏标注面由调用侧 fail-closed gate 拦·替身禁令同族）。"""
    if family == "carry_periodic":
        return "migrate", "migrate_carry_periodic"
    ann = _AGENT_FAMILY_ANNOTATION[family]
    if family == "new_week_templated":
        ann = f"expected_absent@{to_week}"
    return "keep", ann


# ── WP1 判读留痕 gate（零 null 面·fail-closed 不放行） ──────────────────────


def _annotation_gate(annotation: object) -> bool:
    """WP1 annotation 空=fail-closed 不放行（plan_family 投影面 gate·零 null 面）。

    空/None/非 str 即 False——调用侧对该判读降级保守 keep+显式 fallback 标注
    （不炸段不产 null 面·替身禁令同族）。"""
    return isinstance(annotation, str) and bool(annotation.strip())


def _tree_evidence_ref(ev: dict) -> list[str]:
    """WP1 判读留痕·evidence_ref 构造（树域）：证据面四键紧凑引用列表——
    判读可溯源面（禁零锚判读·升级条目 evidence 同族语义）。"""
    refs = []
    for key in ("status_dir", "expiry_dir", "status_raw", "expiry_raw"):
        v = ev.get(key)
        if v is not None:
            refs.append(f"{key}={v}")
    if not refs:
        refs.append("evidence:none_markers（无 tree-op/authorization 证据面）")
    return refs


def _fallback_reading(
    name: str, domain: str, why: str, rationale: str, evidence_ref: list[str],
    annotation: str | None = None,
) -> dict:
    """WP3 兜底治理·fail-closed 读数构造（键族统一·WP1 三件套必载）。

    annotation 缺省=失败语义显式标注 fallback_keep_unjudged（零 null 面——
    WP1 gate 同族：失败案 annotation 非空显式语义非缺省静默）。"""
    return {
        "tree": name, "domain": domain, "family": None,
        "confidence": None, "reasons": why,
        "source": "failed_fallback", "plan_family": "keep",
        "annotation": annotation or "fallback_keep_unjudged",
        "rationale": rationale,
        "evidence_ref": evidence_ref,
        "disposition": "keep" if domain == "tree" else "pending_ledger",
        # WP2 活件对账·去向四选一：树域 failed_fallback=keep（保守封存·三清单
        # 承载+WP3 候裁分支 escalation 面承）；顶层域=pending_ledger（显式挂账
        # 候 COS 规划核——顶层零动作件无处承载必显式挂账·零静默）。
    }


def _slow_path_priority(ev: dict) -> int:
    """WP3 慢道优先级排序（硬时钟确定性面·同档名序 tie-break 零随机）：

    0=活授权在途（expiry_dir=migrate·authorization_active/unparsable——在途嫌疑
      最重先判）；1=证据冲突（status/expiry 双判向分叉）；2=degrade 默认 keep
    （嫌疑最轻后判）。"""
    sd, ed = ev.get("status_dir"), ev.get("expiry_dir")
    if ed == "migrate":
        return 0
    if sd is not None and ed is not None and sd != ed:
        return 1
    return 2


def _agent_verdict_for_tree(
    name: str, tree: Path, ev: dict, from_week: str, to_week: str,
    endpoint: str, token: str | None,
) -> tuple[str, list[str], dict]:
    """单树 agent 语义判断+守门+投影+两门降级——返回 (plan_family, reason_codes, reading)。

    reading=agent_readings 审计元（键族统一：tree/domain/family 原值/confidence/
    reasons/source/plan_family/annotation+WP1 rationale/evidence_ref 三件套+
    WP2 disposition 四选一·fail-closed 形 source=failed_fallback+plan_family=keep
    零动作）。

    WP3 兜底治理改形（2026-11-18）：agent_call_failed/malformed 案一次重试面
    （AGENT_RETRY_MAX=1·重试分支）；重试毕仍败/低置信案=候裁分支（failed_fallback
    keep+disposition 候裁态——escalation 面落卷 fallback_governance 区块承载）。
    """
    reading: dict = {"tree": name, "domain": "tree", "family": None,
                     "confidence": None, "source": "agent",
                     "plan_family": None, "annotation": None,
                     "rationale": None, "evidence_ref": None,
                     "disposition": None}
    evidence_ref = _tree_evidence_ref(ev)
    attempts = 1 + AGENT_RETRY_MAX  # WP3 重试分支：1 次初试+AGENT_RETRY_MAX 次重试
    out: dict | None = None
    call_err: str | None = None
    for attempt in range(1, attempts + 1):
        try:
            payload = {
                "systemPrompt": _AGENT_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": _json.dumps({
                    "tree_name": name,
                    "evidence_summary": {
                        k: ev[k] for k in
                        ("status_dir", "expiry_dir", "status_raw", "expiry_raw")
                    },
                    "tree_brief": _tree_brief(tree),
                    "from_week": from_week,
                    "to_week": to_week,
                }, ensure_ascii=False)}],
                "maxTurns": 1,
            }
            result = _call_agent(payload, endpoint, token)
            text = _extract_agent_text(result)
            out = _parse_agent_verdict(text) if text else None
            call_err = None
            break
        except Exception as e:  # noqa: BLE001 — 超时/端点/网络全族 fail-closed（设计 §一.2）
            call_err = f"{type(e).__name__}"
            out = None
            if attempt < attempts:
                continue  # WP3 重试分支：一次重试面（重试毕仍败=候裁分支）
    if call_err is not None:
        why = f"agent_call_failed: {call_err}"
        retried = attempts > 1
        rationale = (
            f"agent 慢道判断失败降级保守 keep（{why}"
            + (f"·重试 {attempts - 1} 次毕仍败→候裁分支" if retried else "")
            + "·零动作候人工）"
        )
        reading.update({"reasons": why, "source": "failed_fallback",
                        "plan_family": "keep",
                        "annotation": "fallback_keep_unjudged:agent_call_failed",
                        "rationale": rationale,
                        "evidence_ref": evidence_ref,
                        "disposition": "keep",
                        "pending_review": bool(retried)})
        return "keep", [f"agent_call_failed:{call_err}"], reading
    if out is None:
        # 件③ malformed 勘定落卷（notice-207 三款·2026-11-19）：禁只报不勘——
        # result events error 面逐案透传 readings.root_cause（ns4 探针实锚主因=
        # 模型服务供给面败「All fallback models exhausted」·calls=0 零成功调用）
        root_cause = None
        try:
            errs = [str(e.get("message", ""))[:200] for e in (result.get("events") or [])
                    if isinstance(e, dict) and e.get("type") == "error"]
            calls = next((e.get("usageSummary", {}).get("calls")
                          for e in (result.get("events") or [])
                          if isinstance(e, dict) and e.get("type") == "loop_end"), None)
            if errs:
                root_cause = {"layer": "模型服务供给面（三层之外第四面·探针实锚）",
                              "errors": errs, "agent_loop_calls": calls,
                              "note": "零 delta→_parse None→malformed 全族解释"}
        except Exception:  # noqa: BLE001 — 勘定面零炸段
            root_cause = None
        upd = {"reasons": "agent_output_malformed: unparsable",
               "source": "failed_fallback", "plan_family": "keep",
               "annotation": "fallback_keep_unjudged:malformed",
               "rationale": "agent 判读输出解析败降级保守 keep（malformed"
                            f"·重判 {attempts - 1} 次毕仍败→候裁分支·零动作候人工）",
               "evidence_ref": evidence_ref,
               "disposition": "keep",
               "pending_review": True}
        if root_cause:
            upd["root_cause"] = root_cause  # notice-207 三款：禁只报不勘
        reading.update(upd)
        return "keep", ["agent_output_malformed"], reading
    ok, why = _validate_agent_output(out)
    if not ok:
        reading.update({"reasons": f"agent_output_malformed: {why}",
                        "source": "failed_fallback", "plan_family": "keep",
                        "annotation": "fallback_keep_unjudged:malformed",
                        "rationale": f"agent 判读守门败降级保守 keep（{why}"
                                     f"·重判 {attempts - 1} 次毕仍败→候裁分支·零动作候人工）",
                        "evidence_ref": evidence_ref,
                        "disposition": "keep",
                        "pending_review": True})
        return "keep", ["agent_output_malformed"], reading
    family = out["family"]
    conf = float(out["confidence"])
    rationale = str(out["reasons"])
    reading.update({"family": family, "confidence": conf,
                    "reasons": rationale,
                    "rationale": rationale,  # WP1：agent 解析 rationale 透传
                    "evidence_ref": evidence_ref})
    conf_code = "agent_confidence:" + f"{conf:.2f}"
    if conf < AGENT_CONFIDENCE_FLOOR:
        # 护栏 2：低置信保守 keep（投影前拦·误封存可候审补救·误迁移不可逆）
        # WP3：低置信不重试（语义已出·置信不足=候裁面非重试面）
        reading.update({"source": "failed_fallback", "plan_family": "keep",
                        "annotation": "fallback_keep_unjudged:low_confidence",
                        "disposition": "keep", "pending_review": True})
        return "keep", ["agent_low_confidence"], reading
    plan_family, annotation = _project_agent_family(family, to_week)
    if not _annotation_gate(annotation):
        # WP1 annotation 空=fail-closed 不放行：该判读降级保守 keep+显式 fallback
        # 标注（投影枚举扩时漏标注面防线·不炸段不产 null 面）
        reading.update({"source": "failed_fallback", "plan_family": "keep",
                        "annotation": "fallback_annotation_missing:fail_closed",
                        "rationale": "annotation 投影空=fail-closed 不放行（WP1 gate）",
                        "disposition": "keep", "pending_review": True})
        return "keep", ["agent_annotation_gate_fail_closed"], reading
    disposition = "migrate" if plan_family == "migrate" else (
        "carry" if family == "active_tree_ongoing" else "keep")
    # WP2 活件对账·去向四选一（树域）：migrate/keep/carry（active_tree_ongoing=
    # 挂账台账线跨周承接·不迁文件）
    reading.update({"plan_family": plan_family, "annotation": annotation,
                    "disposition": disposition})
    if plan_family == "migrate" and _tree_has_closeout(tree):
        # 附款②（投影后门面）：投影 migrate ∧ 树含 closeout 形文件→降级 keep 候人工复核
        reading["gate"] = "migrate_closeout_conflict"
        return "keep", ["agent_family_" + family, "migrate_closeout_conflict"], reading
    codes = ["agent_family_" + family]
    codes.append(annotation)
    codes.append(conf_code)
    return plan_family, codes, reading


def _agent_verdicts_for_top_files(
    top_files: list[tuple[str, Path]], from_week: str, to_week: str,
    endpoint: str, token: str | None,
) -> list[dict]:
    """顶层文件域合并单次 agent 判断（栏 A 裁决①笔 1 扩·7 件级批量单次调用——
    23:50 时序刚性下省调用数·最坏 1×60s）。

    顶层件域零触三清单（M∪K=S 断言域=trees/ 不变·verify strict 对表域不破）——
    判断结果读数面（agent_readings·domain=top_level）·迁移器消费形候 CTO 面。
    单件守门：family 非值域/conf 非界/reasons 空→该件 failed_fallback 零动作读数。

    WP1/WP2 改形（2026-11-18）：readings 三件套（rationale/evidence_ref/annotation
    零 null）+disposition 四选一（WP2 活件对账——migrate/keep/carry/pending_ledger·
    failed_fallback 案=pending_ledger 显式挂账候 COS 规划核·零静默零动作）。
    """
    names = [n for n, _ in top_files]

    def _zero_action(name: str, why: str, rationale: str) -> dict:
        return {"tree": name, "domain": "top_level", "family": None,
                "confidence": None, "reasons": why, "source": "failed_fallback",
                "plan_family": "keep",
                "annotation": "fallback_keep_unjudged:pending_ledger",
                "rationale": rationale,
                "evidence_ref": ["top_level_file_list"],
                "disposition": "pending_ledger",  # WP2：显式挂账候 COS 规划核
                "pending_review": True}

    readings: dict[str, dict] = {}
    sizes = {}
    try:
        sizes = {n: p.stat().st_size for n, p in top_files}
        payload = {
            "systemPrompt": _AGENT_SYSTEM_PROMPT_TOP,
            "messages": [{"role": "user", "content": _json.dumps({
                "from_week": from_week, "to_week": to_week,
                "files": [
                    {"name": n, "size_bytes": sizes[n]}
                    for n, p in top_files
                ],
            }, ensure_ascii=False)}],
            "maxTurns": 1,
        }
        result = _call_agent(payload, endpoint, token)
        text = _extract_agent_text(result)
        out = _parse_agent_verdict(text) if text else None
        items = out.get("files") if isinstance(out, dict) else None
    except Exception as e:  # noqa: BLE001 — 全族 fail-closed·逐件零动作读数
        for n in names:
            readings[n] = _zero_action(
                n,
                f"agent_call_failed: {type(e).__name__}（顶层件判断失败·显式挂账候 COS）",
                "顶层件 agent 批量判断失败降级（零动作≠静默——WP2 显式挂账 pending_ledger"
                f"候 COS 规划核·{type(e).__name__}）",
            )
        return [readings[n] for n in names]
    for n in names:
        item = next(
            (i for i in (items or [])
             if isinstance(i, dict) and i.get("name") == n),
            None,
        )
        if item is None:
            readings[n] = _zero_action(
                n, "agent_output_malformed: file entry missing（显式挂账候 COS）",
                "顶层件 agent 判读清单缺该件条目（显式挂账 pending_ledger 候 COS）",
            )
            continue
        ok, why = _validate_agent_output(item)
        if not ok:
            readings[n] = _zero_action(
                n, f"agent_output_malformed: {why}（显式挂账候 COS）",
                f"顶层件 agent 判读守门败（{why}·显式挂账 pending_ledger 候 COS）",
            )
            continue
        family = item["family"]
        conf = float(item["confidence"])
        rationale = str(item["reasons"])
        base = {"tree": n, "domain": "top_level", "family": family,
                "confidence": conf, "reasons": rationale,
                "source": "agent", "plan_family": None, "annotation": None,
                "rationale": rationale,  # WP1：agent 解析 rationale 透传
                "evidence_ref": [f"top_level_file:{n}",
                                 f"size_bytes={sizes.get(n, 'n/a')}"],
                "disposition": None}
        if conf < AGENT_CONFIDENCE_FLOOR:
            base.update({"source": "failed_fallback", "plan_family": "keep",
                         "annotation": "fallback_keep_unjudged:low_confidence",
                         "disposition": "pending_ledger", "pending_review": True})
        else:
            pf, ann = _project_agent_family(family, to_week)
            if not _annotation_gate(ann):
                # WP1 annotation gate（零 null 面·顶层域同树域 fail-closed 形）
                base.update({"source": "failed_fallback", "plan_family": "keep",
                             "annotation": "fallback_annotation_missing:fail_closed",
                             "rationale": "annotation 投影空=fail-closed 不放行（WP1 gate）",
                             "disposition": "pending_ledger", "pending_review": True})
            else:
                base["plan_family"], base["annotation"] = pf, ann
                # WP2 四选一（顶层域）：migrate/keep/carry/pending_ledger
                base["disposition"] = (
                    "migrate" if pf == "migrate"
                    else ("carry" if family == "active_tree_ongoing" else "keep")
                )
        readings[n] = base
    return [readings[n] for n in names]


# ── 结构门（STE 锚①·schema 断言·写前自校验——毒化拦不写假卷） ─────────────


def _structure_gate(plan: dict) -> list[str]:
    errors: list[str] = []
    for key in (
        "plan_version", "run_id", "from_week", "to_week",
        "migrate", "keep", "carry_over", "counts",
        "bidirectional_ok", "check_time",
    ):
        if key not in plan:
            errors.append(f"missing required key: {key}")
    counts = plan.get("counts")
    if isinstance(counts, dict):
        if counts.get("migrate") != len(plan.get("migrate", [])):
            errors.append("counts.migrate != len(migrate)（结构毒化拦）")
        if counts.get("keep") != len(plan.get("keep", [])):
            errors.append("counts.keep != len(keep)（结构毒化拦）")
        if counts.get("carry_over") != len(plan.get("carry_over", [])):
            errors.append("counts.carry_over != len(carry_over)（结构毒化拦）")
    else:
        errors.append("counts not a dict")
    if plan.get("bidirectional_ok") is not True and plan.get("verdict") != "fail":
        errors.append("bidirectional_ok!=true 且非 fail verdict（矛盾态拦）")
    # WP1 判读留痕终检（零 null 面·fail-closed 毒化拦）：agent_readings 全集
    # annotation/rationale 非空 str+evidence_ref 非空列表——三件套任一空=不放行。
    for i, r in enumerate(plan.get("agent_readings", []) or []):
        if not isinstance(r, dict):
            errors.append(f"agent_readings[{i}] not a dict（WP1 零 null 面·毒化拦）")
            continue
        for key in ("annotation", "rationale"):
            v = r.get(key)
            if not (isinstance(v, str) and v.strip()):
                errors.append(
                    f"agent_readings[{i}].{key} empty（WP1 判读留痕零 null 面·毒化拦）"
                )
        ev_ref = r.get("evidence_ref")
        if not (isinstance(ev_ref, list) and ev_ref):
            errors.append(
                f"agent_readings[{i}].evidence_ref empty（WP1 判读留痕零 null 面·毒化拦）"
            )
    # WP2 活件对账终检：disposition 四选一值域（migrate/keep/carry/pending_ledger）
    _DISPOSITIONS = ("migrate", "keep", "carry", "pending_ledger")
    for i, r in enumerate(plan.get("agent_readings", []) or []):
        if isinstance(r, dict) and r.get("disposition") not in _DISPOSITIONS:
            errors.append(
                f"agent_readings[{i}].disposition={r.get('disposition')!r} "
                "非四选一值域（WP2 活件对账·毒化拦）"
            )
    return errors


# ── WP2 活件对账（counts↔readings 自动对账·差额=显式 fail-closed 拒产） ────


def reconcile_counts_readings(plan: dict) -> tuple[bool, list[str]]:
    """WP2 counts↔readings 自动对账（2026-11-18·拆解任务书 WP2 面）。

    对表面：
      R1 trees 域——counts.migrate+counts.keep == domain=tree readings 数
        （每树恰一条 reading·M∪K=S 对账投影面）；
      R2 顶层域——counts.top_level == domain=top_level readings 数；
      R3 disposition 值域——readings 全集 disposition ∈ 四选一
        （migrate/keep/carry/pending_ledger）。
    差额≠0 → (False, 差额明细)——显式 fail-closed 拒产（WP5 红闸同源消费）。

    agent_readings 键缺（1.0.0/1.1.0 旧形 plan）=对账域缺位如实注 skip 不红
    （向后兼容·verify 消费面容忍族）。
    """
    diffs: list[str] = []
    readings = plan.get("agent_readings")
    counts = plan.get("counts")
    if not isinstance(readings, list) or not isinstance(counts, dict):
        return True, ["reconciliation_skip:agent_readings/counts 缺位"
                      "（1.0.0/1.1.0 旧形 plan·对账域缺位如实注）"]
    tree_readings = [r for r in readings
                     if isinstance(r, dict) and r.get("domain") == "tree"]
    cm, ck = counts.get("migrate"), counts.get("keep")
    if isinstance(cm, int) and isinstance(ck, int):
        if cm + ck != len(tree_readings):
            diffs.append(
                f"R1 trees 域差额: counts(migrate={cm}+keep={ck})="
                f"{cm + ck} != tree readings {len(tree_readings)}（WP2 对账差额）"
            )
    top_readings = [r for r in readings
                    if isinstance(r, dict) and r.get("domain") == "top_level"]
    ctl = counts.get("top_level")
    if ctl is None:
        if top_readings:
            diffs.append(
                f"R2 顶层域差额: counts.top_level 缺键而顶层 readings="
                f"{len(top_readings)}（WP2 对账差额·1.2.0 形缺键）"
            )
    elif ctl != len(top_readings):
        diffs.append(
            f"R2 顶层域差额: counts.top_level={ctl} != top_level readings "
            f"{len(top_readings)}（WP2 对账差额）"
        )
    _DISPOSITIONS = {"migrate", "keep", "carry", "pending_ledger"}
    for i, r in enumerate(readings):
        if not isinstance(r, dict):
            continue
        d = r.get("disposition")
        if d is not None and d not in _DISPOSITIONS:
            # 缺键（None）=1.1.0 旧形容忍（对账域缺位 skip）·显式错值=红
            diffs.append(
                f"R3 值域差额: readings[{i}].disposition={d!r} "
                "非四选一（WP2 对账差额）"
            )
    return (not diffs), diffs


# ── WP3 fast_path 失败率阈值告警（>20%→_notify_blocking 转人工·WP4 通知链承） ──


def _fallback_rate_alert(
    run_id: str, slow_total: int, failed_total: int,
) -> dict:
    """WP3 兜底治理·失败率告警面：agent 慢道判断 failed_fallback 占比 >
    AGENT_FALLBACK_ALERT_RATE 阈值（>20%·cho/cto 案）→_notify_blocking 转人工
    （weekly_plane_shift canonical notify·WP4 通知链承·never raises 零炸段——
    import 败/发送败均降级如实记不拦段）。

    返回 alert 读数（fallback_governance.alert 区块承载）。"""
    rate = (failed_total / slow_total) if slow_total > 0 else 0.0
    alert: dict = {
        "threshold": AGENT_FALLBACK_ALERT_RATE,
        "slow_total": slow_total,
        "failed_total": failed_total,
        "rate": round(rate, 4),
        "triggered": False,
    }
    if slow_total <= 0 or rate <= AGENT_FALLBACK_ALERT_RATE:
        return alert
    alert["triggered"] = True
    # 同日节流（ns6 拍实锚降噪·限流循环根面治标）：state 文件面同日一发形——
    # SMTP relay 发信限流（ns4/ns6 实锚 Connection closed）根=多拍告警累积——
    # 同日已发即抑制（throttled 读数如实·零静默——state 文件面可审计）。
    stamp = Path(os.environ.get(
        "TRICO_PLAN_ALERT_STATE_DIR", "/var/lib/trirmc")
    ) / f"plan-fallback-alert-{datetime.now(timezone.utc).date()}.done"
    if stamp.is_file():
        alert["throttled"] = True
        alert["note"] = "同日已发（节流形·限流循环根面降噪·state 文件面可审计）"
        return alert
    try:
        from runtime.cognition.weekly_plane_shift import _notify_blocking
        to: list[str] = []
        for key in ("TRICO_PLAN_NOTIFY_TO", "WEEKLY_SHIFT_NOTIFY_TO"):
            addrs = [x.strip() for x in (os.environ.get(key) or "").split(",")
                     if x.strip()]
            if addrs:
                to = addrs
                break
        failures = _notify_blocking(
            subject=f"[plan_scope] agent 慢道失败率超阈 {rate:.0%}"
                    f"（run {run_id}）",
            body=f"WP3 fast_path（agent 慢道判断面）失败率 {rate:.0%} > "
                 f"{AGENT_FALLBACK_ALERT_RATE:.0%} 阈值——"
                 f"failed_fallback {failed_total}/{slow_total}（run_id={run_id}）"
                 "·转人工复核（兜底=异常态非常态·WP3 兜底治理告警面）",
            to=to, context_id=run_id or "plan_scope_fallback_alert",
        )
        alert["notify_failures"] = failures
        alert["notified"] = not failures
        if alert["notified"]:
            try:
                stamp.write_text(_json.dumps({"notified_at": datetime.now(timezone.utc).isoformat()}),
                                 encoding="utf-8")
            except OSError:
                pass  # 登记败不拦（节流面降级·下拍可能重发一封——如实态）
    except Exception as e:  # noqa: BLE001 — 告警面零炸段（降级如实记）
        alert["notify_failures"] = [{"status": "alert_path_failed",
                                     "error": f"{type(e).__name__}: {e}"[:300]}]
        alert["notified"] = False
    return alert


# ── 周目录名解析（实盘形={ISO 年}-W{nn}·2026-W46——§二.8 实锚弹外补） ─────


def _top_expansion_readings(from_dir: Path, to_week: str) -> dict:
    """notice-207 ②一款材料扩围读数（2026-11-19·三子项·纯机械读数面）。

    通读范围 W46 树→W46 周平面根目录文件——三子项读数（零 agent 零清单触：
    M∪K=S=trees 域契约零破·评卷材料同步扩围面）：
      ①需求池只迁未联审件——需求池件（demand-pool 族）联审词面标注读数
        （「联审」词面在=已联审·缺=未联审候迁——判据读数化非动作面）；
      ②任务大表完成/未完成对账——task-inventory 族 [x]/[ ] 词面计数读数；
      ③W47 周共学目录建立建议——共学目录（co-learning/共学 词面目录）在位性
        读数（建议态非动作面·动作候值席/排面）。
    """
    out: dict = {"notice": "notice-207 ②一款扩围读数（纯机械面·零清单触）",
                 "demand_pool": [], "task_inventory": None, "co_learning": None}
    try:
        for f in sorted(from_dir.glob("*demand-pool*")):
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            reviewed = "联审" in text
            out["demand_pool"].append({
                "file": f.name,
                "reviewed_mark": reviewed,
                "migrate_candidate": not reviewed,  # 只迁未联审件·判据读数
            })
    except OSError as e:
        out["demand_pool"] = [{"error": str(e)[:120]}]
    try:
        inv = next(iter(sorted(from_dir.glob("task-inventory*"))), None)
        if inv is not None and inv.is_file():
            text = inv.read_text(encoding="utf-8", errors="replace")
            done = text.count("[x]") + text.count("[X]")
            todo = text.count("[ ]")
            out["task_inventory"] = {"file": inv.name, "done_marks": done,
                                     "todo_marks": todo,
                                     "recon_note": "完成/未完成对账读数（词面计数面）"}
    except OSError as e:
        out["task_inventory"] = {"error": str(e)[:120]}
    out["co_learning"] = {
        "suggest_dir": f"{to_week} 周共学目录（co-learning）",
        "in_place": False,  # 建议态读数（建立动作候值席/排面·零越位）
    }
    return out


def _resolve_week_dir(operating_root: Path, week_token: str, start_date: str | None) -> tuple[Path | None, str | None]:
    """实盘周目录名带年段（`2026-W46`）——start_date ISO 年推算·缺省 glob fallback。

    fallback 多命中=err（fail-closed·不猜）。
    """
    if start_date:
        try:
            year = date.fromisoformat(start_date).isocalendar()[0]
            candidate = operating_root / f"{year}-{week_token}"
            if candidate.is_dir():
                return candidate, None
        except ValueError:
            pass
    hits = sorted(operating_root.glob(f"*-{week_token}"))
    if len(hits) == 1:
        return hits[0], None
    if len(hits) > 1:
        return None, f"week dir ambiguous for {week_token}: {[h.name for h in hits]}"
    return None, None


# ── 主入口 ─────────────────────────────────────────────────────


def run_plan(args: argparse.Namespace, now: datetime | None = None) -> tuple[int, dict]:
    """执行范围预审并返回 (exit_code, plan dict)。now 可注入（单测）。"""
    now = now or datetime.now(timezone.utc)
    operating_root = Path(args.operating_root)
    from_dir, week_err = _resolve_week_dir(operating_root, args.from_week, args.start_date)
    trees_dir = from_dir / "trees" if from_dir is not None else operating_root / "__unresolved__" / "trees"

    errors: list[str] = []
    scan: dict[str, list[str]] | None = None
    scan_err: str | None = None
    if week_err:
        errors.append(week_err)
    else:
        scan, scan_err = scan_trees(trees_dir, now)

    unresolved: Path | None = None
    if from_dir is not None:
        if args.op_id:
            unresolved = from_dir / f"{args.op_id}.unresolved-items.md"
        else:
            unresolved = _find_unresolved(from_dir)
    if unresolved is not None:
        carry_rows, other_count, carry_err = parse_carry_rows(unresolved)
    else:
        carry_rows, other_count, carry_err = [], 0, None

    if scan_err:
        errors.append(scan_err)
    if carry_err:
        errors.append(carry_err)

    # ── agent 慢道分诊（设计定稿卷 §一·scan tags 改写式——下游清单循环/双向断言零改）──
    agent_endpoint = (
        getattr(args, "agent_endpoint", None)
        or os.environ.get("TRICO_PLAN_AGENT_ENDPOINT")
        or _AGENT_ENDPOINT_DEFAULT
    )
    agent_token = os.environ.get("TRIRMC_INTERNAL_TOKEN")  # 值面零回显（D-46）·缺失→401→fail-closed
    slow_readings: dict[str, dict] = {}
    top_readings: list[dict] = []
    fallback_governance: dict = {
        "wp": "WP3 兜底治理（2026-11-18·拆解任务书获批面）",
        "batching": {"batch_size": AGENT_BATCH_SIZE, "batch_max": AGENT_BATCH_MAX,
                     "batches_run": 0, "beyond_limit_skipped": []},
        "slow_order": [],
        "retry": {"max": AGENT_RETRY_MAX, "retry_enabled_trees": 0},
        "pending_review": [],  # 候裁分支落卷（malformed 重判毕仍败/低置信/call 失败重试毕）
    }
    if scan is not None:
        slow: dict[str, dict] = {}
        for name, tags in scan.items():
            if (trees_dir / name).is_dir():  # 散文件不入慢道（判据要点 4·快道 keep 直出）
                ev = _collect_evidence(trees_dir / name, now)
                if _is_slow_path(ev):
                    slow[name] = ev
        # WP3 慢道优先级排序（硬时钟确定性面）：活授权在途 0 档→证据冲突 1 档→
        # 默认 keep 2 档·同档名序 tie-break 零随机——高嫌疑先判（批次拆分前定序）。
        ordered = sorted(slow, key=lambda n: (_slow_path_priority(slow[n]), n))
        fallback_governance["slow_order"] = [
            {"tree": n, "priority": _slow_path_priority(slow[n]),
             "tier": ("active_auth" if _slow_path_priority(slow[n]) == 0
                      else ("conflict" if _slow_path_priority(slow[n]) == 1
                            else "default_keep"))}
            for n in ordered
        ]
        # 附款①总界断言（WP3 批次拆分后形态）：优先级序前 LIMIT（45=15×3）进
        # agent 分批判断·其余 fail-closed keep skipped_over_limit（如实读数非替身）。
        for name in ordered[AGENT_SLOW_PATH_LIMIT:]:
            slow.pop(name)
            scan[name] = ["keep", "skipped_over_limit"]
            slow_readings[name] = {
                "tree": name, "domain": "tree", "family": None,
                "confidence": None,
                "reasons": "skipped_over_limit（慢道总界 45=15×3·fail-closed keep）",
                "source": "failed_fallback", "plan_family": "keep",
                "annotation": "fallback_keep_unjudged:skipped_over_limit",
                "rationale": "慢道树数超总界（批次数上界保险丝·WP3 批次拆分形）"
                             "降级保守 keep 零动作候人工",
                "evidence_ref": ["slow_path_limit:" + str(AGENT_SLOW_PATH_LIMIT)],
                "disposition": "keep",
            }
            fallback_governance["batching"]["beyond_limit_skipped"].append(name)
        # WP3 批次拆分（CFO 15 件/批案）：限内慢道树按优先级序 15 件/批逐批进
        # agent（原单批界 15 退役为批内规模·批数上界 3=段时长保险丝）。
        batches = [ordered[:AGENT_SLOW_PATH_LIMIT][i:i + AGENT_BATCH_SIZE]
                   for i in range(0, min(len(ordered), AGENT_SLOW_PATH_LIMIT),
                                  AGENT_BATCH_SIZE)]
        fallback_governance["batching"]["batches_run"] = len(batches)
        for batch in batches:
            for name in batch:
                if name not in slow:
                    continue
                family, codes, reading = _agent_verdict_for_tree(
                    name, trees_dir / name, slow[name],
                    args.from_week, args.to_week, agent_endpoint, agent_token,
                )
                scan[name] = [family] + codes
                slow_readings[name] = reading
                if reading.get("pending_review"):
                    fallback_governance["pending_review"].append(
                        {"tree": name, "domain": reading.get("domain", "tree"),
                         "disposition": reading.get("disposition"),
                         "why": reading.get("reasons", "")}
                    )
        # 栏 A ⑥：周未完树计数判据（判据面非闸面）——agent 判 active_tree_ongoing
        # 树数>2→各该 reading reasons 如实尾注（不拦停不改判·W43 §五 纪律界）
        ongoing = [n for n, r in slow_readings.items()
                   if r.get("family") == "active_tree_ongoing"]
        if len(ongoing) > 2:
            note = f"；week_unfinished_trees={len(ongoing)}（>2·W43 §五 纪律界·如实记非闸）"
            for n in ongoing:
                slow_readings[n]["reasons"] += note
        # 栏 A ①：顶层文件域实扫+合并单次 agent 判断（纯读数面零触三清单——
        # M∪K=S 断言域=trees/ 不变·verify strict 对表域不破·迁移器消费形候 CTO 面）
        if from_dir is not None:
            top_files = [
                (p.name, p)
                for p in sorted(from_dir.iterdir(), key=lambda q: q.name)
                if p.is_file()
            ]
            if top_files:
                top_readings = _agent_verdicts_for_top_files(
                    top_files, args.from_week, args.to_week,
                    agent_endpoint, agent_token,
                )
                # WP3 候裁分支聚合（顶层域同树域）：顶层 pending_review 件
                # （failed_fallback=pending_ledger 显式挂账案）入治理区块——
                # 零静默零动作（拆解任务书 WP2/WP3 面）
                for r in top_readings:
                    if r.get("pending_review"):
                        fallback_governance["pending_review"].append(
                            {"tree": r.get("tree"), "domain": "top_level",
                             "disposition": r.get("disposition"),
                             "why": r.get("reasons", "")}
                        )

    migrate: list[dict] = []
    keep: list[dict] = []
    agent_readings: list[dict] = []
    if scan is not None:
        for name, tags in scan.items():
            cat, reasons = tags[0], tags[1:]
            # 发现 4（CTO 派工 2026-11-14·八项之 4）：kind=is_dir 实值——散文件
            # 标 file 不再恒 dir（读数面失真修复·双向断言按 entry 名不受影响）。
            kind = "dir" if (trees_dir / name).is_dir() else "file"
            item = {"entry": name, "kind": kind, "reason_codes": reasons}
            if cat == "migrate":
                migrate.append(item)
            else:
                keep.append(item)

    # 双向断言（扫描成功才判——扫描败时 errors 已拦）
    bidir_ok = True
    violations: list[str] = []
    if scan is not None and not errors:
        bidir_ok, violations = bidirectional_check(
            scan, [m["entry"] for m in migrate], [k["entry"] for k in keep]
        )
        if not bidir_ok:
            errors.extend(violations)

    # agent_readings 终形构建（笔 2 契约面·设计 §1.4）：快道树元补齐+慢道/顶层合并
    # （元素键族统一：tree/domain/family 原值/confidence/reasons/source/
    #   plan_family 投影后族/annotation 语义标注——审计面值守读卷即审 agent 判断质量；
    #   WP1 增 rationale/evidence_ref 三件套+WP2 disposition 四选一·零 null 面）
    if scan is not None:
        for name, tags in scan.items():
            if name in slow_readings:
                continue
            cat, reasons = tags[0], tags[1:]
            reason_str = " + ".join(reasons)
            agent_readings.append({
                "tree": name, "domain": "tree", "family": cat,
                "confidence": None, "reasons": reason_str,
                "source": "fast_path", "plan_family": cat,
                # WP1 判读留痕（fast_path 案=规则判读 rationale·零 null 面）
                "annotation": "fast_path_rule_based",
                "rationale": f"快道机械判读（classify_dir degrade 链直出）→{cat}：{reason_str}",
                "evidence_ref": ["classify_dir:" + (reasons[0] if reasons else "no_reason")],
                # WP2 活件对账（树域 fast_path 案去向=清单族直映）
                "disposition": "migrate" if cat == "migrate" else "keep",
            })
    agent_readings.extend(slow_readings[n] for n in sorted(slow_readings))
    agent_readings.extend(top_readings)

    # WP2 counts↔readings 自动对账（差额=显式 fail-closed 拒产·红闸同源）
    recon_ok, recon_diffs = reconcile_counts_readings(
        {"agent_readings": agent_readings,
         "counts": {"migrate": len(migrate), "keep": len(keep),
                    "top_level": len(top_readings)}}
    )
    if not recon_ok:
        errors.extend(recon_diffs)

    # WP3 fast_path（agent 慢道判断面）失败率告警（>20%→_notify_blocking 转人工）
    slow_judged = [r for r in agent_readings
                   if r.get("domain") == "tree"
                   and r.get("source") in ("agent", "failed_fallback")]
    slow_failed = [r for r in slow_judged if r.get("source") == "failed_fallback"]
    fallback_alert = _fallback_rate_alert(
        args.run_id, len(slow_judged), len(slow_failed)
    )
    fallback_governance["fast_path_failure_rate"] = fallback_alert["rate"]
    fallback_governance["alert"] = fallback_alert

    plan: dict = {
        "plan_version": PLAN_VERSION,
        "run_id": args.run_id,
        "from_week": args.from_week,
        "to_week": args.to_week,
        "migrate": migrate,
        "keep": keep,
        "carry_over": carry_rows,
        "counts": {
            "migrate": len(migrate),
            "keep": len(keep),
            "carry_over": len(carry_rows),
            "top_level": len(top_readings),  # WP2 活件对账·顶层域读数
        },
        "bidirectional_ok": bidir_ok,
        "violations": violations,
        "other_unresolved_count": other_count,
        "index_drift": index_drift(from_dir, len(migrate)) if from_dir is not None else {"note": "week dir unresolved（旁证缺位·不拦）"},
        "agent_readings": agent_readings,
        "reconciliation": {"ok": recon_ok, "diffs": recon_diffs},  # WP2 对账读数
        "fallback_governance": fallback_governance,  # WP3 兜底治理区块
        # notice-207 ②一款材料扩围读数（三子项·纯机械面零清单触·评卷材料扩围面）
        "top_expansion": _top_expansion_readings(from_dir, args.to_week) if from_dir is not None else {"notice": "week dir unresolved（skip 注）"},
        # 勘修线②修复（2026-10-23）：载荷随载 resolved 周目录形（year-W 正形）——
        # 下游证据/评分消费面从 plan 载荷取目录时以本形为准（裸 from_week="W41"
        # 无年段=两形并存缺位根因·file missing 7 机制面）。
        "from_week_dir": (from_dir.name if from_dir is not None else None),
        "check_time": now.isoformat(),
    }
    if errors:
        plan["verdict"] = "fail"
        plan["reasons"] = errors
        exit_code = 2
    else:
        gate_errors = _structure_gate(plan)
        if gate_errors:
            plan["verdict"] = "fail"
            plan["reasons"] = gate_errors
            exit_code = 2
        else:
            plan["verdict"] = "pass"
            exit_code = 0
    return exit_code, plan


def _find_unresolved(from_dir: Path) -> Path | None:
    """OP id 未显式传时 glob unresolved-items 件（单一命中用之·多/零命中返回 None）。"""
    hits = sorted(from_dir.glob("OP-*.unresolved-items.md"))
    return hits[0] if len(hits) == 1 else None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FADE-001 阶段 3 迁移范围预审（plan skill·薄壳）")
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--run-dir", required=True, help="本拍 run 目录（plan.json 落卷位·payload 传入）")
    p.add_argument("--run-id", default="", help="run id（payload 铸形段传入·空=留白面）")
    p.add_argument("--operating-root", default="docs/workflow/operating-records")
    p.add_argument("--start-date", default=None, help="New week start date YYYY-MM-DD（周目录年段推算·payload 模板变量现成）")
    p.add_argument("--op-id", default=None, help="OP index id（缺省=自动 glob 单一命中）")
    p.add_argument(
        "--agent-endpoint", default=None,
        help="agent loop 端点覆盖（缺省 env TRICO_PLAN_AGENT_ENDPOINT→"
             "http://localhost:8710/internal/v1/agent·8710 现役路由实勘正形）",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    exit_code, plan = run_plan(args)
    out = _json.dumps(plan, ensure_ascii=False, indent=2)
    run_dir = Path(args.run_dir)
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "plan.json").write_text(out + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001 — 落卷败=哑卷防线（同 qualify run dir 语义）
        print(f"plan.json write failed: {type(e).__name__}: {e}", flush=True)
        return 2
    print(out)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
