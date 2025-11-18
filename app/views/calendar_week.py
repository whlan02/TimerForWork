from __future__ import annotations

from datetime import date, timedelta
from typing import Callable, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QHBoxLayout,
)
from PySide6.QtCore import Qt

from app.models.record import TimeRecord


class WeekView(QWidget):
    """
    Modern week view:
    - Summary header with ISO week number and total (minutes + HH:MM:SS)
    - Scrollable list of "day cards" (Mon..Sun or Mon..Fri in workweek mode)
    - Each day card shows total and per-entry rows (time range, duration HH:MM:SS, note)
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._get_records_for_date: Callable[[date], List[TimeRecord]] = lambda d: []
        self._workweek_only: bool = False

        self._summary = QLabel(self)
        self._summary.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._container = QWidget(self._scroll)
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(8)
        self._scroll.setWidget(self._container)

        root = QVBoxLayout(self)
        root.addWidget(self._summary)
        root.addWidget(self._scroll)
        self.setLayout(root)

    def bind_data(self, get_records_for_date: Callable[[date], List[TimeRecord]]) -> None:
        self._get_records_for_date = get_records_for_date or (lambda d: [])

    def set_workweek_only(self, flag: bool) -> None:
        self._workweek_only = bool(flag)

    @staticmethod
    def _week_range(base: date) -> (date, date):
        monday = base - timedelta(days=base.weekday())
        sunday = monday + timedelta(days=6)
        return monday, sunday

    @staticmethod
    def _fmt_hms(seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _clear_container(self) -> None:
        layout = self._container_layout
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _make_day_card(self, d: date, records: List[TimeRecord]) -> QFrame:
        card = QFrame(self._container)
        card.setFrameShape(QFrame.StyledPanel)
        card.setFrameShadow(QFrame.Raised)
        v = QVBoxLayout(card)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(6)

        day_total_min = sum(r.duration_min for r in records)
        day_total_sec = sum(r.duration_sec for r in records)
        header = QHBoxLayout()
        # Fixed English weekday abbreviations to avoid system locale differences
        weekday_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d.weekday()]
        lbl_date = QLabel(f"{weekday_abbr}, {d.isoformat()}", card)
        lbl_total = QLabel(f"{day_total_min} min ({self._fmt_hms(day_total_sec)})", card)
        lbl_date.setStyleSheet("font-weight: 600;")
        lbl_total.setStyleSheet("color: #555;")
        header.addWidget(lbl_date)
        header.addStretch(1)
        header.addWidget(lbl_total)
        v.addLayout(header)

        if not records:
            v.addWidget(QLabel("No entries", card))
            return card

        for r in records:
            h = QHBoxLayout()
            period = f"{r.start_time.strftime('%H:%M:%S')} - {r.end_time.strftime('%H:%M:%S')}"
            dur = self._fmt_hms(r.duration_sec)
            lbl_left = QLabel(f"{period}", card)
            lbl_right = QLabel(f"{r.duration_min} min ({dur})", card)
            lbl_note = QLabel(r.note or "", card)
            lbl_left.setMinimumWidth(150)
            lbl_note.setWordWrap(True)
            h.addWidget(lbl_left)
            h.addStretch(1)
            h.addWidget(lbl_right)
            v.addLayout(h)
            if r.note:
                v.addWidget(lbl_note)
        return card

    def set_week(self, base_date: date) -> None:
        monday, sunday = self._week_range(base_date)
        iso_week = monday.isocalendar().week
        self._clear_container()

        weekly_total_min = 0
        weekly_total_sec = 0

        days = range(5) if self._workweek_only else range(7)
        for i in days:
            d = monday + timedelta(days=i)
            records = list(self._get_records_for_date(d))
            weekly_total_min += sum(r.duration_min for r in records)
            weekly_total_sec += sum(r.duration_sec for r in records)
            self._container_layout.addWidget(self._make_day_card(d, records))

        title = "Workweek" if self._workweek_only else "Week"
        tail = (
            f"{monday.isoformat()} ~ {sunday.isoformat()}"
            if not self._workweek_only
            else f"{monday.isoformat()} ~ {(monday + timedelta(days=4)).isoformat()}"
        )
        self._summary.setText(
            f"{title} W{iso_week}: {tail} | Total: {weekly_total_min} min ({self._fmt_hms(weekly_total_sec)})"
        )
