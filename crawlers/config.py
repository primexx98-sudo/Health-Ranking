# 셀렉터가 깨지면 이 파일만 수정하면 됩니다.
# 각 사이트에서 F12 → Elements 탭으로 실제 클래스명 확인 후 교체하세요.

PLATFORMS = {
    "kakao": {
        "name": "카카오선물하기",
        "urls": [
            {"url": "https://gift.kakao.com/category/5/subcategory/99",  "category": "건강식품·영양제"},
            {"url": "https://gift.kakao.com/category/5/subcategory/100", "category": "다이어트·이너뷰티"},
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
        "url": "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000020001&pageIdx=1&rowsPerPage=24&t_page=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EA%B4%80&t_click=%EB%9E%AD%ED%82%B9BEST%EC%83%81%ED%92%88%EB%B8%8C%EB%9E%9C%EB%93%9C_%EC%9D%B8%EA%B8%B0%EC%83%81%ED%92%88%EB%8D%94%EB%B3%B4%EA%B8%B0",
        "category": "건강식품",
    },
}

TIMEOUT = 20000   # ms
TOP_N = 10
