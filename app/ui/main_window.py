from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
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

    def _on_pause_clicked(self) -> None:
        if self._timer.is_running():
            self._timer.pause()
        elif self._timer.is_paused():
            self._timer.resume()
