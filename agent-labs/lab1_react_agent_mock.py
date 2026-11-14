"""실습 1. ReAct 에이전트의 구조 이해 (API 키 불필요)

LLM 대신 규칙 기반 '두뇌'를 사용해, 에이전트 루프가
  생각(Thought) → 행동(Action: 도구 호출) → 관찰(Observation)
을 어떻게 반복하는지 눈으로 확인합니다.

실행:  python lab1_react_agent_mock.py
"""
import json

from tools import TOOLS


def mock_brain(goal: str, history: list) -> dict:
    """LLM 역할을 흉내 내는 규칙 기반 의사결정기.

    실제 에이전트에서는 이 자리에 LLM 호출이 들어갑니다(실습 2 참고).
    """
    done = [h["action"] for h in history]
    if "check_inventory" not in done:
        return {"thought": "먼저 2대대의 재고 현황을 확인해야 한다.",
                "action": "check_inventory", "args": {"unit": "2대대"}}
    inv = history[0]["observation"]
    if inv["below_safety"] and "request_supply" not in done:
        item = inv["below_safety"][0]
        return {"thought": f"{item}이(가) 안전재고 미달이다. 보급 요청 초안을 만든다.",
                "action": "request_supply", "args": {"unit": "2대대", "item": item, "amount": 1000}}
    return {"thought": "필요한 정보가 모였다. 지휘관에게 보고한다.", "action": "finish",
            "answer": f"2대대 안전재고 미달 품목: {', '.join(inv['below_safety']) or '없음'}. "
                      "보급 요청 초안을 작성했으며 지휘관 승인을 기다립니다."}


def run(goal: str, max_steps: int = 5):
    print(f"🎯 목표: {goal}\n")
    history = []
    for step in range(1, max_steps + 1):
        decision = mock_brain(goal, history)
        print(f"[{step}] 💭 생각: {decision['thought']}")
        if decision["action"] == "finish":
            print(f"\n✅ 최종 보고: {decision['answer']}")
            return
        print(f"    🔧 행동: {decision['action']}({decision['args']})")
        obs = TOOLS[decision["action"]](**decision["args"])
        print(f"    👀 관찰: {json.dumps(obs, ensure_ascii=False)}\n")
        history.append({"action": decision["action"], "observation": obs})
    print("⚠️ 최대 단계에 도달해 중단했습니다 (무한 루프 방지 장치).")


if __name__ == "__main__":
    run("2대대 보급 상태를 점검하고 부족 품목이 있으면 보급 요청을 준비하라")
