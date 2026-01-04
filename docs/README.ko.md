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

### 규칙 추가 방법

`src/gccapture/rules.py`에 `Rule` 클래스를 하나 추가하고 `DEFAULT_RULES`에 등록하면 됩니다.


