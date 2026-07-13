"""
올리브영 Cloudflare 차단이 IP 기반인지 TLS fingerprint 기반인지 확인하는 1회성 테스트.
Playwright 헤드리스 브라우저로 올리브영 랭킹 페이지 접속 시도 → 성공 여부 출력.
GitHub Actions에서 workflow_dispatch로 실행 후 결과 확인, 확인 끝나면 이 파일 + 임시 워크플로 삭제.
"""
from playwright.sync_api import sync_playwright
from crawlers.base import new_page, save_screenshot
from crawlers.config import PLATFORMS

CFG = PLATFORMS["oliveyoung"]
URL = CFG["url"]

with sync_playwright() as pw:
    browser, context, page = new_page(pw, headless=True)
    try:
        resp = page.goto(URL, timeout=30000, wait_until="domcontentloaded")
        print(f"[결과] status={resp.status if resp else 'None'}")
        page.wait_for_timeout(2000)
        save_screenshot(page, "oliveyoung_playwright_test")

        items = page.query_selector_all("ul.cate_prd_list > li")
        print(f"[결과] 상품 li 개수: {len(items)}")

        title = page.title()
        print(f"[결과] 페이지 타이틀: {title}")

        body_text = page.inner_text("body")[:300]
        print(f"[결과] body 일부: {body_text}")

        if len(items) > 0:
            print("[결론] 성공 — Playwright(실브라우저)로는 접속 가능. TLS/fingerprint 문제였을 가능성.")
        else:
            print("[결론] 실패 — Playwright로도 차단됨. IP 차단 가능성 높음.")
    except Exception as e:
        print(f"[결과] 예외 발생: {type(e).__name__}: {e}")
        save_screenshot(page, "oliveyoung_playwright_error")
        print("[결론] 실패 — 접속 자체가 안 됨.")
    finally:
        browser.close()
