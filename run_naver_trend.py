#!/usr/bin/env python3
"""네이버 DataLab API를 이용한 건강기능식품·일반식품 트렌드 조사

실행:
    python run_naver_trend.py

사전 준비:
    1. https://developers.naver.com → 내 애플리케이션 → 애플리케이션 등록
       (사용 API: 데이터랩(검색어 트렌드), 데이터랩(쇼핑 인사이트) 체크)
    2. 발급된 Client ID / Client Secret을 .env 파일에 입력
       NAVER_CLIENT_ID=xxxxxxxx
       NAVER_CLIENT_SECRET=xxxxxxxx
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

from crawlers.naver_trend import NaverDataLabAPI

# ─── 기간 설정 ────────────────────────────────────────────────────────────────
TODAY = datetime.today()
START = (TODAY - timedelta(days=365)).strftime("%Y-%m-%d")   # 최근 1년
END = TODAY.strftime("%Y-%m-%d")
DATE_TAG = TODAY.strftime("%Y%m%d")

OUT_DIR = Path(__file__).parent / "data" / "naver"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── 건강기능식품 검색어 키워드 그룹 (API: 최대 5개/요청) ─────────────────────
HEALTH_GROUPS = [
    [
        {"groupName": "유산균", "keywords": ["유산균", "프로바이오틱스", "프로바이오틱"]},
        {"groupName": "오메가3", "keywords": ["오메가3", "오메가-3", "피쉬오일", "fish oil"]},
        {"groupName": "비타민", "keywords": ["비타민", "비타민D", "비타민C", "멀티비타민", "종합비타민"]},
        {"groupName": "홍삼", "keywords": ["홍삼", "홍삼정", "홍삼액", "고려홍삼", "정관장"]},
        {"groupName": "콜라겐", "keywords": ["콜라겐", "저분자콜라겐", "피쉬콜라겐", "콜라겐 효능"]},
    ],
    [
        {"groupName": "루테인", "keywords": ["루테인", "루테인 눈", "루테인 효능", "제아잔틴"]},
        {"groupName": "마그네슘", "keywords": ["마그네슘", "마그네슘 보충제", "마그네슘 효능"]},
        {"groupName": "밀크씨슬", "keywords": ["밀크씨슬", "실리마린", "밀크씨슬 간"]},
        {"groupName": "아연", "keywords": ["아연", "아연 보충제", "아연 효능", "zinc"]},
        {"groupName": "코엔자임Q10", "keywords": ["코엔자임Q10", "코큐텐", "CoQ10", "코엔자임"]},
    ],
]

# ─── 일반식품 검색어 키워드 그룹 ─────────────────────────────────────────────
FOOD_GROUPS = [
    [
        {"groupName": "닭가슴살", "keywords": ["닭가슴살", "닭가슴살 요리", "닭가슴살 다이어트", "훈제 닭가슴살"]},
        {"groupName": "단백질바", "keywords": ["단백질바", "프로틴바", "프로틴 간식", "단백질 간식"]},
        {"groupName": "귀리·오트밀", "keywords": ["귀리", "오트밀", "오트", "오버나이트오츠"]},
        {"groupName": "견과류", "keywords": ["견과류", "혼합견과", "아몬드", "호두", "견과 간식"]},
        {"groupName": "그래놀라", "keywords": ["그래놀라", "그라놀라", "뮤즐리", "시리얼"]},
    ],
    [
        {"groupName": "두부", "keywords": ["두부", "순두부", "연두부", "두부 요리"]},
        {"groupName": "현미", "keywords": ["현미", "현미밥", "현미쌀", "현미 효능"]},
        {"groupName": "저칼로리식품", "keywords": ["저칼로리", "저칼로리 식품", "저열량", "저칼로리 간식"]},
        {"groupName": "발효식품", "keywords": ["발효식품", "발효", "청국장", "낫또"]},
        {"groupName": "샐러드", "keywords": ["샐러드", "샐러드 키트", "샐러드 배달", "다이어트 샐러드"]},
    ],
]

# ─── 쇼핑 인사이트 설정 ──────────────────────────────────────────────────────
# 네이버 쇼핑 카테고리 코드 (건강식품: 50000008, 식품: 50000000)
SHOPPING_CATEGORIES = [
    {"name": "건강식품", "param": ["50000008"]},
    {"name": "식품(전체)", "param": ["50000000"]},
]

# 건강기능식품 쇼핑 키워드 (API: 최대 5개/요청, 카테고리: 건강식품)
HEALTH_SHOPPING_KW = [
    [
        {"name": "유산균", "param": ["유산균"]},
        {"name": "오메가3", "param": ["오메가3"]},
        {"name": "비타민D", "param": ["비타민D"]},
        {"name": "홍삼", "param": ["홍삼"]},
        {"name": "콜라겐", "param": ["콜라겐"]},
    ],
    [
        {"name": "루테인", "param": ["루테인"]},
        {"name": "마그네슘", "param": ["마그네슘"]},
        {"name": "밀크씨슬", "param": ["밀크씨슬"]},
        {"name": "아연", "param": ["아연"]},
        {"name": "코엔자임Q10", "param": ["코엔자임Q10", "코큐텐"]},
    ],
]


def save(df: pd.DataFrame, subdir: str, filename: str) -> Path:
    path = OUT_DIR / subdir
    path.mkdir(parents=True, exist_ok=True)
    fp = path / filename
    df.to_csv(fp, index=False, encoding="utf-8-sig")
    print(f"    저장: {fp.relative_to(Path.cwd()) if fp.is_relative_to(Path.cwd()) else fp}")
    return fp


def run_search_trends(api: NaverDataLabAPI) -> tuple[pd.DataFrame, pd.DataFrame]:
    print("\n[1/4] 건강기능식품 검색어 트렌드 수집...")
    frames = [api.search_trend(g, START, END) for g in HEALTH_GROUPS]
    health_df = pd.concat(frames, ignore_index=True)
    save(health_df, "search", f"health_supplement_search_{DATE_TAG}.csv")

    print("[2/4] 일반식품 검색어 트렌드 수집...")
    frames = [api.search_trend(g, START, END) for g in FOOD_GROUPS]
    food_df = pd.concat(frames, ignore_index=True)
    save(food_df, "search", f"general_food_search_{DATE_TAG}.csv")

    return health_df, food_df


def run_shopping_insights(api: NaverDataLabAPI) -> tuple[pd.DataFrame, pd.DataFrame]:
    print("[3/4] 쇼핑 인사이트 - 분야별 트렌드 수집...")
    cat_df = api.shopping_category_trend(SHOPPING_CATEGORIES, START, END)
    save(cat_df, "shopping", f"shopping_category_{DATE_TAG}.csv")

    print("[4/4] 쇼핑 인사이트 - 건강기능식품 키워드 트렌드 수집...")
    frames = [api.shopping_keyword_trend("50000008", kw, START, END) for kw in HEALTH_SHOPPING_KW]
    kw_df = pd.concat(frames, ignore_index=True)
    save(kw_df, "shopping", f"health_shopping_keywords_{DATE_TAG}.csv")

    return cat_df, kw_df


def print_summary(health_search: pd.DataFrame, food_search: pd.DataFrame, kw_df: pd.DataFrame):
    cutoff = (TODAY - timedelta(days=90)).strftime("%Y-%m-%d")
    sep = "─" * 52

    print(f"\n{'='*52}")
    print("  트렌드 요약 — 최근 3개월 평균 검색량 지수")
    print(f"{'='*52}")

    def top5(df: pd.DataFrame, group_col: str, val_col: str) -> pd.Series:
        recent = df[df["날짜"] >= cutoff]
        if recent.empty:
            return pd.Series(dtype=float)
        return recent.groupby(group_col)[val_col].mean().sort_values(ascending=False).head(5)

    print(f"\n건강기능식품 검색어 TOP 5\n{sep}")
    for i, (k, v) in enumerate(top5(health_search, "키워드그룹", "검색량지수").items(), 1):
        print(f"  {i}. {k:<18} {v:>6.1f}")

    print(f"\n일반식품 검색어 TOP 5\n{sep}")
    for i, (k, v) in enumerate(top5(food_search, "키워드그룹", "검색량지수").items(), 1):
        print(f"  {i}. {k:<18} {v:>6.1f}")

    print(f"\n건강식품 쇼핑 키워드 TOP 5 (클릭량 지수)\n{sep}")
    for i, (k, v) in enumerate(top5(kw_df, "키워드", "클릭량지수").items(), 1):
        print(f"  {i}. {k:<18} {v:>6.1f}")

    print(f"\n※ 지수는 100 기준 상대값 (네이버 DataLab 기준)\n")


def main():
    print(f"네이버 DataLab 트렌드 조사  [{START} ~ {END}]")

    try:
        api = NaverDataLabAPI()
    except ValueError as e:
        print(f"\n[API 키 오류]\n{e}")
        sys.exit(1)

    health_search, food_search = run_search_trends(api)
    _, kw_df = run_shopping_insights(api)

    print_summary(health_search, food_search, kw_df)
    print(f"완료  →  {OUT_DIR}")


if __name__ == "__main__":
    main()
