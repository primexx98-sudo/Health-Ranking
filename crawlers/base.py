from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout
from pathlib import Path
import re


def clean_price(text: str) -> str:
    if not text:
        return ""
    digits = re.sub(r"[^\d]", "", text)
    return f"{int(digits):,}원" if digits else text.strip()


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip() if text else ""


def extract_text(page: Page, parent, selector: str) -> str:
    try:
        el = parent.query_selector(selector)
        return clean_text(el.inner_text()) if el else ""
    except Exception:
        return ""


def extract_link(page: Page, parent, selector: str, base_url: str = "") -> str:
    try:
        el = parent.query_selector(selector)
        if not el:
            return ""
        href = el.get_attribute("href") or ""
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return base_url.rstrip("/") + href
        return href
    except Exception:
        return ""


def new_page(playwright) -> tuple:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="ko-KR",
        timezone_id="Asia/Seoul",
        viewport={"width": 1280, "height": 900},
    )
    page = context.new_page()
    return browser, context, page


def save_screenshot(page: Page, name: str):
    path = Path("screenshots")
    path.mkdir(exist_ok=True)
    page.screenshot(path=str(path / f"{name}.png"), full_page=True)
    print(f"  스크린샷 저장: screenshots/{name}.png")
