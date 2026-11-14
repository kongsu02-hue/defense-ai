"""실습 1 — 에이전트 루프의 원리 (API 키 불필요)

에이전트 = 목표를 받으면 '생각 → 도구 호출 → 관찰'을 반복하다가 답을 내는 프로그램.
여기서는 LLM 대신 규칙 기반 '모의 두뇌(mock_brain)'를 써서 루프 구조만 익힙니다.
실습 2에서 이 두뇌 자리를 Claude로 바꿉니다.

실행:  python lab1_agent_loop.py
"""
import json

from tools import TOOLS

MAX_STEPS = 6  # 무한 반복 방지 — 실제 에이전트에도 반드시 필요한 안전장치


def mock_brain(goal: str, history: list) -> dict:
    """다음 행동을 결정한다. 반환: {"thought", "tool", "args"} 또는 {"thought", "answer"}"""
    done = {h["tool"] for h in history}

    if "보급" in goal or "재고" in goal:
        checked = {h["args"]["unit"] for h in history if h["tool"] == "check_inventory"}
        for u in ["1대대", "2대대", "3대대"]:
            if u not in checked:
                return {"thought": f"{u} 재고를 확인해야 한다.", "tool": "check_inventory", "args": {"unit": u}}
        short = [(h["result"]["unit"], h["result"]["below_safety"]) for h in history
                 if h["tool"] == "check_inventory" and h["result"]["below_safety"]]
        if short and "request_supply" not in done:
            unit, items = short[0]
            return {"thought": f"{unit}의 {items[0]} 안전재고 미달 → 보급 요청 초안을 만든다.",
                    "tool": "request_supply", "args": {"unit": unit, "item": items[0], "amount": 1000}}
        lines = [f"- {u}: {', '.join(i)} 안전재고 미달" for u, i in short] or ["- 모든 부대 안전재고 충족"]
        return {"thought": "필요한 정보를 모두 모았다.", "answer": "보급 현황 요약\n" + "\n".join(lines)
                + "\n※ 보급 요청은 지휘관 승인 대기 상태입니다."}

    if "정비" in goal or "차량" in goal:
        if "predict_maintenance" not in done:
            return {"thought": "차량별 정비 위험도를 계산해야 한다.", "tool": "predict_maintenance", "args": {}}
        ranked = history[-1]["result"]
        urgent = [f'{v["id"]}({v["type"]}, 위험 {v["risk"]})' for v in ranked if v["action"] == "즉시 정비"]
        return {"thought": "우선순위가 나왔다.", "answer": "즉시 정비 대상: " + (", ".join(urgent) or "없음")}

    return {"thought": "이 목표를 처리할 규칙이 없다.", "answer": "처리할 수 없는 요청입니다. (보급/정비 관련 질문을 입력하세요)"}


def run_agent(goal: str) -> str:
    print(f"\n목표: {goal}\n" + "=" * 60)
    history = []
    for step in range(1, MAX_STEPS + 1):
        decision = mock_brain(goal, history)
        print(f"[{step}] 생각: {decision['thought']}")
        if "answer" in decision:
            print("-" * 60 + f"\n최종 답변:\n{decision['answer']}")
            return decision["answer"]
        print(f"    행동: {decision['tool']}({decision['args']})")
        result = TOOLS[decision["tool"]](**decision["args"])
        print(f"    관찰: {json.dumps(result, ensure_ascii=False)[:160]}")
        history.append({"tool": decision["tool"], "args": decision["args"], "result": result})
    print("최대 단계 도달 — 사람에게 넘깁니다.")
    return ""


if __name__ == "__main__":
    run_agent("각 대대 보급 재고를 점검하고 부족하면 보급 요청을 준비해줘")
    run_agent("오늘 정비가 시급한 차량을 알려줘")

    # 생각해 볼 점
    # 1) MAX_STEPS를 2로 줄이면 어떻게 되나?
    # 2) request_supply가 approved=False일 때 '승인 대기'로 멈추는 이유는?
    # 3) 규칙 기반 두뇌의 한계는? 새로운 질문(예: "정보 보고서 요약")을 넣어 보자.
