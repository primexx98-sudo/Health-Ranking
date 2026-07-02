from crawlers.kakao import crawl_kakao
from crawlers.daiso import crawl_daiso
from crawlers.oliveyoung import crawl_oliveyoung
from crawlers.classifier import classify, ALL_CATEGORIES, PLATFORMS as PLATFORM_NAMES
from datetime import date
from pathlib import Path
from collections import defaultdict
import pandas as pd
import sys


COLUMNS = ["카테고리", "순위", "상품명", "브랜드", "가격", "상품URL"]


def build_category_stats(results: dict) -> pd.DataFrame:
    counts = defaultdict(lambda: {p: 0 for p in PLATFORM_NAMES})
    total = 0

    for platform, data in results.items():
        for item in data:
            cat = item["카테고리"]
            counts[cat][platform] += 1
            total += 1

    rows = []
    for cat in ALL_CATEGORIES:
        c = counts.get(cat, {p: 0 for p in PLATFORM_NAMES})
        n = sum(c.values())
        rows.append({
            "카테고리":      cat,
            "전체":          n,
            "비율(%)":       round(n / total * 100, 1) if total else 0.0,
            "카카오선물하기": c.get("카카오선물하기", 0),
            "다이소몰":       c.get("다이소몰", 0),
            "올리브영":       c.get("올리브영", 0),
        })

    rows.append({
        "카테고리":      "합계",
        "전체":          total,
        "비율(%)":       100.0,
        "카카오선물하기": sum(r["카카오선물하기"] for r in rows),
        "다이소몰":       sum(r["다이소몰"]       for r in rows),
        "올리브영":       sum(r["올리브영"]       for r in rows),
    })

    return pd.DataFrame(rows)


def write_sheet(writer, sheet_name: str, df: pd.DataFrame):
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    ws = writer.sheets[sheet_name]
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)


def main(output_name: str = ""):
    today = date.today().isoformat()
    print(f"===== {today} 크롤링 시작 =====")

    crawlers = {
        "카카오선물하기": crawl_kakao,
        "다이소몰":       crawl_daiso,
        "올리브영":       crawl_oliveyoung,
    }

    results = {}
    failed  = []

    for sheet_name, crawl_fn in crawlers.items():
        data = crawl_fn()
        if data:
            # 카테고리 분류 (플랫폼 카테고리 → 상품 카테고리)
            for item in data:
                item["카테고리"] = classify(item["상품명"], item.get("브랜드", ""))
            results[sheet_name] = data
        else:
            failed.append(sheet_name)

    if not results:
        print("모든 플랫폼 수집 실패 — 종료")
        sys.exit(1)

    filename      = output_name if output_name else today
    output_path   = Path("data/daily") / today[:7] / f"{filename}.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, data in results.items():
            df = pd.DataFrame(data, columns=COLUMNS)
            write_sheet(writer, sheet_name, df)

        stats_df = build_category_stats(results)
        write_sheet(writer, "카테고리통계", stats_df)

    print(f"\n저장 완료: {output_path}")
    for sheet_name, data in results.items():
        print(f"  {sheet_name}: {len(data)}개")

    if failed:
        print(f"[WARNING] 수집 실패 플랫폼: {', '.join(failed)}")
        if len(failed) == len(crawlers):
            sys.exit(1)


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    main(name)
