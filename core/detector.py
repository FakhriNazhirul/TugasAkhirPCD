"""
core/detector.py
Modul deteksi plat kendaraan menggunakan Haar Cascade OpenCV.
Mendukung multiple cascade files untuk akurasi lebih baik.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional


CASCADE_DIR = Path(__file__).parent.parent / "assets" / "cascades"

# Daftar cascade plat dengan prioritas (lebih banyak stage = lebih akurat tapi lebih lambat)
CASCADE_FILES = [
    "plat-80-25stage.xml",   # Paling akurat
    "plat-40-25stage.xml",
    "plat-30-20stage.xml",
    "plat-20-20stage.xml",
    "plat-20-10stage.xml",
    "plat-5-25stage.xml",
    "plat-5-21stage.xml",
    "plat-5-17stage.xml",
    "plat-5-10stage.xml",
    "plat.xml",              # Fallback
]


class PlateDetector:
    """Detektor plat kendaraan menggunakan Haar Cascade."""

    def __init__(self, cascade_file: str = "plat-80-25stage.xml"):
        self.cascade_path = CASCADE_DIR / cascade_file
        self.cascade = self._load_cascade(str(self.cascade_path))
        self.fallback_cascade = self._load_cascade(
            str(CASCADE_DIR / "plat.xml")
        )

    def _load_cascade(self, path: str) -> Optional[cv2.CascadeClassifier]:
        """Load cascade classifier dari file XML."""
        cascade = cv2.CascadeClassifier(path)
        if cascade.empty():
            print(f"[WARNING] Gagal load cascade: {path}")
            return None
        print(f"[INFO] Cascade berhasil dimuat: {path}")
        return cascade

    def detect(
        self,
        frame: np.ndarray,
        scale_factor: float = 1.1,
        min_neighbors: int = 4,
        min_size: Tuple[int, int] = (60, 20),
        max_size: Tuple[int, int] = (400, 150),
    ) -> List[Tuple[int, int, int, int]]:
        """
        Deteksi plat pada frame.

        Returns:
            List of (x, y, w, h) rectangles
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        plates = []

        # Coba cascade utama
        if self.cascade and not self.cascade.empty():
            plates = self.cascade.detectMultiScale(
                gray,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors,
                minSize=min_size,
                maxSize=max_size,
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

        # Fallback ke cascade dasar jika tidak ada deteksi
        if len(plates) == 0 and self.fallback_cascade and not self.fallback_cascade.empty():
            plates = self.fallback_cascade.detectMultiScale(
                gray,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors - 1,
                minSize=min_size,
                maxSize=max_size,
            )

        return list(plates) if len(plates) > 0 else []

    def crop_plate(
        self,
        frame: np.ndarray,
        rect: Tuple[int, int, int, int],
        padding: int = 5,
    ) -> np.ndarray:
        """Crop area plat dari frame dengan sedikit padding."""
        x, y, w, h = rect
        h_frame, w_frame = frame.shape[:2]

        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(w_frame, x + w + padding)
        y2 = min(h_frame, y + h + padding)

        return frame[y1:y2, x1:x2]

    def preprocess_plate(self, plate_img: np.ndarray) -> np.ndarray:
        """
        Pre-processing citra plat untuk OCR:
        resize, grayscale, threshold, denoise.
        """
        # Resize ke tinggi standar
        target_h = 60
        scale = target_h / plate_img.shape[0]
        new_w = int(plate_img.shape[1] * scale)
        resized = cv2.resize(plate_img, (new_w, target_h), interpolation=cv2.INTER_CUBIC)

        # Grayscale
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Morphological closing untuk sambung karakter
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        return closed

    @staticmethod
    def draw_detections(
        frame: np.ndarray,
        plates: List[Tuple[int, int, int, int]],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
    ) -> np.ndarray:
        """Gambar kotak deteksi pada frame."""
        result = frame.copy()
        for (x, y, w, h) in plates:
            cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
            cv2.putText(
                result, "PLAT",
                (x, y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                color, 1, cv2.LINE_AA
            )
        return result

    def get_available_cascades(self) -> List[str]:
        """Return list cascade yang tersedia."""
        available = []
        for f in CASCADE_FILES:
            if (CASCADE_DIR / f).exists():
                available.append(f)
        return available

    def switch_cascade(self, cascade_file: str):
        """Ganti cascade yang digunakan."""
        new_cascade = self._load_cascade(str(CASCADE_DIR / cascade_file))
        if new_cascade and not new_cascade.empty():
            self.cascade = new_cascade
            self.cascade_path = CASCADE_DIR / cascade_file
