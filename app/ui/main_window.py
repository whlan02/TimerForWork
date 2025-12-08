from __future__ import annotations

from datetime import date, time as dt_time
from typing import Optional

from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
    QFormLayout,
    QDateEdit,
    QTimeEdit,
    QMessageBox,
)

from app.models.record import TimeRecord
from app.services.timer_service import TimerService
from app.storage.excel_store import ExcelStore
from app.views.timer_display import TimerDisplay
from app.views.stats_view import StatsView


class NoteDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Note")
        self.resize(420, 220)
        self._edit = QTextEdit(self)
        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self._edit)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

    def get_text(self) -> Optional[str]:
        if self.exec() == QDialog.Accepted:
            return self._edit.toPlainText().strip()
        return None


class ManualRecordDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manual Record")
        self.resize(420, 320)

        today = QDate.currentDate()
        now_time_obj = QTime.currentTime()
        now_time = QTime(now_time_obj.hour(), now_time_obj.minute(), 0)
        default_end = now_time.addSecs(3600)  # +1h

        self._date_edit = QDateEdit(today, self)
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd")

        self._start_edit = QTimeEdit(now_time, self)
        self._start_edit.setDisplayFormat("HH:mm:ss")

        self._end_edit = QTimeEdit(default_end, self)
        self._end_edit.setDisplayFormat("HH:mm:ss")

        self._duration_edit = QTimeEdit(QTime(1, 0, 0), self)
        self._duration_edit.setDisplayFormat("HH:mm:ss")

        self._note_edit = QTextEdit(self)

        self._msg_label = QLabel("", self)
        self._msg_label.setStyleSheet("color: #b91c1c;")

        form = QFormLayout()
        form.addRow("Date", self._date_edit)
        form.addRow("Start", self._start_edit)
        form.addRow("End", self._end_edit)
        form.addRow("Duration", self._duration_edit)
        form.addRow("Note", self._note_edit)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._msg_label)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        self._start_edit.timeChanged.connect(self._update_duration_from_times)
        self._end_edit.timeChanged.connect(self._update_duration_from_times)

    def _update_duration_from_times(self) -> None:
        start = self._start_edit.time()
        end = self._end_edit.time()
        start_sec = start.hour() * 3600 + start.minute() * 60 + start.second()
        end_sec = end.hour() * 3600 + end.minute() * 60 + end.second()
        diff = max(end_sec - start_sec, 0)
        h = diff // 3600
        m = (diff % 3600) // 60
        s = diff % 60
        self._duration_edit.setTime(QTime(h % 24, m, s))
        if diff <= 0:
            self._msg_label.setText("End time must be after start time.")
        else:
            self._msg_label.setText("")

    def _on_accept(self) -> None:
        record = self._build_record()
        if record is None:
            QMessageBox.warning(self, "Invalid time", "Please ensure end time is after start time.")
            return
        self._result_record = record
        self.accept()

    def _build_record(self) -> Optional[TimeRecord]:
        start = self._start_edit.time()
        end = self._end_edit.time()
        start_sec = start.hour() * 3600 + start.minute() * 60 + start.second()
        end_sec = end.hour() * 3600 + end.minute() * 60 + end.second()
        diff = end_sec - start_sec
        if diff <= 0:
            return None
        d = self._date_edit.date().toPython()
        st = dt_time(start.hour(), start.minute(), start.second())
        et = dt_time(end.hour(), end.minute(), end.second())
        duration_sec = diff
        duration_min = int(round(duration_sec / 60.0))
        note = self._note_edit.toPlainText().strip()
        return TimeRecord(date=d, start_time=st, end_time=et, duration_min=duration_min, duration_sec=duration_sec, note=note)

    def get_record(self) -> Optional[TimeRecord]:
        self._result_record: Optional[TimeRecord] = None
        if self.exec() == QDialog.Accepted:
            return getattr(self, "_result_record", None)
        return None


class MainWindow(QMainWindow):
    def __init__(self, store: ExcelStore, timer: TimerService) -> None:
        super().__init__()
        self.setWindowTitle("Focus Timer")
        self.resize(450, 500) 
        self._store = store
        self._timer = timer

        # --- Central stacked views ---
        self._stack = QStackedWidget(self)
        central = QWidget(self)
        # Light theme background for the container
        central.setStyleSheet("background-color: #F7F7F9;") 
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0) # Full bleed
        layout.addWidget(self._stack)
        self.setCentralWidget(central)

        # Views
        self._timer_view = TimerDisplay(self)
        self._stats_view = StatsView(self._store, self)
        
        self._stack.addWidget(self._timer_view)
        self._stack.addWidget(self._stats_view)
        
        # Default to Timer View
        self._show_timer_view()

        # --- Wiring ---
        
        # Timer Service Events
        self._timer.tick.connect(self._on_tick_timer_view)
        self._timer.started.connect(self._on_started)
        self._timer.paused.connect(self._on_paused)
        self._timer.resumed.connect(self._on_resumed)
        self._timer.stopped.connect(self._on_stopped)

        # Timer View Events
        self._timer_view.start_requested.connect(self._on_start_clicked)
        self._timer_view.pause_requested.connect(self._on_pause_clicked)
        self._timer_view.stop_requested.connect(self._on_record_clicked)
        self._timer_view.stats_requested.connect(self._show_stats_view)
        self._timer_view.manual_requested.connect(self._on_manual_record)
        
        # Stats View Events
        self._stats_view.controls_requested.connect(self._show_timer_view)

        # Initial state
        self._sync_buttons()

    def _show_timer_view(self):
        self._stack.setCurrentWidget(self._timer_view)
        
    def _show_stats_view(self):
        # Refresh stats when entering view
        self._stats_view.refresh()
        self._stack.setCurrentWidget(self._stats_view)

    def _on_tick_timer_view(self, seconds: int, formatted: str) -> None:
        self._timer_view.update_time(formatted)

    def _on_started(self) -> None:
        self._sync_buttons()

    def _on_paused(self) -> None:
        self._sync_buttons()

    def _on_resumed(self) -> None:
        self._sync_buttons()

    def _on_stopped(self, seconds: int) -> None:
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        running = self._timer.is_running()
        paused = self._timer.is_paused()
        
        # Update Timer View UI
        self._timer_view.set_running_state(running, paused)

    def _on_start_clicked(self) -> None:
        self._timer.start()

    def _on_record_clicked(self) -> None:
        res = self._timer.stop()
        if not res:
            return
        start_dt, end_dt, elapsed_sec = res
        dlg = NoteDialog(self)
        note = dlg.get_text()
        if note is None:
            # user canceled; ignore and do not store
            return
        record = TimeRecord.from_datetimes_with_elapsed(start_dt, end_dt, elapsed_seconds=elapsed_sec, note=note)
        self._store.add_record(record)
        
        # refresh views if needed (StatsView refreshes on show)
        self.statusBar().showMessage(f"Recorded {record.duration_min} min", 3000)
        
        # If we were in timer view, reset
        self._timer_view.update_time("00:00:00")

    def _on_manual_record(self) -> None:
        dlg = ManualRecordDialog(self)
        record = dlg.get_record()
        if record is None:
            return
        self._store.add_record(record)
        if self._stack.currentWidget() is self._stats_view:
            self._stats_view.refresh()
        self.statusBar().showMessage(f"Manually recorded {record.duration_min} min", 3000)

    def _on_pause_clicked(self) -> None:
        if self._timer.is_running():
            self._timer.pause()
        elif self._timer.is_paused():
            self._timer.resume()
