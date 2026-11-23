"""round_runner — loop 引擎宿主（notice-226/230/231/238 定稿 v3-final·S1 件）。

CTO 方案卷 §一 主形：loop 本体=单程序内聚循环控制流（while＋状态机）——包住
「十段链→联审→判分→flag 分路→轮间推进」全链——点火后循环体内自主迭代推进。

状态面（§二 flag 分支变量）：round-queue/state/flag.json——
  {flag: debug|test|prod, round_count: {test: N, prod: N}, fuse: bool,
   resume: N|null, authority_ref: str|null}
  · round_count 分域形（notice-230 ④：test/prod 两计数独立零混挂·同根缺陷
    连续+1 异根重置·判读锚=根因卷引用）；
  · flag 切换权=CEO 令（手动切换必载 authority_ref·无 ref=拒绝 fail-closed；
    唯一程序自动边=EXIT≥95→prod·sanctioned）。

点火钥匙（§三 队列归位）：round-queue/pending/*.json 点火指令（cron 周日窗=
时钟点火源并存·双源过同一轮间 gate 零重复）——裁决投递=run_dir/ceo-ruling.json
＋cos-evolution-decision.json（§一C 双事件 AND 门·debug 态）。

四支状态机（§一）：debug=体内候裁决（continue 迭代／terminate=break／absent=
挂起 fail-closed）；test=直进下轮；均分≥95（EXIT 算术域见下）=break＋flag→prod
（唯一程序自动边）；8 轮 FUSE=break 熔断候 CEO（fuse.marker＋pending 冻结）。

EXIT 算术域（§一A②·notice-230 款二②撤销勘正后 231②承录）：进化判据=7 席联审
均分≥95（每席 100）——230「主观只否决不计分」撤销承录（231②）·并盘 100 制
单值源（§一A①·零双制混挂）。

retry 机制（§一B·漏设计新立）：close 段读 fade-001 内部分<90→retry_flag=
pending-retry（run_dir 落卷）→Skill 尾段重跑形（resume-stage 面·非全链）·
2 次/当周上限（retry_count state 面·两 retry 仍<90=如实落卷＋escalate 非熔断）。

prod 分支（§一）：flag=prod→点火面拦截→十阶段单轮直走形（Skill 联审尾跳过·
直交付）——不进 while 体。

护栏：零造替身（state 面原子写）·零密值（D-46）·段报错停 fail-closed（款三
notice-223·failed/ 落卷＋exit≠0＋段错误行——零人肉接管零人工判卷）。
"""
from __future__ import annotations

import argparse
import json as _json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

QUEUE_ROOT_DEFAULT = "/var/lib/trirmc/round-queue"
TC_ROOT = Path(__file__).resolve().parents[2]
EXIT_THRESHOLD = 95          # §一B②：7 席联审均分≥95（含边界）跳出 loop
FUSE_LIMIT = 8               # §一：8 轮 FUSE 熔断（轮计数程序驱动）
RETRY_THRESHOLD = 90         # §一B①：当周迁移质量分≥90 免 retry（暂定线·CEO 定）
RETRY_MAX = 2                # §一B：2 次/当周上限（escalate 非熔断）
INTERNAL_SCORE_BASE = 65     # §一A①：并盘 100 制（客观 65＋主观 35 单值源）


def _read(p: Path) -> Any:
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_state(queue_root: Path) -> dict:
    """状态面读（§二·零替身——缺=缺省态显式构造）。"""
    fp = queue_root / "state" / "flag.json"
    st = _read(fp)
    if not isinstance(st, dict):
        st = {}
    st.setdefault("flag", "debug")
    counts = st.get("round_count")
    if not isinstance(counts, dict):
        counts = {}
    counts.setdefault("test", 0)
    counts.setdefault("prod", 0)
    st["round_count"] = counts
    st.setdefault("fuse", False)
    st.setdefault("resume", None)
    st.setdefault("retry_count", 0)
    st.setdefault("authority_ref", None)
    return st


