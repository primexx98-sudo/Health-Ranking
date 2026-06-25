from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from .config import PLATFORMS, TIMEOUT, TOP_N
from .base import new_page, clean_price, save_screenshot

CFG = PLATFORMS["oliveyoung"]
BASE_URL = "https://www.oliveyoung.co.kr"

# 페이지에 실제로 어떤 요소가 있는지 탐색 후 상품 추출
_JS = """
() => {
    // 상품 리스트 후보 셀렉터 (넓게 시도)
    const candidates = [
        '#totalPrdList > li',
        '.prd-list > li',
        '.prod-list > li',
        '[id*="prdList"] > li',
        '[id*="PrdList"] > li',
        '[class*="prdList"] > li',
        '[class*="prodList"] > li',
        '[class*="goodsList"] > li',
        '[class*="productList"] > li',
        '.inner-list-wrap > li',
        '.list-wrap > li',
    ];

    let items = [];
    let matchedSel = '';
    for (const sel of candidates) {
        const found = Array.from(document.querySelectorAll(sel));
        if (found.length >= 5) { items = found; matchedSel = sel; break; }
    }

    // 폴백: 가격 텍스트를 포함한 li 그룹 탐색
    if (items.length === 0) {
        for (const ul of document.querySelectorAll('ul')) {
            const lis = Array.from(ul.querySelectorAll(':scope > li'));
            if (lis.length >= 8 && lis.some(li => /[\\d,]+원/.test(li.innerText))) {
                items = lis;
                matchedSel = 'fallback:' + (ul.id || ul.className.split(' ')[0]);
                break;
            }
        }
    }

    if (items.length === 0) {
        // 디버그: 페이지에 어떤 ul/li 구조가 있는지 출력
        const debug = Array.from(document.querySelectorAll('ul')).map(ul => ({
            id: ul.id,
            cls: ul.className.substring(0, 50),
            liCount: ul.querySelectorAll(':scope > li').length
        })).filter(d => d.liCount > 0).slice(0, 10);
        return { error: 'no_products', debug };
    }

    return {
        matched: matchedSel,
        items: items.slice(0, 10).map((li, idx) => {
            const link    = li.querySelector('a[href*="goodsNo"], a[href*="goods"], a[href]');
            const price   = (li.innerText.match(/([\\d,]+)원/) || [])[0] || '';
            const rankEl  = li.querySelector('[class*="rank"i], [class*="badge"i], strong');
            const rank    = rankEl ? (parseInt(rankEl.textContent) || idx + 1) : idx + 1;
            const brandEl = li.querySelector('[class*="brand"i], [class*="tx-brand"i], em');
            const brand   = brandEl?.textContent?.trim() || '';
            const nameEl  = li.querySelector('[class*="name"i] span, [class*="name"i], p span, p');
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
            stealth_sync(page)

            page.goto(CFG["url"], timeout=TIMEOUT, wait_until="networkidle")
            page.wait_for_timeout(4000)
            page.evaluate("window.scrollTo(0, 600)")  # 스크롤로 lazy load 트리거
            page.wait_for_timeout(2000)
            save_screenshot(page, "oliveyoung_loaded")

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
            print(f"  [올리브영] 오류: {e}")
        finally:
            browser.close()

    return results
