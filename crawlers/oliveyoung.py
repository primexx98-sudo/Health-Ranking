from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from .config import PLATFORMS, TIMEOUT, TOP_N
from .base import new_page, clean_price, save_screenshot

CFG = PLATFORMS["oliveyoung"]
BASE_URL = "https://www.oliveyoung.co.kr"

_JS = """
() => {
    const selectors = [
        '#totalPrdList > li', '.prd-list > li',
        '[class*="prdList"] > li', '[class*="goodsList"] > li'
    ];

    let items = [];
    for (const sel of selectors) {
        items = Array.from(document.querySelectorAll(sel));
        if (items.length >= 5) break;
    }

    if (items.length === 0) return { error: 'no_products' };

    return {
        items: Array.from(items).slice(0, 10).map((li, idx) => {
            const link    = li.querySelector('a[href*="goodsNo"], a[href]');
            const price   = (li.innerText.match(/([\\d,]+)원/) || [])[0] || '';
            const rankEl  = li.querySelector('[class*="rank"i], [class*="badge"i]');
            const rank    = rankEl ? (parseInt(rankEl.textContent) || idx + 1) : idx + 1;
            const brandEl = li.querySelector('[class*="brand"i], [class*="tx-brand"i]');
            const brand   = brandEl?.textContent?.trim() || '';
            const nameEl  = li.querySelector('[class*="name"i] span, [class*="name"i]');
            const name    = nameEl?.textContent?.trim() || '';
            return { rank, name, brand, price, url: link?.href || '' };
        })
    };
}
"""


def crawl_oliveyoung() -> list[dict]:
    print(f"[올리브영] 크롤링 시작: {CFG['url']}")
    results = []

    with sync_playwright() as pw:
        browser, context, page = new_page(pw)
        try:
            stealth_sync(page)  # Cloudflare 우회

            page.goto(CFG["url"], timeout=TIMEOUT, wait_until="networkidle")
            page.wait_for_timeout(3000)
            save_screenshot(page, "oliveyoung_loaded")

            # 팝업 닫기 시도
            try:
                popup = page.query_selector(".btn-close, .layer-close, [class*='close']")
                if popup:
                    popup.click()
                    page.wait_for_timeout(500)
            except Exception:
                pass

            data = page.evaluate(_JS)

            if data.get("error"):
                save_screenshot(page, "oliveyoung_no_products")
                print(f"  [올리브영] 상품 없음 — {data['error']}")
                return []

            for item in data["items"]:
                results.append({
                    "카테고리": CFG["category"],
                    "순위": item["rank"],
                    "상품명": item["name"],
                    "브랜드": item["brand"],
                    "가격": clean_price(item["price"]),
                    "상품URL": item["url"],
                })

            print(f"  [올리브영] {len(results)}개 수집 완료")

        except Exception as e:
            save_screenshot(page, "oliveyoung_error")
            print(f"  [올리브영] 오류: {e}")
        finally:
            browser.close()

    return results
