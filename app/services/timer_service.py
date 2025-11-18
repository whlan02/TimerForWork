from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from PySide6.QtCore import QObject, QTimer, Signal


class TimerService(QObject):
    tick = Signal(int, str)  # seconds, formatted "HH:MM:SS"
    started = Signal()
    paused = Signal()
    resumed = Signal()
    stopped = Signal(int)  # total worked seconds

    def __init__(self) -> None:
        super().__init__()
        self._timer = QTimer(self)
        self._timer.setInterval(100)  # 100ms for tenths rendering
        self._timer.timeout.connect(self._on_tick)
        self._first_start_dt: Optional[datetime] = None
        self._current_start_dt: Optional[datetime] = None
        self._accumulated_sec: int = 0
        self._last_formatted: str = "00:00:00"

    @staticmethod
    def _fmt(seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def is_running(self) -> bool:
        return self._current_start_dt is not None

    def is_paused(self) -> bool:
        return (self._first_start_dt is not None) and (self._current_start_dt is None) and (self._accumulated_sec >= 0)

    def start(self) -> None:
        if self.is_running() or self.is_paused():
            return
        now = datetime.now()
        self._first_start_dt = now
        self._current_start_dt = now
        self._accumulated_sec = 0
        self._timer.start()
        self.started.emit()
        self.tick.emit(0, "00:00:00")

    def pause(self) -> None:
        if not self.is_running():
            return
        assert self._current_start_dt is not None
        now = datetime.now()
        self._accumulated_sec += int(round((now - self._current_start_dt).total_seconds()))
        self._current_start_dt = None
        self._timer.stop()
        self.paused.emit()
        # keep last tick visible

    def resume(self) -> None:
        if not self.is_paused():
            return
        self._current_start_dt = datetime.now()
        self._timer.start()
        self.resumed.emit()

    def stop(self) -> Optional[Tuple[datetime, datetime, int]]:
        if (self._first_start_dt is None) and (self._current_start_dt is None):
            return None
        now = datetime.now()
        total = self._accumulated_sec
        if self.is_running():
            assert self._current_start_dt is not None
            total += int(round((now - self._current_start_dt).total_seconds()))
        start_dt = self._first_start_dt or now
        end_dt = now
        # reset state
        self._first_start_dt = None
        self._current_start_dt = None
        self._accumulated_sec = 0
        self._timer.stop()
        self.stopped.emit(int(total))
        self.tick.emit(0, "00:00:00")
        return start_dt, end_dt, int(total)

    def _current_elapsed(self) -> int:
        if self.is_running():
            assert self._current_start_dt is not None
            return self._accumulated_sec + int(round((datetime.now() - self._current_start_dt).total_seconds()))
        return self._accumulated_sec

    def _current_elapsed_float(self) -> float:
        if self.is_running():
            assert self._current_start_dt is not None
            return self._accumulated_sec + float((datetime.now() - self._current_start_dt).total_seconds())
        return float(self._accumulated_sec)

    def _on_tick(self) -> None:
        total = self._current_elapsed_float()
        seconds_int = int(total)
        # tenths
        tenths = int((total - seconds_int) * 10) % 10
        base = self._fmt(seconds_int)
        self._last_formatted = f"{base}.{tenths}"
        self.tick.emit(seconds_int, self._last_formatted)



