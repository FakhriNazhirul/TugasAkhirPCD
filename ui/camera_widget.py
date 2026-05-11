"""
ui/camera_widget.py
Widget tampilan live kamera dengan overlay deteksi plat.
"""

import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QRect


class CameraWidget(QLabel):
    """
    Widget untuk menampilkan feed kamera secara live.
    Mendukung overlay kotak deteksi plat dengan animasi.
    """

    # Sinyal ketika plat diklik
    plate_clicked = pyqtSignal(int, int, int, int)  # x, y, w, h

    def __init__(self, parent=None):
        super().__init__(parent)
        self._detections = []          # List of (x, y, w, h)
        self._frame_size = (1280, 720) # Ukuran frame asli
        self._highlight_idx = -1       # Index deteksi yang di-highlight
        self._show_grid = False

        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 360)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background-color: #1a1a2e; border-radius: 8px;")

        # Placeholder text
        self.setText("📷  Kamera belum aktif\nTekan [Mulai Kamera]")
        self.setFont(QFont("Segoe UI", 14))
        self.setStyleSheet(
            "QLabel { background-color: #1a1a2e; color: #666; "
            "border-radius: 8px; border: 2px dashed #333; }"
        )

    def update_frame(self, frame: np.ndarray):
        """Update tampilan dengan frame baru dari kamera."""
        self._frame_size = (frame.shape[1], frame.shape[0])

        # Gambar overlay deteksi langsung pada frame
        display_frame = self._draw_detections_on_frame(frame)

        # Konversi ke QPixmap
        rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        # Scale sesuai widget dengan mempertahankan aspect ratio
        scaled = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.setPixmap(scaled)
        self.setStyleSheet(
            "QLabel { background-color: #1a1a2e; border-radius: 8px; }"
        )

    def _draw_detections_on_frame(self, frame: np.ndarray) -> np.ndarray:
        """Gambar kotak deteksi di atas frame."""
        result = frame.copy()
        for i, (x, y, w, h) in enumerate(self._detections):
            color = (0, 255, 80) if i == self._highlight_idx else (0, 200, 255)
            thickness = 3 if i == self._highlight_idx else 2

            # Kotak deteksi
            cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)

            # Label
            label = f"PLAT #{i + 1}"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(result, (x, y - lh - 10), (x + lw + 6, y), color, -1)
            cv2.putText(
                result, label,
                (x + 3, y - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (0, 0, 0), 1, cv2.LINE_AA,
            )

            # Sudut kotak (corner decoration)
            cl = 12  # corner length
            cv2.line(result, (x, y), (x + cl, y), color, 3)
            cv2.line(result, (x, y), (x, y + cl), color, 3)
            cv2.line(result, (x + w, y), (x + w - cl, y), color, 3)
            cv2.line(result, (x + w, y), (x + w, y + cl), color, 3)
            cv2.line(result, (x, y + h), (x + cl, y + h), color, 3)
            cv2.line(result, (x, y + h), (x, y + h - cl), color, 3)
            cv2.line(result, (x + w, y + h), (x + w - cl, y + h), color, 3)
            cv2.line(result, (x + w, y + h), (x + w, y + h - cl), color, 3)

        return result

    def set_detections(self, detections: list):
        """Set daftar deteksi plat. Format: list of (x, y, w, h)."""
        self._detections = detections

    def set_highlight(self, index: int):
        """Highlight deteksi tertentu."""
        self._highlight_idx = index

    def set_show_grid(self, show: bool):
        self._show_grid = show

    def show_no_camera(self):
        """Tampilkan placeholder ketika kamera mati."""
        self.clear()
        self.setText("📷  Kamera tidak aktif\nTekan [Mulai Kamera]")
        self.setStyleSheet(
            "QLabel { background-color: #1a1a2e; color: #666; "
            "border-radius: 8px; border: 2px dashed #333; font-size: 14px; }"
        )
