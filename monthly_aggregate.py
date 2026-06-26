from pathlib import Path
from datetime import date
from collections import defaultdict
from crawlers.classifier import classify, ALL_CATEGORIES, PLATFORMS as PLATFORM_NAMES
import pandas as pd


PLATFORMS   = ["카카오선물하기", "다이소몰", "올리브영"]
COLUMNS_OUT = ["순위(월평균)", "카테고리", "상품명", "브랜드", "평균가격", "평균순위", "등장횟수"]


def price_to_int(price_str: str) -> float:
    try:
        digits = "".join(c for c in str(price_str) if c.isdigit())
        return float(digits) if digits else 0.0
    except Exception:
        return 0.0


def aggregate_platform(daily_files: list, sheet: str) -> pd.DataFrame:
    frames = []
    for f in daily_files:
        try:
            df = pd.read_excel(f, sheet_name=sheet)
            df["_date"] = f.stem
            frames.append(df)
        except Exception:
            pass

    if not frames:
        return pd.DataFrame(columns=COLUMNS_OUT)

    all_data = pd.concat(frames, ignore_index=True)
    all_data["가격_숫자"] = all_data["가격"].apply(price_to_int)

    grouped = all_data.groupby(["상품명", "브랜드"]).agg(
        평균순위=("순위", "mean"),
        등장횟수=("순위", "count"),
        평균가격_raw=("가격_숫자", "mean"),
    ).reset_index()

    grouped = grouped.sort_values("평균순위").head(10).reset_index(drop=True)
    grouped.insert(0, "순위(월평균)", range(1, len(grouped) + 1))
    grouped["평균순위"] = grouped["평균순위"].round(2)
    grouped["평균가격"] = grouped["평균가격_raw"].apply(
        lambda x: f"{int(x):,}원" if x > 0 else "-"
    )
    grouped["카테고리"] = grouped.apply(
        lambda r: classify(r["상품명"], r["브랜드"]), axis=1
    )

    return grouped[COLUMNS_OUT]


def build_monthly_category_stats(platform_dfs: dict) -> pd.DataFrame:
    counts = defaultdict(lambda: {p: 0 for p in PLATFORM_NAMES})
    total  = 0

    for platform, df in platform_dfs.items():
        if df.empty:
            continue
        for _, row in df.iterrows():
            cat = classify(row.get("상품명", ""), row.get("브랜드", ""))
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


def main():
    today = date.today()
    if today.month == 1:
        target_year, target_month = today.year - 1, 12
    else:
        target_year, target_month = today.year, today.month - 1

    prefix = f"{target_year}-{target_month:02d}"
    print(f"===== {prefix} 월별 취합 시작 =====")

    daily_dir  = Path("data/daily")
    daily_files = sorted(daily_dir.glob(f"{prefix}-*.xlsx"))

    if not daily_files:
        print(f"  데이터 없음: {prefix}-*.xlsx 파일이 없습니다")
        return

    print(f"  일별 파일 {len(daily_files)}개 발견")

    output_path = Path("data/monthly") / f"{prefix}_월별취합.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    platform_dfs = {}
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for platform in PLATFORMS:
            df = aggregate_platform(daily_files, platform)
            platform_dfs[platform] = df
            write_sheet(writer, platform, df)

        stats_df = build_monthly_category_stats(platform_dfs)
        write_sheet(writer, "카테고리통계", stats_df)

    print(f"저장 완료: {output_path}")


if __name__ == "__main__":
    main()
