"""1단계: GPIO 감지 신호 수신 (+ LED·부저 경고)

라즈베리파이 5는 RPi.GPIO가 동작하지 않으므로 gpiozero(lgpio)를 사용합니다.
MOCK 모드에서는 가짜 핀을 쓰고, Enter 키로 움직임을 흉내 냅니다.
"""
import threading
import time

from gpiozero import Device, MotionSensor, LED, Buzzer

import config


class Hardware:
    def __init__(self):
        if config.MOCK:
            from gpiozero.pins.mock import MockFactory
            Device.pin_factory = MockFactory()

        self.pir = MotionSensor(config.PIR_PIN)
        self.led = LED(config.LED_PIN) if config.USE_ALARM else None
        self.buzzer = Buzzer(config.BUZZER_PIN) if config.USE_ALARM else None

        if config.MOCK:
            self._start_keyboard_trigger()

    # ── PIR ──────────────────────────────────────────────
    def wait_for_motion(self):
        """움직임이 감지될 때까지 기다린다 (블로킹)."""
        self.pir.wait_for_motion()

    def wait_for_no_motion(self, timeout=None):
        self.pir.wait_for_no_motion(timeout=timeout)

    # ── 경고 ─────────────────────────────────────────────
    def alarm(self, seconds=config.ALARM_SEC):
        """LED와 부저를 seconds초 동안 켠다."""
        if not config.USE_ALARM:
            return
        self.led.on()
        self.buzzer.on()
        time.sleep(seconds)
        self.led.off()
        self.buzzer.off()

    def close(self):
        for dev in (self.pir, self.led, self.buzzer):
            if dev is not None:
                dev.close()

    # ── MOCK 전용: Enter 키 = 움직임 발생 ─────────────────
    def _start_keyboard_trigger(self):
        pin = Device.pin_factory.pin(config.PIR_PIN)

        def loop():
            while True:
                try:
                    input()
                except EOFError:
                    return
                print("[MOCK] PIR 신호 HIGH (움직임 발생)")
                pin.drive_high()
                time.sleep(0.5)
                pin.drive_low()

        threading.Thread(target=loop, daemon=True).start()
        print("[MOCK] 하드웨어 없이 실행 중 — Enter 키를 누르면 움직임이 감지된 것으로 처리합니다.")
