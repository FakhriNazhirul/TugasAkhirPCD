"""
ui/main_window.py
Jendela utama aplikasi deteksi plat kendaraan.
Layout: Toolbar | Camera Feed | Panel Hasil
"""

import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QComboBox, QSlider, QFrame,
    QStatusBar, QToolBar, QAction, QSpinBox, QGroupBox,
    QCheckBox, QSizePolicy
)
from PyQt5.QtGui import QFont, QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer, pyqtSlot

from core.camera_thread import CameraThread
from core.detector import PlateDetector
from core.ocr import PlateOCR
from core.classifier import VehicleClassifier
from ui.camera_widget import CameraWidget
from ui.result_widget import ResultWidget


STYLE = """
QMainWindow, QWidget {
    background-color: #0d0d1a;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
}
QGroupBox {
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 8px;
    font-size: 11px;
    color: #888;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QPushButton {
    background: #1e3a5f;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
}
QPushButton:hover { background: #2a5298; }
QPushButton:pressed { background: #1a2e6e; }
QPushButton:disabled { background: #222; color: #555; }
QComboBox {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 5px;
    padding: 4px 8px;
    color: #ccc;
}
QComboBox::drop-down { border: none; }
QSlider::groove:horizontal { background: #2a2a4a; height: 4px; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #4a90d9; width: 14px; height: 14px;
    border-radius: 7px; margin: -5px 0;
}
QStatusBar { background: #0a0a15; color: #888; font-size: 11px; }
QLabel { color: #ccc; }
"""


