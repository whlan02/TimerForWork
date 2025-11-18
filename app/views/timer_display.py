from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLCDNumber, QSizePolicy
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


class TimerDisplay(QWidget):
    """
    Large digital timer display using QLCDNumber.
    Shows HH:MM:SS.t (tenths). Purely presentational; bind update_time() to TimerService.tick.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._lcd = QLCDNumber(self)
        # "02:13:36.5" -> 10 characters
        self._lcd.setDigitCount(10)
        self._lcd.setSegmentStyle(QLCDNumber.Filled)
        self._lcd.setSmallDecimalPoint(True)
        self._lcd.setFrameShape(QLCDNumber.NoFrame)
        self._lcd.display("00:00:00.0")

        # Make it large and responsive
        self._lcd.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._lcd.setMinimumWidth(640)
        self._lcd.setMinimumHeight(180)

        # Style: transparent background, orange segments
        self._lcd.setStyleSheet("QLCDNumber { color: #ff8c00; background-color: transparent; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addStretch(1)
        layout.addWidget(self._lcd, 0, Qt.AlignCenter)
        layout.addStretch(1)
        self.setLayout(layout)

    def update_time(self, formatted: str) -> None:
        # Accept "HH:MM:SS" or "HH:MM:SS.t"
        if len(formatted) == 8:
            formatted = formatted + ".0"
        self._lcd.display(formatted)


