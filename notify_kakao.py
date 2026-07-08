"""
GitHub Actions 실패 시 카카오톡 '나에게 보내기'로 알림 전송.
Refresh Token은 사용할 때마다 자동 연장되며, 카카오가 새 Refresh Token을
내려주면 GH_PAT으로 GitHub Secrets(KAKAO_REFRESH_TOKEN)를 갱신한다.
필요 환경변수: KAKAO_REST_API_KEY, KAKAO_REFRESH_TOKEN, GH_PAT,
              GITHUB_REPOSITORY(Actions 기본 제공), RUN_URL
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
SEND_URL  = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


def _post_form(url: str, data: dict, headers: dict | None = None) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req  = urllib.request.Request(url, data=body, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        raise


def refresh_access_token(rest_api_key: str, refresh_token: str) -> dict:
    return _post_form(TOKEN_URL, {
        "grant_type":    "refresh_token",
        "client_id":     rest_api_key,
        "refresh_token": refresh_token,
    })


def send_message(access_token: str, text: str) -> dict:
    template = {"object_type": "text", "text": text, "link": {}, "button_title": "확인"}
    return _post_form(
        SEND_URL,
        {"template_object": json.dumps(template, ensure_ascii=False)},
        headers={"Authorization": f"Bearer {access_token}"},
    )


def update_refresh_token_secret(repo: str, new_refresh_token: str, gh_pat: str):
    env = {**os.environ, "GH_TOKEN": gh_pat}
    subprocess.run(
        ["gh", "secret", "set", "KAKAO_REFRESH_TOKEN", "--repo", repo, "--body", new_refresh_token],
        check=True, env=env,
    )
    print("KAKAO_REFRESH_TOKEN 시크릿 갱신 완료")


def main():
    rest_api_key  = os.environ["KAKAO_REST_API_KEY"]
    refresh_token = os.environ["KAKAO_REFRESH_TOKEN"]
    gh_pat        = os.environ["GH_PAT"]
    repo          = os.environ["GITHUB_REPOSITORY"]
    run_url       = os.environ.get("RUN_URL", "")

    token_res = refresh_access_token(rest_api_key, refresh_token)
    access_token = token_res["access_token"]

    if new_refresh := token_res.get("refresh_token"):
        update_refresh_token_secret(repo, new_refresh, gh_pat)

    text = f"[건강기능식품 크롤러] 수집 실패\n{run_url}"
    result = send_message(access_token, text)
    print(f"카카오톡 알림 발송 완료: {result}")


if __name__ == "__main__":
    main()
