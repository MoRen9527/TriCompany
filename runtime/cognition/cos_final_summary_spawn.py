"""COS final-summary 链后收口（CEO 三层合流 2026-11-26·CTO 令）：
链后联审（轮末钩·round_runner runJointReviewHook）**之后**一步——spawn COS 判断式汇总，
产出 close.json#/final 终版面（七席要点/分歧/收口结论/与初版差异·rationale 必填·非复制拼接）。
回滚：FADE_COS_FINAL=0。spawn 不可用=rc=-2（链零阻断）。"""
from __future__ import annotations

import argparse
import json as _json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_FINAL_PROMPT = """你是 TriCompany COS（值席）终版收口席。对以下 run-dir 做**判断式汇总**（非机器回填/非复制拼接），
产出 close.json 的 final 面（**只输出一个 JSON 对象**·零多余文本）：
{"final": {"seven_seat_points": [{"seat": "...", "point": "..."}],
           "divergences": [{"object": "a|b", "summary": "..."}],
           "conclusion": "<收口结论>",
           "diff_vs_initial": "<与 close 初版的差异要点>",
           "rationale": "<为何如此收口·必填非空>"}}
输入材料：joint-review.json（七席联审）、opinions-*.json（各席独立卷）、close.json（初版）、charter-*.json（任务书）。
纪律：judgement not copy；rationale 必填；只读材料零写入（禁创建/修改/删除任何文件·DP-019）。
run_dir=%s
run_id=%s
"""


def _spawn_seat(run_dir: Path, run_id: str, timeout_s: int = 900) -> dict:
    prompt = _FINAL_PROMPT % (run_dir, run_id)
    dsh_bin = os.environ.get("DSH_BIN", "/srv/fleet/dsh/node_modules/.bin/dsh")
    overlay = os.environ.get(
        "DSH_PRESET_OVERLAY", "/home/fleet/.dsh/patches/headless-agentpresets-overlay.yml")
    cmd = [dsh_bin, "--profile", "headless"]
    if overlay and os.path.isfile(overlay):
        cmd += ["--patch", overlay]
    cmd.append(prompt)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=str(run_dir))
        return {"rc": r.returncode, "out": (r.stdout or "")[-60000:], "err": (r.stderr or "")[:400]}
    except (FileNotFoundError, OSError) as e:
        return {"rc": -2, "out": "", "err": f"spawn unavailable: {type(e).__name__}: {e}"}
    except subprocess.TimeoutExpired:
        return {"rc": -1, "out": "", "err": f"timeout {timeout_s}s"}


def _extract_json(text: str) -> dict | None:
    if not isinstance(text, str):
        return None
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return _json.loads(text[i:j + 1])
    except Exception:
        return None


def _merge_final(run_dir: Path, payload: dict) -> dict | None:
    """把 COS final 面并入 close.json（终版面·rationale 必填校验）。"""
    fin = payload.get("final") if isinstance(payload, dict) else None
    if not isinstance(fin, dict):
        return None
    if not str(fin.get("rationale") or "").strip():
        return None                                   # rationale 必填（判断式）
    cp = run_dir / "close.json"
    try:
        doc = _json.loads(cp.read_text(encoding="utf-8")) if cp.is_file() else {}
    except Exception:
        doc = {}
    if not isinstance(doc, dict):
        doc = {}
    doc["final"] = fin
    cp.write_text(_json.dumps(doc, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    return fin


def run(args: argparse.Namespace) -> tuple[int, dict]:
    run_dir = Path(args.run_dir)
    out: dict = {"cos_final_summary_version": "1.0.0", "run_id": args.run_id}
    if os.environ.get("FADE_COS_FINAL", "1") == "0":
        out["verdict"] = "skip: FADE_COS_FINAL=0"
        return 0, out
    r = _spawn_seat(run_dir, args.run_id, timeout_s=args.spawn_timeout)
    if r["rc"] == -2:
        out["verdict"] = "skip: spawn unavailable（零阻断）"
        out["err"] = r["err"]
        return -2, out
    payload = _extract_json(r["out"]) if r["rc"] == 0 else None
    fin = _merge_final(run_dir, payload or {})
    if fin is None:
        out["verdict"] = "fail: final 面无效（rationale 缺/解析败）"
        return 2, out
    out["verdict"] = "pass"
    out["final_keys"] = sorted(fin.keys())
    return 0, out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="COS final-summary（链后收口·判断式）")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--spawn-timeout", type=int, default=900)
    args = p.parse_args(argv)
    code, out = run(args)
    print(_json.dumps(out, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
