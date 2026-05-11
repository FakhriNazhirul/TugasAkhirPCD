"""
Sistem Deteksi Plat Kendaraan Indonesia
Entry point aplikasi PyQt5
"""

import sys
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QIcon
    from ui.main_window import MainWindow
except ImportError as e:
    print(f"Error: PyQt5 is not installed. Please install it using: pip install PyQt5")
    sys.exit(1)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Deteksi Plat Kendaraan")
    app.setOrganizationName("PlateDetector")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
