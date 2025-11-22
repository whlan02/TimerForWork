from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont

class TimerDisplay(QWidget):
    """
    Modern minimal timer display mimicking the 'Flow' design.
    """
    
    # Signals to communicate user intent to MainWindow
    start_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    stats_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 40)
        self.layout.setSpacing(20)
        self.setMouseTracking(True)
        
        # --- Top Bar (Controls | Stats) ---
        top_bar = QHBoxLayout()
        
        self._btn_controls = QPushButton("Timer")
        self._btn_controls.setObjectName("TabButtonActive")
        self._btn_controls.setCursor(Qt.PointingHandCursor)
        
        self._btn_stats = QPushButton("Stats")
        self._btn_stats.setObjectName("TabButtonInactive")
        self._btn_stats.setCursor(Qt.PointingHandCursor)
        self._btn_stats.clicked.connect(self.stats_requested.emit)

        # Container for the toggle
        toggle_container = QFrame()
        toggle_container.setObjectName("ToggleContainer")
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(4, 4, 4, 4)
        toggle_layout.setSpacing(0)
        toggle_layout.addWidget(self._btn_controls)
        toggle_layout.addWidget(self._btn_stats)
        
        top_bar.addWidget(toggle_container)
        top_bar.addStretch() 
        
        # Top Left aligned
        top_align_layout = QHBoxLayout()
        top_align_layout.addWidget(toggle_container)
        top_align_layout.addStretch()
        
        self.layout.addLayout(top_align_layout)
        self.layout.addStretch(1)
        
        # --- Center Content ---
        center_layout = QVBoxLayout()
        center_layout.setSpacing(10)
        
        self._status_label = QLabel("Ready to Flow")
        self._status_label.setObjectName("StatusLabel")
        self._status_label.setAlignment(Qt.AlignCenter)
        
        self._time_label = QLabel("00:00:00")
        self._time_label.setObjectName("TimeLabel")
        self._time_label.setAlignment(Qt.AlignCenter)
        
        center_layout.addWidget(self._status_label)
        center_layout.addWidget(self._time_label)
        
        self.layout.addLayout(center_layout)
        self.layout.addStretch(1)
        
        # --- Bottom Button ---
        self._action_btn = QPushButton("Start Focus")
        self._action_btn.setObjectName("ActionButton")
        self._action_btn.setCursor(Qt.PointingHandCursor)
        self._action_btn.setFixedHeight(60)
        self._action_btn.clicked.connect(self._on_action_clicked)
        
        # Stop Button (Initially hidden)
        self._stop_btn = QPushButton("Record")
        self._stop_btn.setObjectName("StopButton")
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.clicked.connect(self.stop_requested.emit)
        self._stop_btn.setVisible(False)

        # Container to center the button and limit width
        btn_container = QVBoxLayout()
        btn_container.setAlignment(Qt.AlignCenter)
        
        self._action_btn.setMinimumWidth(200)
        btn_container.addWidget(self._action_btn)
        btn_container.addWidget(self._stop_btn)
        
        self.layout.addLayout(btn_container)

        # --- Styling ---
        self._apply_styles()
        
        # Internal state
        self._is_running = False
        self._is_paused = False

    def _on_action_clicked(self):
        if self._is_running:
            # If running, we pause
            self.pause_requested.emit()
        elif self._is_paused:
            # When paused, the same button resumes via pause handler
            self.pause_requested.emit()
        else:
            self.start_requested.emit()

    def update_time(self, formatted: str) -> None:
        parts = formatted.split(':')
        if len(parts) == 3:
            if parts[0] == "00":
                # Show MM:SS
                text = f"{parts[1]}:{parts[2].split('.')[0]}"
            else:
                text = formatted.split('.')[0]
        else:
            text = formatted
            
        self._time_label.setText(text)

    def set_running_state(self, is_running: bool, is_paused: bool):
        self._is_running = is_running
        self._is_paused = is_paused
        if is_running:
            self._status_label.setText("Focusing...")
            self._status_label.setStyleSheet("color: #16a34a;") # Green (lighter theme)
            self._action_btn.setText("Pause")
            self._time_label.setStyleSheet("color: #111111;")
            self._stop_btn.setVisible(True)
        elif is_paused:
            self._status_label.setText("Paused")
            self._status_label.setStyleSheet("color: #b45309;") # Amber-ish text
            self._action_btn.setText("Resume")
            self._time_label.setStyleSheet("color: #6b7280;")
            self._stop_btn.setVisible(True)
        else:
            self._status_label.setText("Ready to Flow")
            self._status_label.setStyleSheet("color: #16a34a;")
            self._action_btn.setText("Start")
            self._time_label.setStyleSheet("color: #111111;")
            self._stop_btn.setVisible(False)

    def _apply_styles(self):
        # Light theme colors
        bg_color = "#F7F7F9"
        accent_green = "#16a34a"
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                font-family: 'Segoe UI', sans-serif;
            }}
            
            /* Top Toggle */
            QFrame#ToggleContainer {{
                background-color: #e5e7eb;
                border-radius: 18px;
            }}
            QPushButton#TabButtonActive {{
                background-color: #ffffff;
                color: #111111;
                border: none;
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

            /* Main Labels */
            QLabel#StatusLabel {{
                color: {accent_green};
                font-size: 16px;
                font-weight: 600;
                letter-spacing: 1px;
                text-transform: uppercase;
                background-color: transparent;
            }}
            QLabel#TimeLabel {{
                color: #111111;
                font-size: 96px;
                font-weight: bold;
                background-color: transparent;
            }}
            
            /* Action Button */
            QPushButton#ActionButton {{
                background-color: #111111;
                color: #ffffff;
                border: none;
                border-radius: 30px; /* Pill shape */
                font-size: 18px;
                font-weight: bold;
                padding: 0 30px;
            }}
            QPushButton#ActionButton:hover {{
                background-color: #0f172a;
            }}
            QPushButton#ActionButton:pressed {{
                background-color: #1f2937;
            }}
            
            /* Stop Button */
            QPushButton#StopButton {{
                background-color: transparent;
                color: #6b7280;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                margin-top: 10px;
            }}
            QPushButton#StopButton:hover {{
                color: #b91c1c;
                text-decoration: underline;
            }}
        """)
