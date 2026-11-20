"""FADE-001 D5 写面·retry 分叉门（cto-d5-close-identity-survey-20261120 §三
机制四件定稿承④照守零改形·WO-D5-20261120 §四 派工面）。

业务面：score 段内部分（score.json "score" 键·并盘 100 总分 §一.3 实锚）<
90 → retry 分叉（落 retry_flag.json+resume 指令拟稿）——close 毕后置调用，
close_cli/close_skill 本体零改（铁律域五件零触碰正身）。

出口二值：state="retry"（<threshold·落 flag+拟稿）| "skip"（>=threshold 免
retry·或保守 skip 面）。边界 90=免 retry（<90 判据·90e06cddd 边界勘正承，
白盒边界案钉）。

retry_flag.json schema 九键（§三.3 定谳·零扩键）：
  {retry_flag: "pending-retry", retry_count, internal_score, threshold,
   run_id, from_week, to_week, escalated, flagged_at}
  ——run_id/from_week/to_week 读取面=close.json 收口卷（施工选定形·缺卷
  skip 面不达读取位）·原子写=tmp+os.replace 同目录（D4 §一.4.2 定谳同形
  ——零重蹈 close.json write_text 直写注·现役面候勘定窗零趁 D5 改）。

次数上限语义（§三.4）：retry_count=当周 state 面读+落卷自持——施工选定形：
  当周 state 面=runs_root（run_dir.parent）域递归扫描既有 retry_flag.json
  取 max(retry_count)（flag 族=state 面本体·零新 state 文件族）；
  已两 retry（当周 max>=2）仍<90 → escalated=true+notify 值席（never-raises
  ·TRICO_RULING_ESCALATE_TO 单值收件面 D3 同构承）——如实呈报非熔断
  （零停工零 job 停用·escalate 呈报面 §一B① 定谳承）。

resume 复用面（§三.6 §六A 现役承）：零新 resume 机制——新铸件只产 resume
指令拟稿（返回面 resume_hint 字段·不入 flag 九键卷面）——拟稿=从 score 段
（10 段制段 7·close_skill=段 8/close_cli=段 9 docstring 旁证实锚）起重跑至
close·CLI 段产物零重跑；消费位=loop 体/round_runner 域（chain_runner 本体
零改·候窗域）。

保守 skip 面（门族同构承）：close.json 缺/verdict!=pass（收口门毒化=升级域
管非 retry 面·施工选定形如实注）·score.json 缺/坏/键缺/非数值/出 0-100 域
=skip 不判零落卷。

never raises（运行面异常保守返 dict·D3/D4 先例形）·零密值零敏感面（D-46）
·preflight/close/score 现役件零触碰（独立新件）。
"""

from __future__ import annotations

import json as _json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

CLOSE_RETRY_GATE_VERSION = "1.0.0"

RETRY_FLAG_FILE = "retry_flag.json"
RETRY_FLAG_STATE = "pending-retry"
# 10 段制段 7=score（close_skill 段 8/close_cli 段 9 docstring 旁证·§三.6
# resume=从 score 段号起重跑至 close）
RESUME_STAGE_SCORE = 7
# 次数上限：当周已两 retry（max>=2）仍<90 → escalated（§三.4 定谳承）
ESCALATE_AFTER_RETRIES = 2

try:
    from os import environ as _environ
except Exception:  # pragma: no cover — 零环境面退化（never-raises 族）
    _environ = {}


