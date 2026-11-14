"""실습 2 — Claude 기반 도구 사용 에이전트 (Human-in-the-loop 포함)

실습 1의 mock_brain 자리를 Claude가 대신합니다. Claude는 tools.py의 도구 설명을 읽고
어떤 도구를 어떤 인자로 부를지 스스로 결정합니다. 단, 보급 요청(request_supply)은
반드시 터미널에서 사람이 승인해야 실행됩니다.

준비:  pip install -r requirements.txt
       PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
실행:  python lab2_claude_agent.py
       python lab2_claude_agent.py "오늘 정보 보고서를 신뢰도 기준으로 요약해줘"
"""
import json
import sys

import anthropic

from tools import TOOL_SCHEMAS, TOOLS

MODEL = "claude-opus-5-5"
MAX_STEPS = 10

SYSTEM = """당신은 국방 교육용 참모 보조 에이전트입니다. 데이터는 모두 가상입니다.
- 사실은 반드시 도구로 확인하고, 추측은 추측이라고 밝힌다.
- 정보 보고서는 출처와 신뢰도를 함께 제시하고, 상충하는 보고는 상충한다고 말한다.
- 보급 요청 등 실행 행위는 초안만 만들며, 최종 결정은 지휘관(사람)이 한다.
- 최종 답변은 한국어로, 결론 → 근거 → 권고 순서로 간결하게 작성한다."""


def run_tool(name: str, args: dict) -> str:
    if name == "request_supply":
        print(f"\n  ⚠ 보급 요청 승인 필요: {args}")
        ok = input("  지휘관 승인? (y/n): ").strip().lower() == "y"
        result = TOOLS[name](**args, approved=ok)
        if not ok:
            result["status"] = "지휘관 거부"
    else:
        result = TOOLS[name](**args)
    return json.dumps(result, ensure_ascii=False)


def run_agent(goal: str) -> None:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": goal}]
    print(f"\n목표: {goal}\n" + "=" * 60)

    for step in range(1, MAX_STEPS + 1):
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            tools=TOOL_SCHEMAS,
            messages=messages,
            output_config={"effort": "medium"},
            # 안전 분류기가 거절하면 서버가 다른 모델로 자동 재시도
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )

        if response.stop_reason == "refusal":
            print("요청이 거절되었습니다:", response.stop_details)
            return

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"[{step}] Claude: {block.text.strip()}")

        if response.stop_reason != "tool_use":
            return  # end_turn / max_tokens — 최종 답변 출력 완료

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"    행동: {block.name}({block.input})")
                try:
                    content, is_error = run_tool(block.name, block.input), False
                except Exception as e:  # 잘못된 인자 등은 에러로 돌려주면 Claude가 스스로 고친다
                    content, is_error = f"도구 실행 오류: {e}", True
                print(f"    관찰: {content[:160]}")
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": content, "is_error": is_error})
        messages.append({"role": "user", "content": results})  # 병렬 호출 결과는 한 메시지로

    print("최대 단계 도달 — 사람에게 넘깁니다.")


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or "각 대대 보급 재고를 점검하고, 안전재고 미달 품목이 있으면 보급 요청을 준비해줘"
    run_agent(goal)
