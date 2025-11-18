from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QToolBar,
    QStatusBar,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
)

from app.models.record import TimeRecord
from app.services.timer_service import TimerService
from app.storage.excel_store import ExcelStore
from app.views.calendar_month import MonthCalendar
from app.views.calendar_week import WeekView
from app.views.timer_display import TimerDisplay


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


class MainWindow(QMainWindow):
    def __init__(self, store: ExcelStore, timer: TimerService) -> None:
        super().__init__()
        self.setWindowTitle("Time Recorder")
        self.resize(920, 640)
        self._store = store
        self._timer = timer

        # Toolbar
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        self._act_start = QAction("Start", self)
        self._act_record = QAction("Save", self)
        self._act_pause = QAction("Pause", self)
        self._act_month = QAction("Month", self)
        self._act_week = QAction("Week", self)
        self._act_timer = QAction("Timer", self)
        toolbar.addAction(self._act_start)
        toolbar.addAction(self._act_record)
        toolbar.addAction(self._act_pause)
        toolbar.addSeparator()
        toolbar.addAction(self._act_month)
        toolbar.addAction(self._act_week)
        toolbar.addAction(self._act_timer)

        # Status bar
        status = QStatusBar(self)
        self.setStatusBar(status)
        self._elapsed_label = QLabel("Elapsed: 00:00:00", self)
        status.addPermanentWidget(self._elapsed_label)

        # Central stacked views
        self._stack = QStackedWidget(self)
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self._stack)
        self.setCentralWidget(central)

        self._month = MonthCalendar(get_total_minutes=self._store.get_total_minutes, parent=self)
        self._week = WeekView(self)
        self._week.bind_data(self._store.get_records_for_date)
        self._timer_view = TimerDisplay(self)
        self._stack.addWidget(self._month)
        self._stack.addWidget(self._week)
        self._stack.addWidget(self._timer_view)
        self._stack.setCurrentWidget(self._month)

        # Wiring
        self._act_month.triggered.connect(lambda: self._stack.setCurrentWidget(self._month))
        self._act_week.triggered.connect(lambda: self._stack.setCurrentWidget(self._week))
        self._act_timer.triggered.connect(lambda: self._stack.setCurrentWidget(self._timer_view))
        self._act_start.triggered.connect(self._on_start_clicked)
        self._act_record.triggered.connect(self._on_record_clicked)
        self._act_pause.triggered.connect(self._on_pause_clicked)

        self._month.selectionChanged.connect(self._on_calendar_selection_changed)
        self._timer.tick.connect(self._on_tick)
        self._timer.tick.connect(self._on_tick_timer_view)
        self._timer.started.connect(self._on_started)
        self._timer.paused.connect(self._on_paused)
        self._timer.resumed.connect(self._on_resumed)
        self._timer.stopped.connect(self._on_stopped)

        # Initial state
        self._update_week_from_calendar()
        self._sync_buttons()

    def _on_tick(self, seconds: int, formatted: str) -> None:
        self._elapsed_label.setText(f"Elapsed: {formatted}")

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
        idle = not running and not paused
        self._act_start.setEnabled(idle)
        self._act_record.setEnabled(not idle)  # Allow recording when running or paused
        self._act_pause.setEnabled(not idle)
        # Switch pause button text only when visible (running -> Pause, paused -> Resume)
        if running:
            self._act_pause.setText("Pause")
        elif paused:
            self._act_pause.setText("Resume")

    def _on_start_clicked(self) -> None:
        self._timer.start()
        self.statusBar().showMessage("Started", 2000)

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
        # refresh views
        self._month.refresh()
        self._update_week_from_calendar()
        self.statusBar().showMessage(f"Recorded {record.duration_min} min", 3000)

    def _on_calendar_selection_changed(self) -> None:
        self._update_week_from_calendar()

    def _selected_date(self) -> date:
        qd: QDate = self._month.selectedDate()
        return qd.toPython()

    def _update_week_from_calendar(self) -> None:
        sel = self._selected_date()
        self._week.set_week(sel)

    def _on_pause_clicked(self) -> None:
        if self._timer.is_running():
            self._timer.pause()
            self.statusBar().showMessage("Paused", 1500)
        elif self._timer.is_paused():
            self._timer.resume()
            self.statusBar().showMessage("Resumed", 1500)