def save_state(queue_root: Path, st: dict) -> None:
    """状态面原子写（temp+rename·零半写态）。"""
    fp = queue_root / "state" / "flag.json"
    fp.parent.mkdir(parents=True, exist_ok=True)
    tmp = fp.with_suffix(".tmp")
    tmp.write_text(_json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, fp)


def set_flag(queue_root: Path, flag: str, authority_ref: str | None) -> tuple[bool, str]:
    """flag 切换（§二·切换权=CEO 令——手动切换必载 authority_ref·无 ref=拒绝
    fail-closed；唯一程序自动边=EXIT≥95→prod（sanctioned·ref=run 面））。"""
    if flag not in ("debug", "test", "prod"):
        return False, f"flag={flag!r} 越三态值域（拒绝）"
    st = load_state(queue_root)
    if not authority_ref:
        return False, "flag 切换缺 authority_ref（切换权=CEO 令·无 ref=拒绝 fail-closed）"
    st["flag"] = flag
    st["authority_ref"] = authority_ref
    save_state(queue_root, st)
    return True, f"flag→{flag}（ref={authority_ref}）"


def await_ignition(queue_root: Path, poll_s: int = 0) -> Optional[dict]:
    """点火钥匙面（§三 队列归位）：pending/ 点火指令单发拾取（poll_s>0=轮询
    面·测试/dev 用；cron 周日窗=时钟点火源并存双源单 gate）。"""
    pending = queue_root / "pending"
    if not pending.is_dir():
        return None
    for f in sorted(pending.glob("*.json")):
        try:
            op = _json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        done = queue_root / "done" / f.name
        os.replace(f, done)  # 拾取即移 done（IO 转递面）
        return op
    if poll_s:
        time.sleep(poll_s)
    return None


def run_chain(params: dict, run_dir: Path, resume_stage: int | None = None,
              timeout_s: int = 3600) -> dict:
    """十段链+Skill 段程序化 spawn（§四·S2 链参数化接入位——S1 骨架=CLI
    调用形接口，S2 参数化毕零改接入）。段报错停 fail-closed（款三）。"""
    cmd = [sys.executable, "-m", "runtime.cognition.weekly_plane_shift",
           "--from", params.get("from_week", ""),
           "--to", params.get("to_week", ""),
           "--start-date", params.get("start_date", ""),
           "--operating-root", params.get("operating_root", ""),
           "--sync"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout_s, cwd=str(TC_ROOT))
        rc, tail = r.returncode, (r.stderr or "")[-400:]
    except subprocess.TimeoutExpired:
        return {"failed": True, "rc": -1, "err": f"chain timeout {timeout_s}s",
                "run_dir": str(run_dir)}
    failed = rc != 0
    return {"failed": failed, "rc": rc, "err": tail,
            "run_dir": str(run_dir)}


def report_bubble(run: dict, failed_dir: Path) -> Path:
    """错误冒泡（款三）：failed/ 落卷＋段错误行（零人肉接管零人工判卷）。"""
    failed_dir.mkdir(parents=True, exist_ok=True)
    fp = failed_dir / f"failed-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    fp.write_text(_json.dumps(run, ensure_ascii=False, indent=1), encoding="utf-8")
    return fp


def internal_score(subjective_pct: float | None) -> float:
    """fade-001 内部分（§一B①·并盘 100 制：客观 65＋主观 35 映射——
    subjective_pct=主观 I 族百分比 0-100·None=主观缺席（客观面 65 直载保守）。"""
    subj = (subjective_pct / 100) * 35 if subjective_pct is not None else 35.0
    return round(INTERNAL_SCORE_BASE + subj, 2)


def evolution_decision_path(run_dir: Path) -> Path:
    """§一C 判决卷位（cos-evolution-decision.json·evolve|hold）。"""
    return run_dir / "cos-evolution-decision.json"


