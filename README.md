# PIR 연동 AIoT 스마트 CCTV

라즈베리파이 5 + 카메라 + PIR 센서로 만든 AIoT 스마트 CCTV입니다.
PIR 센서가 움직임을 감지하면 카메라로 촬영하고, 사람인지 판별한 뒤
LED·부저로 경고하고 텔레그램으로 사진을 전송합니다.

## 빠른 시작 (하드웨어 없이 테스트)
```bash
git clone https://github.com/mokpoproject/smart_CCTV.git
cd smart_CCTV
source ~/cctv-env/bin/activate
MOCK=1 CAMERA_SOURCE=file python3 main.py
```
Enter 키를 누를 때마다 움직임이 감지된 것으로 처리됩니다. 종료는 Ctrl+C입니다.
`cctv-env` 가상환경이 없다면 아래 [설치](#설치)를 먼저 진행하세요.

## 동작 흐름
PIR 감지 → 카메라 촬영 → 사람 판별(OpenCV HOG) → LED·부저 경고 + 텔레그램 전송 → 기록 저장

## 파일 구조
| 파일 | 단계 | 역할 |
|---|---|---|
| `main.py` | 전체 | 1~4단계를 순서대로 연결하는 메인 루프 |
| `config.py` | - | 핀 번호, 경로, 판별 기준 등 설정 |
| `hardware.py` | 1단계 | PIR 센서 감지, LED·부저 경고 (gpiozero) |
| `camera.py` | 2단계 | 카메라 촬영 (picamera2 / USB 웹캠 / 테스트 이미지) |
| `detector.py` | 2단계 | AI 사람 판별 (OpenCV HOG) |
| `notifier.py` | 3단계 | 텔레그램 사진 전송 (백그라운드) |
| `event_log.py` | 4단계 | 사진 저장 + SQLite 이벤트 기록 |
| `telegram_test.py` | 3단계 | 텔레그램 채팅 ID 찾기, 전송 테스트 |
| `pir_test.py` | 1단계 | PIR 센서 단독 테스트 (배선 확인용) |

## 하드웨어
| 부품 | 용도 |
|---|---|
| Raspberry Pi 5 | 메인 보드 |
| USB 웹캠 (또는 카메라 모듈 + Pi 5 전용 케이블) | 촬영 |
| PIR 센서 (HC-SR501) | 움직임 감지 |
| LED + 220Ω 저항 | 경고 표시 |
| 능동 부저 | 경고음 |
| 점퍼선, 브레드보드 | 배선 |

## 배선
| 부품 | 핀 |
|---|---|
| PIR VCC | 5V (2번) |
| PIR GND | GND (6번) |
| PIR OUT | GPIO17 (11번) |
| LED (+) → 220Ω | GPIO27 (13번) |
| 부저 (+) | GPIO22 (15번) |
| LED·부저 (−) | GND (14번) |

- 핀 번호는 **SD카드 슬롯 쪽 끝이 1번**이고, 보드 바깥쪽 줄이 짝수(2, 4, 6…), 안쪽 줄이 홀수(1, 3, 5…)입니다.
- PIR 센서의 핀 순서(VCC·OUT·GND)는 제품마다 다를 수 있으니, 흰 렌즈 돔을 빼서 핀 옆 글씨를 확인하세요.
- **배선은 반드시 라즈베리파이 전원을 끈 상태에서** 합니다. VCC와 GND를 바꿔 꽂으면 센서가 망가질 수 있습니다.
- LED와 부저는 선택 부품입니다. 연결하지 않아도 프로그램은 정상 동작합니다.

## 설치

### 1. 시스템 패키지
picamera2, gpiozero 등은 pip가 아니라 apt로 설치해야 합니다. (`requirements.txt` 대신 아래 명령 사용)
```bash
sudo apt update
sudo apt install -y git python3-picamera2 python3-opencv python3-numpy python3-gpiozero python3-lgpio python3-requests python3-flask
```

### 2. 가상환경
apt로 설치한 picamera2를 쓰려면 `--system-site-packages` 옵션이 필요합니다.
기존에 이 옵션 없이 만든 가상환경에서는 picamera2를 불러올 수 없습니다.
```bash
python3 -m venv --system-site-packages ~/cctv-env
source ~/cctv-env/bin/activate
```

### 3. 설치 확인
```bash
python3 -c "import cv2, numpy, picamera2, gpiozero, requests; print('OK')"
```
`OK`가 출력되면 설치 완료입니다.

카메라를 연결한 뒤에는 사진이 찍히는지 확인합니다. (SSH에서도 동작)
```bash
rpicam-still -o test.jpg
```
## 하드웨어 테스트

### USB 웹캠
```bash
lsusb                      # 목록에 웹캠 이름이 보이면 인식 성공
sudo apt install -y v4l-utils
v4l2-ctl --list-devices    # 웹캠 이름 아래 첫 번째 /dev/videoN 이 웹캠
```
`pispbe`, `rpi-hevc-dec`, `rp1-cfe` 아래 장치는 라즈베리파이 내부 장치이므로 무시합니다.
웹캠이 `/dev/video0`이 아니면 `config.py`의 `USB_CAMERA_INDEX`를 그 번호로 바꿉니다.

사진 한 장 찍어 보기:
```bash
python3 -c "import cv2; c=cv2.VideoCapture(0); [c.read() for _ in range(10)]; ok,f=c.read(); print('촬영 성공' if ok else '실패'); ok and cv2.imwrite('usbtest.jpg', f)"
```
노트북으로 가져와 확인하기 (노트북 cmd에서, IP는 라즈베리파이에서 `hostname -I`로 확인):
```bash
scp h223603@라즈베리파이IP:~/usbtest.jpg .
```

### PIR 센서
1. 센서 뒷면 나사 조절: **지속 시간(Tx)은 반시계 끝까지(가장 짧게)**, **감도(Sx)는 가운데**
2. 전원을 켜고 **약 1분 기다린 뒤**(센서 안정화) 테스트합니다.
```bash
python3 pir_test.py
```
손을 흔들면 `감지`, 가만히 있으면 `없음`이 출력되면 정상입니다.

### 전체 실행 (PIR + USB 웹캠)
```bash
CAMERA_SOURCE=usb python3 main.py
```
CSI 카메라 모듈을 쓰는 경우는 `rpicam-still -o test.jpg`로 먼저 촬영을 확인합니다.

## 텔레그램 설정

### 1. 봇 만들기 (폰 텔레그램 앱)
1. 검색창에서 **@BotFather**를 찾아 대화를 시작합니다.
2. `/newbot`을 보내고, 봇 이름과 아이디(끝이 `bot`으로 끝나야 함, 예: `mokpo_cctv_bot`)를 정합니다.
3. BotFather가 알려 주는 **토큰**(`123456789:ABC...` 형태)을 복사해 둡니다.
4. 방금 만든 내 봇을 검색해서 **`/start`를 한 번 보냅니다.** (보내야 채팅 ID를 찾을 수 있음)

### 2. 토큰 입력
```bash
cp .env.example .env
nano .env   # TELEGRAM_TOKEN= 뒤에 토큰 붙여 넣기
```

### 3. 채팅 ID 찾기
```bash
python3 telegram_test.py chatid
```
출력된 숫자를 `.env`의 `TELEGRAM_CHAT_ID=` 뒤에 넣습니다.

### 4. 전송 테스트
```bash
python3 telegram_test.py
```
폰으로 테스트 메시지와 사진이 오면 연결 완료입니다.

토큰이 비어 있으면 `main.py`는 실제로 보내지 않고 화면에 `[DRY-RUN]`으로만 표시합니다.
`.env`는 `.gitignore`에 들어 있어 GitHub에 올라가지 않습니다. **토큰을 코드나 README에 직접 쓰지 마세요.**

## 실행
```bash
python3 main.py                            # 실제 하드웨어
MOCK=1 CAMERA_SOURCE=file python3 main.py  # 하드웨어 없이 테스트 (Enter = 움직임 감지)
python3 main.py --log                      # 최근 감지 기록 보기
```
하드웨어 없이 테스트할 때는 `test_images/` 폴더에 사람 사진(전신)을 넣어 두면
촬영한 것처럼 차례로 사용합니다.

## 사용 모듈
| 모듈 | 용도 |
|---|---|
| picamera2 | 카메라 촬영 |
| opencv | 영상 처리, 사람 판별 |
| numpy | 이미지 배열 처리 |
| gpiozero, lgpio | GPIO 제어 (Pi 5는 RPi.GPIO 미지원) |
| requests | 텔레그램 Bot API 전송 |
| sqlite3 | 이벤트 기록 (파이썬 기본 모듈) |
| flask | 웹 스트리밍 (선택, 추후) |
