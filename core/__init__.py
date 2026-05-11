"""core package — Komponen pemrosesan utama."""
from .detector import PlateDetector
from .ocr import PlateOCR
from .classifier import VehicleClassifier, VehicleInfo
from .camera_thread import CameraThread

__all__ = ["PlateDetector", "PlateOCR", "VehicleClassifier", "VehicleInfo", "CameraThread"]
