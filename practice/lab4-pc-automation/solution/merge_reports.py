"""실습 4 참고 답안 — 일일 보고 자동 취합기 (표준 라이브러리만 사용)

사용: python merge_reports.py <보고함 폴더>
"""
import csv
import json
import shutil
import sys
from datetime import date
from pathlib import Path

FIELDS = ["분대", "편성", "현재", "장비이상", "특이사항"]


def read_report(path: Path) -> dict:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or set(FIELDS) - set(rows[0]):
        raise ValueError("열 이름이 형식과 다릅니다")
    r = rows[0]
    return {"분대": r["분대"].strip(), "편성": int(r["편성"]), "현재": int(r["현재"]),
            "장비이상": int(r["장비이상"]), "특이사항": r["특이사항"].strip()}


def main(folder: str) -> int:
    box = Path(folder)
    today = date.today().strftime("%Y%m%d")
    squads = json.loads((box / "분대목록.json").read_text(encoding="utf-8"))

    reports, errors, done = {}, [], []
    for path in sorted(box.glob(f"{today}_*.csv")):
        try:
            r = read_report(path)
            reports[r["분대"]] = r
            done.append(path)
        except Exception as e:  # 한 파일 오류로 전체가 멈추지 않게
            errors.append(f"{path.name}: {e}")

    rows = [reports.get(s, {"분대": s, "편성": "", "현재": "", "장비이상": "", "특이사항": "미보고"}) for s in squads]
    reported = [r for r in rows if r["편성"] != ""]
    total_org = sum(r["편성"] for r in reported)
    total_now = sum(r["현재"] for r in reported)
    total_bad = sum(r["장비이상"] for r in reported)
    missing = [r["분대"] for r in rows if r["편성"] == ""]

    out_csv = box / f"취합_{today}.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
        w.writerow({"분대": "합계", "편성": total_org, "현재": total_now, "장비이상": total_bad, "특이사항": ""})

    lines = [f"[일일 보고 취합 {today[:4]}.{today[4:6]}.{today[6:]}] ※ 가상 데이터",
             f"인원 {total_now}/{total_org}, 장비 이상 {total_bad}건",
             f"미보고: {', '.join(missing) if missing else '없음'}", ""]
    lines += [f"- {r['분대']}: {r['현재']}/{r['편성']}, 이상 {r['장비이상']} {r['특이사항']}".rstrip()
              for r in reported]
    out_txt = box / f"취합_{today}.txt"
    out_txt.write_text("\n".join(lines), encoding="utf-8")

    archive = box / "처리완료"
    archive.mkdir(exist_ok=True)
    for p in done:
        shutil.move(p, archive / p.name)

    print("\n".join(lines))
    print(f"\n저장: {out_csv.name}, {out_txt.name} / 처리 {len(done)}건 → 처리완료/")
    if errors:
        print("오류:\n  " + "\n  ".join(errors))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        sys.exit("사용: python merge_reports.py <보고함 폴더>")
    sys.exit(main(sys.argv[1]))
