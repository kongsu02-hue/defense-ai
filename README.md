# 국방 AI 교육

AI 기초부터 국방 분야 활용, 윤리·보안, **AI 에이전트 실습**까지 다루는 교육 자료입니다.

🌐 **웹사이트:** https://__OWNER__.github.io/__NAME__/

## 구성

| 경로 | 내용 |
|---|---|
| `index.html` | 교육 홈페이지 |
| `materials/defense-ai-lecture.pptx` | 국방 AI 교육 슬라이드 |
| `simulator.html` | 국방 AI 실습 시뮬레이터 (표적 탐지, 예측정비, 적대적 공격, 결심지원) |
| `agent-lab.html` | 웹 기반 AI 에이전트 실습실 (API 키 불필요) |
| `agent-labs/` | Python AI 에이전트 실습 예제 |

## AI 에이전트 실습 (`agent-labs/`)

| 실습 | 파일 | 설명 |
|---|---|---|
| 1 | `lab1_react_agent_mock.py` | 규칙 기반 두뇌로 ReAct(생각→행동→관찰) 루프 이해. API 키 불필요 |
| 2 | `lab2_claude_tool_agent.py` | Claude API 도구 사용 에이전트. 보급 요청 시 지휘관 승인(Human-in-the-loop) |
| 3 | `lab3_multi_agent_staff.py` | 정보·군수·정비 참모 에이전트 + 참모장 종합 보고 |

공통 도구는 `tools.py`, 가상 데이터는 `data/*.json`에 있습니다.

```powershell
cd agent-labs
python lab1_react_agent_mock.py

pip install -r requirements.txt
$env:ANTHROPIC_API_KEY="sk-ant-..."
python lab2_claude_tool_agent.py "2대대와 3대대 보급 상태를 비교하고 조치를 건의하라"
python lab3_multi_agent_staff.py
```

> 모든 데이터는 교육용 가상 데이터입니다. 실제 부대·장비·작전 정보와 무관합니다.
