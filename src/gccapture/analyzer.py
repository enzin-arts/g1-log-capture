from __future__ import annotations

import json
from dataclasses import asdict
from typing import Iterable

from .models import AnalysisReport, EventKind, GCEvent
from .parser import parse_gc_log_lines
from .rules import DEFAULT_RULES, RuleContext


def analyze_gc_log(lines: Iterable[str], *, max_pause_ms: float) -> AnalysisReport:
    events = list(parse_gc_log_lines(lines))

    pauses = [
        e
        for e in events
        if e.kind == EventKind.PAUSE and e.duration_ms is not None
    ]
    pauses_sorted = sorted(pauses, key=lambda e: (e.duration_ms or 0.0), reverse=True)
    worst = pauses_sorted[:10]
    over_budget = [e for e in pauses if (e.duration_ms or 0.0) > max_pause_ms]

    ctx = RuleContext(max_pause_ms=max_pause_ms)
    findings = []
    for rule in DEFAULT_RULES:
        f = rule.evaluate(events, ctx)
        if f is not None:
            findings.append(f)

    return AnalysisReport(
        max_pause_ms=max_pause_ms,
        total_pause_events=len(pauses),
        over_budget_pause_events=len(over_budget),
        worst_pauses=worst,
        findings=findings,
    )


def report_to_json(report: AnalysisReport) -> str:
    def _event_to_dict(e: GCEvent) -> dict:
        d = asdict(e)
        d["kind"] = e.kind.value
        return d

    payload = {
        "max_pause_ms": report.max_pause_ms,
        "total_pause_events": report.total_pause_events,
        "over_budget_pause_events": report.over_budget_pause_events,
        "worst_pauses": [_event_to_dict(e) for e in report.worst_pauses],
        "findings": [asdict(f) for f in report.findings],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


