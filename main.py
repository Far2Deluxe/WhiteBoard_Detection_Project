from src.gui.app import WhiteboardApp
from PyQt6.QtWidgets import QApplication
import sys


def launch_whiteboard_gui():
    existing = QApplication.instance()
    app = existing if existing is not None else QApplication(sys.argv)
    window = WhiteboardApp()
    window.run()
    return app.exec()


if __name__ == "__main__":
    sys.exit(launch_whiteboard_gui())