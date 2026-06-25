import streamlit as st
import pandas as pd
import subprocess
from datetime import date
from pathlib import Path

from crawlers.kakao import crawl_kakao
from crawlers.daiso import crawl_daiso
from crawlers.oliveyoung import crawl_oliveyoung

st.set_page_config(page_title="건강기능식품 랭킹 수집기", layout="wide")
st.title("건강기능식품 판매순위 수집기")
st.caption(f"오늘: {date.today().isoformat()}")

COLUMNS = ["카테고리", "순위", "상품명", "브랜드", "가격", "상품URL"]
BASE_DIR = Path(__file__).parent


def save_excel(results: dict, today: str) -> Path:
    output_path = BASE_DIR / "data" / "daily" / f"{today}.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, data in results.items():
            df = pd.DataFrame(data, columns=COLUMNS)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
    return output_path


st.info(
    "올리브영 수집 시 **브라우저 창이 열립니다**. "
    "Cloudflare 체크박스가 뜨면 직접 클릭해주세요. (집 IP에서는 대부분 자동 통과됩니다)",
    icon="ℹ️"
)

if st.button("크롤링 시작", type="primary", use_container_width=True):
    today = date.today().isoformat()
    results = {}
    failed = []

    col1, col2, col3 = st.columns(3)

    PLATFORMS = [
        ("카카오선물하기", lambda: crawl_kakao(headless=True),  col1),
        ("다이소몰",       lambda: crawl_daiso(headless=True),  col2),
        ("올리브영",       lambda: crawl_oliveyoung(headless=False), col3),
    ]

    for name, fn, col in PLATFORMS:
        with col:
            with st.status(f"{name} 수집 중...", expanded=True) as status:
                try:
                    data = fn()
                    if data:
                        results[name] = data
                        status.update(label=f"{name} — {len(data)}개 완료", state="complete")
                    else:
                        failed.append(name)
                        status.update(label=f"{name} — 수집 실패", state="error")
                except Exception as e:
                    failed.append(name)
                    status.update(label=f"{name} — 오류", state="error")
                    st.error(str(e))

    if results:
        st.divider()
        st.subheader("수집 결과")

        tabs = st.tabs(list(results.keys()))
        for tab, (sheet_name, data) in zip(tabs, results.items()):
            with tab:
                df = pd.DataFrame(data, columns=COLUMNS)
                st.dataframe(df, use_container_width=True, hide_index=True)

        output_path = save_excel(results, today)
        st.success(f"엑셀 저장 완료: `{output_path}`")

        if failed:
            st.warning(f"수집 실패: {', '.join(failed)}")

        st.divider()
        if st.button("GitHub에 Push", use_container_width=True):
            cmds = [
                ["git", "add", "data/daily/"],
                ["git", "commit", "-m", f"data: {today} 일별 수집 (로컬)"],
                ["git", "push"],
            ]
            ok = True
            for cmd in cmds:
                r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR))
                if r.returncode != 0 and "nothing to commit" not in r.stdout:
                    st.error(f"오류: {r.stderr}")
                    ok = False
                    break
            if ok:
                st.success("GitHub Push 완료!")
