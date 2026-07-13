"""
올리브영 크롤러
Playwright(헤드리스 브라우저)로 카카오·다이소와 동일한 방식 사용.
curl_cffi(TLS 흉내만 내는 순수 HTTP 요청)는 JS를 실행하지 않아
GitHub Actions(Azure 데이터센터 IP)에서 Cloudflare에 고정 차단됨.

2026-07-13 검증: Playwright(진짜 브라우저) + playwright-stealth 조합도 여전히 막힘 —
stealth 제거 후 재테스트해도 동일하게 막혀 브라우저 지문 문제가 아님을 확인.
가정용 IP는 체크박스 없이 바로 통과하는 반면 Actions IP는 매번 Cloudflare Turnstile
("사람인지 확인하십시오") 인터랙티브 챌린지를 띄움 → Azure 데이터센터 IP 평판 자체가
원인. 다이소·카카오는 동일 환경에서 문제없이 통과하므로 올리브영 랭킹 페이지
(getBestList.do)에만 더 강한 봇 방어가 걸려 있는 것으로 추정.
대응: Turnstile 체크박스를 Playwright로 직접 클릭하는 로직(_try_pass_turnstile) 추가.
"""
from playwright.sync_api import sync_playwright
from .config import PLATFORMS, TIMEOUT, TOP_N
from .base import new_page, clean_price, save_screenshot

CFG = PLATFORMS["oliveyoung"]

MAX_RETRIES = 3
RETRY_DELAY = 5000  # ms, Cloudflare 간헐적 차단 대비 재시도 간격

# ul.cate_prd_list > li 기반 추출
# - span.tx_brand  : 브랜드
# - p.tx_name      : 상품명
# - span.tx_cur .tx_num : 가격
# - div.prd_name a[href] : 링크 (href의 t_number= 값이 실제 순위)
_JS = """
() => {
    const items = Array.from(document.querySelectorAll('ul.cate_prd_list > li'));
    if (items.length === 0) return { error: 'no_products' };

    const out = [];
    for (const li of items) {
        const brandEl = li.querySelector('span.tx_brand');
        const nameEl  = li.querySelector('p.tx_name');
        const priceEl = li.querySelector('span.tx_cur .tx_num');
        const linkEl  = li.querySelector('div.prd_name a[href]');
        if (!nameEl) continue;

        const href = linkEl?.getAttribute('href') || '';
        const m    = href.match(/t_number=(\\d+)/);
        const url  = href.startsWith('http') ? href : 'https://www.oliveyoung.co.kr' + href;

        out.push({
            rank:  m ? parseInt(m[1], 10) : out.length + 1,
            brand: brandEl?.innerText.trim() || '',
            name:  nameEl.innerText.trim(),
            price: priceEl?.innerText.trim() || '',
            url,
        });
    }
    out.sort((a, b) => a.rank - b.rank);
    return out.length ? { items: out.slice(0, 10) } : { error: 'no_valid_items' };
}
"""


def _try_pass_turnstile(page) -> bool:
    """Cloudflare Turnstile 체크박스('사람인지 확인하십시오')가 뜬 경우 클릭 시도."""
    print(f"  [올리브영] DEBUG frames (초기): {[f.url for f in page.frames]}")
    page.wait_for_timeout(4000)
    print(f"  [올리브영] DEBUG frames (4초 대기 후): {[f.url for f in page.frames]}")
    cf_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
    if cf_frames:
        try:
            body_html = cf_frames[-1].locator("body").inner_html(timeout=5000)
            print(f"  [올리브영] DEBUG turnstile frame body (앞 2000자): {body_html[:2000]}")
        except Exception as e:
            print(f"  [올리브영] DEBUG body 추출 실패: {type(e).__name__}: {e}")

    try:
        frame = page.frame_locator('iframe[src*="challenges.cloudflare.com"]').last
        checkbox = frame.locator('input[type="checkbox"]')
        checkbox.wait_for(state="visible", timeout=8000)
        checkbox.click()
        print("  [올리브영] Turnstile 체크박스 클릭 시도")
        page.wait_for_load_state("networkidle", timeout=TIMEOUT)
        page.wait_for_timeout(2000)
        return True
    except Exception as e:
        print(f"  [올리브영] Turnstile 미탐지/처리 불가: {type(e).__name__}: {e}")
        return False


def _crawl_once(page) -> list[dict]:
    page.goto(CFG["url"], timeout=TIMEOUT, wait_until="networkidle")
    page.wait_for_timeout(2000)

    data = page.evaluate(_JS)
    if data.get("error") and _try_pass_turnstile(page):
        data = page.evaluate(_JS)

    if data.get("error"):
        print(f"  [올리브영] 상품 없음 — {data['error']}")
        return []

    results = []
    for item in data["items"]:
        results.append({
            "카테고리": CFG["category"],
            "순위":    item["rank"],
            "상품명":  item["name"],
            "브랜드":  item["brand"],
            "가격":    clean_price(f"{item['price']}원") if item["price"] else "",
            "상품URL": item["url"],
        })
    return results[:TOP_N]


def crawl_oliveyoung(headless: bool = True) -> list[dict]:
    print(f"[올리브영] 크롤링 시작 (Playwright)")

    with sync_playwright() as pw:
        browser, context, page = new_page(pw, headless=headless)
        try:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    results = _crawl_once(page)
                    if results:
                        print(f"  [올리브영] {len(results)}개 수집 완료")
                        return results
                    print(f"  [올리브영] 시도 {attempt}/{MAX_RETRIES} 실패")
                except Exception as e:
                    print(f"  [올리브영] 오류: {type(e).__name__}: {e} — 시도 {attempt}/{MAX_RETRIES} 실패")

                if attempt < MAX_RETRIES:
                    page.wait_for_timeout(RETRY_DELAY)

            save_screenshot(page, "oliveyoung_no_items")
            print(f"  [올리브영] {MAX_RETRIES}회 재시도 후 최종 실패")
            return []

        except Exception as e:
            save_screenshot(page, "oliveyoung_error")
            print(f"  [올리브영] 오류: {type(e).__name__}: {e}")
            return []
        finally:
            browser.close()
