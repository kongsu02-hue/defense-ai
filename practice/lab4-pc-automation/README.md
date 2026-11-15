# 실습 4. 내 PC 업무 자동화 앱 — 일일 보고 자동 취합기

**목표:** 매일 반복하는 PC 작업(여러 사람의 보고 파일을 모아 한 장으로 정리)을 AI 에이전트와 함께 자동화 앱으로 만들고, Windows 작업 스케줄러에 등록한다.
**도구:** Python 3.10+, Claude Code, `agent-labs/lab3_pc_agent.py` · **시간:** 90분

## 상황 (가상)

매일 17시까지 각 분대가 `보고함` 폴더에 CSV 보고(인원·장비 이상·특이사항)를 넣는다.
행정병이 이를 열어 복사·붙여넣기로 취합 보고서를 만드는 데 30분이 걸린다.

## 1. 연습용 데이터 만들기

```powershell
cd practice\lab4-pc-automation
python make_sample.py          # 홈 폴더 아래 '보고함_실습' 폴더에 가상 보고 6개 생성
```

## 2. 에이전트에게 앱 개발 맡기기

Claude Code에 아래 요구사항을 준다.

| 번호 | 요구사항 |
|---|---|
| R1 | `merge_reports.py <폴더>` 로 실행, 폴더 안 오늘 날짜 CSV를 모두 읽는다 |
| R2 | 분대별 인원(편성/현재), 장비 이상 건수, 특이사항을 한 표로 합친다 |
| R3 | 보고가 없는 분대를 '미보고'로 표시한다 (분대 목록은 설정 파일) |
| R4 | 결과를 `취합_YYYYMMDD.csv`(엑셀용 UTF-8 BOM)와 `취합_YYYYMMDD.txt`(메신저 붙여넣기용)로 저장 |
| R5 | 원본 파일은 수정·삭제하지 않는다. 처리한 파일은 `처리완료/` 하위 폴더로 이동만 한다 |
| R6 | 표준 라이브러리만 사용, 오류가 나도 다른 파일은 계속 처리하고 오류 목록을 출력 |

## 3. 검증

```powershell
python merge_reports.py "$HOME\보고함_실습"
```

- 미보고 분대가 정확히 표시되는가?
- 잘못된 형식의 파일(샘플에 1개 포함)에서 멈추지 않는가?
- 원본이 그대로 남아 있는가?

## 4. 작업 스케줄러 등록

```powershell
$py = (Get-Command python).Source
$act = New-ScheduledTaskAction -Execute $py -Argument "`"$PWD\merge_reports.py`" `"$HOME\보고함_실습`""
$trg = New-ScheduledTaskTrigger -Daily -At 17:10
Register-ScheduledTask -TaskName "일일보고취합_실습" -Action $act -Trigger $trg
# 실습 후 삭제: Unregister-ScheduledTask -TaskName "일일보고취합_실습" -Confirm:$false
```

## 5. PC 제어 에이전트로 점검

```powershell
python agent-labs\lab3_pc_agent.py "보고함_실습 폴더 상태를 요약하고 오늘 취합 파일이 만들어졌는지 확인해줘"
```

## 참고 답안

[`solution/merge_reports.py`](solution/merge_reports.py)

## 생각해 볼 점

- 에이전트에게 PC 전체 권한을 주면 편하지만, 왜 폴더 제한·승인·삭제 금지를 두는가?
- 업무망 PC에 이런 자동화를 설치하려면 어떤 승인 절차가 필요한가?
