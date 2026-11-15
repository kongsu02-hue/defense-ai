# 국방 AI 교육

2026년 국방 AI 현황(공개 자료 기반)과, **AI 에이전트로 업무용 앱을 만들고 GitHub로 관리하고 PC 업무를 자동화하는** 실습 과정입니다.

🌐 **웹사이트:** https://kongsu02-hue.github.io/defense-ai/

## 구성

| 경로 | 내용 |
|---|---|
| `index.html` | 과정 소개, 시간표 |
| `lecture.html` | 강의: 한국·미국 국방 AI 정책과 예산, 전장 사례, 국제 규범 (출처 포함) |
| `agent-lab.html` | AI 에이전트: 앱 개발 · GitHub · PC 제어, 안전 원칙 |
| `practice.html` | 앱 개발 실습 4개 + 종합 과제 |
| `agent-labs/` | Python 에이전트 3종 |
| `practice/` | 실습 파일 (요구사항, 테스트, 가상 데이터, 참고 답안) |
| `cmmc/index.html` | CMMC 레벨 1 실습 시뮬레이터: 범위 정의 → 가상 PowerShell 점검·조치 → 설정·문서 작업 → 증거 → 자체평가 → SPRS 제출 모의 |
| `simulator.html` | 부록: AI 모델 개념 시뮬레이터 |

## AI 에이전트 (`agent-labs/`)

| 파일 | 하는 일 | 안전장치 |
|---|---|---|
| `agent_core.py` | 공통 루프: 도구 호출, 사람 승인, 기록(`logs/`), 최대 반복 | — |
| `lab1_app_builder.py` | 요구사항으로 앱 작성 → 테스트 → 수정 반복 | `workspace/` 밖 접근 차단, 명령 허용 목록 + 승인 |
| `lab2_github_agent.py` | 저장소·이슈·PR·Actions 점검, 브랜치·커밋·초안 PR | 쓰기 작업 전부 승인, main 직접 푸시 금지 |
| `lab3_pc_agent.py` | PC 상태 점검, 파일 검색, 폴더 정리, 프로그램 열기 | 홈 폴더 제한, 삭제 도구 없음, 위험 명령 차단 |

```powershell
cd agent-labs
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY="sk-ant-..."
python lab1_app_builder.py
python lab2_github_agent.py --repo ..
python lab3_pc_agent.py
```

## 앱 개발 실습 (`practice/`)

| 실습 | 내용 | 검증 |
|---|---|---|
| `lab1-checklist` | Claude Code로 장비 점검 체크리스트 웹앱 | 요구사항 R1~R7 |
| `lab2-maintenance` | 테스트 주도로 정비 이력 분석기 | `pytest -q` (8개) |
| `lab3-github-flow` | 이슈 → PR → Actions → Pages 배포 | CI 통과, 리뷰 |
| `lab4-pc-automation` | 일일 보고 자동 취합기 + 작업 스케줄러 | 미보고 표시, 원본 보존 |

교관용 답안 확인: `cd practice\lab2-maintenance; $env:SOLUTION="1"; pytest -q`

> 모든 데이터는 교육용 가상 데이터입니다. 실습 코드는 교육 목적으로 Claude API를 사용하며, 실제 군 업무망에서는 승인된 AI 체계와 보안 규정을 따르십시오.
