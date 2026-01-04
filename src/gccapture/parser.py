from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable, Iterator, Optional

from .models import EventKind, GCEvent


# Unified logging examples:
# [2026-01-04T10:10:10.123+0900][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 512M->123M(2048M) 12.345ms
# [0.123s][info][gc] GC(12) Pause Remark 45.678ms
#
# Note: trailing "\b" after ")" breaks matching because ")" is not a word-char, so
# the boundary condition is not satisfied (non-word -> non-word). Use a safer guard.
_GC_ID_RE = re.compile(r"(?<!\w)GC\((\d+)\)")
_DURATION_MS_RE = re.compile(r"(?P<ms>\d+(?:\.\d+)?)ms\b")

# Best-effort pause name capture: "Pause ... 12.3ms"
_PAUSE_NAME_RE = re.compile(r"\bPause\s+(?P<name>.+?)\s+(?:\d+(?:\.\d+)?)ms\b")

# Optional tags segment: [..][..][gc,phases] style; we keep them if present
_TAGS_PREFIX_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\[(?P<level>[^\]]+)\]\[(?P<tags>[^\]]+)\]\s+")


def _extract_gc_id(line: str) -> Optional[int]:
    m = _GC_ID_RE.search(line)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _extract_duration_ms(line: str) -> Optional[float]:
    # Prefer last "...ms" in the line (pause lines can contain multiple durations)
    ms_matches = list(_DURATION_MS_RE.finditer(line))
    if not ms_matches:
        return None
    m = ms_matches[-1]
    try:
        return float(m.group("ms"))
    except ValueError:
        return None


def _extract_tags(line: str) -> tuple[str, ...]:
    m = _TAGS_PREFIX_RE.match(line)
    if not m:
        return ()
    tags = m.group("tags").strip()
    # tags may be "gc" or "gc,phases"
    return tuple(t.strip() for t in tags.split(",") if t.strip())


def parse_gc_log_lines(lines: Iterable[str]) -> Iterator[GCEvent]:
    """
    Parse GC log lines (best-effort).

    Output includes pause events with duration_ms when recognized.
    """
    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        e = GCEvent(raw=line, line_no=idx, gc_id=_extract_gc_id(line), tags=_extract_tags(line))

        if " Pause " in line or line.strip().startswith("GC(") and "Pause " in line:
            name_m = _PAUSE_NAME_RE.search(line)
            name = name_m.group("name").strip() if name_m else ""
            e = replace(e, kind=EventKind.PAUSE, name=name, duration_ms=_extract_duration_ms(line))
        else:
            # Still capture duration for potential phase/aux events if present
            dur = _extract_duration_ms(line)
            if dur is not None:
                e = replace(e, duration_ms=dur)

        yield e


