# 건강기능식품 판매순위 크롤러

올리브영 · 다이소몰 · 카카오 선물하기 건강기능식품 TOP10을 매일 자동 수집합니다.

## 구조

```
data/
  daily/   YYYY-MM-DD.xlsx        # 일별 수집 (3개 시트)
  monthly/ YYYY-MM_월별취합.xlsx   # 월별 평균순위 집계 (3개 시트)
```

## 자동화

- 매일 09:00 KST — daily_crawl.yml 실행
- 매월 1일 09:00 KST — monthly_aggregate.yml 실행 (전월 취합)

## 셀렉터 수정

사이트 구조 변경 시 crawlers/config.py 만 수정하세요.

## 로컬 실행

pip install -r requirements.txt
playwright install chromium
python main.py
python monthly_aggregate.py

## GitHub Actions 설정

Settings > Actions > General > Workflow permissions > Read and write permissions 체크
