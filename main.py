from crawlers.kakao import crawl_kakao
from crawlers.daiso import crawl_daiso
from crawlers.oliveyoung import crawl_oliveyoung
from datetime import date
from pathlib import Path
import pandas as pd
import sys


COLUMNS = ["카테고리", "순위", "상품명", "브랜드", "가격", "상품URL"]


def main():
    today = date.today().isoformat()
    print(f"===== {today} 크롤링 시작 =====")

    crawlers = {
        "카카오선물하기": crawl_kakao,
        "다이소몰": crawl_daiso,
        "올리브영": crawl_oliveyoung,
    }

    results = {}
    failed = []

    for sheet_name, crawl_fn in crawlers.items():
        data = crawl_fn()
        if data:
            results[sheet_name] = data
        else:
            failed.append(sheet_name)

    if not results:
        print("모든 플랫폼 수집 실패 — 종료")
        sys.exit(1)

    output_path = Path("data/daily") / f"{today}.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, data in results.items():
            df = pd.DataFrame(data, columns=COLUMNS)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)

    print(f"\n저장 완료: {output_path}")

    if failed:
        print(f"수집 실패 플랫폼: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
