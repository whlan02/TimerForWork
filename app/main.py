from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLocale

from app.services.timer_service import TimerService
from app.storage.excel_store import ExcelStore
from app.ui.main_window import MainWindow


def main() -> int:
    # Force English locale globally (affects standard dialogs/day names)
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    app = QApplication(sys.argv)
    store = ExcelStore()
    timer = TimerService()
    win = MainWindow(store=store, timer=timer)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())



