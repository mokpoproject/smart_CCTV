"""2단계 (전반): 카메라 촬영

picamera2(CSI 카메라) → USB 웹캠 → 테스트 이미지 순서로 쓸 수 있는 것을 고릅니다.
카메라가 아직 없을 때는 test_images 폴더의 사진을 차례로 '촬영'한 것처럼 돌려줍니다.
"""
import itertools

import cv2
import numpy as np

import config


class Camera:
    def __init__(self, source=config.CAMERA_SOURCE):
        self.backend = None
        self._cam = None

        order = ["picamera", "usb", "file"] if source == "auto" else [source]
        for name in order:
            try:
                getattr(self, f"_open_{name}")()
                self.backend = name
                break
            except Exception as e:
                print(f"[카메라] {name} 사용 불가: {e}")

        if self.backend is None:
            raise RuntimeError("사용할 수 있는 카메라가 없습니다.")
        print(f"[카메라] {self.backend} 모드로 시작")

    # ── 백엔드별 열기 ─────────────────────────────────────
    def _open_picamera(self):
        from picamera2 import Picamera2
        cam = Picamera2()
        cam.configure(cam.create_still_configuration(
            main={"size": config.FRAME_SIZE, "format": "RGB888"}))  # OpenCV와 같은 BGR 순서로 나옴
        cam.start()
        self._cam = cam

    def _open_usb(self):
        cap = cv2.VideoCapture(config.USB_CAMERA_INDEX)
        if not cap.isOpened():
            raise RuntimeError("USB 웹캠을 찾지 못함")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_SIZE[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_SIZE[1])
        self._cam = cap

    def _open_file(self):
        files = sorted(p for p in config.TEST_IMAGE_DIR.glob("*")
                       if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
        if not files:
            print(f"[카메라] {config.TEST_IMAGE_DIR} 에 사진이 없어 빈 화면을 사용합니다.")
        self._cam = itertools.cycle(files) if files else None

    # ── 촬영 ─────────────────────────────────────────────
    def capture(self):
        """사진 한 장을 찍어 OpenCV 이미지(BGR numpy 배열)로 돌려준다."""
        if self.backend == "picamera":
            return self._cam.capture_array()

        if self.backend == "usb":
            ok, frame = self._cam.read()
            if not ok:
                raise RuntimeError("웹캠 프레임 읽기 실패")
            return frame

        # file 모드
        if self._cam is None:
            w, h = config.FRAME_SIZE
            return np.zeros((h, w, 3), dtype=np.uint8)
        path = next(self._cam)
        print(f"[카메라] 테스트 이미지 사용: {path.name}")
        return cv2.imread(str(path))

    def close(self):
        if self.backend == "picamera":
            self._cam.stop()
            self._cam.close()
        elif self.backend == "usb":
            self._cam.release()
