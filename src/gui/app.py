import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QFileDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QFrame, QStatusBar, QAbstractItemView, QProgressBar, QSlider, QSizePolicy, QComboBox
)
from PyQt6.QtGui import QPixmap, QIcon, QImage, QImageReader, QFont, QPainter, QGuiApplication, QRegion
from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve, QEvent, QPoint, QTimer

# Add the project root to Python path so we can import from src.detection
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.detection.detection_module import detect_whiteboards, move_detected_images


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


class StyledButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._shadow = None
        self._hover_anim = None
        self._leave_anim = None
        self._ensure_shadow()
        self.installEventFilter(self)

    def _ensure_shadow(self):
        # Lazy-import to avoid effect when parent is None
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setColor(Qt.GlobalColor.black)
        self._shadow.setOffset(0, 6)
        self._shadow.setBlurRadius(12)
        self.setGraphicsEffect(self._shadow)

    def eventFilter(self, obj, event):
        if obj is self:
            if event.type() == QEvent.Type.Enter:
                self._animate_shadow(blur_end=28, y_offset_end=12)
            elif event.type() == QEvent.Type.Leave:
                self._animate_shadow(blur_end=12, y_offset_end=6)
        return super().eventFilter(obj, event)

    def _animate_shadow(self, blur_end: int, y_offset_end: int):
        if self._shadow is None:
            return
        # Animate blur radius
        blur_anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        blur_anim.setDuration(180)
        blur_anim.setStartValue(self._shadow.blurRadius())
        blur_anim.setEndValue(blur_end)
        blur_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # Animate vertical offset
        offset_anim = QPropertyAnimation(self._shadow, b"yOffset", self)
        offset_anim.setDuration(180)
        offset_anim.setStartValue(self._shadow.yOffset())
        offset_anim.setEndValue(y_offset_end)
        offset_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # Start both
        blur_anim.start()
        offset_anim.start()


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0,0,0,140);")
        self._container = QWidget(self)
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        self._label = QLabel("Working...")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: white; font-size: 16px;")
        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(10)
        self._bar.setStyleSheet(
            "QProgressBar { background: rgba(255,255,255,0.15); border-radius: 6px; }"
            "QProgressBar::chunk { background: #8ab4f8; border-radius: 6px; }"
        )
        layout.addWidget(self._label)
        layout.addWidget(self._bar)
        self.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())
            # center container to 320px width
            w = min(360, self.width() - 40)
            self._container.setFixedWidth(w)
            self._container.adjustSize()
            self._container.move(
                (self.width() - self._container.width()) // 2,
                (self.height() - self._container.height()) // 2,
            )

    def show_overlay(self, text: str = "Working..."):
        self._label.setText(text)
        self.show()
        QGuiApplication.processEvents()

    def hide_overlay(self):
        self.hide()


