"""PIR 연동 AIoT 스마트 CCTV — 메인 프로그램

동작 흐름 (보고서 4단계)
  1단계  PIR 센서 감지 신호 수신        → hardware.py
  2단계  카메라 촬영 + AI 사람 판별      → camera.py, detector.py
  3단계  텔레그램 사진 실시간 전송       → notifier.py
  4단계  타임스탬프·이미지 로그 저장     → event_log.py

실행
  python3 main.py          # 실제 하드웨어
  MOCK=1 python3 main.py   # 하드웨어 없이 테스트 (Enter = 움직임 감지)
  python3 main.py --log    # 최근 감지 기록 보기
"""
import sys
import time
from datetime import datetime

import config
from event_log import EventLog


def show_log():
    rows = EventLog().recent(20)
    if not rows:
        print("기록이 없습니다.")
        return
    print(f"{'ID':>3}  {'시각':19}  사람  수  전송  사진")
    for id_, ts, is_person, cnt, sent, path in rows:
        print(f"{id_:>3}  {ts}  {'O' if is_person else 'X':^4} {cnt:>2}  {'O' if sent else 'X':^4}  {path}")


def handle_event(camera, detector, notifier, log, hw):
    """움직임 1회에 대한 2~4단계 처리"""
    now = datetime.now()
    print(f"\n[{now:%H:%M:%S}] 1단계: 움직임 감지")

    # 2단계: 촬영 + 사람 판별
    frame = camera.capture()
    t0 = time.time()
    is_person, count, annotated = detector.detect(frame)
    print(f"[{now:%H:%M:%S}] 2단계: 판별 결과 = {'사람 ' + str(count) + '명' if is_person else '사람 아님'} "
          f"({time.time() - t0:.2f}초)")

    # 4단계(먼저): 사진·기록 저장 — 사람이 아니어도 기록은 남김
    image_path = log.save_image(annotated, now)
    event_id = log.add(now, is_person, count, image_path)
    print(f"[{now:%H:%M:%S}] 4단계: 기록 저장 #{event_id} → {image_path.relative_to(config.BASE_DIR)}")

    if not is_person:
        return

    # 3단계: 텔레그램 전송 (백그라운드) + 경고
    caption = f"🚨 침입 감지\n시각: {now:%Y-%m-%d %H:%M:%S}\n검출 인원: {count}명"
    notifier.send_photo(image_path, caption, on_done=lambda ok: log.mark_sent(event_id, ok))
    print(f"[{now:%H:%M:%S}] 3단계: 텔레그램 전송 요청")
    hw.alarm()


def main():
    if "--log" in sys.argv:
        show_log()
        return

    # 무거운 모듈은 필요할 때만 불러옴
    from camera import Camera
    from detector import PersonDetector
    from hardware import Hardware
    from notifier import TelegramNotifier

    hw = Hardware()
    camera = Camera()
    detector = PersonDetector()
    notifier = TelegramNotifier()
    log = EventLog()

    print("스마트 CCTV 감시 시작 (종료: Ctrl+C)")
    try:
        while True:
            hw.wait_for_motion()                 # 1단계: 감지될 때까지 대기
            handle_event(camera, detector, notifier, log, hw)
            time.sleep(config.COOLDOWN_SEC)      # 연속 알림 방지
            hw.wait_for_no_motion(timeout=30)    # 센서가 원래 상태로 돌아올 때까지
            print("다시 감시 중...")
    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        camera.close()
        hw.close()


if __name__ == "__main__":
    main()
