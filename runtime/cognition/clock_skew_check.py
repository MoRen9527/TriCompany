"""clock_skew_check — 服务器时钟偏差自动告警（2026-08-24，CEO 批准）

对比本机时钟与权威 HTTP Date 源（百度/Cloudflare 双源），偏差超阈值即经
canonical notify 通道邮件告警。设计为 TriMC cron every-job 每小时执行：

  npx tsx src/cli.ts cron add --name clock-skew-check --every 3600000 \\
    --command "cd /srv/fleet/TriCompany && python3.8 -m runtime.cognition.clock_skew_check" \\
    --cwd /srv/fleet --run-as fleet

判定口径：
  - 双源任一可用即判（skew 取绝对值最小者；网络延迟只会高估偏差方向，
    60s 阈值下无影响）
  - 全部源不可达 → unverifiable，exit 0 不告警（网络抖动不制造假警报）
  - |skew| > threshold（默认 60s）→ 邮件告警 + exit 1（连续 3 次后
    healthz cron.degraded=true，邮件 + healthz 双通道信号）

Python 3.8 stdlib only（与周平面迁移五段链同解释器约束）。
"""

from __future__ import annotations

import argparse
import json as _json
import os
import sys
import urllib.request
from datetime import datetime, timezone

SOURCES = [
    "https://www.baidu.com",
    "https://www.taobao.com",
    "https://www.cloudflare.com",  # 部分 UA/网络下 HEAD 403，作第三备源
]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_http_date(value: str):
    """RFC 7231 IMF-fixdate: 'Mon, 24 Aug 2026 01:25:16 GMT'."""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def probe(source: str, timeout: float = 10.0):
    """HEAD 请求取 Date 头；返回 (skew_s|None, note)。skew = local - remote。"""
    local_before = _now_utc()
    try:
        req = urllib.request.Request(source, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            date_hdr = resp.headers.get("Date")
    except Exception as e:
        return None, "unreachable:%s" % type(e).__name__
    local_after = _now_utc()
    remote = _parse_http_date(date_hdr or "")
    if remote is None:
        return None, "bad_date_header"
    # 请求真实发出时刻落在 [local_before, local_after] 内，取中点估计
    mid = local_before + (local_after - local_before) / 2
    return (mid - remote).total_seconds(), "ok"


def main() -> int:
    p = argparse.ArgumentParser(description="server clock skew monitor")
    p.add_argument("--threshold", type=float, default=60.0,
                   help="alert when |skew| > this seconds (default 60)")
    p.add_argument("--dry-run", action="store_true",
                   help="print would-notify instead of sending")
    args = p.parse_args()

    skews = []
    notes = {}
    for s in SOURCES:
        skew, note = probe(s)
        notes[s] = note
        if skew is not None:
            skews.append(skew)

    result = {
        "objectType": "CLOCK_SKEW_CHECK",
        "threshold_s": args.threshold,
        "sources": notes,
        "check_time": _now_utc().isoformat(),
    }
    if not skews:
        result.update(status="unverifiable", skew_s=None)
        print(_json.dumps(result, ensure_ascii=False))
        return 0  # 网络不可达不制造假警报

    skew = min(skews, key=abs)  # 双源取偏差最小者（最接近真实）
    result.update(skew_s=round(skew, 3))

    if abs(skew) <= args.threshold:
        result.update(status="ok")
        print(_json.dumps(result, ensure_ascii=False))
        return 0

    result.update(status="alert")
    # stderr 摘要行：TriMC cron log 的 errorMessage 通道只取 stderr 段，
    # 写在这里保证 jobs 列表/日志界面可直接读出偏差值（CTO 审核建议）
    print("CLOCK SKEW ALERT %+.1fs (threshold %.0fs)" % (skew, args.threshold), file=sys.stderr)
    subject = "[TriMC] 服务器时钟偏差告警 %+.1fs（阈值 %.0fs）" % (skew, args.threshold)
    body_lines = [
        "服务器时钟偏差自动告警（clock-skew-check，每小时）",
        "",
        "状态: alert（|%+.1fs| > %.0fs）" % (skew, args.threshold),
        "实测: 本机 - 权威源 = %+.3f 秒（双源: %s）" % (skew, _json.dumps(notes, ensure_ascii=False)),
        "风险: 周平面迁移 cron（周日 23:59 北京时间 Asia/Shanghai）依赖本机钟，偏差已超阈值",
        "",
        "处置: chronyc tracking 查同步状态 -> chronyc makestep 校时 -> 复跑本检查",
        "（TriMC runbook §7 周日触发前时钟三查同款动作）",
        "",
        "说明: 偏差修复前每小时重复提醒（持续真值 escalation，healthz degraded 同步可见）",
    ]
    if args.dry_run:
        result.update(notify="dry_run", subject=subject)
        print(_json.dumps(result, ensure_ascii=False))
        return 1
    try:
        from runtime.cognition.notify import send_notification
        to = [x.strip() for x in (os.environ.get("CLOCK_SKEW_SMTP_TO") or "").split(",") if x.strip()]
        r = send_notification(
            subject=subject, body="\n".join(body_lines), to=to,
            context_id="clock-skew-check", trigger_mode="cron",
        )
        result.update(notify=r.get("status"))
    except Exception as e:  # notify best-effort：告警判定不因通知通道失败而吞
        result.update(notify="failed:%s" % e)
    print(_json.dumps(result, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    sys.exit(main())
