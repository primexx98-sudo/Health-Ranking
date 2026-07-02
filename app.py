import streamlit as st
import pandas as pd
import subprocess
from datetime import date, timedelta
from pathlib import Path

from crawlers.kakao import crawl_kakao
from crawlers.daiso import crawl_daiso
from crawlers.oliveyoung import crawl_oliveyoung

st.set_page_config(page_title="건강기능식품 랭킹", layout="wide", page_icon="💊")

BASE_DIR  = Path(__file__).parent
DAILY_DIR = BASE_DIR / "data" / "daily"
MON_DIR   = BASE_DIR / "data" / "monthly"
COLUMNS   = ["카테고리", "순위", "상품명", "브랜드", "가격", "상품URL"]
PLATFORMS = ["카카오선물하기", "다이소몰", "올리브영"]


# ─────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────
def load_daily(path: Path) -> dict[str, pd.DataFrame]:
    if not path.exists():
        return {}
    xl = pd.ExcelFile(path, engine="openpyxl")
    return {s: xl.parse(s) for s in xl.sheet_names}


def rank_delta(today_df: pd.DataFrame, prev_df: pd.DataFrame) -> pd.DataFrame:
    """오늘 순위와 어제 순위 비교 → 변동 컬럼 추가"""
    if prev_df is None or prev_df.empty:
        today_df = today_df.copy()
        today_df["변동"] = "NEW"
        return today_df
    merged = today_df.merge(
        prev_df[["상품명", "순위"]].rename(columns={"순위": "_prev"}),
        on="상품명", how="left"
    )
    def fmt(row):
        if pd.isna(row["_prev"]):
            return "🆕"
        diff = int(row["_prev"]) - int(row["순위"])
        if diff > 0:   return f"▲{diff}"
        if diff < 0:   return f"▼{abs(diff)}"
        return "―"
    merged["변동"] = merged.apply(fmt, axis=1)
    return merged.drop(columns=["_prev"])


def save_excel(results: dict, today: str) -> Path:
    out = DAILY_DIR / today[:7] / f"{today}.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet, data in results.items():
            df = pd.DataFrame(data, columns=COLUMNS)
            df.to_excel(writer, sheet_name=sheet, index=False)
            ws = writer.sheets[sheet]
            for col in ws.columns:
                w = max(len(str(c.value or "")) for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(w + 4, 60)
    return out


def git_push(today: str):
    cmds = [
        ["git", "add", "data/"],
        ["git", "commit", "-m", f"data: {today} 수집 (로컬)"],
        ["git", "pull", "--rebase"],
        ["git", "push"],
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR))
        if r.returncode != 0 and "nothing to commit" not in r.stdout + r.stderr:
            return False, r.stderr
    return True, ""


# ─────────────────────────────────────────
# 사이드바 — 네비게이션
# ─────────────────────────────────────────
st.sidebar.title("💊 건강기능식품 랭킹")
page = st.sidebar.radio("메뉴", ["오늘 랭킹", "월별 리포트", "수동 수집"])
st.sidebar.caption(f"기준일: {date.today().isoformat()}")


# ─────────────────────────────────────────
# 페이지 1: 오늘 랭킹
# ─────────────────────────────────────────
if page == "오늘 랭킹":
    st.title("📊 오늘의 랭킹")

    today     = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    today_path = DAILY_DIR / today[:7] / f"{today}.xlsx"
    prev_path  = DAILY_DIR / yesterday[:7] / f"{yesterday}.xlsx"

    today_data = load_daily(today_path)
    prev_data  = load_daily(prev_path)

    if not today_data:
        st.warning(f"오늘({today}) 수집 데이터가 없습니다. **수동 수집** 메뉴에서 수집하거나 GitHub Actions 결과를 확인하세요.")
        st.stop()

    tabs = st.tabs(PLATFORMS)
    for tab, platform in zip(tabs, PLATFORMS):
        with tab:
            df = today_data.get(platform)
            if df is None or df.empty:
                st.info("수집 데이터 없음")
                continue

            prev_df = prev_data.get(platform) if prev_data else None
            df_show = rank_delta(df, prev_df)

            # 순위 변동 요약
            new_cnt  = (df_show["변동"] == "🆕").sum()
            up_cnt   = df_show["변동"].str.startswith("▲").sum()
            down_cnt = df_show["변동"].str.startswith("▼").sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("신규 진입", f"{new_cnt}개")
            c2.metric("순위 상승", f"{up_cnt}개")
            c3.metric("순위 하락", f"{down_cnt}개")

            st.dataframe(
                df_show[["순위", "변동", "상품명", "브랜드", "가격", "카테고리"]],
                use_container_width=True, hide_index=True,
            )