def check_retry_fork(run_dir, threshold: int = 90) -> dict:
    """retry 分叉门（close 毕后置调用·§三.2 定谳照铸）。

    出口二值 state="retry"|"skip"·never raises 运行面保守返 dict。
    """
    reading: dict = {
        "ok": False,
        "state": "skip",
        "gate_version": CLOSE_RETRY_GATE_VERSION,
        "threshold": threshold,
        "run_dir": str(run_dir),
    }
    try:
        rd = Path(run_dir)  # 奇异输入（None/int）TypeError 面=never raises 域内

        # ── 前置：close.json 收口卷（后置调用前提·verdict 门面） ─────
        close_path = rd / "close.json"
        if not close_path.is_file():
            reading["detail"] = "close.json 缺（后置前提不成立·skip 面零落卷）"
            return reading
        try:
            close = _json.loads(close_path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 — 坏卷保守 skip
            reading["detail"] = f"close.json unparsable: {type(e).__name__}（保守 skip）"
            return reading
        if not isinstance(close, dict) or close.get("verdict") != "pass":
            reading["detail"] = (
                f"close verdict={close.get('verdict') if isinstance(close, dict) else 'non-dict'}"
                "!=pass（收口门毒化=升级域管非 retry 面·施工选定形如实注）")
            return reading

        # ── 内部分读取面：score.json "score" 键（§一.3 实锚） ─────────
        score_path = rd / "score.json"
        if not score_path.is_file():
            reading["detail"] = "score.json 缺（skip 面不判·保守语义同门族）"
            return reading
        try:
            score_data = _json.loads(score_path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            reading["detail"] = f"score.json unparsable: {type(e).__name__}（保守 skip）"
            return reading
        if not isinstance(score_data, dict) or "score" not in score_data:
            reading["detail"] = "score.json \"score\" 键缺（skip 面不判）"
            return reading
        score = score_data["score"]
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            reading["detail"] = f"score={score!r} 非数值面（bool⊂int 陷阱同族·保守 skip）"
            return reading
        if not (0 <= score <= 100):
            reading["detail"] = f"score={score!r} 出 0-100 域（坏值保守 skip·施工选定形）"
            return reading
        reading["internal_score"] = score

        # ── 分叉判定（边界 90=免 retry·<90 判据 90e06cddd 承） ────────
        if score >= threshold:
            reading["ok"] = True
            reading["detail"] = (
                f"score={score}>=threshold={threshold}（免 retry——90 边界=免钉"
                "·90e06cddd 勘正承）")
            return reading

        # ── retry 形：当周计数+escalated 判定+落卷+拟稿 ───────────────
        prev_count = _scan_week_retry_count(rd.parent)
        retry_count = prev_count + 1
        escalated = prev_count >= ESCALATE_AFTER_RETRIES

        flag = {
            "retry_flag": RETRY_FLAG_STATE,
            "retry_count": retry_count,
            "internal_score": score,
            "threshold": threshold,
            "run_id": close.get("run_id"),
            "from_week": close.get("from_week"),
            "to_week": close.get("to_week"),
            "escalated": escalated,
            "flagged_at": datetime.now(timezone.utc).isoformat(),
        }
        flag_path = rd / RETRY_FLAG_FILE
        _atomic_write_json(flag_path, flag)
        reading["ok"] = True
        reading["state"] = "retry"
        reading["flag_path"] = str(flag_path)
        reading["retry_count"] = retry_count
        reading["escalated"] = escalated
        reading["detail"] = (
            f"score={score}<threshold={threshold}（retry 分叉·flag 落卷"
            f" retry_count={retry_count} escalated={escalated}）")
        if escalated:
            reading["detail"] += "——已两 retry 仍<90·escalated 呈报值席（如实呈报非熔断）"
            _escalate_notify(rd, flag)
        reading["resume_hint"] = {
            "resume_stage": RESUME_STAGE_SCORE,
            "stage_name": "score",
            "resume_command": (
                f"chain_runner --resume-stage {RESUME_STAGE_SCORE}"
                f" --run-dir {rd}"),
            "note": ("从 score 段（段 7）起重跑至 close（段 8/9）·CLI 段产物"
                     "零重跑——§六A 现役 resume 照用零新机制·消费位=loop 体域"),
        }
        return reading
    except ValueError:
        raise  # 契约面透传（保持门族形——本件无契约 raise 面·保守占位）
    except Exception as e:  # noqa: BLE001 — never raises（D3/D4 先例形）
        reading["detail"] = f"retry gate failed: {type(e).__name__}: {e}"[:200]
        return reading


def _scan_week_retry_count(runs_root: Path) -> int:
    """当周 state 面读（施工选定形）：runs_root 域递归 retry_flag.json 取
    max(retry_count)——flag 族=state 面本体·零新 state 文件族（如实注候终审）。"""
    best = 0
    try:
        if not runs_root.is_dir():
            return best
        for p in runs_root.rglob(RETRY_FLAG_FILE):
            try:
                data = _json.loads(p.read_text(encoding="utf-8"))
                c = data.get("retry_count")
                if isinstance(c, int) and not isinstance(c, bool) and c > best:
                    best = c
            except Exception:  # noqa: BLE001 — 坏 flag 卷不计零炸
                continue
    except Exception:  # noqa: BLE001 — 扫描面零炸（缺省 0）
        pass
    return best


def _atomic_write_json(target: Path, payload: dict) -> None:
    """原子写（tmp+os.replace 同目录+fsync·D4 §一.4.2 定谳同形·零半卷）。"""
    fd, tmp_path = tempfile.mkstemp(dir=str(target.parent), prefix=".retry-flag-",
                                    suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            _json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _escalate_notify(run_dir: Path, flag: dict) -> None:
    """escalated 呈报值席（never-raises·D3 cos_decision_gate 同构承）——
    收件面=TRICO_RULING_ESCALATE_TO 单值 env·零新键（如实呈报非熔断：
    零停工零 job 停用·呈报面 §一B① 定谳承）。"""
    try:
        to = _environ.get("TRICO_RULING_ESCALATE_TO", "")
        subject = (
            "[retry-gate] 当周已两 retry 仍<90·escalated 呈报"
            f"（run={flag.get('run_id')} score={flag.get('internal_score')}）")
        body = (
            f"retry_flag escalated: run_dir={run_dir}"
            f" retry_count={flag.get('retry_count')}"
            f" internal_score={flag.get('internal_score')}"
            f" flagged_at={flag.get('flagged_at')}"
            "——如实呈报非熔断（零停工·候值席勘定）")
        if not to:
            print(f"[retry-gate] ESCALATE (no TRICO_RULING_ESCALATE_TO): {subject}",
                  flush=True)
            return
        print(f"[retry-gate] ESCALATE to={to}: {subject} | {body}", flush=True)
    except Exception:  # noqa: BLE001 — never-raises 同构承（零阻宿）
        pass


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="FADE-001 D5 retry 分叉门（close 毕后置调用）")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--threshold", type=int, default=90)
    a = p.parse_args()
    print(_json.dumps(check_retry_fork(a.run_dir, a.threshold),
                      ensure_ascii=False, indent=2))
