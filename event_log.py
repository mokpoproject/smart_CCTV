"""4단계: 타임스탬프 및 이미지 로그 저장

사진은 captures/날짜/시간.jpg 로 저장하고,
이벤트 정보는 SQLite 데이터베이스(events.db)에 기록합니다.
SQLite는 파이썬 기본 모듈이라 따로 설치할 필요가 없습니다.
"""
import sqlite3
from datetime import datetime

import cv2

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL,   -- 감지 시각 (YYYY-MM-DD HH:MM:SS)
    is_person   INTEGER NOT NULL,   -- 사람 판별 결과 (1/0)
    person_cnt  INTEGER NOT NULL,   -- 검출된 사람 수
    image_path  TEXT    NOT NULL,   -- 저장된 사진 경로
    sent        INTEGER DEFAULT 0   -- 텔레그램 전송 성공 여부 (1/0)
)
"""


class EventLog:
    def __init__(self, db_path=config.DB_PATH):
        self.db_path = str(db_path)
        with self._conn() as c:
            c.execute(SCHEMA)

    def _conn(self):
        # 전송 결과는 다른 스레드에서 기록하므로 호출마다 새 연결을 연다
        return sqlite3.connect(self.db_path)

    def save_image(self, image, now=None):
        now = now or datetime.now()
        folder = config.CAPTURE_DIR / now.strftime("%Y%m%d")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{now.strftime('%H%M%S')}.jpg"
        cv2.imwrite(str(path), image)
        return path

    def add(self, now, is_person, person_cnt, image_path):
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO events (ts, is_person, person_cnt, image_path) VALUES (?, ?, ?, ?)",
                (now.strftime("%Y-%m-%d %H:%M:%S"), int(is_person), person_cnt, str(image_path)))
            return cur.lastrowid

    def mark_sent(self, event_id, ok):
        with self._conn() as c:
            c.execute("UPDATE events SET sent = ? WHERE id = ?", (int(ok), event_id))

    def recent(self, n=10):
        with self._conn() as c:
            return c.execute(
                "SELECT id, ts, is_person, person_cnt, sent, image_path FROM events "
                "ORDER BY id DESC LIMIT ?", (n,)).fetchall()
