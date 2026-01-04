from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .models import Finding, FindingSeverity, GCEvent


def _contains_any(s: str, needles: Iterable[str]) -> bool:
    sl = s.lower()
    return any(n.lower() in sl for n in needles)


@dataclass(frozen=True)
class RuleContext:
    max_pause_ms: float


class Rule:
    rule_id: str
    title: str

    def evaluate(self, events: list[GCEvent], ctx: RuleContext) -> Finding | None:  # pragma: no cover
        raise NotImplementedError


class HumongousRule(Rule):
    rule_id = "g1.humongous"
    title = "Humongous 할당/영역 증가 패턴"

    def evaluate(self, events: list[GCEvent], ctx: RuleContext) -> Finding | None:
        matches: list[GCEvent] = []
        for e in events:
            if _contains_any(e.raw, ["humongous", "g1 humongous allocation"]):
                matches.append(e)

        if len(matches) == 0:
            return None

        severity = FindingSeverity.WARN if len(matches) < 5 else FindingSeverity.CRITICAL
        evidence = [f"L{e.line_no}: {e.raw}" for e in matches[:10]]
        advice = [
            "Humongous 객체(일반적으로 region의 50% 이상)가 자주 생기면 G1이 region을 통째로 점유/반납하며 pause와 단편화가 악화될 수 있습니다.",
            "애플리케이션 측: 큰 배열/버퍼/문자열 등 대형 객체 생성 패턴(특히 burst)을 점검하세요.",
            "JVM 옵션: `-XX:G1HeapRegionSize`를 키우는 것을 검토하세요(예: 1m -> 2m/4m). 단, region이 커지면 세밀한 수집은 불리할 수 있습니다.",
        ]
        return Finding(
            rule_id=self.rule_id,
            title=self.title,
            severity=severity,
            evidence=evidence,
            advice=advice,
            metrics={"matches": len(matches)},
        )


class ToSpaceExhaustedRule(Rule):
    rule_id = "g1.to_space_exhausted"
    title = "To-space exhausted / Evacuation Failure 패턴"

    def evaluate(self, events: list[GCEvent], ctx: RuleContext) -> Finding | None:
        matches: list[GCEvent] = []
        for e in events:
            if _contains_any(e.raw, ["to-space exhausted", "evacuation failure"]):
                matches.append(e)

        if not matches:
            return None

        severity = FindingSeverity.CRITICAL
        evidence = [f"L{e.line_no}: {e.raw}" for e in matches[:10]]
        advice = [
            "Evacuation 시 복사해둘 여유 region(to-space)이 부족하면 STW가 길어지고(또는 Full GC) 급격한 지연이 발생할 수 있습니다.",
            "우선 힙 여유를 확보하세요: 힙 크기(Xmx) 증가 또는 할당률 급증 구간 점검.",
            "G1 리저브를 늘려 여유 region을 확보하는 옵션을 검토하세요: `-XX:G1ReservePercent`.",
            "단편화/혼합 수집 타이밍 이슈라면 IHOP/혼합 수집 관련 파라미터를 조정해 볼 수 있습니다: `-XX:InitiatingHeapOccupancyPercent` 등.",
        ]
        return Finding(
            rule_id=self.rule_id,
            title=self.title,
            severity=severity,
            evidence=evidence,
            advice=advice,
            metrics={"matches": len(matches)},
        )


