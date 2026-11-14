"""실습용 도구(Tool) 모음 — 모든 실습이 공통으로 사용합니다.

에이전트는 '생각 → 도구 호출 → 관찰'을 반복합니다. 이 파일의 함수들이 그 '도구'입니다.
데이터는 모두 교육용 가상 데이터(data/*.json)입니다.
"""
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"


def _load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def check_inventory(unit: str) -> dict:
    """부대별 보급품 재고와 남은 일수를 계산한다."""
    inv = _load("inventory.json")
    if unit not in inv["units"]:
        return {"error": f"알 수 없는 부대: {unit}", "available": list(inv["units"])}
    stock = inv["units"][unit]
    days = {k: round(v / inv["daily_consumption"][k], 1) for k, v in stock.items()}
    short = [k for k, d in days.items() if d < inv["safety_days"]]
    return {"unit": unit, "stock": stock, "days_left": days, "below_safety": short}


def predict_maintenance(threshold: float = 0.6) -> list:
    """간단한 규칙 기반 위험점수로 정비 우선순위를 산출한다 (0~1)."""
    out = []
    for v in _load("vehicles.json")["vehicles"]:
        score = (
            0.4 * min(v["km_since_service"] / 15000, 1)
            + 0.3 * min(max(v["engine_temp_avg"] - 85, 0) / 20, 1)
            + 0.3 * min(v["vibration"] / 0.8, 1)
        )
        if v["last_fault"] != "없음":
            score = min(score + 0.1, 1)
        out.append({"id": v["id"], "type": v["type"], "risk": round(score, 2),
                    "action": "즉시 정비" if score >= threshold else "정기 점검"})
    return sorted(out, key=lambda x: -x["risk"])


def get_reports() -> list:
    """수집된 정보 보고서 목록을 반환한다."""
    return _load("reports.json")["reports"]


def request_supply(unit: str, item: str, amount: int, approved: bool = False) -> dict:
    """보급 요청을 생성한다. 사람(지휘관)의 승인 없이는 실행되지 않는다."""
    if not approved:
        return {"status": "승인 대기", "unit": unit, "item": item, "amount": amount,
                "message": "지휘관 승인이 필요합니다 (Human-in-the-loop)."}
    return {"status": "요청 완료", "unit": unit, "item": item, "amount": amount}


# Claude API에 넘길 도구 정의(JSON Schema)
TOOL_SCHEMAS = [
    {
        "name": "check_inventory",
        "description": "부대의 보급품 재고, 품목별 남은 일수, 안전재고(3일) 미달 품목을 조회한다.",
        "input_schema": {
            "type": "object",
            "properties": {"unit": {"type": "string", "description": "부대명. 예: 1대대, 2대대, 3대대"}},
            "required": ["unit"],
            "additionalProperties": False,
        },
    },
    {
        "name": "predict_maintenance",
        "description": "차량 센서 데이터로 정비 위험점수(0~1)를 계산해 우선순위 목록을 반환한다.",
        "input_schema": {
            "type": "object",
            "properties": {"threshold": {"type": "number", "description": "즉시 정비 기준 점수 (기본 0.6)"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_reports",
        "description": "오늘 수집된 정보 보고서(시간, 출처, 내용, 신뢰도)를 반환한다.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "request_supply",
        "description": "보급 요청 초안을 만든다. 실제 요청은 지휘관 승인 후에만 실행된다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "unit": {"type": "string"},
                "item": {"type": "string"},
                "amount": {"type": "integer"},
            },
            "required": ["unit", "item", "amount"],
            "additionalProperties": False,
        },
    },
]

TOOLS = {
    "check_inventory": check_inventory,
    "predict_maintenance": predict_maintenance,
    "get_reports": get_reports,
    "request_supply": request_supply,
}
