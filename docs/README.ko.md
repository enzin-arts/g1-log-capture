## G1GC Pause Time Analyzer & Advisor

Java **G1GC 로그**(초기 버전은 Java 9+ Unified Logging을 우선 대상으로 함)를 파싱해서:

- **STW(Stop-The-World) Pause** 이벤트를 수집/정렬하고
- 성능 저하를 유발하는 대표 패턴을 자동 탐지하며
- **근거 라인(evidence)**과 함께 **룰 기반 튜닝 제안**을 출력하는 도구입니다.

### 빠른 시작(Windows)

설치(editable):

```bash
py -m pip install -e .
```

분석 실행:

```bash
g1gc-advisor --log path\to\gc.log --max-pause-ms 200
```

`g1gc-advisor`가 인식되지 않으면 모듈로 실행:

```bash
py -m gccapture.cli --log path\to\gc.log --max-pause-ms 200
```

JSON 저장:

```bash
g1gc-advisor --log gc.log --max-pause-ms 200 --json-out report.json
```

### 지원 로그 포맷(초기)

- Java 9+ Unified Logging (`-Xlog:gc*`)
- 예시:
  - `GC(12) Pause Young (Normal) (G1 Evacuation Pause) ... 15.123ms`
  - `to-space exhausted`, `Evacuation Failure`, `Concurrent Mode Failure`, `Humongous` 같은 키워드 기반 탐지

### 진단 규칙(초기)

- **Humongous 할당**
  - 제안: `-XX:G1HeapRegionSize` 증가 검토(휴몽거스 빈도 완화 가능), 대형 객체 생성 패턴 점검
- **To-space exhausted / Evacuation Failure**
  - 제안: 힙 여유 확보(힙 크기/할당률 버스트 완화), `-XX:G1ReservePercent` 검토, 단편화/혼합 수집 타이밍 점검
- **Concurrent Mode Failure**
  - 제안: IHOP 조정으로 마킹 시작을 앞당김(`-XX:InitiatingHeapOccupancyPercent`), `-XX:ConcGCThreads`/CPU 경합 점검, 할당률 버스트 완화
- **Remark 과다(긴 Pause Remark)**
  - 제안: `-XX:+ParallelRefProcEnabled` 검토, `-XX:ParallelGCThreads` 점검

### 진단이 뜨는 조건(Rule trigger conditions)

현재 버전은 **룰 기반(rule-based)** 입니다. 파서가 뽑아낸 이벤트들에서 **키워드/단순 임계치**로 조건을 만족하면 Finding(진단)을 생성합니다.

참고:

- “pause 이벤트”는 한 줄에 `Pause ... <N>ms` 형태가 있을 때로 인식하며, 그 줄에 `...ms`가 여러 개면 **마지막 `ms`** 값을 pause duration으로 사용합니다.
- “목표 pause”는 `--max-pause-ms` 값입니다(개념적으로 `MaxGCPauseMillis`).

#### `g1.over_budget_summary` (Pause 목표 초과 요약)

- **조건**: `duration_ms > max_pause_ms`인 pause 이벤트가 1개 이상 존재
- **근거(evidence)**: 목표 초과 pause들의 “이름”(best-effort로 `Pause ...`에서 추출)별 발생 횟수 상위 목록
- **심각도(severity)**:
  - 목표 초과 건수 < 5면 `warn`
  - 그 외 `critical`

#### `g1.to_space_exhausted` (To-space exhausted / Evacuation Failure)

- **조건**: 아래 키워드 중 하나를 포함하는 로그 라인이 존재
  - `to-space exhausted`
  - `evacuation failure`
- **심각도**: 항상 `critical` (대개 STW 급증/Full GC 위험과 강하게 연관)

#### `g1.concurrent_mode_failure` (Concurrent Mode Failure)

- **조건**: `concurrent mode failure`를 포함하는 로그 라인이 존재
- **심각도**: 항상 `critical`

#### `g1.humongous` (Humongous 할당/영역 증가)

- **조건**: `humongous`(대소문자 무시)를 포함하는 로그 라인이 존재
- **심각도**:
  - 매칭 건수 < 5면 `warn`
  - 그 외 `critical`

#### `g1.long_remark` (긴 Pause Remark)

- **조건**:
  - `Pause Remark` 이벤트로 인식되고,
  - `duration_ms >= max(max_pause_ms, 200ms)` 를 만족
- **심각도**:
  - 긴 remark 건수 < 3이면 `warn`
  - 그 외 `critical`

### 규칙 추가 방법

`src/gccapture/rules.py`에 `Rule` 클래스를 하나 추가하고 `DEFAULT_RULES`에 등록하면 됩니다.


