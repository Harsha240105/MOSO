from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication, Qt, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu

from moso_ui.aura_orb import AuraOrb, OrbState
from moso_ui.conversation import ConversationBubble
from moso_ui.settings import AuraSettings
from moso_ui.tray import SystemTray


class AuraApp:
    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("MOSO Aura")
        self._app.setQuitOnLastWindowClosed(False)

        self._settings = AuraSettings()
        self._orb = AuraOrb()
        self._bubble = ConversationBubble()
        self._tray = SystemTray()

        self._setup_connections()
        self._load_position()

    def _setup_connections(self):
        self._tray.show_action.triggered.connect(self._show_orb)
        self._tray.quit_action.triggered.connect(self._quit)
        self._tray.settings_action.triggered.connect(self._show_about)
        self._orb.clicked.connect(self._toggle_bubble)

    def _load_position(self):
        if self._settings.orb_x > 0 and self._settings.orb_y > 0:
            self._orb.move(self._settings.orb_x, self._settings.orb_y)
        else:
            screen = self._app.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self._orb.move(geo.right() - 120, geo.bottom() - 120)

    def _save_position(self):
        self._settings.orb_x = self._orb.x()
        self._settings.orb_y = self._orb.y()
        self._settings.save()

    def _show_orb(self):
        self._orb.show()
        self._orb.raise_()

    def _toggle_bubble(self):
        if self._bubble.isVisible():
            self._bubble.hide()
        else:
            bx = self._orb.x() + self._orb.width() + 10
            by = self._orb.y()
            self._bubble.move(bx, by)
            self._bubble.show()
            self._bubble.raise_()

    def _show_about(self):
        self._bubble.set_text("MOSO AI - Aura UI\n\n"
                              "Privacy-first local AI assistant.\n\n"
                              "Version: 0.2.0")
        self._toggle_bubble()

    def _quit(self):
        self._save_position()
        self._bubble.close()
        self._orb.close()
        self._app.quit()

    def run(self):
        self._orb.show()
        self._tray.show()
        return self._app.exec()


def main():
    app = AuraApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
