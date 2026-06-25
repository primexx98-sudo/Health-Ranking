from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from .config import PLATFORMS, TOP_N
from .base import new_page, clean_price, save_screenshot

CFG = PLATFORMS["oliveyoung"]
BASE_URL = "https://www.oliveyoung.co.kr"

# 올리브영 랭킹 베스트 페이지 전용 추출
_JS = """
() => {
    // getBestList 페이지 상품 카드 탐색
    const candidates = [
        '.prd-item', '.prod-item', '.goods-item',
        '[class*="prdItem"]', '[class*="prodItem"]',
        '#bestRankingWrap li', '.best-list li',
        '.ranking-wrap li', '.rank-list li',
        '#totalPrdList > li', '.prd-list > li',
    ];

    let items = [];
    let matchedSel = '';
    for (const sel of candidates) {
        const found = Array.from(document.querySelectorAll(sel));
        if (found.length >= 3) { items = found; matchedSel = sel; break; }
    }

    // 폴백: 가격 포함 반복 요소 탐색 (li 또는 div)
    if (items.length === 0) {
        for (const parent of document.querySelectorAll('ul, ol, div')) {
            const children = Array.from(parent.querySelectorAll(':scope > li, :scope > div'));
            if (children.length >= 3 && children.filter(el => /[\\d,]+원/.test(el.innerText)).length >= 3) {
                items = children;
                matchedSel = 'auto:' + (parent.id || parent.className.trim().split(' ')[0]);
                break;
            }
        }
    }

    if (items.length === 0) {
        const ulInfo = Array.from(document.querySelectorAll('ul,ol')).map(u => ({
            id: u.id, cls: u.className.substring(0,40), len: u.children.length
        })).filter(u => u.len > 0);
        return { error: 'no_products', debug: ulInfo.slice(0, 10) };
    }

    return {
        matched: matchedSel,
        items: Array.from(items).slice(0, 10).map((el, idx) => {
            const link    = el.querySelector('a[href*="goodsNo"], a[href*="goods"], a[href]');
            const price   = (el.innerText.match(/([\\d,]+)원/) || [])[0] || '';
            const rankEl  = el.querySelector('[class*="rank"i], [class*="num"i], strong');
            const rank    = rankEl ? (parseInt(rankEl.textContent) || idx + 1) : idx + 1;
            const brandEl = el.querySelector('[class*="brand"i], [class*="tx-brand"i], em');
            const brand   = brandEl?.textContent?.trim() || '';
            const nameEl  = el.querySelector('[class*="name"i] span, [class*="name"i], p span, p');
            const name    = nameEl?.textContent?.trim() || '';
            return { rank, name, brand, price, url: link?.href || '' };
        })
    };
}
"""


def crawl_oliveyoung(headless: bool = True) -> list[dict]:
    print(f"[올리브영] 크롤링 시작: {CFG['url']}")
    results = []

    with sync_playwright() as pw:
        browser, context, page = new_page(pw, headless=headless)
        try:
            if headless:
                Stealth().apply_stealth_sync(page)

            page.goto(CFG["url"], timeout=60000, wait_until="domcontentloaded")
            save_screenshot(page, "oliveyoung_loaded")
            page.wait_for_timeout(2000)
            page.evaluate("window.scrollTo(0, 600)")
            page.wait_for_timeout(1000)
            page.evaluate("window.scrollTo(0, 1200)")
            page.wait_for_timeout(2000)

            data = page.evaluate(_JS)

            if data.get("error"):
                save_screenshot(page, "oliveyoung_no_products")
                print(f"  [올리브영] 상품 없음 — debug: {data.get('debug', [])}")
                return []

            print(f"  [올리브영] 셀렉터 매칭: {data.get('matched')}")

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
            print(f"  [올리브영] 오류: {type(e).__name__}: {e}")
        finally:
            browser.close()

    return results
