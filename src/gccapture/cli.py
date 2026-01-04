from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .analyzer import analyze_gc_log, report_to_json
from .report import render_text_report


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="g1gc-advisor", description="G1GC Pause Time Analyzer & Advisor (rule-based)")
    p.add_argument("--log", required=True, help="GC 로그 파일 경로")
    p.add_argument("--max-pause-ms", type=float, default=200.0, help="목표 pause 시간(ms). 기본값 200")
    p.add_argument("--json-out", default=None, help="JSON 리포트 저장 경로(선택)")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    log_path = Path(args.log)
    if not log_path.exists():
        raise SystemExit(f"로그 파일이 없습니다: {log_path}")

    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        report = analyze_gc_log(f, max_pause_ms=float(args.max_pause_ms))

    print(render_text_report(report))

    if args.json_out:
        out = Path(args.json_out)
        out.write_text(report_to_json(report), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


