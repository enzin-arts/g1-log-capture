## G1GC Pause Time Analyzer & Advisor

A rule-based analyzer that parses **G1GC logs** and:

- Detects **Stop-The-World (STW) pauses** exceeding a target (`MaxGCPauseMillis`)
- Flags common performance-degrading patterns (e.g., **to-space exhausted**, **humongous allocations**, **concurrent mode failure**, **long remark**)
- Produces **actionable tuning suggestions** with evidence lines

### Docs (KR / EN)

- **Korean**: `docs/README.ko.md`
- **English**: `docs/README.en.md`

### Quickstart

Install (editable):

```bash
py -m pip install -e .
```

Run:

```bash
g1gc-advisor --log path\to\gc.log --max-pause-ms 200
```

Without installing (module execution):

```bash
py -m gccapture.cli --log path\to\gc.log --max-pause-ms 200
```

Write JSON report:

```bash
g1gc-advisor --log gc.log --max-pause-ms 200 --json-out report.json
```



