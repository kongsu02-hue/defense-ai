"""정비 이력 분석 도구 — 실습 2에서 AI 에이전트와 함께 완성할 파일입니다.

tests/test_maintenance.py 의 테스트가 모두 통과하도록 아래 함수를 구현하세요.
함수 이름과 인자는 바꾸지 마세요.
"""


def load_csv(path):
    """CSV를 읽어 dict 리스트로 반환. 숫자 열(km, cost, km_since_service)은 int로 변환."""
    raise NotImplementedError


def summary_by_vehicle(records):
    """차량별 {"count": 정비횟수, "total_cost": 총비용, "failures": 고장횟수, "last_date": 최근정비일} 반환."""
    raise NotImplementedError


def monthly_cost(records):
    """{"YYYY-MM": 해당 월 총비용} 을 월 순서대로 반환."""
    raise NotImplementedError


def service_due(vehicles, interval_km=10000, warn_ratio=0.9):
    """정비 주기 대비 주행거리로 상태를 판정.
    km_since_service >= interval_km → "초과", >= interval_km*warn_ratio → "임박", 그 외 "정상".
    [{"vehicle_id", "type", "km_since_service", "status"}] 를 km_since_service 내림차순으로 반환."""
    raise NotImplementedError


def report(records, vehicles):
    """사람이 읽는 한국어 요약 보고서 문자열. 초과·임박 차량과 고장이 가장 잦은 차량을 포함."""
    raise NotImplementedError


if __name__ == "__main__":
    from pathlib import Path

    here = Path(__file__).parent / "data"
    print(report(load_csv(here / "records.csv"), load_csv(here / "vehicles.csv")))
