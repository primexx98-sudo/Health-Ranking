# 셀렉터가 깨지면 이 파일만 수정하면 됩니다.
# 각 사이트에서 F12 → Elements 탭으로 실제 클래스명 확인 후 교체하세요.

PLATFORMS = {
    "kakao": {
        "name": "카카오선물하기",
        "urls": [
            {"url": "https://gift.kakao.com/category/5/subcategory/99",  "category": "건강식품·영양제"},
            {"url": "https://gift.kakao.com/category/5/subcategory/100", "category": "홍삼·건강즙"},
        ],
    },
    "daiso": {
        "name": "다이소몰",
        "url": "https://www.daisomall.co.kr/ds/exhCtgr/C208/CTGR_00022/CTGR_01020",
        "category": "건강식품",
        "wait_selector": ".ranking-list li, .rankList li, ul.pdList li",
        "item": ".ranking-list > li, .rankList > li, ul.pdList > li",
        "rank": ".ranking-num, .rank-num, .rankNum, em.num",
        "name": ".pd-name a, .pdNm a, .prdNm, .item-name",
        "brand": ".brand-name, .brandNm, .brand",
        "price": ".price em, .sell-price em, .salePrice em",
        "link": "a.pd-name, a.pdNm, .pd-thumb a",
    },
    "oliveyoung": {
        "name": "올리브영",
        "url": "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000020001&pageIdx=1&rowsPerPage=10",
        "category": "건강식품",
    },
}

TIMEOUT = 20000   # ms
TOP_N = 10
