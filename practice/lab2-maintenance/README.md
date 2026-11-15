# 실습 2. 테스트 주도로 업무 도구 만들기 — 정비 이력 분석기

**목표:** "테스트가 곧 요구사항"인 방식으로 AI 에이전트에게 일을 맡기고, 결과를 테스트로 검증한다.
**도구:** Python 3.10+, pytest, Claude Code(또는 `agent-labs/lab1_app_builder.py`) · **시간:** 90분

## 구성

| 파일 | 내용 |
|---|---|
| `data/records.csv` | 차량 정비 이력 10건 (가상) |
| `data/vehicles.csv` | 차량별 정비 후 주행거리 (가상) |
| `maintenance.py` | **채울 파일.** 함수 뼈대와 설명만 있음 |
| `tests/test_maintenance.py` | 통과해야 할 테스트 8개 |
| `solution/maintenance.py` | 참고 답안 (교관용) |

## 진행 순서

```powershell
cd practice\lab2-maintenance
pip install pytest
pytest -q                     # 처음엔 8개 모두 실패 — 정상
claude                        # Claude Code 실행
```

1. 에이전트에게 지시: *"tests/test_maintenance.py를 읽고, 테스트를 고치지 말고 maintenance.py만 구현해서 모두 통과시켜라. 표준 라이브러리만 사용."*
2. 에이전트가 테스트를 실행·수정하는 과정을 관찰한다. **테스트 파일을 바꾸려 하면 거부한다.**
3. `pytest -q`로 직접 확인하고, `python maintenance.py`로 보고서를 출력해 본다.
4. 기능 추가를 **테스트부터** 요청한다: *"차량 종류별 평균 정비비 함수를 추가하라. 먼저 실패하는 테스트를 쓰고 보여준 다음 구현하라."*

## 교관 확인

```powershell
$env:SOLUTION="1"; pytest -q    # 참고 답안으로 8개 통과 확인
```

## 생각해 볼 점

- 에이전트가 테스트를 통과시키려고 **테스트를 고치거나 특정 값을 하드코딩**하면? → 사람이 diff를 읽어야 하는 이유
- 실제 정비 데이터를 외부 AI 서비스에 올려도 되는가? → 보안 등급과 승인된 체계 확인
