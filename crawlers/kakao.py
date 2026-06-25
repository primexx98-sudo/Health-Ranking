from playwright.sync_api import sync_playwright
from .config import PLATFORMS, TIMEOUT, TOP_N
from .base import new_page, clean_price, save_screenshot

CFG = PLATFORMS["kakao"]

_JS = """
() => {
    const selectors = [
        '[class*="GoodsItem"]', '[class*="goodsItem"]',
        '[class*="ProductItem"]', '[class*="productItem"]',
        '[class*="PrdItem"]', '[class*="prdItem"]',
        '.goods-list > li', '.prd-list > li', '.goods_list > li'
    ];

    let items = [];
    for (const sel of selectors) {
        items = Array.from(document.querySelectorAll(sel));
        if (items.length >= 5) break;
    }

    if (items.length < 5) {
        for (const ul of document.querySelectorAll('ul, ol')) {
            const lis = Array.from(ul.children);
            if (lis.length >= 8 && lis[0]?.innerText?.includes('원')) {
                items = lis;
                break;
            }
        }
    }

    if (items.length === 0) return { error: 'no_products' };

    return {
        items: Array.from(items).slice(0, 10).map((el, idx) => {
            const link  = el.querySelector('a[href*="/product/"], a[href*="/goods/"], a[href]');
            const price = (el.innerText.match(/([\\d,]+)원/) || [])[0] || '';
            const lines = el.innerText.split(/[\\n\\r]/).map(s => s.trim()).filter(Boolean);
            const brand = lines.find(t => t.length >= 2 && t.length <= 20 && !/원$/.test(t)) || '';
            const name  = lines
                .filter(t => t !== brand && !/^[\\d,]+원?$/.test(t) && !t.includes('후기'))
                .sort((a, b) => b.length - a.length)[0] || '';
            return { rank: idx + 1, name, brand, price, url: link?.href || '' };
        })
    };
}
"""


def _crawl_one(page, url_cfg: dict) -> list[dict]:
    url      = url_cfg["url"]
    category = url_cfg["category"]
    slug     = category.replace("·", "_").replace(" ", "")

    page.goto(url, timeout=TIMEOUT, wait_until="networkidle")
    page.wait_for_timeout(3000)
    save_screenshot(page, f"kakao_{slug}_loaded")

    data = page.evaluate(_JS)
    if data.get("error"):
        save_screenshot(page, f"kakao_{slug}_no_products")
        print(f"  [카카오/{category}] 상품 없음")
        return []

    results = []
    for item in data["items"]:
        results.append({
            "카테고리": category,
            "순위": item["rank"],
            "상품명": item["name"],
            "브랜드": item["brand"],
            "가격": clean_price(item["price"]),
            "상품URL": item["url"],
        })
    print(f"  [카카오/{category}] {len(results)}개 수집 완료")
    return results


def crawl_kakao(headless: bool = True) -> list[dict]:
    print(f"[카카오선물하기] 크롤링 시작 — {len(CFG['urls'])}개 카테고리")
    results = []

    with sync_playwright() as pw:
        browser, context, page = new_page(pw, headless=headless)
        try:
            for url_cfg in CFG["urls"]:
                results.extend(_crawl_one(page, url_cfg))
        except Exception as e:
            save_screenshot(page, "kakao_error")
            print(f"  [카카오] 오류: {type(e).__name__}: {e}")
        finally:
            browser.close()

    return results
