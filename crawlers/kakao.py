from playwright.sync_api import sync_playwright
from .config import PLATFORMS, TIMEOUT, TOP_N
from .base import new_page, clean_price, save_screenshot

CFG = PLATFORMS["kakao"]

# gc-product 웹 컴포넌트 기반 추출
# - span.txt_prdbrand : 브랜드
# - strong.txt_prdname : 상품명
# - a.link_prdunit    : 링크
# - .area_ad/.txt_ad/gc-product-ad-badge : MD추천 광고 → 제외
_JS = """
() => {
    function isAd(el) {
        return !!(el.querySelector(
            '.area_ad, .txt_ad, gc-product-ad-badge, [class*="ad-badge"]'
        ));
    }

    // 1순위: gc-product 웹 컴포넌트
    let items = Array.from(document.querySelectorAll('gc-product'));

    // 2순위: a.link_prdunit 가장 많은 .list_prd 컨테이너의 자식
    if (items.length < 5) {
        let best = null, bestCount = 0;
        for (const list of document.querySelectorAll('.list_prd, [class*="list_prd"]')) {
            const cnt = list.querySelectorAll('a.link_prdunit').length;
            if (cnt > bestCount) { best = list; bestCount = cnt; }
        }
        if (best) items = Array.from(best.children);
    }

    if (items.length === 0) return { error: 'no_products' };

    const out = [];
    for (const el of items) {
        if (isAd(el)) continue;

        const linkEl  = el.querySelector('a.link_prdunit[href]');
        const brandEl = el.querySelector('span.txt_prdbrand');
        const nameEl  = el.querySelector('strong.txt_prdname');
        const priceM  = el.innerText.match(/([\\d,]+)원/);
        const href    = linkEl?.getAttribute('href') || '';

        out.push({
            rank:  out.length + 1,
            brand: brandEl?.innerText.trim() || '',
            name:  nameEl?.innerText.trim()  || '',
            price: priceM ? priceM[0] : '',
            url:   href.startsWith('http') ? href : 'https://gift.kakao.com' + href,
        });
        if (out.length >= 10) break;
    }
    return out.length ? { items: out } : { error: 'no_valid_items' };
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
        print(f"  [카카오/{category}] 상품 없음 — {data['error']}")
        return []

    results = []
    for item in data["items"]:
        results.append({
            "카테고리": category,
            "순위":    item["rank"],
            "상품명":  item["name"],
            "브랜드":  item["brand"],
            "가격":    clean_price(item["price"]),
            "상품URL": item["url"],
        })
    print(f"  [카카오/{category}] {len(results)}개 수집 완료")
    return results


def crawl_kakao(headless: bool = True) -> list[dict]:
    print(f"[카카오선물하기] 크롤링 시작 - {len(CFG['urls'])}개 카테고리")
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