class MainWindow(QMainWindow):
    """Jendela utama aplikasi deteksi plat."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚗  Sistem Deteksi Plat Kendaraan Indonesia")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        # Core components
        self.camera_thread = CameraThread(camera_index=0)
        self.detector = PlateDetector()
        self.ocr = PlateOCR()
        self.classifier = VehicleClassifier()

        # State
        self._camera_running = False
        self._detection_active = True
        self._frame_skip = 0          # Counter untuk skip frame
        self._detect_every_n = 3      # Deteksi setiap N frame (hemat CPU)
        self._last_plates = []

        self.setStyleSheet(STYLE)
        self._build_ui()
        self._connect_signals()
        self._update_status("Siap. Tekan [Mulai Kamera] untuk memulai.")

    # ─── UI Builder ──────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(12)

        # Kiri: kamera + kontrol
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        # Toolbar kamera
        left_panel.addWidget(self._build_camera_toolbar())

        # Feed kamera
        self.camera_widget = CameraWidget()
        left_panel.addWidget(self.camera_widget, stretch=1)

        # Kontrol deteksi
        left_panel.addWidget(self._build_detection_controls())

        # Kanan: hasil deteksi
        self.result_widget = ResultWidget()
        self.result_widget.setFixedWidth(380)

        root.addLayout(left_panel, stretch=1)
        root.addWidget(self.result_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_engine_label = QLabel(f"OCR: {self.ocr.engine_name}")
        self.status_engine_label.setStyleSheet("color: #4a90d9; padding-right: 10px;")
        self.status_bar.addPermanentWidget(self.status_engine_label)

        self.status_fps_label = QLabel("FPS: --")
        self.status_fps_label.setStyleSheet("color: #888; padding-right: 10px;")
        self.status_bar.addPermanentWidget(self.status_fps_label)

        # Timer FPS counter
        self._fps_timer = QTimer()
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_counter = 0

    def _build_camera_toolbar(self) -> QWidget:
        """Baris kontrol kamera atas."""
        bar = QWidget()
        bar.setStyleSheet("background: #16213e; border-radius: 8px;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Judul
        title = QLabel("📹  Live Kamera")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        layout.addStretch()

        # Pilih kamera
        layout.addWidget(QLabel("Kamera:"))
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["Kamera 0 (Default)", "Kamera 1", "Kamera 2"])
        self.camera_combo.setFixedWidth(160)
        layout.addWidget(self.camera_combo)

        # Pilih cascade
        layout.addWidget(QLabel("Cascade:"))
        self.cascade_combo = QComboBox()
        available = self.detector.get_available_cascades()
        self.cascade_combo.addItems(available)
        self.cascade_combo.setCurrentText("plat-80-25stage.xml")
        self.cascade_combo.setFixedWidth(200)
        self.cascade_combo.currentTextChanged.connect(self._on_cascade_changed)
        layout.addWidget(self.cascade_combo)

        # Tombol mulai/stop
        self.btn_start = QPushButton("▶  Mulai Kamera")
        self.btn_start.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: #2a7a4a; color: white; border: none;
                border-radius: 6px; padding: 8px 20px;
            }
            QPushButton:hover { background: #3a9a5a; }
        """)
        self.btn_start.clicked.connect(self._toggle_camera)
        layout.addWidget(self.btn_start)

        return bar

    def _build_detection_controls(self) -> QGroupBox:
        """Panel kontrol parameter deteksi."""
        group = QGroupBox("Parameter Deteksi")
        layout = QHBoxLayout(group)
        layout.setSpacing(16)

        # Scale factor
        sf_box = QVBoxLayout()
        sf_box.addWidget(QLabel("Scale Factor"))
        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setRange(110, 150)
        self.slider_scale.setValue(110)
        self.slider_scale.setFixedWidth(120)
        self.scale_label = QLabel("1.10")
        self.slider_scale.valueChanged.connect(
            lambda v: self.scale_label.setText(f"{v/100:.2f}")
        )
        sf_box.addWidget(self.slider_scale)
        sf_box.addWidget(self.scale_label)
        layout.addLayout(sf_box)

        # Min neighbors
        mn_box = QVBoxLayout()
        mn_box.addWidget(QLabel("Min Neighbors"))
        self.spin_neighbors = QSpinBox()
        self.spin_neighbors.setRange(1, 10)
        self.spin_neighbors.setValue(4)
        self.spin_neighbors.setFixedWidth(80)
        mn_box.addWidget(self.spin_neighbors)
        layout.addLayout(mn_box)

        # Deteksi setiap N frame
        nf_box = QVBoxLayout()
        nf_box.addWidget(QLabel("Deteksi per N Frame"))
        self.spin_skip = QSpinBox()
        self.spin_skip.setRange(1, 10)
        self.spin_skip.setValue(3)
        self.spin_skip.setFixedWidth(80)
        nf_box.addWidget(self.spin_skip)
        layout.addLayout(nf_box)

        layout.addStretch()

        # Toggle deteksi
        self.chk_detect = QCheckBox("Aktifkan Deteksi")
        self.chk_detect.setChecked(True)
        self.chk_detect.stateChanged.connect(
            lambda s: setattr(self, "_detection_active", bool(s))
        )
        layout.addWidget(self.chk_detect)

        # Tombol capture manual
        self.btn_capture = QPushButton("📷  Capture & OCR")
        self.btn_capture.setEnabled(False)
        self.btn_capture.clicked.connect(self._manual_capture)
        layout.addWidget(self.btn_capture)

        return group

    # ─── Signals ─────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self.camera_thread.frame_ready.connect(self._on_frame)
        self.camera_thread.camera_error.connect(self._on_camera_error)
        self.camera_thread.status_changed.connect(self._update_status)

    # ─── Slots ───────────────────────────────────────────────────────────────

    @pyqtSlot(np.ndarray)
    def _on_frame(self, frame: np.ndarray):
        """Terima frame baru dari CameraThread."""
        self._fps_counter += 1
        self._frame_skip = (self._frame_skip + 1) % self.spin_skip.value()

        # Jalankan deteksi setiap N frame
        if self._detection_active and self._frame_skip == 0:
            scale = self.slider_scale.value() / 100.0
            neighbors = self.spin_neighbors.value()
            plates = self.detector.detect(frame, scale_factor=scale, min_neighbors=neighbors)
            self._last_plates = plates

            # Jika ada deteksi baru, jalankan OCR otomatis
            if plates:
                self._run_ocr_on_plates(frame, plates)

        self.camera_widget.set_detections(self._last_plates)
        self.camera_widget.update_frame(frame)

    def _run_ocr_on_plates(self, frame: np.ndarray, plates: list):
        """Jalankan OCR pada semua plat yang terdeteksi."""
        for rect in plates:
            cropped = self.detector.crop_plate(frame, rect)
            if cropped.size == 0:
                continue
            preprocessed = self.detector.preprocess_plate(cropped)
            text, conf = self.ocr.read(preprocessed)

            if text and conf > 0.3:  # Threshold confidence minimal
                info = self.classifier.classify(text, conf)
                self.result_widget.add_result(info)

    @pyqtSlot()
    def _manual_capture(self):
        """Capture frame saat ini dan paksa OCR."""
        # Akan diimplementasikan: ambil frame terakhir dari camera_thread
        self._update_status("Capture manual — fitur segera hadir")

    @pyqtSlot(str)
    def _on_camera_error(self, msg: str):
        self.camera_widget.show_no_camera()
        self._update_status(f"⚠️  {msg}")
        self._set_camera_state(False)

    @pyqtSlot(str)
    def _on_cascade_changed(self, filename: str):
        self.detector.switch_cascade(filename)
        self._update_status(f"Cascade diganti ke: {filename}")

    def _toggle_camera(self):
        if self._camera_running:
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self):
        idx = self.camera_combo.currentIndex()
        self.camera_thread.set_camera(idx)
        self.camera_thread.start()
        self._set_camera_state(True)
        self._fps_timer.start(1000)

    def _stop_camera(self):
        self.camera_thread.stop()
        self.camera_widget.show_no_camera()
        self._set_camera_state(False)
        self._fps_timer.stop()
        self._last_plates = []

    def _set_camera_state(self, running: bool):
        self._camera_running = running
        self.btn_capture.setEnabled(running)
        if running:
            self.btn_start.setText("⏹  Stop Kamera")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: #7a2a2a; color: white; border: none;
                    border-radius: 6px; padding: 8px 20px;
                }
                QPushButton:hover { background: #9a3a3a; }
            """)
        else:
            self.btn_start.setText("▶  Mulai Kamera")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background: #2a7a4a; color: white; border: none;
                    border-radius: 6px; padding: 8px 20px;
                }
                QPushButton:hover { background: #3a9a5a; }
            """)

    def _update_fps(self):
        self.status_fps_label.setText(f"FPS: {self._fps_counter}")
        self._fps_counter = 0

    def _update_status(self, msg: str):
        self.status_bar.showMessage(msg)

    def closeEvent(self, event):
        """Pastikan thread kamera dihentikan saat aplikasi ditutup."""
        self._stop_camera()
        super().closeEvent(event)