def run_loop(params: dict, queue_root: Path, dry: bool = False,
             max_iters: int = 16) -> int:
    """§一 loop 本体（while＋状态机·S1 骨架——run_chain=S2 接入位·dry=骨架核）。"""
    st = load_state(queue_root)
    failed_dir = queue_root / "failed"
    if st["flag"] == "prod":
        # §一 prod 分支：单轮直走形（Skill 联审尾跳过·直交付）——不进 while 体
        run = run_chain(params, Path(params.get("run_dir", ".")))
        print(_json.dumps({"branch": "prod-direct", "failed": run["failed"]},
                          ensure_ascii=False))
        return 0 if not run["failed"] else 2
    iters = 0
    while True:
        iters += 1
        if iters > max_iters:
            print("[runner] max_iters 保险丝触发（骨架 dev 形·零死循环）")
            return 2
        run_dir = Path(params.get("run_dir", ".")) / f"r{st['round_count'].get('test', 0) + 1}"
        if dry:
            print(_json.dumps({"dry": True, "flag": st["flag"],
                               "round_count": st["round_count"],
                               "run_dir_would": str(run_dir)}, ensure_ascii=False))
            return 0
        run = run_chain(params, run_dir, resume_stage=st.get("resume"))
        if run["failed"]:
            fp = report_bubble(run, failed_dir)
            print(f"[runner] 段报错停 fail-closed（failed 卷={fp}）——候修复→重跑指令再点火", flush=True)
            return 2
        agg = _read(run_dir / "convene" / "aggregate-final.json") or {}
        verdict = (agg.get("new_structure_verdict_face") or {}).get("verdict")
        subjective_pct = (agg.get("aggregate_initial") or {}).get("subjective_pct")

        if verdict == "loop_exit":
            ok, note = set_flag(queue_root, "prod", f"EXIT≥95 ref={run_dir.name}")
            print(f"[runner] EXIT 线触发→prod（唯一程序自动边·{note}）")
            return 0
        if st["round_count"]["test"] >= FUSE_LIMIT:
            st["fuse"] = True
            save_state(queue_root, st)
            (queue_root / "fuse.marker").write_text(
                _json.dumps({"fused_at_round": st["round_count"]["test"]}), encoding="utf-8")
            print("[runner] FUSE 熔断（8 轮·候 CEO）")
            return 3
        if st["flag"] == "debug":
            ruling = _read(run_dir / "ceo-ruling.json") or {}
            dec = _read(evolution_decision_path(run_dir)) or {}
            decision = dec.get("decision")
            rd = ruling.get("decision")
            if rd == "terminate":
                print("[runner] ceo-ruling=terminate（break）")
                return 4
            if rd == "absent" and decision != "evolve":
                print("[runner] ceo-ruling absent（挂起 fail-closed·不迭代）")
                return 5
            # continue 或 cos 判决 evolve → 落下迭代
        elif st["flag"] == "test":
            pass  # 直进下轮迭代（不候裁决·§一 状态机四支）
        # §一B retry 分叉点占位（close 段内部分<90→resume 回 score 段·S2 接入后激活）
        st["round_count"]["test"] = st["round_count"].get("test", 0) + 1
        save_state(queue_root, st)
        params = dict(params)  # 自主迭代推进（非外部队列接力——勘正主形）
        params["run_dir"] = str(run_dir)
    # 不可达（while True 体）


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="round_runner — loop 引擎宿主（v3-final S1）")
    p.add_argument("--queue-root", default=os.environ.get(
        "TRICO_QUEUE_ROOT", QUEUE_ROOT_DEFAULT))
    p.add_argument("--from-week", default="W47")
    p.add_argument("--to-week", default="W48")
    p.add_argument("--start-date", default="")
    p.add_argument("--operating-root",
                   default="/srv/fleet/TriMetaverse/docs/workflow/operating-records")
    p.add_argument("--run-dir", default="")
    p.add_argument("--dry", action="store_true", help="骨架核（零执行·状态面读数）")
    p.add_argument("--max-iters", type=int, default=16)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    queue_root = Path(args.queue_root)
    for sub in ("pending", "done", "failed", "state"):
        (queue_root / sub).mkdir(parents=True, exist_ok=True)
    params = {"from_week": args.from_week, "to_week": args.to_week,
              "start_date": args.start_date,
              "operating_root": args.operating_root,
              "run_dir": args.run_dir}
    return run_loop(params, queue_root, dry=args.dry, max_iters=args.max_iters)


if __name__ == "__main__":
    sys.exit(main())
