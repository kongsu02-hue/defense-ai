# AI 에이전트 실습

에이전트는 목표를 받으면 **생각 → 도구 호출 → 관찰**을 반복해 스스로 일을 진행하는 AI 프로그램입니다.
세 단계로 실습합니다. 모든 데이터(`data/*.json`)는 교육용 가상 데이터입니다.

| 실습 | 파일 | 준비물 | 배우는 것 |
|---|---|---|---|
| 0. 웹 실습 | [`../agent-lab.html`](../agent-lab.html) | 브라우저 | 루프를 한 단계씩 진행하며 흐름 관찰, 지휘관 승인/거부 |
| 1. 루프 원리 | `lab1_agent_loop.py` | Python 3.10+ | 규칙 기반 '두뇌'로 루프 구조, 단계 제한, 승인 대기 |
| 2. Claude 에이전트 | `lab2_claude_agent.py` | Python + Anthropic API 키 | LLM이 도구를 골라 호출, 오류 처리, Human-in-the-loop |

공통 도구는 `tools.py`에 있습니다.

| 도구 | 하는 일 |
|---|---|
| `check_inventory(unit)` | 부대 재고, 품목별 남은 일수, 안전재고(3일) 미달 품목 |
| `predict_maintenance(threshold)` | 주행거리·엔진온도·진동으로 정비 위험점수(0~1) 산출 |
| `get_reports()` | 출처·신뢰도가 다른 관측 보고 4건 |
| `request_supply(unit, item, amount)` | 보급 요청 초안 — **사람 승인 없이는 실행되지 않음** |

## 실행 방법 (Windows PowerShell)

```powershell
cd agent-labs

# 실습 1 — API 키 없이 실행
python lab1_agent_loop.py

# 실습 2 — Claude 연동
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python lab2_claude_agent.py
python lab2_claude_agent.py "오늘 정보 보고서를 신뢰도 기준으로 요약해줘"
python lab2_claude_agent.py "정비가 시급한 차량과 그 이유를 알려줘"
```

실습 2는 `claude-opus-5-5` 모델을 쓰며, 안전 분류기가 요청을 거절하면 서버가 다른 모델로 자동 재시도하도록(`fallbacks="default"`) 설정되어 있습니다.

## 과제

1. `lab1_agent_loop.py`의 `MAX_STEPS`를 2로 줄여 실행하고, 단계 제한이 왜 필요한지 설명하라.
2. 실습 2에서 보급 요청을 거부(`n`)했을 때 Claude의 최종 답변이 어떻게 달라지는지 비교하라.
3. `tools.py`에 새 도구(예: 부대 위치 조회)를 추가하고 `TOOL_SCHEMAS`에 설명을 넣어 Claude가 사용하게 하라.
4. 정보 보고서 요약에서 신뢰도 '하' 보고서를 근거로 쓰지 않도록 하려면 프롬프트(SYSTEM)와 도구 중 어디를 바꾸는 것이 더 안전한가?

> AI는 판단을 돕는 도구이며, 실행 행위의 최종 결정은 사람이 합니다.
