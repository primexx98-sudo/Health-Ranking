from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .config import PLATFORMS, TIMEOUT, TOP_N
from .base import new_page, extract_text, extract_link, clean_price, save_screenshot

CFG = PLATFORMS["oliveyoung"]
BASE_URL = "https://www.oliveyoung.co.kr"


def crawl_oliveyoung() -> list[dict]:
    print(f"[올리브영] 크롤링 시작: {CFG['url']}")
    results = []

    with sync_playwright() as pw:
        browser, context, page = new_page(pw)
        try:
            page.goto(CFG["url"], timeout=TIMEOUT, wait_until="networkidle")

            # 올리브영은 성인 확인 팝업이 뜰 수 있음
            try:
                popup = page.query_selector("button[class*='close'], .layer-close, .btn-close")
                if popup:
                    popup.click()
                    page.wait_for_timeout(500)
            except Exception:
                pass

            try:
                page.wait_for_selector(CFG["wait_selector"], timeout=TIMEOUT)
            except PWTimeout:
                save_screenshot(page, "oliveyoung_timeout")
                print("  [올리브영] 셀렉터 대기 시간 초과 — config.py의 wait_selector 확인 필요")
                return []

            items = page.query_selector_all(CFG["item"])[:TOP_N]

            if not items:
                save_screenshot(page, "oliveyoung_no_items")
                print("  [올리브영] 상품 목록을 찾지 못했습니다 — config.py의 item 셀렉터 확인 필요")
                return []

            for i, item in enumerate(items, start=1):
                rank_text = extract_text(page, item, CFG["rank"])
                rank = int(rank_text) if rank_text.isdigit() else i

                name = extract_text(page, item, CFG["name"])
                brand = extract_text(page, item, CFG["brand"])
                price_raw = extract_text(page, item, CFG["price"])
                url = extract_link(page, item, CFG["link"], BASE_URL)

                results.append({
                    "카테고리": CFG["category"],
                    "순위": rank,
                    "상품명": name,
                    "브랜드": brand,
                    "가격": clean_price(price_raw),
                    "상품URL": url,
                })

            print(f"  [올리브영] {len(results)}개 수집 완료")

        except Exception as e:
            save_screenshot(page, "oliveyoung_error")
            print(f"  [올리브영] 오류 발생: {e}")
        finally:
            browser.close()

    return results
