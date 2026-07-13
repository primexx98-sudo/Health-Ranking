"""
올리브영 자동 수집이 실패한 날, 사용자가 직접 캡쳐를 보내주면
(Claude가 이미지에서 읽어낸) TOP10을 그날 daily xlsx에 반영하는 스크립트.

전제: 카카오·다이소는 이미 수집되어 그날 xlsx가 존재함
(main.py는 플랫폼 1개만 실패해도 다른 두 개는 정상 저장하고 종료함).
이 스크립트는 "올리브영" 시트만 추가/교체하고 카테고리통계를 재계산한다.

사용법:
    python manual_oliveyoung.py <YYYY-MM-DD> <items.json>

items.json 형식 (상품URL은 캡쳐에 안 보이면 빈 문자열로 둬도 됨):
    [
      {"순위": 1, "브랜드": "칼로(Kalo)", "상품명": "...", "가격": "8500"},
      ...
    ]
"""
import json
import sys
from pathlib import Path

import pandas as pd

from crawlers.base import clean_price
from crawlers.classifier import classify
from main import COLUMNS, build_category_stats, write_sheet


def inject(target_date: str, items: list[dict]):
    path = Path("data/daily") / target_date[:7] / f"{target_date}.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"{path} 없음 — 먼저 해당일 daily 수집(main.py)이 실행돼 있어야 합니다.")
    if not items:
        raise ValueError("items가 비어 있습니다.")

    data = []
    for item in items:
        name  = item.get("상품명", "")
        brand = item.get("브랜드", "")
        price = item.get("가격", "")
        data.append({
            "카테고리": classify(name, brand),
            "순위":    item.get("순위"),
            "상품명":  name,
            "브랜드":  brand,
            "가격":    clean_price(f"{price}원") if price else "",
            "상품URL": item.get("상품URL", ""),
        })
    data.sort(key=lambda x: x["순위"] if x["순위"] is not None else 9999)

    existing = pd.read_excel(path, sheet_name=None)
    results = {name: existing[name].to_dict("records")
               for name in ("카카오선물하기", "다이소몰") if name in existing}
    results["올리브영"] = data

    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        write_sheet(writer, "올리브영", pd.DataFrame(data, columns=COLUMNS))
        write_sheet(writer, "카테고리통계", build_category_stats(results))

    print(f"올리브영 수동 입력 반영 완료: {path} ({len(data)}개)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("사용법: python manual_oliveyoung.py <YYYY-MM-DD> <items.json>")
        sys.exit(1)
    target_date, items_path = sys.argv[1], sys.argv[2]
    with open(items_path, encoding="utf-8") as f:
        loaded_items = json.load(f)
    inject(target_date, loaded_items)
