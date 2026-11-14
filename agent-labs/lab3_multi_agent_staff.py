"""실습 3. 멀티 에이전트 참모회의 (정보·군수·정비 → 종합)

역할이 다른 전문 에이전트 3개가 각자 분석하고,
'참모장' 에이전트가 결과를 종합해 지휘관 결심 보고서를 작성합니다.
각 에이전트에게는 자기 업무에 필요한 도구만 줍니다 (최소 권한 원칙).

실행:  python lab3_multi_agent_staff.py
"""
import json

import anthropic

from tools import TOOL_SCHEMAS, TOOLS

MODEL = "claude-opus-5-5"
client = anthropic.Anthropic()

STAFF = {
    "정보참모": {
        "tools": ["get_reports"],
        "role": "정보 보고서의 신뢰도를 평가하고, 확인된 사실과 미확인 첩보를 구분해 요약한다.",
    },
    "군수참모": {
        "tools": ["check_inventory"],
        "role": "1·2·3대대 재고를 모두 확인하고 안전재고 미달 품목과 우선순위를 정리한다.",
    },
    "정비참모": {
        "tools": ["predict_maintenance"],
        "role": "차량 정비 위험도를 분석하고 즉시 정비가 필요한 차량과 가용 차량 수를 정리한다.",
    },
}


def agent(name: str, role: str, tool_names: list, task: str) -> str:
    tools = [t for t in TOOL_SCHEMAS if t["name"] in tool_names]
    messages = [{"role": "user", "content": task}]
    for _ in range(6):
        r = client.messages.create(
            model=MODEL, max_tokens=8000, tools=tools, messages=messages,
            system=f"당신은 {name}입니다. {role} 데이터 근거로 5줄 이내 한국어 보고.",
        )
        messages.append({"role": "assistant", "content": r.content})
        uses = [b for b in r.content if b.type == "tool_use"]
        if not uses:
            return "".join(b.text for b in r.content if b.type == "text")
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": u.id,
             "content": json.dumps(TOOLS[u.name](**u.input), ensure_ascii=False)}
            for u in uses
        ]})
    return "(시간 초과)"


def main():
    task = "오늘 오전 상황을 점검하라."
    reports = {}
    for name, cfg in STAFF.items():
        print(f"\n━━ {name} 분석 중 ━━")
        reports[name] = agent(name, cfg["role"], cfg["tools"], task)
        print(reports[name])

    print("\n━━ 참모장 종합 ━━")
    summary = client.messages.create(
        model=MODEL, max_tokens=8000,
        system=("당신은 참모장입니다. 참모 보고를 종합해 지휘관 결심 보고서를 작성합니다. "
                "형식: ①상황 요약 ②위험 요소 ③건의 방책 2개(장단점) ④지휘관 결심 필요 사항. "
                "미확인 첩보에 근거한 판단은 명확히 구분하세요."),
        messages=[{"role": "user", "content": json.dumps(reports, ensure_ascii=False)}],
    )
    print("".join(b.text for b in summary.content if b.type == "text"))
    print("\n※ 최종 결심은 지휘관이 합니다. AI는 참모 보조 역할입니다.")


if __name__ == "__main__":
    main()
