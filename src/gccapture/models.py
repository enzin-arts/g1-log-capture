from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EventKind(str, Enum):
    PAUSE = "pause"
    OTHER = "other"


@dataclass(frozen=True)
class GCEvent:
    """
    Parsed GC event (best-effort).

    Primarily targets Java 9+ Unified Logging lines such as:
      GC(12) Pause Young (Normal) (G1 Evacuation Pause) ... 15.123ms
    """

    raw: str
    line_no: int
    gc_id: Optional[int] = None
    kind: EventKind = EventKind.OTHER
    name: str = ""
    duration_ms: Optional[float] = None
    tags: tuple[str, ...] = ()


class FindingSeverity(str, Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    severity: FindingSeverity
    evidence: list[str] = field(default_factory=list)
    advice: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisReport:
    max_pause_ms: float
    total_pause_events: int
    over_budget_pause_events: int
    worst_pauses: list[GCEvent]
    findings: list[Finding]


