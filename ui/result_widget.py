"""
ui/result_widget.py
Panel hasil deteksi: menampilkan nomor plat, wilayah, kategori, jenis kendaraan.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy, QPushButton
)
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from core.classifier import VehicleInfo


CATEGORY_COLORS = {
    "Kendaraan Pribadi":    ("#2d6a4f", "#40916c"),   # hijau
    "Angkutan Umum":        ("#1d3557", "#457b9d"),   # biru
    "Dinas Pemerintah":     ("#7b2d00", "#e63900"),   # merah
    "Diplomatik / Konsuler":("#4a1942", "#9b5de5"),   # ungu
    "Tidak Dikenali":       ("#333333", "#666666"),   # abu
}


class PlateResultCard(QFrame):
    """Kartu hasil deteksi satu plat."""

    def __init__(self, info: VehicleInfo, parent=None):
        super().__init__(parent)
        self.info = info
        self._build_ui()

    def _build_ui(self):
        bg_dark, bg_light = CATEGORY_COLORS.get(
            self.info.vehicle_category,
            ("#333333", "#666666")
        )

        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bg_dark}, stop:1 {bg_light}
                );
                border-radius: 10px;
                padding: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # Nomor plat (besar)
        plate_label = QLabel(
            self.info.plate_number if self.info.is_valid else self.info.raw_text
        )
        plate_label.setFont(QFont("Courier New", 22, QFont.Bold))
        plate_label.setAlignment(Qt.AlignCenter)
        plate_label.setStyleSheet("color: white; letter-spacing: 4px;")
        layout.addWidget(plate_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: rgba(255,255,255,0.3);")
        layout.addWidget(sep)

        # Grid info
        grid = QHBoxLayout()
        grid.setSpacing(10)

        grid.addWidget(self._info_block("🗺️ Wilayah", self.info.region_name))
        grid.addWidget(self._info_block("🚗 Kategori", self.info.vehicle_category))
        grid.addWidget(self._info_block("🔖 Jenis", self.info.vehicle_type))
        grid.addWidget(self._info_block("🎯 Akurasi", f"{self.info.confidence * 100:.1f}%"))

        layout.addLayout(grid)

    def _info_block(self, title: str, value: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: rgba(0,0,0,0.3); border-radius: 6px;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(2)

        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 8))
        t.setStyleSheet("color: rgba(255,255,255,0.7);")
        vl.addWidget(t)

        v = QLabel(value)
        v.setFont(QFont("Segoe UI", 9, QFont.Bold))
        v.setStyleSheet("color: white;")
        v.setWordWrap(True)
        vl.addWidget(v)

        return w


class ResultWidget(QWidget):
    """
    Panel kanan — menampilkan riwayat hasil deteksi plat.
    Riwayat bisa di-scroll, entri paling baru di atas.
    """

    cleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: list[VehicleInfo] = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # Header
        header = QWidget()
        header.setStyleSheet("background: #16213e; border-radius: 8px;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 8, 12, 8)

        title = QLabel("📋  Hasil Deteksi")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #e0e0e0;")
        hl.addWidget(title)

        hl.addStretch()

        self.count_label = QLabel("0 plat")
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet("color: #888;")
        hl.addWidget(self.count_label)

        clear_btn = QPushButton("Bersihkan")
        clear_btn.setFont(QFont("Segoe UI", 9))
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #e63946; color: white;
                border: none; border-radius: 5px;
                padding: 4px 10px;
            }
            QPushButton:hover { background: #c1121f; }
        """)
        clear_btn.clicked.connect(self.clear_results)
        hl.addWidget(clear_btn)

        root.addWidget(header)

        # Scroll area untuk kartu hasil
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 6px; background: #111; }
            QScrollBar::handle:vertical { background: #444; border-radius: 3px; }
        """)

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        self.scroll.setWidget(self.cards_container)
        root.addWidget(self.scroll)

        # Placeholder ketika belum ada hasil
        self._placeholder = QLabel(
            "Belum ada deteksi\n\nArahkan kamera ke plat kendaraan"
        )
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setFont(QFont("Segoe UI", 11))
        self._placeholder.setStyleSheet(
            "color: #555; background: #0f0f23; border-radius: 8px; padding: 30px;"
        )
        root.addWidget(self._placeholder)

    def add_result(self, info: VehicleInfo):
        """Tambahkan hasil deteksi baru ke daftar."""
        self._results.insert(0, info)
        self._placeholder.hide()

        card = PlateResultCard(info)
        # Masukkan di posisi 0 (sebelum stretch)
        self.cards_layout.insertWidget(0, card)

        self.count_label.setText(f"{len(self._results)} plat")

        # Auto-scroll ke atas
        self.scroll.verticalScrollBar().setValue(0)

    def clear_results(self):
        """Hapus semua hasil."""
        self._results.clear()
        # Hapus semua kartu
        while self.cards_layout.count() > 1:  # sisakan stretch
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.count_label.setText("0 plat")
        self._placeholder.show()
        self.cleared.emit()

    def get_latest(self) -> VehicleInfo | None:
        return self._results[0] if self._results else None
