"""네이버 DataLab API - 검색어 트렌드 & 쇼핑 인사이트"""

import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class NaverDataLabAPI:
    SEARCH_URL = "https://openapi.naver.com/v1/datalab/search"
    SHOPPING_CATEGORY_URL = "https://openapi.naver.com/v1/datalab/shopping/categories"
    SHOPPING_KEYWORD_URL = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"

    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID", "")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경변수가 없습니다.\n"
                ".env 파일에 아래 두 줄을 추가하세요:\n"
                "  NAVER_CLIENT_ID=발급받은_Client_ID\n"
                "  NAVER_CLIENT_SECRET=발급받은_Client_Secret\n"
                "발급: https://developers.naver.com → 내 애플리케이션 → 애플리케이션 등록\n"
                "  (사용 API: 검색어 트렌드, 쇼핑 인사이트 체크)"
            )

    @property
    def _headers(self) -> dict:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json",
        }

    def _post(self, url: str, body: dict) -> dict:
        resp = requests.post(url, headers=self._headers, json=body, timeout=15)
        resp.raise_for_status()
        return resp.json()

    # ─── 검색어 트렌드 ───────────────────────────────────────────────
    def search_trend(
        self,
        keyword_groups: list[dict],
        start_date: str,
        end_date: str,
        time_unit: str = "month",
    ) -> pd.DataFrame:
        """검색어 트렌드 조회 (최대 5개 그룹 / 그룹당 키워드 최대 20개)

        keyword_groups 예시:
            [{"groupName": "유산균", "keywords": ["유산균", "프로바이오틱스"]}]
        """
        data = self._post(
            self.SEARCH_URL,
            {
                "startDate": start_date,
                "endDate": end_date,
                "timeUnit": time_unit,
                "keywordGroups": keyword_groups,
            },
        )
        rows = []
        for item in data.get("results", []):
            for d in item["data"]:
                rows.append(
                    {"날짜": d["period"], "키워드그룹": item["title"], "검색량지수": d["ratio"]}
                )
        return pd.DataFrame(rows)

    # ─── 쇼핑 인사이트 - 분야별 ──────────────────────────────────────
    def shopping_category_trend(
        self,
        categories: list[dict],
        start_date: str,
        end_date: str,
        time_unit: str = "month",
        device: str = "",
        ages: list = [],
        gender: str = "",
    ) -> pd.DataFrame:
        """쇼핑 분야별 클릭 트렌드 조회 (최대 5개 카테고리)

        categories 예시:
            [{"name": "건강식품", "param": ["50000008"]}]
        """
        data = self._post(
            self.SHOPPING_CATEGORY_URL,
            {
                "startDate": start_date,
                "endDate": end_date,
                "timeUnit": time_unit,
                "category": categories,
                "device": device,
                "ages": ages,
                "gender": gender,
            },
        )
        rows = []
        for item in data.get("results", []):
            for d in item["data"]:
                rows.append(
                    {"날짜": d["period"], "카테고리": item["title"], "클릭량지수": d["ratio"]}
                )
        return pd.DataFrame(rows)

    # ─── 쇼핑 인사이트 - 키워드별 ────────────────────────────────────
    def shopping_keyword_trend(
        self,
        category: str,
        keywords: list[dict],
        start_date: str,
        end_date: str,
        time_unit: str = "month",
        device: str = "",
        ages: list = [],
        gender: str = "",
    ) -> pd.DataFrame:
        """쇼핑 카테고리 내 키워드별 클릭 트렌드 조회 (최대 5개 키워드)

        keywords 예시:
            [{"name": "유산균", "param": ["유산균"]}]
        """
        data = self._post(
            self.SHOPPING_KEYWORD_URL,
            {
                "startDate": start_date,
                "endDate": end_date,
                "timeUnit": time_unit,
                "category": category,
                "keyword": keywords,
                "device": device,
                "ages": ages,
                "gender": gender,
            },
        )
        rows = []
        for item in data.get("results", []):
            for d in item["data"]:
                rows.append(
                    {"날짜": d["period"], "키워드": item["title"], "클릭량지수": d["ratio"]}
                )
        return pd.DataFrame(rows)
