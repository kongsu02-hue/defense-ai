from pathlib import Path

import pytest

from maintenance import load_csv, monthly_cost, report, service_due, summary_by_vehicle

DATA = Path(__file__).parent.parent / "data"


@pytest.fixture
def records():
    return load_csv(DATA / "records.csv")


@pytest.fixture
def vehicles():
    return load_csv(DATA / "vehicles.csv")


def test_load_csv_converts_numbers(records, vehicles):
    assert len(records) == 10
    assert records[0]["vehicle_id"] == "V-101"
    assert records[0]["cost"] == 85000 and isinstance(records[0]["km"], int)
    assert vehicles[2]["km_since_service"] == 14100


def test_summary_by_vehicle(records):
    s = summary_by_vehicle(records)
    assert s["V-203"] == {"count": 3, "total_cost": 685000, "failures": 2, "last_date": "2026-03-28"}
    assert s["V-102"]["failures"] == 0
    assert set(s) == {"V-101", "V-102", "V-203", "V-204", "V-305"}


def test_summary_empty():
    assert summary_by_vehicle([]) == {}


def test_monthly_cost_sorted(records):
    m = monthly_cost(records)
    assert list(m) == ["2026-01", "2026-02", "2026-03", "2026-04"]
    assert m["2026-01"] == 445000
    assert m["2026-04"] == 30000


def test_service_due_status_and_order(vehicles):
    due = service_due(vehicles)
    assert [v["vehicle_id"] for v in due] == ["V-203", "V-101", "V-305", "V-204", "V-102"]
    status = {v["vehicle_id"]: v["status"] for v in due}
    assert status == {"V-203": "초과", "V-101": "임박", "V-305": "임박", "V-204": "정상", "V-102": "정상"}


def test_service_due_boundary():
    v = [{"vehicle_id": "A", "type": "t", "km_since_service": 10000},
         {"vehicle_id": "B", "type": "t", "km_since_service": 9000},
         {"vehicle_id": "C", "type": "t", "km_since_service": 8999}]
    assert [x["status"] for x in service_due(v)] == ["초과", "임박", "정상"]


def test_service_due_custom_interval(vehicles):
    status = {v["vehicle_id"]: v["status"] for v in service_due(vehicles, interval_km=8000)}
    assert status["V-204"] == "임박" and status["V-101"] == "초과"


def test_report_mentions_key_facts(records, vehicles):
    text = report(records, vehicles)
    assert "V-203" in text and "초과" in text
    assert "V-101" in text and "임박" in text
    assert "고장" in text
