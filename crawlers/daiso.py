from playwright.sync_api import sync_playwright
from .config import PLATFORMS, TIMEOUT, TOP_N
from .base import new_page, clean_price, save_screenshot

CFG = PLATFORMS["daiso"]
BASE_URL = "https://www.daisomall.co.kr"

# "실시간 랭킹" 텍스트를 포함한 섹션을 찾아 JS로 직접 추출
_JS = """
() => {
    // 1) "실시간 랭킹" 텍스트 근처 컨테이너 찾기
    let container = null;
    for (const node of document.querySelectorAll('*')) {
        if (node.childElementCount === 0) {
            const t = node.textContent.trim();
            if (t.includes('실시간') && t.includes('랭킹')) {
                let p = node.parentElement;
                for (let i = 0; i < 10; i++) {
                    if (!p) break;
                    if (p.querySelectorAll('li').length >= 5) { container = p; break; }
                    p = p.parentElement;
                }
                if (container) break;
            }
        }
    }

    // 2) 못 찾으면 일반 셀렉터 폴백
    if (!container) {
        for (const sel of ['.rnkList', '.rankList', '.ranking-list', '.realRnkList', 'ul.pdList']) {
            const el = document.querySelector(sel);
            if (el && el.querySelectorAll('li').length >= 3) { container = el; break; }
        }
    }

    if (!container) return { error: 'no_ranking_section' };

    const items = Array.from(container.querySelectorAll('li')).slice(0, 10);
    return {
        items: items.map((li, idx) => {
            const link  = li.querySelector('a[href]');
            const price = (li.innerText.match(/([\\d,]+)원/) || [])[0] || '';
            const lines = li.innerText.split(/[\\n\\r]/).map(s => s.trim()).filter(Boolean);
            const name  = lines
                .filter(t => t.length > 2 && !/^[\\d,]+원?$/.test(t) && !t.includes('후기') && !t.includes('★'))
                .sort((a, b) => b.length - a.length)[0] || '';
            const numEl = li.querySelector('[class*="num"i]');
            const rank  = numEl ? (parseInt(numEl.textContent) || idx + 1) : idx + 1;
            return { rank, name, price, url: link?.href || '' };
        })
    };
}
"""


def crawl_daiso(headless: bool = True) -> list[dict]:
    print(f"[다이소몰] 크롤링 시작: {CFG['url']}")
    results = []

    with sync_playwright() as pw:
        browser, context, page = new_page(pw, headless=headless)
        try:
            page.goto(CFG["url"], timeout=TIMEOUT, wait_until="networkidle")
            page.wait_for_timeout(2000)
            save_screenshot(page, "daiso_loaded")

            data = page.evaluate(_JS)

            if data.get("error"):
                save_screenshot(page, "daiso_no_ranking")
                print(f"  [다이소] 랭킹 섹션 없음 — {data['error']}")
                return []

            for item in data["items"]:
                results.append({
                    "카테고리": CFG["category"],
                    "순위": item["rank"],
                    "상품명": item["name"],
                    "브랜드": "다이소",
                    "가격": clean_price(item["price"]),
                    "상품URL": item["url"],
                })

            print(f"  [다이소] {len(results)}개 수집 완료")

        except Exception as e:
            save_screenshot(page, "daiso_error")
            print(f"  [다이소] 오류: {e}")
        finally:
            browser.close()

    return results
