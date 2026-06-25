"""
올리브영 크롤러
curl_cffi로 Chrome TLS 핑거프린트 모방 → Cloudflare 우회
PC 꺼진 상태에서도 GitHub Actions에서 완전 자동 실행 가능
"""
import re
from curl_cffi import requests as cf
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

# li 블록 단위 추출
_LI_RE    = re.compile(r"<li[^>]*>.*?</li>", re.DOTALL)
_RANK_RE  = re.compile(r"t_number=(\d+)")
_GOODS_RE = re.compile(r"goodsNo=([A-Z0-9]+)")
_BRAND_RE = re.compile(r'class="tx_brand">([^<]+)</span>')
_NAME_RE  = re.compile(r'class="tx_name">([^<]+)</p>')
_PRICE_RE = re.compile(r'class="tx_cur"><span class="tx_num">([\d,]+)</span>')


def _parse(html: str) -> list[dict]:
    results = []
    for block in _LI_RE.findall(html):
        if "Best_Sellingbest" not in block or "t_number=" not in block:
            continue
        rank_m  = _RANK_RE.search(block)
        goods_m = _GOODS_RE.search(block)
        brand_m = _BRAND_RE.search(block)
        name_m  = _NAME_RE.search(block)
        price_m = _PRICE_RE.search(block)
        if not (rank_m and goods_m and name_m):
            continue
        results.append({
            "카테고리": CFG["category"],
            "순위":    int(rank_m.group(1)),
            "상품명":  name_m.group(1).strip(),
            "브랜드":  brand_m.group(1).strip() if brand_m else "",
            "가격":    clean_price(f"{price_m.group(1)}원") if price_m else "",
            "상품URL": (
                f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do"
                f"?goodsNo={goods_m.group(1)}"
            ),
        })
    results.sort(key=lambda x: x["순위"])
    return results[:TOP_N]


def crawl_oliveyoung(headless: bool = True) -> list[dict]:
    """headless 인수는 하위 호환을 위해 유지 (curl_cffi 방식에서 미사용)"""
    print(f"[올리브영] 크롤링 시작 (curl_cffi)")
    try:
        res = cf.get(URL, headers=HEADERS, impersonate="chrome124", timeout=20)
        if res.status_code != 200:
            print(f"  [올리브영] HTTP {res.status_code} — 수집 실패")
            return []

        results = _parse(res.text)
        print(f"  [올리브영] {len(results)}개 수집 완료")
        return results

    except Exception as e:
        print(f"  [올리브영] 오류: {type(e).__name__}: {e}")
        return []
