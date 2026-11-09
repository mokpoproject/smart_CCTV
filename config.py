"""프로젝트 설정 모음

핀 번호, 저장 경로, 판별 기준 같은 값을 한곳에서 관리합니다.
텔레그램 토큰처럼 비밀 값은 코드에 쓰지 않고 .env 파일에서 읽어 옵니다.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_env(path=BASE_DIR / ".env"):
    """.env 파일의 KEY=VALUE 줄을 환경변수로 읽어 온다 (추가 패키지 불필요)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()

# ── 실행 모드 ─────────────────────────────────────────────
# MOCK=1 이면 PIR 센서·LED·부저를 가짜 핀으로 흉내 내고,
# 키보드 Enter로 '움직임 감지'를 발생시킵니다. (하드웨어 없이 테스트용)
MOCK = os.getenv("MOCK", "0") == "1"

# ── 1단계: GPIO 핀 번호 (BCM 번호) ───────────────────────
PIR_PIN = 17      # PIR OUT  → 11번 핀
LED_PIN = 27      # LED (+)  → 13번 핀 (220Ω 저항 거쳐서)
BUZZER_PIN = 22   # 부저 (+) → 15번 핀
USE_ALARM = True  # LED·부저 경고를 쓸지 여부

# ── 2단계: 카메라 / AI 판별 ──────────────────────────────
# "auto" : picamera2 → USB 웹캠 → 테스트 이미지 순서로 자동 선택
# "picamera" / "usb" / "file" 로 고정할 수도 있음
CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "auto")
USB_CAMERA_INDEX = 0
FRAME_SIZE = (1280, 720)
TEST_IMAGE_DIR = BASE_DIR / "test_images"   # file 모드에서 쓸 사진 폴더

DETECT_WIDTH = 640         # 판별 전에 이 너비로 줄여서 속도 확보
PERSON_MIN_SCORE = 0.5     # HOG 점수가 이 값 이상이면 사람으로 인정

# ── 3단계: 텔레그램 ──────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
# 토큰이 없으면 실제 전송 대신 화면에 [DRY-RUN]으로만 출력

# ── 4단계: 로그 저장 ─────────────────────────────────────
CAPTURE_DIR = BASE_DIR / "captures"     # 촬영 사진 저장 폴더
DB_PATH = BASE_DIR / "events.db"        # 이벤트 기록 (SQLite)

# ── 동작 옵션 ────────────────────────────────────────────
COOLDOWN_SEC = 10   # 한 번 처리한 뒤 이 시간 동안은 다시 감지해도 무시 (알림 폭탄 방지)
ALARM_SEC = 2       # 사람 판별 시 LED·부저를 켜 둘 시간
