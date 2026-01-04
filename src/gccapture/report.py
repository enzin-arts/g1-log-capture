from __future__ import annotations

from .models import AnalysisReport


def render_text_report(r: AnalysisReport) -> str:
    lines: list[str] = []
    lines.append("G1GC Pause Time Analyzer & Advisor")
    lines.append("")
    lines.append(f"- MaxGCPauseMillis(목표): {r.max_pause_ms:.1f} ms")
    lines.append(f"- Pause 이벤트 수: {r.total_pause_events}")
    lines.append(f"- 목표 초과(Pause > 목표) 수: {r.over_budget_pause_events}")
    lines.append("")

    if r.worst_pauses:
        lines.append("최악(가장 긴) Pause Top 10:")
        for e in r.worst_pauses:
            dur = f"{(e.duration_ms or 0.0):.3f}ms"
            name = e.name or "(unknown)"
            lines.append(f"  - L{e.line_no} GC({e.gc_id}) {dur} | {name}")
        lines.append("")

    if not r.findings:
        lines.append("진단 결과: 특이 패턴을 찾지 못했습니다(또는 로그 포맷 미지원).")
        return "\n".join(lines)

    lines.append("자동 진단/제안:")
    for f in r.findings:
        sev = f.severity.value.upper()
        lines.append(f"")
        lines.append(f"[{sev}] {f.title} ({f.rule_id})")
        if f.metrics:
            lines.append(f"- metrics: {f.metrics}")
        if f.evidence:
            lines.append("- evidence:")
            for ev in f.evidence:
                lines.append(f"  - {ev}")
        if f.advice:
            lines.append("- advice:")
            for ad in f.advice:
                lines.append(f"  - {ad}")

    return "\n".join(lines)


