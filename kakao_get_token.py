"""
카카오톡 '나에게 보내기' 알림용 최초 1회 토큰 발급 스크립트 (로컬에서만 실행).

사전 준비 (developers.kakao.com):
  1. 애플리케이션 추가
  2. 앱 설정 > 카카오 로그인 활성화
  3. 앱 설정 > 카카오 로그인 > Redirect URI 에 https://localhost.com 등록
  4. 앱 설정 > 카카오 로그인 > 동의항목 > "카카오톡 메시지 전송(talk_message)" 를
     선택 동의로 설정 (앱 소유자 본인 계정은 별도 검수 없이 사용 가능)
  5. 앱 키 > REST API 키를 .env 의 KAKAO_REST_API_KEY 에 저장
  6. 앱 설정 > 보안 > Client Secret이 "사용함(필수)"이면, 코드 값을
     .env 의 KAKAO_CLIENT_SECRET 에 저장 ("사용안함"이면 비워둬도 됨)

실행:
  python kakao_get_token.py
"""
import json
import os
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()

REDIRECT_URI = "https://localhost.com"
TOKEN_URL    = "https://kauth.kakao.com/oauth/token"


def main():
    rest_api_key  = os.environ.get("KAKAO_REST_API_KEY")
    client_secret = os.environ.get("KAKAO_CLIENT_SECRET")
    if not rest_api_key:
        print("`.env` 에 KAKAO_REST_API_KEY 를 먼저 채워주세요.")
        return

    auth_url = (
        "https://kauth.kakao.com/oauth/authorize?"
        + urllib.parse.urlencode({
            "client_id":     rest_api_key,
            "redirect_uri":  REDIRECT_URI,
            "response_type": "code",
            "scope":         "talk_message",
        })
    )
    print("1) 아래 URL을 브라우저에서 열고 카카오 로그인/동의를 진행하세요:\n")
    print(f"   {auth_url}\n")
    print("2) 로그인 후 '사이트에 연결할 수 없음' 페이지로 이동하는데, 정상입니다.")
    print("   주소창의 URL에서 code=... 부분 값만 복사하세요.\n")

    code = input("3) 복사한 code 값을 붙여넣으세요: ").strip()

    form = {
        "grant_type":    "authorization_code",
        "client_id":      rest_api_key,
        "redirect_uri":   REDIRECT_URI,
        "code":           code,
    }
    if client_secret:
        form["client_secret"] = client_secret

    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(TOKEN_URL, data=data)
    with urllib.request.urlopen(req, timeout=15) as res:
        token = json.loads(res.read())

    if "refresh_token" not in token:
        print("토큰 발급 실패:", token)
        return

    print("\n발급 완료. 아래 값을 GitHub Secrets 에 등록합니다 (gh cli 사용)...")
    import subprocess
    subprocess.run(["gh", "secret", "set", "KAKAO_REST_API_KEY", "--body", rest_api_key], check=True)
    subprocess.run(["gh", "secret", "set", "KAKAO_REFRESH_TOKEN", "--body", token["refresh_token"]], check=True)
    if client_secret:
        subprocess.run(["gh", "secret", "set", "KAKAO_CLIENT_SECRET", "--body", client_secret], check=True)
    print("KAKAO_REST_API_KEY, KAKAO_REFRESH_TOKEN, KAKAO_CLIENT_SECRET 시크릿 등록 완료.")
    print("남은 작업: GH_PAT 시크릿 등록 (README/설계서 참고)")


if __name__ == "__main__":
    main()