class ConcurrentModeFailureRule(Rule):
    rule_id = "g1.concurrent_mode_failure"
    title = "Concurrent Mode Failure 패턴"

    def evaluate(self, events: list[GCEvent], ctx: RuleContext) -> Finding | None:
        matches: list[GCEvent] = []
        for e in events:
            if _contains_any(e.raw, ["concurrent mode failure"]):
                matches.append(e)

        if not matches:
            return None

        severity = FindingSeverity.CRITICAL
        evidence = [f"L{e.line_no}: {e.raw}" for e in matches[:10]]
        advice = [
            "Concurrent marking이 제때 끝나지 못하면(할당률/CPU 경합) STW로 전환되며 긴 pause가 발생할 수 있습니다.",
            "마킹 시작을 더 앞당기도록 IHOP 조정을 검토하세요: `-XX:InitiatingHeapOccupancyPercent` (낮추면 더 일찍 시작).",
            "동시 GC 쓰레드가 부족하면 `-XX:ConcGCThreads`를 늘리는 것을 검토하세요(전체 CPU 여유가 있어야 효과적).",
            "할당률이 과도한 구간(버스트 트래픽/배치)을 찾아 완화(버퍼링/레이트리밋/객체 재사용)하는 것도 중요합니다.",
        ]
        return Finding(
            rule_id=self.rule_id,
            title=self.title,
            severity=severity,
            evidence=evidence,
            advice=advice,
            metrics={"matches": len(matches)},
        )


class LongRemarkRule(Rule):
    rule_id = "g1.long_remark"
    title = "Remark 단계 과다(긴 Pause Remark)"

    def evaluate(self, events: list[GCEvent], ctx: RuleContext) -> Finding | None:
        remark_events = [e for e in events if "pause remark" in e.name.lower() or "pause remark" in e.raw.lower()]
        if not remark_events:
            return None

        # Heuristic: remark pause > max_pause_ms or > 200ms
        threshold = max(ctx.max_pause_ms, 200.0)
        long_remarks = [e for e in remark_events if (e.duration_ms or 0) >= threshold]
        if not long_remarks:
            return None

        severity = FindingSeverity.WARN if len(long_remarks) < 3 else FindingSeverity.CRITICAL
        evidence = [f"L{e.line_no}: {e.raw}" for e in long_remarks[:10]]
        advice = [
            "Remark는 참조 처리(Reference Processing)와 같은 작업이 집중되면 길어질 수 있습니다.",
            "옵션 검토: `-XX:+ParallelRefProcEnabled` 활성화로 참조 처리를 병렬화할 수 있습니다.",
            "또한 `-XX:ParallelGCThreads`(STW 작업 스레드)가 지나치게 낮지 않은지 점검하세요.",
        ]
        return Finding(
            rule_id=self.rule_id,
            title=self.title,
            severity=severity,
            evidence=evidence,
            advice=advice,
            metrics={"remark_events": len(remark_events), "long_remarks": len(long_remarks), "threshold_ms": threshold},
        )


class OverBudgetPauseSummaryRule(Rule):
    rule_id = "g1.over_budget_summary"
    title = "Pause 목표치 초과 요약"

    def evaluate(self, events: list[GCEvent], ctx: RuleContext) -> Finding | None:
        pauses = [e for e in events if e.duration_ms is not None and "pause" in e.raw.lower()]
        if not pauses:
            return None
        over = [e for e in pauses if (e.duration_ms or 0) > ctx.max_pause_ms]
        if not over:
            return None

        # quick cause histogram from pause name
        cause_counts = Counter((e.name or "unknown") for e in over)
        top = cause_counts.most_common(5)
        evidence = [f"{name}: {cnt}회" for name, cnt in top]
        advice = [
            f"Pause 목표({ctx.max_pause_ms}ms)를 초과한 이벤트가 {len(over)}/{len(pauses)}회입니다.",
            "아래 개별 패턴 진단(To-space/Humongous/Remark/CMF 등)을 함께 확인하세요.",
        ]
        severity = FindingSeverity.WARN if len(over) < 5 else FindingSeverity.CRITICAL
        return Finding(
            rule_id=self.rule_id,
            title=self.title,
            severity=severity,
            evidence=evidence,
            advice=advice,
            metrics={"pause_events": len(pauses), "over_budget": len(over)},
        )


DEFAULT_RULES: list[Rule] = [
    OverBudgetPauseSummaryRule(),
    ToSpaceExhaustedRule(),
    ConcurrentModeFailureRule(),
    HumongousRule(),
    LongRemarkRule(),
]


