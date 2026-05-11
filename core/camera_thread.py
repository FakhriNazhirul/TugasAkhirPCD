"""
core/camera_thread.py
QThread untuk mengambil frame kamera secara live tanpa memblokir UI.
"""

import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage


class CameraThread(QThread):
    """
    Thread yang membaca frame dari kamera secara terus-menerus
    dan memancarkan sinyal ke UI thread.
    """

    # Sinyal: frame BGR as numpy array
    frame_ready = pyqtSignal(np.ndarray)
    # Sinyal: error message
    camera_error = pyqtSignal(str)
    # Sinyal: status kamera
    status_changed = pyqtSignal(str)

    def __init__(self, camera_index: int = 0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self._running = False
        self._cap: cv2.VideoCapture = None
        self.fps_target = 30

    def run(self):
        """Main loop thread — baca frame dari kamera."""
        self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            self.camera_error.emit(
                f"Tidak dapat membuka kamera (index {self.camera_index}). "
                "Pastikan kamera terhubung."
            )
            return

        # Set resolusi
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps_target)

        self._running = True
        self.status_changed.emit("Kamera aktif")

        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                self.camera_error.emit("Gagal membaca frame dari kamera.")
                break

            self.frame_ready.emit(frame)
            # Throttle agar tidak terlalu cepat
            self.msleep(1000 // self.fps_target)

        self._cap.release()
        self.status_changed.emit("Kamera dimatikan")

    def stop(self):
        """Hentikan thread dengan aman."""
        self._running = False
        self.wait(2000)  # Tunggu maksimal 2 detik

    def set_camera(self, index: int):
        """Ganti kamera (harus stop dulu)."""
        self.camera_index = index

    @staticmethod
    def numpy_to_qimage(frame: np.ndarray) -> QImage:
        """Konversi frame numpy BGR ke QImage untuk ditampilkan di PyQt5."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        return QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
