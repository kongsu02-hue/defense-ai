"""실습 4용 가상 보고 파일을 홈 폴더의 '보고함_실습'에 만든다."""
import json
from datetime import date
from pathlib import Path

box = Path.home() / "보고함_실습"
box.mkdir(exist_ok=True)
today = date.today().strftime("%Y%m%d")

HEADER = "분대,편성,현재,장비이상,특이사항\n"
reports = {
    "1분대": "1분대,10,9,0,1명 휴가\n",
    "2분대": "2분대,10,10,1,무전기 배터리 불량\n",
    "3분대": "3분대,9,8,0,1명 외진\n",
    "5분대": "5분대,10,10,2,차량 전조등 고장; 발전기 시동 불량\n",
    "6분대": "6분대,10,10,0,\n",
}
for squad, row in reports.items():
    (box / f"{today}_{squad}.csv").write_text(HEADER + row, encoding="utf-8-sig")

# 형식이 잘못된 파일 (오류 처리 확인용)
(box / f"{today}_7분대.csv").write_text("분대;인원\n7분대;열\n", encoding="utf-8")

# 분대 목록 설정 — 4분대와 7분대는 정상 보고가 없다
(box / "분대목록.json").write_text(
    json.dumps(["1분대", "2분대", "3분대", "4분대", "5분대", "6분대", "7분대"], ensure_ascii=False),
    encoding="utf-8")

print(f"생성 완료: {box}  (가상 데이터)")
