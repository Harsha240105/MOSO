from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

BUBBLE_WIDTH = 360
BUBBLE_HEIGHT = 300


class ConversationBubble(QFrame):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(BUBBLE_WIDTH, BUBBLE_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("MOSO")
        title.setStyleSheet("color: #8A2BE2; font-weight: bold; font-size: 13px; background: transparent;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("X")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,30); color: #aaa; border: none;
                border-radius: 10px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(255,80,80,80); color: white; }
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self._display = QTextBrowser()
        self._display.setOpenExternalLinks(False)
        self._display.setStyleSheet("""
            QTextBrowser {
                background: rgba(20,20,40,200);
                color: #ddd;
                border: 1px solid rgba(138,43,226,80);
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        self._display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self._display)

        self.setStyleSheet("""
            ConversationBubble {
                background: rgba(15,15,35,220);
                border: 1px solid rgba(138,43,226,100);
                border-radius: 16px;
            }
        """)

        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide)
        self._hide_delay = 0

    def show_message(self, text: str, hide_after_seconds: int = 0):
        self._display.append(text)
        self.show()
        self.raise_()
        if hide_after_seconds > 0:
            self._hide_delay = hide_after_seconds
            self._auto_hide_timer.start(hide_after_seconds * 1000)

    def set_text(self, text: str):
        self._display.clear()
        self._display.setPlainText(text)

    def clear(self):
        self._display.clear()

    def set_visible(self, visible: bool):
        if visible:
            self.show()
        else:
            self.hide()
