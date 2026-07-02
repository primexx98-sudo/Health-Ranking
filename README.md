# 건강기능식품 판매순위 크롤러

올리브영 · 다이소몰 · 카카오 선물하기 건강기능식품 TOP10을
**매일 09:00 KST GitHub Actions가 자동 수집**합니다. PC가 꺼져 있어도 동작합니다.

> 상세 내용은 **설계서.md** 참고

---

## 빠른 시작

```bash
# 1. 의존성 설치 (최초 1회)
pip install -r requirements.txt
playwright install chromium

# 2. 대시보드 실행
streamlit run app.py      # → http://localhost:8501

# 3. 수동 수집 (터미널)
python main.py
```

---

## 대시보드 메뉴 (`app.py`)

| 메뉴 | 내용 |
|------|------|
| 오늘 랭킹 | 플랫폼별 TOP10 + 어제 대비 순위 변동 (▲▼🆕) |
| 월별 리포트 | 월 선택 → 평균순위 TOP10 + 신규 진입 상품 하이라이트 |
| 수동 수집 | 지금 즉시 수집 + GitHub Push |

---

## 자동화 구조

```
매일 09:00 KST
  └── GitHub Actions (daily_crawl.yml)
        ├── 카카오선물하기  Playwright headless
        ├── 다이소몰        Playwright headless (상세페이지 브랜드 보강)
        └── 올리브영        curl_cffi (Cloudflare TLS 우회)
              ↓
        data/daily/YYYY-MM/YYYY-MM-DD.xlsx  → git push

매월 1일 09:00 KST
  └── GitHub Actions (monthly_aggregate.yml)
        └── data/monthly/YYYY-MM_월별취합.xlsx → git push
```

---

## 수집 대상

| 플랫폼 | 카테고리 | 크롤링 방식 |
|--------|---------|-------------|
| 카카오 선물하기 | 건강식품·영양제 (subcategory/99) | Playwright + JS (`gc-product`, `span.txt_prdbrand`, `strong.txt_prdname`) |
| 카카오 선물하기 | 다이어트·이너뷰티 (subcategory/100) | Playwright + JS (MD추천 광고 자동 제외) |
| 다이소몰 | 건강식품 실시간 랭킹 | Playwright + JS + 상세페이지 브랜드 보강 |
| 올리브영 | 건강식품 판매랭킹 | **curl_cffi** + BeautifulSoup (Cloudflare 우회) |

---

## 데이터 위치

```
data/daily/   YYYY-MM/YYYY-MM-DD.xlsx  ← 시트 4개: 카카오 / 다이소 / 올리브영 / 카테고리통계 (월별 하위폴더)
data/monthly/ YYYY-MM_월별취합.xlsx     ← 월평균순위 TOP10
```

---

## GitHub Actions 수동 실행

https://github.com/primexx98-sudo/Health-Ranking/actions
→ 워크플로 선택 → **Run workflow**

---

## 트러블슈팅

| 증상 | 원인 | 조치 |
|------|------|------|
| 올리브영 403 | curl_cffi Chrome 버전이 Cloudflare에서 차단됨 | `oliveyoung.py`의 `impersonate` 값을 최신 버전으로 변경 (현재: `chrome146`). 지원 버전 확인: `python -c "from curl_cffi.requests import BrowserType; print([b.value for b in BrowserType])"` |
| 카카오/다이소 상품 0개 | 사이트 HTML 구조 변경 | 해당 크롤러의 `_JS` 변수 내 셀렉터 수정 |
| 다이소 브랜드 누락 | 상세페이지 셀렉터 변경 | `daiso.py`의 `_JS_BRAND` 내 `a.brand-area .detail-title` 갱신 |
| Actions push 실패 | PAT 만료 | GitHub에서 재발급 후 remote URL 재설정 |
| Actions push 충돌 (`[rejected] fetch first`) | 다른 커밋이 먼저 push됨 | 두 workflow 모두 commit 후 `git pull --rebase` 있는지 확인 |
| Actions git push 권한 오류 | permissions 누락 | `daily_crawl.yml` / `monthly_aggregate.yml`에 `permissions: contents: write` 확인 |
| libasound2 오류 | ubuntu-latest 사용 | `daily_crawl.yml`의 `runs-on`을 ubuntu-22.04로 유지 |
| PermissionError (xlsx) | 파일이 Excel에서 열려있음 | 파일 닫고 재실행 |
| URL 변경 | 사이트 개편 | `crawlers/config.py`만 수정 |
