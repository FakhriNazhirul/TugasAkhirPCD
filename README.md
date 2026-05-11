# 🚗 Sistem Deteksi Plat Kendaraan Indonesia

Aplikasi desktop **PyQt5** dengan live kamera untuk mendeteksi dan membaca nomor plat kendaraan Indonesia secara real-time, beserta klasifikasi jenis kendaraannya.

---

## ✨ Fitur

| Fitur | Keterangan |
|-------|-----------|
| 📷 Live Kamera | Feed kamera real-time dengan overlay deteksi |
| 🔍 Deteksi Plat | Haar Cascade OpenCV (11 cascade tersedia) |
| 📖 OCR Otomatis | Baca nomor plat dengan EasyOCR atau Tesseract |
| 🗂️ Klasifikasi | Kategori: Pribadi, Umum, Dinas, Diplomatik |
| 🗺️ Wilayah | Identifikasi kota/provinsi dari kode plat |
| 📋 Riwayat | Panel scrollable semua deteksi sesi ini |
| ⚙️ Konfigurasi | Pilih cascade, atur threshold, skip frame |

---

## 📁 Struktur Proyek

```
plate-detector/
│
├── main.py                     # Entry point
├── requirements.txt            
├── README.md
│
├── assets/
│   └── cascades/               # File Haar Cascade XML
│       ├── plat.xml            # Cascade dasar (fallback)
│       ├── plat-5-10stage.xml  # 5 pos samples, 10 stages
│       ├── plat-5-17stage.xml
│       ├── plat-5-21stage.xml
│       ├── plat-5-25stage.xml
│       ├── plat-20-10stage.xml # 20 pos samples, 10 stages
│       ├── plat-20-20stage.xml
│       ├── plat-30-20stage.xml
│       ├── plat-40-25stage.xml
│       ├── plat-80-25stage.xml # Paling akurat (default)
│       ├── A-9-23stage.xml
│       ├── stopsign-10stage.xml
│       ├── stop-stage17.xml
│       └── stop-stage21.xml
│
├── core/
│   ├── __init__.py
│   ├── detector.py             # Deteksi plat dengan Haar Cascade
│   ├── ocr.py                  # OCR (EasyOCR / Tesseract)
│   ├── classifier.py           # Klasifikasi jenis kendaraan
│   └── camera_thread.py        # QThread untuk live kamera
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # Jendela utama PyQt5
│   ├── camera_widget.py        # Widget tampilan kamera
│   └── result_widget.py        # Panel hasil deteksi
│
└── utils/
    ├── __init__.py
    └── plate_parser.py         # Utilitas format & ekspor
```

---

## 🚀 Instalasi

```bash
# 1. Clone / download proyek
cd plate-detector

# 2. Install dependencies Python
pip install -r requirements.txt

# 3. (Opsional) Install Tesseract jika tidak pakai EasyOCR
#    Windows: https://github.com/UB-Mannheim/tesseract/wiki
#    Linux:   sudo apt install tesseract-ocr
#    macOS:   brew install tesseract

# 4. Jalankan
python main.py
```

---

## 🔧 Penggunaan

1. Buka aplikasi → tekan **▶ Mulai Kamera**
2. Pilih **Cascade** yang diinginkan (default: `plat-80-25stage.xml` — paling akurat)
3. Arahkan kamera ke plat kendaraan
4. Hasil deteksi muncul otomatis di panel kanan:
   - **Nomor Plat** (hasil OCR)
   - **Wilayah** (kota/provinsi)
   - **Kategori** (Pribadi / Umum / Dinas / Diplomatik)
   - **Jenis Kendaraan**
   - **Akurasi OCR**

---

## 📊 Cascade Files

Penamaan cascade: `plat-{pos_samples}-{stages}stage.xml`

| File | Pos Samples | Stages | Keterangan |
|------|-------------|--------|-----------|
| `plat-80-25stage.xml` | 80 | 25 | **Paling akurat**, lebih lambat |
| `plat-40-25stage.xml` | 40 | 25 | Akurat, cukup cepat |
| `plat-30-20stage.xml` | 30 | 20 | Seimbang |
| `plat-20-20stage.xml` | 20 | 20 | Cepat |
| `plat-5-25stage.xml`  | 5  | 25 | Dataset kecil, 25 stage |
| `plat-5-10stage.xml`  | 5  | 10 | Paling cepat |
| `plat.xml`            | -  | -  | Default / fallback |

---

## 🏷️ Format Plat Indonesia

```
[Kode Wilayah] [Nomor Seri] [Huruf Seri]
      B            1234          CD
      D            5678          EF
```

**Kategori kendaraan** ditentukan dari:
- Kode wilayah (A-Z, AA-AG, BA-BP, DA-DS, KA-KU)
- Panjang nomor seri (1 digit → dinas pemerintah)
- Rentang nomor (7000–9999 → angkutan umum)
- Kode diplomatik (CD, CC)

---

## 🛠️ Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Kamera tidak terdeteksi | Coba ganti index kamera (0, 1, 2) |
| OCR tidak akurat | Pastikan pencahayaan cukup; coba cascade berbeda |
| EasyOCR error | `pip install easyocr torch` |
| Tesseract error | Install binary Tesseract, tambahkan ke PATH |
| Deteksi lambat | Naikkan nilai "Deteksi per N Frame" |
