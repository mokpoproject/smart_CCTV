"""3단계: 텔레그램 봇 사진 실시간 전송

Telegram Bot API의 sendPhoto를 requests로 직접 호출합니다.
전송은 별도 스레드에서 처리해서(비동기) 센서 감시가 멈추지 않게 합니다.
토큰이 설정되지 않았으면 실제로 보내지 않고 [DRY-RUN]으로만 출력합니다.
"""
import threading

import requests

import config


class TelegramNotifier:
    def __init__(self):
        self.enabled = bool(config.TELEGRAM_TOKEN and config.TELEGRAM_CHAT_ID)
        if not self.enabled:
            print("[텔레그램] 토큰/채팅ID가 없어 DRY-RUN 모드로 동작합니다 (.env 확인)")

    def send_photo(self, image_path, caption, on_done=None):
        """사진 전송을 백그라운드로 시작한다. 끝나면 on_done(성공여부)를 호출."""
        def job():
            ok = self._send(image_path, caption)
            if on_done:
                on_done(ok)
        threading.Thread(target=job, daemon=True).start()

    def _send(self, image_path, caption):
        if not self.enabled:
            print(f"[DRY-RUN] 텔레그램 전송 생략: {image_path} / {caption}")
            return False

        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendPhoto"
        try:
            with open(image_path, "rb") as f:
                r = requests.post(url, data={"chat_id": config.TELEGRAM_CHAT_ID, "caption": caption},
                                  files={"photo": f}, timeout=15)
            ok = r.ok and r.json().get("ok", False)
            print(f"[텔레그램] 전송 {'성공' if ok else '실패: ' + r.text[:200]}")
            return ok
        except requests.RequestException as e:
            print(f"[텔레그램] 네트워크 오류: {e}")
            return False
