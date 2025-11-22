from __future__ import annotations

from datetime import date, datetime, timedelta, time
from typing import List, Dict, Tuple, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QGridLayout, QSpacerItem, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QColor, QMouseEvent

from app.models.record import TimeRecord

class RecordListDialog(QDialog):
    """
    Displays a list of TimeRecords in a simple table.
    """
    def __init__(self, title: str, records: List[TimeRecord], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        if not records:
            layout.addWidget(QLabel("No records found.", alignment=Qt.AlignCenter))
        else:
            table = QTableWidget(len(records), 4) # Start, End, Duration, Note
            table.setHorizontalHeaderLabels(["Start", "End", "Duration", "Note"])
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            table.verticalHeader().setVisible(False)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            for r_idx, r in enumerate(records):
                dur_str = f"{r.duration_min}m"
                table.setItem(r_idx, 0, QTableWidgetItem(r.start_time.strftime("%H:%M")))
                table.setItem(r_idx, 1, QTableWidgetItem(r.end_time.strftime("%H:%M")))
                table.setItem(r_idx, 2, QTableWidgetItem(dur_str))
                table.setItem(r_idx, 3, QTableWidgetItem(r.note))
                
            layout.addWidget(table)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class HeatmapBlock(QFrame):
    """
    A single block in the heatmap (representing a time slot or a day).
    """
    hovered = Signal(str, int) # label_text, seconds
    clicked = Signal()
    
    def __init__(self, label: str, seconds: int, color: str, parent=None):
        super().__init__(parent)
        self.label = label
        self.seconds = seconds
        self.default_color = color
        
        self.setStyleSheet(f"""
            HeatmapBlock {{
                background-color: {color};
                border-radius: 4px;
            }}
            HeatmapBlock:hover {{
                border: 1px solid white;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        
    def enterEvent(self, event):
        self.hovered.emit(self.label, self.seconds)
        super().enterEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class WeekGrid(QWidget):
    hover_stats = Signal(str, str) # main_text, sub_text
    hover_cleared = Signal()
    # Signal to request displaying records: date, period_index (0-2) or None for whole day
    request_records = Signal(object, object) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Data storage
        self.total_week_seconds = 0
        
    def update_data(self, monday: date, records_map: Dict[date, List[TimeRecord]]):
        # Clear existing
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            if w: w.setParent(None)
            
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        periods = [
            ("Morning", 0, 12),
            ("Afternoon", 12, 18),
            ("Evening", 18, 24)
        ]
        
        self.total_week_seconds = 0
        
        # 7 Columns (Days)
        for col, day_name in enumerate(days):
            current_date = monday + timedelta(days=col)
            day_records = records_map.get(current_date, [])
            
            # Calculate daily total
            day_total = sum(r.duration_sec for r in day_records)
            self.total_week_seconds += day_total
            
            # Create Day Label (Bottom) - Hoverable for day total
            # Now distinct logic inside HoverLabel to handle clicks
            day_label_widget = HoverLabel(days[col], day_total, "Day Total")
            day_label_widget.hovered.connect(self._on_block_hover)
            # Bind current_date
            day_label_widget.clicked.connect(lambda d=current_date: self.request_records.emit(d, None))
            
            self.layout.addWidget(day_label_widget, 3, col)
            
            period_seconds_map = {0: 0, 1: 0, 2: 0}
            
            for rec in day_records:
                s = rec.start_time.hour + rec.start_time.minute/60.0
                e = rec.end_time.hour + rec.end_time.minute/60.0
                if e < s: e = 24.0 
                
                duration = rec.duration_sec
                
                def intersect(r_start, r_end, p_start, p_end):
                    return max(0, min(r_end, p_end) - max(r_start, p_start))
                
                full_dur_h = e - s
                if full_dur_h <= 0: continue
                
                for p_idx, (_, p_start, p_end) in enumerate(periods):
                    h_overlap = intersect(s, e, p_start, p_end)
                    if h_overlap > 0:
                        ratio = h_overlap / full_dur_h
                        period_seconds_map[p_idx] += int(duration * ratio)

            # Draw blocks
            for row, (p_name, _, _) in enumerate(periods):
                secs = period_seconds_map[row]
                color = self._get_color(secs, row) 
                
                block_label = f"{day_name} {p_name}"
                block = HeatmapBlock(block_label, secs, color)
                block.hovered.connect(self._on_block_hover)
                # Pass date and row (period_idx)
                block.clicked.connect(lambda d=current_date, p=row: self.request_records.emit(d, p))
                block.setFixedHeight(60)
                self.layout.addWidget(block, row, col)
        # enable mouse tracking to receive leaveEvent
        self.setMouseTracking(True)

    def leaveEvent(self, event):
        self.hover_cleared.emit()
        super().leaveEvent(event)

    def _get_color(self, seconds: int, period_idx: int) -> str:
        # Light theme palette: gray for 0, green gradients for >0
        if seconds == 0: return "#e5e7eb"  # light gray
        hours = seconds / 3600.0
        if hours < 0.5: return "#bbf7d0"  # green-200
        if hours < 1.0: return "#86efac"  # green-300
        if hours < 2.0: return "#4ade80"  # green-400
        if hours < 3.0: return "#22c55e"  # green-500
        if hours < 4.0: return "#16a34a"  # green-600
        return "#15803d"                 # green-700

    def _on_block_hover(self, label: str, seconds: int):
        formatted = self._fmt_time(seconds)
        self.hover_stats.emit(formatted, label)
        
    @staticmethod
    def _fmt_time(seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"


class HoverLabel(QLabel):
    hovered = Signal(str, int)
    clicked = Signal()

    def __init__(self, text, seconds, meta):
        super().__init__(text)
        self.seconds = seconds
        self.meta = meta
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: #6b7280; padding: 5px;")
        self.setCursor(Qt.PointingHandCursor)
        
    def enterEvent(self, event):
        self.hovered.emit(self.meta, self.seconds)
        super().enterEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class MonthGrid(QWidget):
    hover_stats = Signal(str, str)
    hover_cleared = Signal()
    request_records = Signal(object) # date only

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(10, 10, 10, 10)

    def update_data(self, year: int, month: int, records_map: Dict[date, List[TimeRecord]]):
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            if w: w.setParent(None)

        import calendar
        cal = calendar.monthcalendar(year, month)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d in enumerate(days):
            l = QLabel(d)
            l.setAlignment(Qt.AlignCenter)
            l.setStyleSheet("color: #666;")
            self.layout.addWidget(l, 0, i)
            
        for r_idx, week in enumerate(cal):
            for c_idx, day_num in enumerate(week):
                if day_num == 0:
                    continue
                
                d_date = date(year, month, day_num)
                day_recs = records_map.get(d_date, [])
                total_sec = sum(r.duration_sec for r in day_recs)
                
                color = self._get_color(total_sec)
                
                block = HeatmapBlock(f"{d_date.strftime('%b %d')}", total_sec, color)
                block.setFixedSize(40, 40) 
                block.hovered.connect(lambda l, s: self.hover_stats.emit(self._fmt_time(s), l))
                block.clicked.connect(lambda d=d_date: self.request_records.emit(d))
                
                num_lbl = QLabel(str(day_num), block)
                num_lbl.setStyleSheet("color: rgba(0,0,0,0.55); font-size: 10px; background: transparent;")
                num_lbl.move(4, 2)
                num_lbl.adjustSize()
                num_lbl.setAttribute(Qt.WA_TransparentForMouseEvents) # Allow clicks to pass through
                
                self.layout.addWidget(block, r_idx + 1, c_idx)
        self.setMouseTracking(True)

    def leaveEvent(self, event):
        self.hover_cleared.emit()
        super().leaveEvent(event)

    def _get_color(self, seconds: int) -> str:
        # Light theme palette: gray for 0, green gradients for >0
        if seconds == 0: return "#e5e7eb"  # gray-300
        h = seconds / 3600.0
        if h < 1: return "#bbf7d0"   # green-200
        if h < 3: return "#86efac"   # green-300
        if h < 5: return "#4ade80"   # green-400
        if h < 7: return "#22c55e"   # green-500
        return "#16a34a"             # green-600

    @staticmethod
    def _fmt_time(seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"


class StatsView(QWidget):
    """
    Combined Stats Interface (Week/Month)
    """
    controls_requested = Signal()

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self._store = store
        self._current_date = date.today()
        self._mode = "week" # or "month"
        self._last_month_total_sec: int = 0
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # --- Top Bar (Controls | Stats) ---
        top_bar = QHBoxLayout()
        
        self._btn_controls = QPushButton("Controls")
        self._btn_controls.setObjectName("TabButtonInactive")
        self._btn_controls.setCursor(Qt.PointingHandCursor)
        self._btn_controls.clicked.connect(self.controls_requested.emit)
        
        self._btn_stats = QPushButton("Stats")
        self._btn_stats.setObjectName("TabButtonActive")
        self._btn_stats.setCursor(Qt.PointingHandCursor)

        # Container for the toggle
        toggle_container = QFrame()
        toggle_container.setObjectName("ToggleContainer")
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(4, 4, 4, 4)
        toggle_layout.setSpacing(0)
        toggle_layout.addWidget(self._btn_controls)
        toggle_layout.addWidget(self._btn_stats)
        
        top_align_layout = QHBoxLayout()
        top_align_layout.addWidget(toggle_container)
        top_align_layout.addStretch()
        
        self.layout.addLayout(top_align_layout)
        
        # --- Header (Nav + Switcher) ---
        header_layout = QHBoxLayout()
        
        self._btn_prev = QPushButton("<")
        self._btn_next = QPushButton(">")
        for b in [self._btn_prev, self._btn_next]:
            b.setFixedSize(30, 30)
            b.setStyleSheet("background: transparent; color: #888; font-weight: bold; font-size: 18px; border: none;")
            b.setCursor(Qt.PointingHandCursor)
            
        self._lbl_date_range = QLabel()
        self._lbl_date_range.setStyleSheet("color: #111111; font-size: 16px; font-weight: 600;")
        self._lbl_date_range.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(self._btn_prev)
        header_layout.addWidget(self._lbl_date_range)
        header_layout.addWidget(self._btn_next)
        header_layout.addStretch()
        
        # View Switcher (segmented control)
        self._btn_week = QPushButton("Week")
        self._btn_month = QPushButton("Month")
        for b in [self._btn_week, self._btn_month]:
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(30)
            b.setMinimumWidth(64)
        self._btn_week.setChecked(True)

        self._mode_container = QFrame()
        self._mode_container.setObjectName("ModeContainer")
        mode_layout = QHBoxLayout(self._mode_container)
        mode_layout.setContentsMargins(4, 4, 4, 4)
        mode_layout.setSpacing(4)
        mode_layout.addWidget(self._btn_week)
        mode_layout.addWidget(self._btn_month)

        header_layout.addWidget(self._mode_container)
        
        self.layout.addLayout(header_layout)
        
        # --- Total Display ---
        self._lbl_total_val = QLabel("0h 0m")
        self._lbl_total_val.setAlignment(Qt.AlignCenter)
        self._lbl_total_val.setStyleSheet("color: #111111; font-size: 48px; font-weight: bold;")
        
        self._lbl_total_sub = QLabel("Total This Week")
        self._lbl_total_sub.setAlignment(Qt.AlignCenter)
        self._lbl_total_sub.setStyleSheet("color: #6b7280; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;")
        
        self.layout.addWidget(self._lbl_total_val)
        self.layout.addWidget(self._lbl_total_sub)
        
        # --- Content Stack ---
        self._stack = QStackedWidget()
        self._week_view = WeekGrid()
        self._month_view = MonthGrid()
        
        self._stack.addWidget(self._week_view)
        self._stack.addWidget(self._month_view)
        
        self.layout.addWidget(self._stack)
        self.layout.addStretch()
        
        # --- Styling ---
        self._apply_styles()

        # --- Events ---
        self._btn_prev.clicked.connect(self._on_prev)
        self._btn_next.clicked.connect(self._on_next)
        self._btn_week.clicked.connect(lambda: self._set_mode("week"))
        self._btn_month.clicked.connect(lambda: self._set_mode("month"))
        
        self._week_view.hover_stats.connect(self._update_temp_stats)
        self._week_view.hover_cleared.connect(self._restore_default_totals)
        self._week_view.request_records.connect(self._show_records_for_period)
        
        self._month_view.hover_stats.connect(self._update_temp_stats)
        self._month_view.hover_cleared.connect(self._restore_default_totals)
        self._month_view.request_records.connect(lambda d: self._show_records_for_period(d, None))
        
        # Initial Load
        self._refresh()

    def refresh(self):
        self._refresh()

    def _set_mode(self, mode):
        self._mode = mode
        self._btn_week.setChecked(mode == "week")
        self._btn_month.setChecked(mode == "month")
        self._update_switcher_styles()
        self._stack.setCurrentWidget(self._week_view if mode == "week" else self._month_view)
        self._refresh()
        
    def _update_switcher_styles(self):
        active = "background-color: #ffffff; color: #111111; border: 1px solid #e5e7eb; border-radius: 10px; font-weight: 600;"
        inactive = "background-color: transparent; color: #6b7280; border: none; border-radius: 10px;"

        self._btn_week.setStyleSheet(active if self._btn_week.isChecked() else inactive)
        self._btn_month.setStyleSheet(active if self._btn_month.isChecked() else inactive)

    def _apply_styles(self):
        bg_color = "#F7F7F9"
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                font-family: 'Segoe UI', sans-serif;
            }}
            QFrame#ModeContainer {{
                background-color: #e5e7eb;
                border-radius: 16px;
            }}
            QFrame#ToggleContainer {{
                background-color: #e5e7eb;
                border-radius: 18px;
            }}
            QPushButton#TabButtonActive {{
                background-color: #ffffff;
                color: #111111;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton#TabButtonInactive {{
                background-color: transparent;
                color: #6b7280;
                border: none;
                border-radius: 14px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton#TabButtonInactive:hover {{
                color: #111111;
            }}
            
            /* Table Styles */
            QTableWidget {{
                background-color: #ffffff;
                color: #111111;
                gridline-color: #e5e7eb;
                border: 1px solid #e5e7eb;
            }}
            QHeaderView::section {{
                background-color: #f3f4f6;
                color: #111111;
                padding: 4px;
                border: 1px solid #e5e7eb;
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: #d1fae5;
            }}
        """)
        self._update_switcher_styles()

    def _on_prev(self):
        if self._mode == "week":
            self._current_date -= timedelta(days=7)
        else:
            y, m = self._current_date.year, self._current_date.month
            m -= 1
            if m < 1:
                m = 12
                y -= 1
            self._current_date = date(y, m, 1)
        self._refresh()

    def _on_next(self):
        if self._mode == "week":
            self._current_date += timedelta(days=7)
        else:
            y, m = self._current_date.year, self._current_date.month
            m += 1
            if m > 12:
                m = 1
                y += 1
            self._current_date = date(y, m, 1)
        self._refresh()

    def _refresh(self):
        if self._mode == "week":
            self._load_week()
        else:
            self._load_month()

    def _load_week(self):
        monday = self._current_date - timedelta(days=self._current_date.weekday())
        sunday = monday + timedelta(days=6)
        m1 = monday.strftime("%b %d")
        m2 = sunday.strftime("%b %d")
        self._lbl_date_range.setText(f"{m1} - {m2}")
        
        records_map = {}
        for i in range(7):
            d = monday + timedelta(days=i)
            records_map[d] = self._store.get_records_for_date(d)
            
        self._week_view.update_data(monday, records_map)
        self._lbl_total_sub.setText("Total This Week")
        self._show_default_total(self._week_view.total_week_seconds)

    def _load_month(self):
        y, m = self._current_date.year, self._current_date.month
        self._lbl_date_range.setText(self._current_date.strftime("%B %Y"))
        
        import calendar
        _, last_day = calendar.monthrange(y, m)
        records_map = {}
        total_sec = 0
        for d_num in range(1, last_day + 1):
            d = date(y, m, d_num)
            recs = self._store.get_records_for_date(d)
            records_map[d] = recs
            total_sec += sum(r.duration_sec for r in recs)
            
        self._month_view.update_data(y, m, records_map)
        self._lbl_total_sub.setText("Total This Month")
        self._last_month_total_sec = total_sec
        self._show_default_total(total_sec)

    def _update_temp_stats(self, main_text, sub_text):
        self._lbl_total_val.setText(main_text)
        self._lbl_total_sub.setText(sub_text)

    def _show_default_total(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        self._lbl_total_val.setText(f"{h}h {m}m")

    def _restore_default_totals(self):
        # Restore totals when hover leaves the grids
        if self._mode == "week":
            self._lbl_total_sub.setText("Total This Week")
            self._show_default_total(self._week_view.total_week_seconds)
        else:
            self._lbl_total_sub.setText("Total This Month")
            self._show_default_total(self._last_month_total_sec)

    def _show_records_for_period(self, d: date, period_idx: Optional[int]):
        records = self._store.get_records_for_date(d)
        
        if period_idx is not None:
            # Filter records that overlap with the period
            # 0: 0-12, 1: 12-18, 2: 18-24
            p_start_h = 0
            p_end_h = 24
            
            if period_idx == 0:
                p_start_h, p_end_h = 0, 12
            elif period_idx == 1:
                p_start_h, p_end_h = 12, 18
            elif period_idx == 2:
                p_start_h, p_end_h = 18, 24
                
            filtered = []
            for r in records:
                s = r.start_time.hour + r.start_time.minute/60.0
                e = r.end_time.hour + r.end_time.minute/60.0
                if e < s: e = 24.0 # Should not happen given assumed data constraints but safety check
                
                # Check overlap
                overlap = max(0, min(e, p_end_h) - max(s, p_start_h))
                if overlap > 0:
                    filtered.append(r)
            records = filtered
            
        title = f"Records for {d.strftime('%b %d, %Y')}"
        if period_idx is not None:
            p_names = ["Morning", "Afternoon", "Evening"]
            title += f" ({p_names[period_idx]})"
            
        dlg = RecordListDialog(title, records, self)
        dlg.exec()
