"""PIR 센서 단독 테스트

배선 확인용입니다. 센서 앞에서 손을 흔들면 '감지', 가만히 있으면 '없음'이 출력됩니다.
  python3 pir_test.py
전원을 켠 직후 약 1분은 센서가 안정화되는 시간이라 신호가 불규칙할 수 있습니다.
종료: Ctrl+C
"""
import time
from datetime import datetime
from signal import pause

from gpiozero import MotionSensor

import config

pir = MotionSensor(config.PIR_PIN)
count = 0
start = None


def on_motion():
    global count, start
    count += 1
    start = time.time()
    print(f"[{datetime.now():%H:%M:%S}] 🔴 감지 ({count}회)")


def on_no_motion():
    held = f" — 신호 유지 {time.time() - start:.1f}초" if start else ""
    print(f"[{datetime.now():%H:%M:%S}] ⚪ 없음{held}")


pir.when_motion = on_motion
pir.when_no_motion = on_no_motion

print(f"PIR 센서 테스트 (GPIO{config.PIR_PIN}, 11번 핀) — 현재 상태: {'감지' if pir.motion_detected else '없음'}")
print("센서 앞에서 손을 흔들어 보세요. 종료: Ctrl+C\n")
try:
    pause()
except KeyboardInterrupt:
    print(f"\n종료 — 총 {count}회 감지")
