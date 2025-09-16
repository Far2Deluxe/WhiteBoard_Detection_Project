import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QFileDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QFrame, QStatusBar
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize


class WhiteboardApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("📋 Whiteboard Detection")
        self.setGeometry(200, 100, 1000, 700)

        # Selected folder
        self.folder_path = None

        # --- Central Widget ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Header Bar (like a toolbar) ---
        header = QFrame()
        header.setFrameShape(QFrame.Shape.NoFrame)
        header_layout = QHBoxLayout(header)

        self.btn_select_folder = QPushButton("📂 Select Folder")
        self.btn_select_folder.clicked.connect(self.select_folder)

        self.btn_run_detection = QPushButton("🚀 Run Detection")
        self.btn_run_detection.clicked.connect(self.run_detection)
        self.btn_run_detection.setEnabled(False)

        # Add buttons to header
        header_layout.addWidget(self.btn_select_folder)
        header_layout.addWidget(self.btn_run_detection)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # --- Thumbnails Grid ---
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.thumbnail_list.setIconSize(QSize(150, 150))
        self.thumbnail_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.thumbnail_list.setSpacing(15)
        self.thumbnail_list.setStyleSheet("""
            QListWidget::item {
                border: 1px solid #444;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }
            QListWidget::item:hover {
                background-color: #444;
            }
        """)

        main_layout.addWidget(self.thumbnail_list)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # --- Global Stylesheet (dark modern theme) ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #202124;
                color: white;
            }
            QPushButton {
                background-color: #3c4043;
                border: none;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #5f6368;
            }
            QPushButton:disabled {
                background-color: #2c2f31;
                color: #777;
            }
            QStatusBar {
                background-color: #2c2f31;
                color: #bbb;
            }
        """)

    # --- Folder selection ---
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.folder_path = folder
            self.btn_run_detection.setEnabled(True)
            self.status_bar.showMessage(f"Selected folder: {folder}")
            self.load_thumbnails(folder)

    # --- Load thumbnails into the grid ---
    def load_thumbnails(self, folder):
      
        self.thumbnail_list.clear()
        for filename in os.listdir(folder):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                filepath = os.path.join(folder, filename)
                pixmap = QPixmap(filepath).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)
                item = QListWidgetItem(QIcon(pixmap), filename)
                item.setData(Qt.ItemDataRole.UserRole, filepath)
                self.thumbnail_list.addItem(item)

    # --- Run YOLO detection (placeholder for now) ---
    def run_detection(self):
        if not self.folder_path:
            return
        self.status_bar.showMessage("🚀 Running YOLO detection... (not yet connected)")
        # TODO: connect with Detector and update GUI results


    def run(self):
        self.show()


# --- Run app directly ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhiteboardApp()
    window.run()
    sys.exit(app.exec())
