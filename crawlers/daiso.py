from playwright.sync_api import sync_playwright
from .config import PLATFORMS, TIMEOUT, TOP_N
from .base import new_page, clean_price, save_screenshot

CFG = PLATFORMS["daiso"]
BASE_URL = "https://www.daisomall.co.kr"

# a.detail-link[href] 기반 카드 수집
# - swiper-slide-duplicate(루프 복제) 제외
# - pdNo 기준 중복 제거
# - div.product-title : 상품명
_JS_COLLECT = """
() => {
    const seen  = new Set();
    const cards = [];

    for (const a of document.querySelectorAll('a.detail-link[href]')) {
        if (a.closest('.swiper-slide-duplicate')) continue;

        const href = a.getAttribute('href') || '';
        const m    = href.match(/pdNo=([^&]+)/);
        if (!m) continue;

        const pdNo = m[1];
        if (seen.has(pdNo)) continue;
        seen.add(pdNo);

        const nameEl  = a.querySelector('div.product-title');
        const priceEl = a.querySelector('[class*="price"]');
        const fullUrl = href.startsWith('http')
            ? href
            : 'https://www.daisomall.co.kr' + href;

        cards.push({
            pdNo,
            name:  nameEl?.innerText.trim()  || '',
            price: priceEl?.innerText.trim() || '',
            url:   fullUrl,
        });
        if (cards.length >= 10) break;
    }
    return { count: cards.length, items: cards };
}
"""

# 상세페이지에서 브랜드 추출: a.brand-area .detail-title
_JS_BRAND = """
() => {
    const el = document.querySelector('a.brand-area .detail-title');
    return el ? el.innerText.trim() : '';
}
"""


def _fetch_brand(page, url: str) -> str:
    try:
        page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        return page.evaluate(_JS_BRAND)
    except Exception:
        return ""


def crawl_daiso(headless: bool = True) -> list[dict]:
    print(f"[다이소몰] 크롤링 시작: {CFG['url']}")
    results = []

    with sync_playwright() as pw:
        browser, context, page = new_page(pw, headless=headless)
        try:
            page.goto(CFG["url"], timeout=TIMEOUT, wait_until="networkidle")
            page.wait_for_timeout(2000)
            save_screenshot(page, "daiso_loaded")

            data  = page.evaluate(_JS_COLLECT)
            items = data.get("items", [])

            # 10개 미만이면 Next 버튼 클릭 후 재추출 (최대 6회)
            for _ in range(6):
                if len(items) >= TOP_N:
                    break
                try:
                    btn = page.query_selector(".swiper-button-next")
                    if not btn:
                        break
                    btn.click()
                    page.wait_for_timeout(800)
                    data  = page.evaluate(_JS_COLLECT)
                    items = data.get("items", [])
                except Exception:
                    break

            if not items:
                save_screenshot(page, "daiso_no_items")
                print("  [다이소] 상품 없음")
                return []

            # 각 상품 상세페이지 방문 → 브랜드 추출
            for idx, item in enumerate(items[:TOP_N]):
                brand = _fetch_brand(page, item["url"])
                name  = item["name"]
                # 브랜드명이 상품명 앞에 중복으로 붙어있으면 제거
                if brand and name.startswith(brand):
                    name = name[len(brand):].strip()

                results.append({
                    "카테고리": CFG["category"],
                    "순위":    idx + 1,
                    "상품명":  name,
                    "브랜드":  brand,
                    "가격":    clean_price(item["price"]) if item["price"] else "",
                    "상품URL": item["url"],
                })

            print(f"  [다이소] {len(results)}개 수집 완료")

        except Exception as e:
            save_screenshot(page, "daiso_error")
            print(f"  [다이소] 오류: {e}")
        finally:
            browser.close()

    return results
