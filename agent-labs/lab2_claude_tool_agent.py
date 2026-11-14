"""실습 2. Claude API 도구 사용(Tool Use) 에이전트

실습 1의 규칙 기반 '두뇌'를 실제 LLM(Claude)으로 바꿉니다.
LLM이 스스로 어떤 도구를 어떤 순서로 쓸지 결정합니다.
보급 요청(request_supply)은 사람의 승인을 받아야만 실행됩니다.

준비:
  pip install -r requirements.txt
  set ANTHROPIC_API_KEY=sk-ant-...      (PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-...")
실행:
  python lab2_claude_tool_agent.py "2대대와 3대대 보급 상태를 비교하고 필요한 조치를 건의하라"
"""
import json
import sys

import anthropic

from tools import TOOL_SCHEMAS, TOOLS

MODEL = "claude-opus-5-5"
SYSTEM = (
    "당신은 육군 대대 참모를 돕는 군수·정비 AI 보조관입니다. "
    "반드시 도구로 확인한 데이터에 근거해 답하고, 추측은 '추정'이라고 표시하세요. "
    "보급 요청 같은 실행 행동은 초안만 만들고 최종 결정은 지휘관에게 맡기세요. "
    "답변은 한국어로, 결론-근거-건의 순서로 간결하게 작성하세요."
)


def execute(name: str, args: dict) -> str:
    if name == "request_supply":
        print(f"\n🛑 승인 요청: {args}")
        ok = input("   지휘관 승인하시겠습니까? (y/N) ").strip().lower() == "y"
        args = {**args, "approved": ok}
    try:
        return json.dumps(TOOLS[name](**args), ensure_ascii=False)
    except Exception as e:  # 도구 오류도 에이전트에게 알려준다
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def run(goal: str, max_turns: int = 8):
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": goal}]
    for _ in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        if response.stop_reason == "refusal":
            print("요청이 거절되었습니다.")
            return
        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            print("\n✅ 최종 답변\n" + "".join(b.text for b in response.content if b.type == "text"))
            return

        results = []
        for t in tool_uses:
            print(f"🔧 {t.name}({json.dumps(t.input, ensure_ascii=False)})")
            results.append({"type": "tool_result", "tool_use_id": t.id, "content": execute(t.name, t.input)})
        messages.append({"role": "user", "content": results})
    print("⚠️ 최대 턴 수에 도달했습니다.")


if __name__ == "__main__":
    run(" ".join(sys.argv[1:]) or "전 대대 보급 상태와 차량 정비 우선순위를 점검하고 오늘 조치사항을 건의하라")
