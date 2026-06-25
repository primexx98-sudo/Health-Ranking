from playwright.sync_api import sync_playwright
from .config import PLATFORMS, TIMEOUT, TOP_N
from .base import new_page, clean_price, save_screenshot

CFG = PLATFORMS["kakao"]
BASE_URL = "https://gift.kakao.com"

# 상품 그리드에서 첫 10개 추출 (추천순 = 사실상 인기순)
_JS = """
() => {
    // Kakao Gift는 React 컴포넌트 기반 — class 이름에 hash가 붙음
    // 여러 패턴으로 상품 카드 탐색
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

    // 폴백: 가격 텍스트 포함 반복 그룹 탐색
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
            // 브랜드: 짧은 텍스트 (보통 첫 번째 줄)
            const brand = lines.find(t => t.length >= 2 && t.length <= 20 && !/원$/.test(t)) || '';
            // 상품명: 가장 긴 텍스트
            const name  = lines
                .filter(t => t !== brand && !/^[\\d,]+원?$/.test(t) && !t.includes('후기'))
                .sort((a, b) => b.length - a.length)[0] || '';
            return { rank: idx + 1, name, brand, price, url: link?.href || '' };
        })
    };
}
"""


def crawl_kakao() -> list[dict]:
    print(f"[카카오선물하기] 크롤링 시작: {CFG['url']}")
    results = []

    with sync_playwright() as pw:
        browser, context, page = new_page(pw)
        try:
            page.goto(CFG["url"], timeout=TIMEOUT, wait_until="networkidle")
            page.wait_for_timeout(3000)  # React 렌더링 대기
            save_screenshot(page, "kakao_loaded")

            data = page.evaluate(_JS)

            if data.get("error"):
                save_screenshot(page, "kakao_no_products")
                print(f"  [카카오] 상품 없음 — {data['error']}")
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

            print(f"  [카카오] {len(results)}개 수집 완료")

        except Exception as e:
            save_screenshot(page, "kakao_error")
            print(f"  [카카오] 오류: {e}")
        finally:
            browser.close()

    return results
