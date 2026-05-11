"""
core/ocr.py
Modul OCR untuk membaca teks plat kendaraan.
Menggunakan EasyOCR sebagai engine utama, pytesseract sebagai fallback.
"""

import re
import cv2
import numpy as np
from typing import Optional, Tuple


class PlateOCR:
    """
    OCR engine untuk membaca nomor plat kendaraan Indonesia.
    Mencoba EasyOCR terlebih dahulu, fallback ke pytesseract.
    """

    def __init__(self, use_gpu: bool = False):
        self._reader = None
        self._use_gpu = use_gpu
        self._engine = "none"
        self._init_engine()

    def _init_engine(self):
        """Inisialisasi OCR engine yang tersedia."""
        # Coba EasyOCR dulu
        try:
            import easyocr
            self._reader = easyocr.Reader(["en"], gpu=self._use_gpu, verbose=False)
            self._engine = "easyocr"
            print("[OCR] Menggunakan EasyOCR")
            return
        except ImportError:
            print("[OCR] EasyOCR tidak tersedia")

        # Fallback ke pytesseract
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._engine = "tesseract"
            print("[OCR] Menggunakan Tesseract")
            return
        except Exception:
            print("[OCR] Tesseract tidak tersedia")

        print("[OCR] Tidak ada engine OCR yang tersedia, hasil OCR akan kosong")

    def read(self, plate_img: np.ndarray) -> Tuple[str, float]:
        """
        Baca teks dari citra plat.

        Args:
            plate_img: citra plat yang sudah di-preprocess (grayscale atau BGR)

        Returns:
            (text, confidence) — text adalah teks yang terdeteksi,
            confidence adalah nilai kepercayaan 0.0–1.0
        """
        if self._engine == "easyocr":
            return self._read_easyocr(plate_img)
        elif self._engine == "tesseract":
            return self._read_tesseract(plate_img)
        else:
            return "", 0.0

    def _read_easyocr(self, img: np.ndarray) -> Tuple[str, float]:
        """Baca menggunakan EasyOCR."""
        try:
            # EasyOCR butuh BGR atau RGB
            if len(img.shape) == 2:
                img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                img_bgr = img

            results = self._reader.readtext(img_bgr, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ")
            if not results:
                return "", 0.0

            # Gabungkan semua teks yang terdeteksi
            texts = []
            confidences = []
            for (_, text, conf) in results:
                texts.append(text.upper())
                confidences.append(conf)

            combined = " ".join(texts).strip()
            avg_conf = sum(confidences) / len(confidences)
            return combined, avg_conf

        except Exception as e:
            print(f"[OCR EasyOCR Error] {e}")
            return "", 0.0

    def _read_tesseract(self, img: np.ndarray) -> Tuple[str, float]:
        """Baca menggunakan pytesseract."""
        try:
            import pytesseract

            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img

            # Config khusus plat: 1 baris, karakter alfanumerik
            config = (
                "--oem 3 --psm 8 "
                "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )
            text = pytesseract.image_to_string(gray, config=config).strip().upper()

            # Confidence dari data detail
            data = pytesseract.image_to_data(gray, config=config, output_type=pytesseract.Output.DICT)
            confs = [int(c) for c in data["conf"] if int(c) > 0]
            avg_conf = (sum(confs) / len(confs) / 100) if confs else 0.0

            return text, avg_conf

        except Exception as e:
            print(f"[OCR Tesseract Error] {e}")
            return "", 0.0

    @property
    def engine_name(self) -> str:
        return self._engine
