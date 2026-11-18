"""지금 사진 한 장 찍어서 텔레그램으로 보내기

  python3 snap.py            # 사람 판별 결과(박스)까지 그려서 전송
  python3 snap.py --raw      # 판별 없이 찍은 그대로 전송

카메라 각도 확인, 텔레그램 연결 확인, 시연용으로 쓸 수 있습니다.
사진은 captures 폴더에도 저장됩니다. (감지 기록 DB에는 남기지 않음)
"""
import sys
from datetime import datetime

import config
from camera import Camera
from event_log import EventLog
from notifier import TelegramNotifier


def main():
    raw = "--raw" in sys.argv
    notifier = TelegramNotifier()
    camera = Camera()
    try:
        frame = camera.capture()
    finally:
        camera.close()

    now = datetime.now()
    caption = f"📷 수동 촬영\n시각: {now:%Y-%m-%d %H:%M:%S}"

    if not raw:
        from detector import create_detector
        is_person, count, frame = create_detector().detect(frame)
        caption += f"\n사람 판별: {f'{count}명' if is_person else '없음'}"

    path = EventLog.save_image(frame, now)   # 사진만 저장
    print(f"[저장] {path.relative_to(config.BASE_DIR)}")

    if not notifier.enabled:
        print("텔레그램이 설정되지 않아 저장만 했습니다. (.env의 TELEGRAM_TOKEN, TELEGRAM_CHAT_ID 확인)")
        return

    if notifier.send_photo_now(path, caption):
        print("✅ 텔레그램 전송 완료 — 폰에서 확인하세요!")
    else:
        print("❌ 전송 실패 — 위 오류 메시지를 확인하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
