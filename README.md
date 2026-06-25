# 건강기능식품 판매순위 크롤러

올리브영 · 다이소몰 · 카카오 선물하기 건강기능식품 TOP10을
**매일 09:00 KST GitHub Actions가 자동 수집**합니다. PC가 꺼져 있어도 동작합니다.

---

## 빠른 시작 (처음 설치)

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 실행 방법

| 목적 | 명령어 |
|------|--------|
| 일별 수집 (로컬) | `python main.py` |
| 로컬 UI (수동/디버그) | `streamlit run app.py` → http://localhost:8501 |
| 월별 집계 (수동) | `python monthly_aggregate.py` |

---

## 자동화

- **매일 09:00 KST** — `.github/workflows/daily_crawl.yml`
- **매월 1일 09:00 KST** — `.github/workflows/monthly_aggregate.yml`
- 수동 실행: https://github.com/primexx98-sudo/Health-Ranking/actions → Run workflow

---

## 수집 대상

| 플랫폼 | 카테고리 | 방식 |
|--------|---------|------|
| 카카오 선물하기 | 건강식품·영양제 / 다이어트·이너뷰티 | Playwright + JS |
| 다이소몰 | 건강식품 | Playwright + JS |
| 올리브영 | 건강식품 판매랭킹 | **curl_cffi** (Cloudflare 우회) |

---

## 데이터 위치

```
data/daily/   YYYY-MM-DD.xlsx        ← 시트 3개 (카카오 · 다이소 · 올리브영)
data/monthly/ YYYY-MM_월별취합.xlsx   ← 월평균순위 TOP10
```

---

## URL · 셀렉터 변경

`crawlers/config.py` 만 수정하면 됩니다.
올리브영 HTML 구조 변경 시 `crawlers/oliveyoung.py` 내 regex 수정.

---

## 트러블슈팅

| 증상 | 원인 및 조치 |
|------|-------------|
| Actions push 실패 | PAT 만료 → GitHub에서 재발급 후 remote URL 재설정 |
| libasound2 오류 | `runs-on`이 ubuntu-latest로 바뀐 경우 → ubuntu-22.04로 고정 |
| 올리브영 403 | curl_cffi impersonate 버전 구버전 → chrome124 또는 최신으로 변경 |
| 카카오/다이소 상품 0개 | 사이트 HTML 구조 변경 → crawlers/kakao.py 또는 daiso.py 내 `_JS` 수정 |

자세한 내용은 **설계서.md** 참고.