# ─────────────────────────────────────────
# 페이지 2: 월별 리포트
# ─────────────────────────────────────────
elif page == "월별 리포트":
    st.title("📅 월별 리포트")

    # 월 선택
    available = sorted([p.stem for p in MON_DIR.glob("*.xlsx")], reverse=True) if MON_DIR.exists() else []
    if not available:
        st.warning("월별 취합 데이터가 없습니다. GitHub Actions monthly_aggregate.yml을 실행하세요.")
        st.stop()

    selected = st.selectbox("월 선택", available)
    mon_path = MON_DIR / f"{selected}.xlsx"
    mon_data = load_daily(mon_path)

    # 이번 달 일별 데이터에서 첫 등장일 계산 (신규 진입 판단)
    ym = selected[:7]  # "2026-06"
    prev_ym = (date(int(ym[:4]), int(ym[5:7]), 1) - timedelta(days=1)).strftime("%Y-%m")
    prev_mon_dir   = DAILY_DIR / prev_ym
    prev_mon_files = sorted(prev_mon_dir.glob(f"{prev_ym}-*.xlsx")) if prev_mon_dir.exists() else []
    prev_names: set = set()
    for f in prev_mon_files:
        xl = pd.ExcelFile(f, engine="openpyxl")
        for s in xl.sheet_names:
            prev_names.update(xl.parse(s)["상품명"].tolist())

    tabs = st.tabs(PLATFORMS)
    for tab, platform in zip(tabs, PLATFORMS):
        with tab:
            df = mon_data.get(platform)
            if df is None or df.empty:
                st.info("집계 데이터 없음")
                continue

            # 신규 진입 표시
            if "상품명" in df.columns:
                df = df.copy()
                df["신규"] = df["상품명"].apply(lambda n: "🆕" if n not in prev_names else "")

            st.subheader(f"{selected[:7]} 평균순위 TOP10")
            cols = [c for c in ["순위(월평균)", "신규", "상품명", "브랜드", "평균가격", "평균순위", "등장횟수"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)

            # 이번 달 신규 진입 상품 하이라이트
            new_items = df[df["신규"] == "🆕"] if "신규" in df.columns else pd.DataFrame()
            if not new_items.empty:
                st.success(f"이번 달 신규 진입: {', '.join(new_items['상품명'].tolist())}")


# ─────────────────────────────────────────
# 페이지 3: 수동 수집
# ─────────────────────────────────────────
elif page == "수동 수집":
    st.title("🔄 수동 수집")
    st.caption("GitHub Actions가 매일 09:00 자동 실행됩니다. 이 페이지는 즉시 수집이 필요할 때 사용하세요.")

    if st.button("지금 수집 시작", type="primary", use_container_width=True):
        today   = date.today().isoformat()
        results = {}
        failed  = []

        col1, col2, col3 = st.columns(3)
        crawl_targets = [
            ("카카오선물하기", lambda: crawl_kakao(headless=True),      col1),
            ("다이소몰",       lambda: crawl_daiso(headless=True),      col2),
            ("올리브영",       lambda: crawl_oliveyoung(headless=True), col3),
        ]

        for name, fn, col in crawl_targets:
            with col:
                with st.status(f"{name} 수집 중...", expanded=True) as status:
                    try:
                        data = fn()
                        if data:
                            results[name] = data
                            status.update(label=f"{name} ✅ {len(data)}개", state="complete")
                        else:
                            failed.append(name)
                            status.update(label=f"{name} ❌ 실패", state="error")
                    except Exception as e:
                        failed.append(name)
                        status.update(label=f"{name} ❌ 오류", state="error")
                        st.error(str(e))

        if results:
            out = save_excel(results, today)
            st.success(f"저장 완료: `{out}`")

            if failed:
                st.warning(f"수집 실패: {', '.join(failed)}")

            st.divider()
            if st.button("GitHub에 Push", use_container_width=True):
                ok, err = git_push(today)
                if ok:
                    st.success("GitHub Push 완료!")
                else:
                    st.error(f"Push 실패: {err}")
