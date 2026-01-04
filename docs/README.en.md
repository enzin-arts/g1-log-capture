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

### How to add new rules

Edit `src/gccapture/rules.py` and add a new `Rule` implementation, then register it in `DEFAULT_RULES`.


