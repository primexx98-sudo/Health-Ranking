"""
올리브영 크롤러
curl_cffi로 Chrome TLS 핑거프린트 모방 → Cloudflare 우회
PC 꺼진 상태에서도 GitHub Actions에서 완전 자동 실행 가능
"""
import re
from curl_cffi import requests as cf
from bs4 import BeautifulSoup
from .config import PLATFORMS, TOP_N
from .base import clean_price

CFG = PLATFORMS["oliveyoung"]
URL = CFG["url"]
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.oliveyoung.co.kr/store/display/getCategoryShop.do?dispCatNo=10000020001",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    results = []

    for li in soup.select("ul.cate_prd_list > li"):
        brand_el = li.select_one("span.tx_brand")
        name_el  = li.select_one("p.tx_name")
        price_el = li.select_one("span.tx_cur .tx_num")
        link_el  = li.select_one("div.prd_name a[href]")

        if not name_el:
            continue

        href   = link_el.get("href", "") if link_el else ""
        rank_m = re.search(r"t_number=(\d+)", href)
        url    = href if href.startswith("http") else f"https://www.oliveyoung.co.kr{href}"

        results.append({
            "카테고리": CFG["category"],
            "순위":    int(rank_m.group(1)) if rank_m else len(results) + 1,
            "상품명":  name_el.get_text(strip=True),
            "브랜드":  brand_el.get_text(strip=True) if brand_el else "",
            "가격":    clean_price(f"{price_el.get_text(strip=True)}원") if price_el else "",
            "상품URL": url,
        })

    results.sort(key=lambda x: x["순위"])
    return results[:TOP_N]


def crawl_oliveyoung(headless: bool = True) -> list[dict]:
    """headless 인수는 하위 호환을 위해 유지 (curl_cffi 방식에서 미사용)"""
    print(f"[올리브영] 크롤링 시작 (curl_cffi)")
    try:
        res = cf.get(URL, headers=HEADERS, impersonate="chrome131", timeout=20)
        if res.status_code != 200:
            print(f"  [올리브영] HTTP {res.status_code} — 수집 실패")
            return []

        results = _parse(res.text)
        print(f"  [올리브영] {len(results)}개 수집 완료")
        return results

    except Exception as e:
        print(f"  [올리브영] 오류: {type(e).__name__}: {e}")
        return []
