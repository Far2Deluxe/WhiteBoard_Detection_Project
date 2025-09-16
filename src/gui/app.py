import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QFileDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QFrame, QStatusBar, QAbstractItemView
)
from PyQt6.QtGui import QPixmap, QIcon, QImage, QImageReader
from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QThread
from detection_module import detect_whiteboards, move_detected_images


class ThumbnailWorker(QObject):
    imageLoaded = pyqtSignal(str, QImage)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop = False

    def stop(self):
        self._stop = True

    def _iter_image_files(self, folder):
        for filename in os.listdir(folder):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                yield os.path.join(folder, filename)

    def load_from_folder(self, folder):
        for path in self._iter_image_files(folder):
            if self._stop:
                break
            image = self._read_thumbnail_image(path, 150, 150)
            if image is not None:
                self.imageLoaded.emit(path, image)
        self.finished.emit()

    def load_from_files(self, filepaths):
        for path in filepaths:
            if self._stop:
                break
            image = self._read_thumbnail_image(path, 150, 150)
            if image is not None:
                self.imageLoaded.emit(path, image)
        self.finished.emit()

    def _read_thumbnail_image(self, path, width, height):
        reader = QImageReader(path)
        reader.setAutoTransform(True)
        # Compute scaled size while keeping aspect ratio
        size = reader.size()
        if size.isValid() and not size.isEmpty():
            # QSize.scaled in PyQt6 does not accept a TransformationMode; provide only aspect ratio mode
            scaled = size.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
            reader.setScaledSize(scaled)
        image = reader.read()
        return image if not image.isNull() else None


class WhiteboardApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("📋 Whiteboard Detection")
        self.setGeometry(200, 100, 1000, 700)

        # Selected folder
        self.folder_path = None
        self.detect_result = None
        self.detected_images = []
        self.excluded_images = set()
        self._thumb_thread = None
        self._thumb_worker = None

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

        self.btn_move_all = QPushButton("📦 Create + Move Detected")
        self.btn_move_all.clicked.connect(self.move_detected)
        self.btn_move_all.setVisible(False)
        self.btn_move_all.setEnabled(False)

        self.btn_exclude_selected = QPushButton("🚫 Exclude Selected")
        self.btn_exclude_selected.clicked.connect(self.exclude_selected)
        self.btn_exclude_selected.setVisible(False)
        self.btn_exclude_selected.setEnabled(False)

        # Add buttons to header
        header_layout.addWidget(self.btn_select_folder)
        header_layout.addWidget(self.btn_run_detection)
        header_layout.addWidget(self.btn_exclude_selected)
        header_layout.addWidget(self.btn_move_all)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # --- Thumbnails Grid ---
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.thumbnail_list.setIconSize(QSize(150, 150))
        self.thumbnail_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.thumbnail_list.setSpacing(15)
        self.thumbnail_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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
        self._cancel_thumbnail_loading()
        self.thumbnail_list.clear()

        # Reset action buttons when browsing
        self.btn_exclude_selected.setVisible(False)
        self.btn_move_all.setVisible(False)
        self.btn_exclude_selected.setEnabled(False)
        self.btn_move_all.setEnabled(False)

        # Start background loading
        self._thumb_thread = QThread()
        self._thumb_worker = ThumbnailWorker()
        self._thumb_worker.moveToThread(self._thumb_thread)
        self._thumb_thread.started.connect(lambda: self._thumb_worker.load_from_folder(folder))
        self._thumb_worker.imageLoaded.connect(self._on_thumbnail_loaded)
        self._thumb_worker.finished.connect(self._thumb_thread.quit)
        self._thumb_worker.finished.connect(self._thumb_worker.deleteLater)
        self._thumb_thread.finished.connect(self._on_thumbnail_finished)
        self._thumb_thread.finished.connect(self._thumb_thread.deleteLater)
        self._thumb_thread.start()

    # --- Run YOLO detection and show results ---
    def run_detection(self):
        if not self.folder_path:
            return
        self.status_bar.showMessage("🚀 Running YOLO detection...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.detect_result = detect_whiteboards(self.folder_path)
            self.detected_images = list(self.detect_result.get("detected_images", []))
            self.excluded_images = set()
            self.show_detected_thumbnails()
            stats = self.detect_result.get("stats", {})
            self.status_bar.showMessage(
                f"✅ Detection complete: {stats.get('detected_count', 0)}/{stats.get('total_images', 0)} images contain whiteboards"
            )
        except Exception as e:
            self.status_bar.showMessage(f"❌ Detection failed: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def show_detected_thumbnails(self):
        self._cancel_thumbnail_loading()
        self.thumbnail_list.clear()

        filepaths = [p for p in self.detected_images if p not in self.excluded_images]

        # Show controls now; enable after first item arrives
        self.btn_exclude_selected.setVisible(True)
        self.btn_move_all.setVisible(True)
        self.btn_exclude_selected.setEnabled(False)
        self.btn_move_all.setEnabled(False)

        self._thumb_thread = QThread()
        self._thumb_worker = ThumbnailWorker()
        self._thumb_worker.moveToThread(self._thumb_thread)
        self._thumb_thread.started.connect(lambda: self._thumb_worker.load_from_files(filepaths))
        self._thumb_worker.imageLoaded.connect(self._on_thumbnail_loaded)
        self._thumb_worker.finished.connect(self._thumb_thread.quit)
        self._thumb_worker.finished.connect(self._thumb_worker.deleteLater)
        self._thumb_thread.finished.connect(self._on_thumbnail_finished)
        self._thumb_thread.finished.connect(self._thumb_thread.deleteLater)
        self._thumb_thread.start()

    def exclude_selected(self):
        selected_items = list(self.thumbnail_list.selectedItems())
        if not selected_items:
            return
        for item in selected_items:
            path = item.data(Qt.ItemDataRole.UserRole)
            self.excluded_images.add(path)
        self.show_detected_thumbnails()
        remaining = self.thumbnail_list.count()
        self.status_bar.showMessage(f"🗂️ Excluded {len(selected_items)}. Remaining to move: {remaining}")

    def move_detected(self):
        if not self.folder_path or not self.detected_images:
            return
        remaining = [p for p in self.detected_images if p not in self.excluded_images]
        if not remaining:
            self.status_bar.showMessage("ℹ️ Nothing to move.")
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            moved = move_detected_images(remaining, self.folder_path)
            self.status_bar.showMessage(f"📦 Moved {moved} images to 'Whiteboards' folder")
            # Refresh both the folder view and detected results
            self.load_thumbnails(self.folder_path)
        except Exception as e:
            self.status_bar.showMessage(f"❌ Move failed: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_thumbnail_loaded(self, filepath, image):
        pixmap = QPixmap.fromImage(image)
        filename = os.path.basename(filepath)
        item = QListWidgetItem(QIcon(pixmap), filename)
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        self.thumbnail_list.addItem(item)

        has_items = self.thumbnail_list.count() > 0
        if self.btn_exclude_selected.isVisible():
            self.btn_exclude_selected.setEnabled(has_items)
            self.btn_move_all.setEnabled(has_items)

    def _on_thumbnail_finished(self):
        self._thumb_thread = None
        self._thumb_worker = None

    def _cancel_thumbnail_loading(self):
        if self._thumb_worker is not None:
            self._thumb_worker.stop()
        if self._thumb_thread is not None:
            self._thumb_thread.quit()
            self._thumb_thread.wait(100)

    def closeEvent(self, event):
        self._cancel_thumbnail_loading()
        super().closeEvent(event)


    def run(self):
        self.show()


# --- Run app directly ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhiteboardApp()
    window.run()
    sys.exit(app.exec())