class ToastNotification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._label = QLabel("", self)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(
            "background: rgba(32,33,36,230); color: white; border-radius: 10px; padding: 12px 16px;"
        )
        self._label.setMinimumWidth(240)
        self._fade_in = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_out = QPropertyAnimation(self, b"windowOpacity", self)
        self.setWindowOpacity(0.0)
        self.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._label.resize(self.size())

    def show_toast(self, text: str, timeout_ms: int = 2200):
        self._label.setText(text)
        self.adjustSize()
        # position at bottom-right inside parent
        if self.parent() is not None:
            parent_rect = self.parent().rect()
            margin = 16
            desired_width = max(260, min(420, self.parent().width() // 3))
            self.resize(desired_width, self.sizeHint().height())
            x = parent_rect.right() - self.width() - margin
            y = parent_rect.bottom() - self.height() - margin - 24
            self.move(self.parent().mapToGlobal(QPoint(x, y)))
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        # Fade in
        self._fade_in.stop()
        self._fade_in.setDuration(200)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_in.start()
        # Auto fade out
        def _fade_out():
            self._fade_out.stop()
            self._fade_out.setDuration(250)
            self._fade_out.setStartValue(1.0)
            self._fade_out.setEndValue(0.0)
            self._fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
            self._fade_out.start()
            self._fade_out.finished.connect(self.hide)
        QTimer.singleShot(timeout_ms, _fade_out)


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
        self.models_dir = os.path.abspath(".")
        self.selected_model_path = None

        # --- Central Widget ---
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 20, 18, 20)
        sidebar_layout.setSpacing(14)

        brand = QLabel("🖼️📚 Whiteboard Detection")
        brand.setObjectName("brand")
        brand.setStyleSheet("font-size: 18px; font-weight: 600; color: #e8eaed;")

        subtitle = QLabel("Detects Whiteboard Images in a Folders")
        subtitle.setStyleSheet("color: #aab0b7;")

        self.btn_select_folder = StyledButton("📂 Select Folder")
        self.btn_select_folder.clicked.connect(self.select_folder)

        self.btn_run_detection = StyledButton("🚀 Run Detection")
        self.btn_run_detection.clicked.connect(self.run_detection)
        self.btn_run_detection.setEnabled(False)

        # Threshold control
        # Model selection
        model_title = QLabel("Model (.pt)")
        model_title.setStyleSheet("color: #aab0b7; font-size: 12px;")
        model_row = QHBoxLayout()
        model_row.setSpacing(8)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(False)
        self.model_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.model_combo.setStyleSheet(
            "QComboBox { background: #2a2d31; border: 1px solid rgba(255,255,255,0.08);"
            "color: #e8eaed; border-radius: 8px; padding: 6px 8px; }"
            "QComboBox QAbstractItemView { background: #1f2226; color: #e8eaed;"
            "selection-background-color: rgba(138,180,248,0.18);"
            "selection-color: #e8eaed; border: 1px solid rgba(255,255,255,0.08); }"
        )
        self.btn_pick_models = StyledButton("📁")
        self.btn_pick_models.setToolTip("Pick models directory")
        self.btn_pick_models.setFixedSize(30, 30)
        self.btn_pick_models.setStyleSheet("font-size: 14px; padding: 0; min-width: 30px; min-height: 30px;")
        self.btn_pick_models.clicked.connect(self.pick_models_dir)
        model_row.addWidget(self.model_combo, 1)
        model_row.addWidget(self.btn_pick_models, 0)

        self._populate_models()

        threshold_title = QLabel("Confidence Threshold")
        threshold_title.setStyleSheet("color: #aab0b7; font-size: 12px;")
        self.threshold_value_label = QLabel("50%")
        self.threshold_value_label.setStyleSheet("color: #e8eaed; font-weight: 600;")
        threshold_header = QHBoxLayout()
        threshold_header.addWidget(threshold_title)
        threshold_header.addStretch()
        threshold_header.addWidget(self.threshold_value_label)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(10, 95)
        self.threshold_slider.setSingleStep(1)
        self.threshold_slider.setValue(50)
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_value_label.setText(f"{v}%")
        )
        self.threshold_slider.setStyleSheet(
            "QSlider::groove:horizontal { height: 6px; background: rgba(255,255,255,0.12); border-radius: 4px; }"
            "QSlider::sub-page:horizontal { background: #8ab4f8; border-radius: 4px; }"
            "QSlider::handle:horizontal { background: white; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }"
            "QSlider::handle:horizontal:hover { background: #dfe6ff; }"
        )

        self.btn_exclude_selected = StyledButton("🚫 Exclude Selected")
        self.btn_exclude_selected.clicked.connect(self.exclude_selected)
        self.btn_exclude_selected.setVisible(False)
        self.btn_exclude_selected.setEnabled(False)

        self.btn_move_all = StyledButton("📦 Move Into Whiteboards ")
        self.btn_move_all.clicked.connect(self.move_detected)
        self.btn_move_all.setVisible(False)
        self.btn_move_all.setEnabled(False)

        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(self.btn_select_folder)
        sidebar_layout.addWidget(self.btn_run_detection)
        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(model_title)
        sidebar_layout.addLayout(model_row)
        sidebar_layout.addSpacing(12)
        sidebar_layout.addLayout(threshold_header)
        sidebar_layout.addWidget(self.threshold_slider)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.btn_exclude_selected)
        sidebar_layout.addWidget(self.btn_move_all)

        # --- Content Area ---
        content = QFrame()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)

        hero = QFrame()
        hero.setObjectName("hero")
        hero.setMaximumHeight(92)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(14, 10, 14, 10)
        hero_top = QHBoxLayout()
        hero_top.setContentsMargins(0, 0, 0, 0)
        hero_top.setSpacing(8)
        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(2)
        hero_title = QLabel("Whiteboard Detection")
        hero_title.setStyleSheet("font-size: 18px; font-weight: 700;")
        hero_sub = QLabel("Select a folder, set confidence, and run detection.")
        hero_sub.setStyleSheet("color: #aab0b7;")
        title_box.addWidget(hero_title)
        title_box.addWidget(hero_sub)
        hero_top.addLayout(title_box, 1)
        self.btn_refresh = StyledButton("⟳")
        self.btn_refresh.setToolTip("Refresh images")
        self.btn_refresh.setFixedSize(30, 30)
        self.btn_refresh.setStyleSheet("font-size: 14px; padding: 0; min-width: 30px; min-height: 30px;")
        self.btn_refresh.clicked.connect(self.refresh_images)
        hero_top.addWidget(self.btn_refresh, 0)
        hero_layout.addLayout(hero_top)
        content_layout.addWidget(hero, 0)

        # --- Thumbnails Grid ---
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.thumbnail_list.setIconSize(QSize(150, 150))
        self.thumbnail_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.thumbnail_list.setSpacing(15)
        self.thumbnail_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.thumbnail_list.setStyleSheet("""
            QListWidget {
                outline: none;
            }
            QListWidget::item {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 10px;
                margin: 5px;
                color: #e8eaed;
            }
            QListWidget::item:hover {
                background-color: rgba(138,180,248,0.08);
                border-color: rgba(138,180,248,0.35);
            }
            QListWidget::item:selected {
                background-color: rgba(138,180,248,0.18);
                border-color: rgba(138,180,248,0.6);
            }
        """)

        # Card for list
        list_card = QFrame()
        list_card.setObjectName("listCard")
        list_card_layout = QVBoxLayout(list_card)
        list_card_layout.setContentsMargins(8, 8, 8, 8)
        list_card_layout.addWidget(self.thumbnail_list)
        content_layout.addWidget(list_card, 1)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content, 1)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # --- Global Stylesheet (dark modern theme) ---
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f1012, stop:1 #1a1c20);
                color: #e8eaed;
                font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
            }
            QFrame#sidebar {
                background: rgba(255,255,255,0.04);
                border-right: 1px solid rgba(255,255,255,0.06);
                border-top-right-radius: 14px;
                border-bottom-right-radius: 14px;
                backdrop-filter: blur(10px);
            }
            QFrame#content {
                background: transparent;
            }
            QFrame#hero, QFrame#listCard {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 14px;
                backdrop-filter: blur(6px);
            }
            QPushButton {
                background-color: #2a2d31;
                border: 1px solid rgba(255,255,255,0.08);
                color: #e8eaed;
                padding: 10px 18px;
                font-size: 14px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #33373c;
                border-color: rgba(138,180,248,0.35);
            }
            QPushButton:pressed {
                background-color: #272a2e;
            }
            QPushButton:disabled {
                background-color: #1a1c20;
                color: #777;
                border-color: rgba(255,255,255,0.04);
            }
            QStatusBar {
                background-color: #1a1c20;
                color: #aab0b7;
                border-top: 1px solid rgba(255,255,255,0.06);
            }
            QWidget#centralWidget, QWidget {
                background: transparent;
            }
            QListWidget {
                background: transparent;
            }
        """)

        # Overlay and toast
        self._overlay = LoadingOverlay(self)
        self._toast = ToastNotification(self)

    # --- Folder selection ---
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.folder_path = folder
            self.btn_run_detection.setEnabled(True)
            self.status_bar.showMessage(f"Selected folder: {folder}")
            self._toast.show_toast("Folder selected. Thumbnails loading…")
            self.load_thumbnails(folder)

    def pick_models_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Models Folder", self.models_dir)
        if folder:
            self.models_dir = folder
            self._populate_models()
            self._toast.show_toast("Models list updated.")

    def _populate_models(self):
        self.model_combo.clear()
        pt_files = []
        for root, _, files in os.walk(self.models_dir):
            for f in files:
                if f.lower().endswith('.pt'):
                    pt_files.append(os.path.join(root, f))
        pt_files.sort()
        if not pt_files:
            self.model_combo.addItem("No .pt models found", userData=None)
            self.selected_model_path = None
            return
        for path in pt_files:
            display = os.path.relpath(path, self.models_dir)
            self.model_combo.addItem(display, userData=path)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        # Initialize selection
        self._on_model_changed(self.model_combo.currentIndex())

    def _on_model_changed(self, idx: int):
        data = self.model_combo.itemData(idx)
        self.selected_model_path = data if isinstance(data, str) else None

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
        self._overlay.show_overlay("Running detection…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            # Map slider value (10-95) to 0.10 - 0.95
            conf_threshold = float(self.threshold_slider.value()) / 100.0
            kwargs = {"conf_threshold": conf_threshold}
            if self.selected_model_path:
                kwargs["model_path"] = self.selected_model_path
            self.detect_result = detect_whiteboards(self.folder_path, **kwargs)
            self.detected_images = list(self.detect_result.get("detected_images", []))
            self.excluded_images = set()
            self.show_detected_thumbnails()
            stats = self.detect_result.get("stats", {})
            self.status_bar.showMessage(
                f"✅ Detection complete: {stats.get('detected_count', 0)}/{stats.get('total_images', 0)} images contain whiteboards"
            )
            self._toast.show_toast("Detection complete.")
        except Exception as e:
            self.status_bar.showMessage(f"❌ Detection failed: {e}")
            self._toast.show_toast("Detection failed.")
        finally:
            QApplication.restoreOverrideCursor()
            self._overlay.hide_overlay()

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
            self._toast.show_toast("Nothing to move.")
            return
        self._overlay.show_overlay("Moving images…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            moved = move_detected_images(remaining, self.folder_path)
            self.status_bar.showMessage(f"📦 Moved {moved} images to 'Whiteboards' folder")
            self._toast.show_toast(f"Moved {moved} images.")
            # Refresh both the folder view and detected results
            self.load_thumbnails(self.folder_path)
        except Exception as e:
            self.status_bar.showMessage(f"❌ Move failed: {e}")
            self._toast.show_toast("Move failed.")
        finally:
            QApplication.restoreOverrideCursor()
            self._overlay.hide_overlay()

    def _on_thumbnail_loaded(self, filepath, image):
        pixmap = QPixmap.fromImage(image)
        filename = os.path.basename(filepath)
        # Append confidence if available
        conf_map = None
        if isinstance(self.detect_result, dict):
            conf_map = self.detect_result.get("image_confidences")
        label_text = filename
        if conf_map and filepath in conf_map:
            conf_pct = int(round(conf_map[filepath] * 100))
            label_text = f"{filename}\nConfidence: {conf_pct}%"
        item = QListWidgetItem(QIcon(pixmap), label_text)
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
        # Subtle window fade-in
        self.setWindowOpacity(0.0)
        self.show()
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()

    def refresh_images(self):
        if self.folder_path is None:
            self._toast.show_toast("No folder selected.")
            return
        # If detection results are showing (exclude/move buttons visible), refresh that view
        if self.btn_exclude_selected.isVisible():
            self.show_detected_thumbnails()
            self.status_bar.showMessage("🔄 Refreshed detected thumbnails.")
        else:
            self.load_thumbnails(self.folder_path)
            self.status_bar.showMessage("🔄 Refreshed folder thumbnails.")


# --- Run app directly ---
if __name__ == "__main__":
    def launch_whiteboard_gui():
        existing = QApplication.instance()
        app = existing if existing is not None else QApplication(sys.argv)
        window = WhiteboardApp()
        window.run()
        return app.exec()

    sys.exit(launch_whiteboard_gui())
