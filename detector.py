"""2단계 (후반): AI 사람 판별

OpenCV에 내장된 HOG + SVM 사람 검출기를 사용합니다.
추가 모델 파일을 받을 필요가 없고 라즈베리파이에서도 가볍게 돌아갑니다.
나중에 정확도를 높이고 싶으면 이 파일만 MobileNet-SSD / YOLO 등으로 바꾸면 됩니다.
"""
import cv2
import numpy as np

import config


class PersonDetector:
    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect(self, frame):
        """
        frame 안에 사람이 있는지 판별한다.

        반환값: (사람 여부, 사람 수, 박스를 그린 이미지)
        """
        # 1) 속도를 위해 크기 줄이기
        h, w = frame.shape[:2]
        scale = config.DETECT_WIDTH / w if w > config.DETECT_WIDTH else 1.0
        small = cv2.resize(frame, None, fx=scale, fy=scale) if scale != 1.0 else frame

        # 2) HOG 사람 검출
        boxes, weights = self.hog.detectMultiScale(
            small, winStride=(8, 8), padding=(8, 8), scale=1.05)

        # 3) 점수가 낮은 결과 버리기
        people = [b for b, s in zip(boxes, np.ravel(weights)) if s >= config.PERSON_MIN_SCORE]

        # 4) 원래 크기 이미지에 박스 그리기
        annotated = frame.copy()
        for (x, y, bw, bh) in people:
            x, y, bw, bh = (int(v / scale) for v in (x, y, bw, bh))
            cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
            cv2.putText(annotated, "PERSON", (x, max(y - 8, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return len(people) > 0, len(people), annotated
