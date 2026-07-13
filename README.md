# 건강기능식품 판매순위 크롤러

올리브영 · 다이소몰 · 카카오 선물하기 건강기능식품 TOP10을
**매일 09:00 KST GitHub Actions가 자동 수집**합니다. PC가 꺼져 있어도 동작합니다.

> 구조·로직 상세는 **설계서.md**, 작업 히스토리는 **기록.md** 참고

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
| 월별 리포트 | 월 선택 → 평균순위 TOP20 (등장횟수 3회 미만 제외, 20개 미달 시 2회→1회로 완화) + 신규 진입 상품 하이라이트 |
| 수동 수집 | 지금 즉시 수집 + GitHub Push |

---

## 자동화 구조

```
매일 09:00 KST
  └── GitHub Actions (daily_crawl.yml)
        ├── 카카오선물하기  Playwright headless
        ├── 다이소몰        Playwright headless (상세페이지 브랜드 보강)
        └── 올리브영        Playwright headless (Cloudflare JS 챌린지 우회)
              ↓
        data/daily/YYYY-MM/YYYY-MM-DD.xlsx  → git push

매월 1일 09:00 KST
  └── GitHub Actions (monthly_aggregate.yml)
        └── data/monthly/YYYY-MM_월별취합.xlsx → git push
```

수집 대상·URL·셀렉터 등 상세는 설계서.md 3장·6장 참고.

---

## 데이터 위치

```
data/daily/   YYYY-MM/YYYY-MM-DD.xlsx  ← 시트 4개: 카카오 / 다이소 / 올리브영 / 카테고리통계 (월별 하위폴더)
data/monthly/ YYYY-MM_월별취합.xlsx     ← 월평균순위 TOP20
```

---

## GitHub Actions 수동 실행

https://github.com/primexx98-sudo/Health-Ranking/actions
→ 워크플로 선택 → **Run workflow**

---

## 트러블슈팅

문제 발생 시 원인별 조치 파일·수정 위치는 **설계서.md 13장 (유지보수 가이드)** 참고. 자주 나오는 것만 요약:

| 증상 | 조치 |
|------|------|
| 올리브영 상품 0개 | Playwright 셀렉터(`ul.cate_prd_list` 등) 확인, 3회 재시도로 일시적 실패는 자동 대응 |
| Actions push 충돌/실패 | `git pull --rebase` 포함 여부, PAT 만료 여부 확인 |
| PermissionError (xlsx) | 파일을 Excel에서 닫고 재실행 |
| 월별취합 xlsx 병합 충돌 | Actions가 매월 1일 같은 파일을 재생성해 로컬 push와 충돌 가능. 원본 daily 데이터 동일하면 최신 로직 버전을 채택(설계서.md 13장) |

수집 실패 시 GitHub 계정 이메일 + 카카오톡("나에게 보내기")으로 알림이 옵니다 (설정 완료, 2026-07-08). 재설정 필요 시 설계서.md 8장 참고 (`kakao_get_token.py` 1회 실행).

**올리브영이 Cloudflare 차단으로 실패했을 때**: `크롤러_실패시.md` + 랭킹 페이지 캡쳐를 Claude에게 함께 전달하면 절차대로 자동 처리됩니다 (상세는 설계서.md 8장). 카카오·다이소는 올리브영 실패와 무관하게 항상 정상 수집됩니다.
