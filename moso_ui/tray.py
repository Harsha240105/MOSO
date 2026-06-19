from __future__ import annotations

import os

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class SystemTray(QSystemTrayIcon):
    def __init__(self, parent=None):
        icon = _make_icon()
        super().__init__(icon, parent)
        self.setToolTip("MOSO AI")

        menu = QMenu()
        self._show_action = menu.addAction("Show Orb")
        menu.addSeparator()
        self._settings_action = menu.addAction("Settings...")
        menu.addSeparator()
        self._quit_action = menu.addAction("Quit")
        self.setContextMenu(menu)

        self.activated.connect(self._on_activate)

    @property
    def show_action(self):
        return self._show_action

    @property
    def settings_action(self):
        return self._settings_action

    @property
    def quit_action(self):
        return self._quit_action

    def _on_activate(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_action.trigger()

    def show_notification(self, title: str, message: str, duration_ms: int = 3000):
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration_ms)


def _make_icon() -> QIcon:
    pm = QPixmap(32, 32)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#8A2BE2"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 28, 28)
    p.setPen(QColor(255, 255, 255, 200))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "M")
    p.end()
    return QIcon(pm)
