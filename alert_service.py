# -*- coding: utf-8 -*-
"""告警管理与推送模块"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional

import config


@dataclass
class AlertRecord:
    """结构化的告警记录，便于数据库与推送公用"""

    person_id: str
    person_label: str
    alert_type: str
    message: str
    duration_seconds: float
    triggered_at: float
    channels: List[str]
    status: str = "new"
    id: Optional[int] = None

    def to_payload(self) -> Dict[str, object]:
        """转换为可供前端/Socket消费的字典"""
        payload = asdict(self)
        payload["duration_seconds"] = round(self.duration_seconds, 1)
        return payload


class AlertDatabase:
    """使用SQLite记录告警日志，支持基本CRUD"""

    def __init__(self, db_path: str) -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    person_label TEXT,
                    alert_type TEXT NOT NULL,
                    message TEXT,
                    duration_seconds REAL,
                    triggered_at REAL,
                    channels TEXT,
                    status TEXT DEFAULT 'new'
                )
                """
            )

    def insert(self, record: AlertRecord) -> AlertRecord:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO alert_logs (
                    person_id, person_label, alert_type, message,
                    duration_seconds, triggered_at, channels, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.person_id,
                    record.person_label,
                    record.alert_type,
                    record.message,
                    record.duration_seconds,
                    record.triggered_at,
                    ",".join(record.channels),
                    record.status,
                ),
            )
            record.id = cursor.lastrowid
        return record

    def list_alerts(self, limit: int = 50) -> List[Dict[str, object]]:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "SELECT * FROM alert_logs ORDER BY triggered_at DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
        results: List[Dict[str, object]] = []
        for row in rows:
            data = dict(row)
            channels = data.get("channels") or ""
            data["channels"] = [ch for ch in channels.split(",") if ch]
            results.append(data)
        return results

    def update_status(self, alert_id: int, status: str) -> bool:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "UPDATE alert_logs SET status = ? WHERE id = ?",
                (status, alert_id),
            )
            return cursor.rowcount > 0

    def count_alerts_since(self, since_timestamp: float) -> int:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "SELECT COUNT(*) AS cnt FROM alert_logs WHERE triggered_at >= ?",
                (since_timestamp,),
            )
            row = cursor.fetchone()
            return int(row["cnt"]) if row else 0

    def reset_all(self) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM alert_logs")


class AlertChannelDispatcher:
    """调度多种告警渠道，便于未来扩展"""

    def __init__(self, socketio=None) -> None:
        self.socketio = socketio

    def dispatch(self, record: AlertRecord) -> None:
        for channel in config.ALERT_CHANNELS:
            handler = getattr(self, f"_send_{channel}", None)
            if handler:
                handler(record)
            else:
                self._send_log(record, prefix=f"[未实现渠道 {channel}]")

    def _send_log(self, record: AlertRecord, prefix: str = "[告警]") -> None:
        timestamp = time.strftime("%H:%M:%S", time.localtime(record.triggered_at))
        print(f"{prefix} {timestamp} - {record.message}")

    def _send_socket(self, record: AlertRecord) -> None:
        if not self.socketio:
            return
        try:
            payload = record.to_payload()
            print(f"Socket 推送: event={config.ALERT_SOCKET_EVENT} payload={payload}")
            # 直接调用 emit，由 Flask-SocketIO 负责转发到已连接客户端
            self.socketio.emit(config.ALERT_SOCKET_EVENT, payload)
            print("Socket 推送完成")
        except Exception as exc:
            self._send_log(record, prefix=f"[Socket失败:{exc}]")

    # 预留接口
    def _send_email(self, record: AlertRecord) -> None:  # pragma: no cover
        self._send_log(record, prefix="[邮件待实现]")

    def _send_sms(self, record: AlertRecord) -> None:  # pragma: no cover
        self._send_log(record, prefix="[短信待实现]")

    def _send_webhook(self, record: AlertRecord) -> None:  # pragma: no cover
        self._send_log(record, prefix="[Webhook待实现]")


class AlertEngine:
    """负责根据检测结果触发离岗告警"""

    def __init__(
        self, database: AlertDatabase, dispatcher: AlertChannelDispatcher
    ) -> None:
        self.db = database
        self.dispatcher = dispatcher
        self.threshold = config.OFF_DUTY_ALERT_THRESHOLD
        self.cooldown = config.ALERT_COOLDOWN
        self.person_states: Dict[str, Dict[str, float]] = {}
        self.grace_period = config.ALERT_PERSON_GRACE

    def process_detection(self, status_detail: Dict[str, object]) -> List[AlertRecord]:
        """根据单帧检测结果更新状态并触发告警"""
        persons: List[Dict[str, object]] = status_detail.get("details", [])  # type: ignore[arg-type]
        now = time.time()
        seen_ids = set()
        triggered: List[AlertRecord] = []

        for idx, person in enumerate(persons):
            person_id = self._build_person_id(person, idx)
            seen_ids.add(person_id)
            state = self.person_states.setdefault(
                person_id,
                {
                    "last_seen": now,
                    "last_on_duty": now,
                    "last_alert": 0.0,
                },
            )
            state["last_seen"] = now
            if person.get("on_duty"):
                state["last_on_duty"] = now
                continue

            elapsed = now - state["last_on_duty"]
            if elapsed < self.threshold:
                continue
            if now - state["last_alert"] < self.cooldown:
                continue

            record = AlertRecord(
                person_id=person_id,
                person_label=f"人员{idx + 1}",
                alert_type="off_duty",
                message=f"检测离岗 {int(elapsed)} 秒，超出阈值",
                duration_seconds=elapsed,
                triggered_at=now,
                channels=config.ALERT_CHANNELS,
            )
            saved = self.db.insert(record)
            self.dispatcher.dispatch(saved)
            triggered.append(saved)
            state["last_alert"] = now

        self._cleanup_stale_entries(now, seen_ids)
        return triggered

    def _cleanup_stale_entries(self, now: float, seen_ids: Iterable[str]) -> None:
        to_remove = []
        for person_id, state in self.person_states.items():
            if person_id in seen_ids:
                continue
            if now - state.get("last_seen", 0) > self.grace_period:
                to_remove.append(person_id)
        for person_id in to_remove:
            self.person_states.pop(person_id, None)

    def _build_person_id(self, person: Dict[str, object], index: int) -> str:
        bbox = person.get("bbox")
        if bbox is None:
            bbox = [0.0, 0.0, 0.0, 0.0]
        else:
            try:
                bbox = [float(v) for v in bbox]
            except TypeError:
                bbox = [0.0, 0.0, 0.0, 0.0]
        try:
            x1, y1, x2, y2 = map(float, bbox)
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
        except Exception:
            cx = index * 50.0
            cy = 0.0
        return f"p{index}_{int(cx)}_{int(cy)}"


def create_alert_engine(socketio=None) -> AlertEngine:
    database = AlertDatabase(config.ALERT_DB_PATH)
    dispatcher = AlertChannelDispatcher(socketio=socketio)
    return AlertEngine(database, dispatcher)
