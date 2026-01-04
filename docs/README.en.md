## G1GC Pause Time Analyzer & Advisor

This project parses **Java G1GC logs** (Java 9+ Unified Logging is the current primary target) and automatically:

- Finds **STW (Stop-The-World) pause** events and ranks the worst ones
- Detects common GC patterns that often cause latency spikes
- Prints **evidence lines** and **rule-based tuning advice**

### Quickstart (Windows)

Install (editable):

```bash
py -m pip install -e .
```

Analyze a log:

```bash
g1gc-advisor --log path\to\gc.log --max-pause-ms 200
```

If `g1gc-advisor` is not on PATH, run as a module:

```bash
py -m gccapture.cli --log path\to\gc.log --max-pause-ms 200
```

Save JSON:

```bash
g1gc-advisor --log gc.log --max-pause-ms 200 --json-out report.json
```

### Supported log format (initial)

- Java 9+ Unified Logging (`-Xlog:gc*`) with lines like:
  - `GC(12) Pause Young (Normal) (G1 Evacuation Pause) ... 15.123ms`
  - keywords such as `to-space exhausted`, `Evacuation Failure`, `Concurrent Mode Failure`, `Humongous`

### Rules (initial)

- **Humongous allocations**
  - Advice: consider `-XX:G1HeapRegionSize` (bigger regions can reduce humongous frequency), and review large-object allocation patterns in the app.
- **To-space exhausted / Evacuation Failure**
  - Advice: increase headroom (heap sizing / allocation spikes), consider `-XX:G1ReservePercent`, review fragmentation and mixed GC timing.
- **Concurrent Mode Failure**
  - Advice: start marking earlier (`-XX:InitiatingHeapOccupancyPercent`), check `-XX:ConcGCThreads` and CPU contention, mitigate allocation bursts.
- **Long Remark**
  - Advice: consider `-XX:+ParallelRefProcEnabled`, verify `-XX:ParallelGCThreads`.

### Rule trigger conditions

This project is currently **rule-based**. Each finding is produced by scanning parsed events for **keywords** and **simple thresholds**.

Notes:

- A “pause event” is recognized when a line contains `Pause ... <N>ms` and we take the **last** `...ms` on the line as the pause duration.
- The “target pause” is `--max-pause-ms` (conceptually `MaxGCPauseMillis`).

#### `g1.over_budget_summary` (Pause budget summary)

- **Triggers when**: at least one pause event has `duration_ms > max_pause_ms`.
- **Evidence**: histogram of over-budget pause “names” (best-effort extracted from the `Pause ...` part).
- **Severity**:
  - `warn` if over-budget count < 5
  - `critical` otherwise

#### `g1.to_space_exhausted` (To-space exhausted / Evacuation Failure)

- **Triggers when**: a log line contains either:
  - `to-space exhausted`, or
  - `evacuation failure`
- **Severity**: always `critical` (this usually correlates with severe STW spikes / Full GC risk).

#### `g1.concurrent_mode_failure` (Concurrent Mode Failure)

- **Triggers when**: a log line contains `concurrent mode failure`.
- **Severity**: always `critical`.

#### `g1.humongous` (Humongous allocations)

- **Triggers when**: a log line contains `humongous` (case-insensitive).
- **Severity**:
  - `warn` if matches < 5
  - `critical` otherwise

#### `g1.long_remark` (Long Pause Remark)

- **Triggers when**:
  - an event is recognized as `Pause Remark`, and
  - `duration_ms >= max(max_pause_ms, 200ms)`
- **Severity**:
  - `warn` if long remarks < 3
  - `critical` otherwise

### How to add new rules

Edit `src/gccapture/rules.py` and add a new `Rule` implementation, then register it in `DEFAULT_RULES`.


