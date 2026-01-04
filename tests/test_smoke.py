from __future__ import annotations

from pathlib import Path

from gccapture.analyzer import analyze_gc_log


def test_analyze_sample_log_smoke():
    sample = Path("samples/g1_sample.log")
    assert sample.exists()

    report = analyze_gc_log(sample.read_text(encoding="utf-8").splitlines(True), max_pause_ms=200.0)

    assert report.total_pause_events >= 1
    assert report.over_budget_pause_events >= 1

    rule_ids = {f.rule_id for f in report.findings}
    assert "g1.to_space_exhausted" in rule_ids
    assert "g1.humongous" in rule_ids
    assert "g1.concurrent_mode_failure" in rule_ids
    assert "g1.long_remark" in rule_ids


