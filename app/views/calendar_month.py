from __future__ import annotations

from datetime import date
from typing import Callable, Optional

from PySide6.QtCore import QDate, Qt, QLocale
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QCalendarWidget


class MonthCalendar(QCalendarWidget):
    """
    轻量月视图：根据当日总分钟数对单元格背景着色。
    get_total_minutes: Callable[[date], int]
    """

    def __init__(self, get_total_minutes: Callable[[date], int], parent=None) -> None:
        super().__init__(parent)
        self._get_total = get_total_minutes
        self.setGridVisible(True)
        # Force English locale for day names and month names
        self.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        # 美化：周起始为周一（默认受区域影响，这里强制周一起）
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)

    def refresh(self) -> None:
        self.updateCells()

    def _color_for_minutes(self, minutes: int) -> Optional[QColor]:
        if minutes <= 0:
            return None
        # 0..480 分钟 映射为浅蓝 -> 深蓝
        ratio = min(minutes / 480.0, 1.0)
        # 使用 HSL（蓝色 210°），随时长加深饱和度与降低亮度
        color = QColor.fromHsl(210, int(60 + 160 * ratio), int(245 - 140 * ratio))
        color.setAlpha(120)  # 半透明，避免遮挡文字
        return color

    def paintCell(self, painter, rect, qdate: QDate) -> None:  # type: ignore[override]
        # 先按默认绘制（包含日期文字）
        super().paintCell(painter, rect, qdate)
        d: date = qdate.toPython()
        mins = self._get_total(d)
        color = self._color_for_minutes(mins)
        if color:
            painter.save()
            painter.fillRect(rect.adjusted(1, 1, -1, -1), QBrush(color))
            painter.restore()



