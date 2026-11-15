"""실습 2 참고 답안 — 정비 이력 분석 도구 (표준 라이브러리만 사용)"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

NUMERIC = {"km", "cost", "km_since_service"}


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k: int(v) if k in NUMERIC else v for k, v in row.items()} for row in csv.DictReader(f)]


def summary_by_vehicle(records):
    out = {}
    for r in records:
        s = out.setdefault(r["vehicle_id"], {"count": 0, "total_cost": 0, "failures": 0, "last_date": ""})
        s["count"] += 1
        s["total_cost"] += r["cost"]
        s["failures"] += r["kind"] == "고장"
        s["last_date"] = max(s["last_date"], r["date"])
    return out


def monthly_cost(records):
    totals = defaultdict(int)
    for r in records:
        totals[r["date"][:7]] += r["cost"]
    return dict(sorted(totals.items()))


def service_due(vehicles, interval_km=10000, warn_ratio=0.9):
    def status(km):
        if km >= interval_km:
            return "초과"
        return "임박" if km >= interval_km * warn_ratio else "정상"

    rows = [{**{k: v[k] for k in ("vehicle_id", "type", "km_since_service")}, "status": status(v["km_since_service"])}
            for v in vehicles]
    return sorted(rows, key=lambda v: v["km_since_service"], reverse=True)


def report(records, vehicles):
    due = service_due(vehicles)
    summary = summary_by_vehicle(records)
    failures = Counter({vid: s["failures"] for vid, s in summary.items() if s["failures"]})
    lines = ["[정비 현황 보고] ※ 교육용 가상 데이터", ""]
    for label in ("초과", "임박"):
        hits = [f'{v["vehicle_id"]}({v["type"]}, {v["km_since_service"]:,}km)' for v in due if v["status"] == label]
        lines.append(f"- 정비 주기 {label}: " + (", ".join(hits) if hits else "없음"))
    if failures:
        vid, n = failures.most_common(1)[0]
        lines.append(f"- 고장 최다 차량: {vid} ({n}회, 총비용 {summary[vid]['total_cost']:,}원)")
    lines.append("- 월별 정비비: " + ", ".join(f"{m} {c:,}원" for m, c in monthly_cost(records).items()))
    lines += ["", "건의: 초과 차량은 즉시 정비 입고, 임박 차량은 이번 주 정비 일정 편성."]
    return "\n".join(lines)


if __name__ == "__main__":
    here = Path(__file__).parent.parent / "data"
    print(report(load_csv(here / "records.csv"), load_csv(here / "vehicles.csv")))
