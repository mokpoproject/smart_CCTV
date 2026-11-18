"""2단계 (후반): AI 사람 판별

두 가지 판별기를 지원하며 config.DETECTOR 로 고릅니다.

  mobilenet (기본) : MobileNet-SSD 딥러닝 모델 (OpenCV DNN)
                     - 사람의 생김새를 학습한 모델이라 기둥·봉 같은 세로선 오탐이 적음
                     - 상반신만 보이거나 앉아 있어도 검출
                     - 모델 파일(약 23MB)은 처음 실행할 때 models/ 폴더로 자동 다운로드
  hog              : OpenCV 내장 HOG + SVM
                     - 추가 파일 불필요, 하지만 서 있는 전신만 검출하고 오탐이 많음

모델을 미리 받아 두거나 사진 한 장으로 테스트하려면:
  python3 detector.py              # 모델 다운로드 + 확인
  python3 detector.py 사진.jpg     # 그 사진에서 사람 판별
"""
import hashlib
import sys

import cv2
import numpy as np

import config

# ── MobileNet-SSD (Caffe, PASCAL VOC 20클래스) ──────────────────────────
# 출처: https://github.com/chuanqi305/MobileNet-SSD (MIT License)
MODEL_FILES = {
    "deploy.prototxt": (
        "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/deploy.prototxt",
        "2d180f723b3109e21f8287f6b3c691390d07b60eed998327cd3259ffa0e50608",
    ),
    "mobilenet_iter_73000.caffemodel": (
        "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/mobilenet_iter_73000.caffemodel",
        "52eed8be80522c152a17fb56740de705b79881bde1a167e0e747310523685fc7",
    ),
}
VOC_CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car",
               "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person",
               "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
PERSON_CLASS_ID = VOC_CLASSES.index("person")   # 15


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_model():
    """모델 파일이 없거나 손상됐으면 내려받는다. 파일 경로 2개를 돌려준다."""
    import requests

    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, (url, sha) in MODEL_FILES.items():
        path = config.MODEL_DIR / name
        if not (path.exists() and _sha256(path) == sha):
            print(f"[판별기] 모델 다운로드 중: {name} ...")
            tmp = path.with_suffix(path.suffix + ".part")
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if _sha256(tmp) != sha:
                tmp.unlink()
                raise RuntimeError(f"{name} 파일이 손상됐습니다 (해시 불일치). 다시 실행해 보세요.")
            tmp.replace(path)
            print(f"[판별기] 다운로드 완료: {name}")
        paths[name] = path
    return paths["deploy.prototxt"], paths["mobilenet_iter_73000.caffemodel"]


def _draw(frame, boxes):
    """boxes: [(x1, y1, x2, y2, 라벨), ...] 를 빨간 박스로 그린 이미지를 돌려준다."""
    out = frame.copy()
    for x1, y1, x2, y2, label in boxes:
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(out, label, (x1, max(y1 - 8, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return out


class MobileNetDetector:
    name = "MobileNet-SSD"

    def __init__(self):
        prototxt, weights = ensure_model()
        self.net = cv2.dnn.readNetFromCaffe(str(prototxt), str(weights))

    def detect(self, frame):
        """반환값: (사람 여부, 사람 수, 박스를 그린 이미지)"""
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                                     0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        det = self.net.forward()   # shape: (1, 1, N, 7) → [_, 클래스, 확신도, x1, y1, x2, y2]

        boxes = []
        for i in range(det.shape[2]):
            cls, conf = int(det[0, 0, i, 1]), float(det[0, 0, i, 2])
            if cls != PERSON_CLASS_ID or conf < config.PERSON_CONFIDENCE:
                continue
            x1, y1, x2, y2 = (det[0, 0, i, 3:7] * np.array([w, h, w, h])).astype(int)
            x1, y1 = max(x1, 0), max(y1, 0)
            x2, y2 = min(x2, w - 1), min(y2, h - 1)
            boxes.append((x1, y1, x2, y2, f"PERSON {conf * 100:.0f}%"))

        return len(boxes) > 0, len(boxes), _draw(frame, boxes)


class HogDetector:
    name = "HOG"

    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect(self, frame):
        """반환값: (사람 여부, 사람 수, 박스를 그린 이미지)"""
        h, w = frame.shape[:2]
        scale = config.DETECT_WIDTH / w if w > config.DETECT_WIDTH else 1.0
        small = cv2.resize(frame, None, fx=scale, fy=scale) if scale != 1.0 else frame

        rects, weights = self.hog.detectMultiScale(
            small, winStride=(8, 8), padding=(8, 8), scale=1.05)

        boxes = []
        for (x, y, bw, bh), s in zip(rects, np.ravel(weights)):
            if s < config.PERSON_MIN_SCORE:
                continue
            x, y, bw, bh = (int(v / scale) for v in (x, y, bw, bh))
            boxes.append((x, y, x + bw, y + bh, "PERSON"))

        return len(boxes) > 0, len(boxes), _draw(frame, boxes)


def create_detector():
    """config.DETECTOR 에 맞는 판별기를 만든다. MobileNet을 못 쓰면 HOG로 대신한다."""
    if config.DETECTOR == "mobilenet":
        try:
            d = MobileNetDetector()
            print(f"[판별기] {d.name} 사용")
            return d
        except Exception as e:
            print(f"[판별기] MobileNet-SSD 사용 불가 ({e}) → HOG로 대신합니다.")
    d = HogDetector()
    print(f"[판별기] {d.name} 사용")
    return d


# 예전 코드 호환용 이름
PersonDetector = create_detector


if __name__ == "__main__":
    detector = create_detector()
    if len(sys.argv) > 1:
        img = cv2.imread(sys.argv[1])
        if img is None:
            sys.exit(f"사진을 열 수 없습니다: {sys.argv[1]}")
        is_person, count, out = detector.detect(img)
        out_path = "detect_result.jpg"
        cv2.imwrite(out_path, out)
        print(f"결과: {'사람 ' + str(count) + '명' if is_person else '사람 없음'} → {out_path}")
    else:
        print("모델 준비 완료")
