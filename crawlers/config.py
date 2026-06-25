# 셀렉터가 깨지면 이 파일만 수정하면 됩니다.
# 각 사이트에서 F12 → Elements 탭으로 실제 클래스명 확인 후 교체하세요.

PLATFORMS = {
    "kakao": {
        "name": "카카오선물하기",
        "url": "https://gift.kakao.com/category/5/subcategory/99",
        "category": "건강식품",
        "wait_selector": "[class*='ranking'], [class*='Ranking'], [class*='prdItem']",
        "item": "[class*='rankingItem'], [class*='RankingItem'], [class*='ranking_item']",
        "rank": "[class*='rank']:first-of-type, [class*='Rank']:first-of-type, em.num, .num",
        "name": "[class*='productName'], [class*='product_name'], [class*='name']",
        "brand": "[class*='brandName'], [class*='brand_name'], [class*='brand']",
        "price": "[class*='price']:not([class*='original']):not([class*='Origin'])",
        "link": "a",
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
        "url": "https://www.oliveyoung.co.kr/store/display/getCategoryShop.do?dispCatNo=10000020001",
        "category": "건강식품",
        "wait_selector": "#totalPrdList > li, .prd-list > li",
        "item": "#totalPrdList > li, .prd-list > li",
        "rank": "span.badge-ranking, .num-rank, .prd-rank strong",
        "name": "p.prd-name span, .prd_name span, .tx-name",
        "brand": "span.tx-brand, .brand-name, .prd-brand",
        "price": "span.price-2 em, .prd-price .price-2 em, .tx-cur",
        "link": "a.prd-item, .prd-name a, a[href*='goodsNo']",
    },
}

TIMEOUT = 20000   # ms
TOP_N = 10
