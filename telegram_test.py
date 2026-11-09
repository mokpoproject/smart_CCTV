"""텔레그램 봇 연결 도우미

1) 채팅 ID 찾기
     python3 telegram_test.py chatid
   → 봇에게 아무 메시지나 먼저 보낸 뒤 실행하면 내 채팅 ID를 알려 줍니다.

2) 전송 테스트
     python3 telegram_test.py
   → .env에 넣은 토큰과 채팅 ID로 테스트 메시지와 사진을 보냅니다.
"""
import sys
from datetime import datetime

import cv2
import numpy as np
import requests

import config

API = "https://api.telegram.org/bot{token}/{method}"


def call(method, **kwargs):
    url = API.format(token=config.TELEGRAM_TOKEN, method=method)
    try:
        r = requests.post(url, timeout=15, **kwargs)
    except requests.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        print("   → 라즈베리파이가 인터넷에 연결돼 있는지 확인하세요 (ping -c 3 google.com)")
        sys.exit(1)

    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code == 401:
        print("❌ 토큰이 잘못됐습니다. .env의 TELEGRAM_TOKEN을 BotFather가 준 값 그대로 넣었는지 확인하세요.")
        sys.exit(1)
    if not data.get("ok"):
        print(f"❌ 실패 ({r.status_code}): {data.get('description', r.text[:200])}")
        if "chat not found" in str(data.get("description", "")):
            print("   → 채팅 ID가 틀렸거나, 아직 봇에게 메시지를 보낸 적이 없습니다.")
        sys.exit(1)
    return data["result"]


def find_chat_id():
    updates = call("getUpdates")
    chats = {}
    for u in updates:
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat")
        if chat:
            name = chat.get("first_name") or chat.get("title") or ""
            chats[chat["id"]] = name

    if not chats:
        print("⚠️ 받은 메시지가 없습니다.")
        print("   → 텔레그램에서 내 봇을 찾아 '/start' 또는 아무 메시지나 보낸 뒤 다시 실행하세요.")
        return

    print("✅ 찾은 채팅 ID:")
    for cid, name in chats.items():
        print(f"   {cid}  ({name})")
    print("\n이 숫자를 .env의 TELEGRAM_CHAT_ID= 뒤에 넣으세요.")


def make_test_image():
    img = np.full((360, 640, 3), 40, np.uint8)
    cv2.putText(img, "SMART CCTV TEST", (90, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
    cv2.putText(img, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (150, 230),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)
    ok, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def send_test():
    if not config.TELEGRAM_CHAT_ID:
        print("❌ .env에 TELEGRAM_CHAT_ID가 없습니다. 먼저 'python3 telegram_test.py chatid'로 찾으세요.")
        sys.exit(1)

    me = call("getMe")
    print(f"✅ 봇 연결 확인: @{me['username']}")

    call("sendMessage", data={"chat_id": config.TELEGRAM_CHAT_ID,
                              "text": "📡 스마트 CCTV 연결 테스트 메시지입니다."})
    print("✅ 테스트 메시지 전송 완료")

    call("sendPhoto", data={"chat_id": config.TELEGRAM_CHAT_ID, "caption": "📷 테스트 사진"},
         files={"photo": ("test.jpg", make_test_image(), "image/jpeg")})
    print("✅ 테스트 사진 전송 완료 — 폰에서 확인해 보세요!")


def main():
    if not config.TELEGRAM_TOKEN:
        print("❌ .env에 TELEGRAM_TOKEN이 없습니다.")
        print("   → cp .env.example .env 후 BotFather에게 받은 토큰을 넣으세요.")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "chatid":
        find_chat_id()
    else:
        send_test()


if __name__ == "__main__":
    main()
