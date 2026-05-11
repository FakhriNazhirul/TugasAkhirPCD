"""
core/classifier.py
Klasifikasi jenis kendaraan berdasarkan format plat kendaraan Indonesia.
Menentukan: jenis kendaraan, wilayah, dan kategori (umum/pribadi/dinas/dll)
"""

import re
from dataclasses import dataclass
from typing import Optional


# ─── Data wilayah berdasarkan kode huruf depan plat ───────────────────────────
REGION_MAP = {
    # Jawa Barat & Banten
    "A": "Banten (Serang, Cilegon, Lebak, Pandeglang, Tangerang)",
    "B": "Jakarta, Depok, Bekasi, Tangerang",
    "D": "Bandung Raya (Bandung, Cimahi, Bandung Barat, Sumedang)",
    "E": "Cirebon, Indramayu, Majalengka, Kuningan",
    "F": "Bogor, Cianjur, Sukabumi",
    "T": "Purwakarta, Karawang, Subang",
    "Z": "Garut, Tasikmalaya, Ciamis, Banjar, Pangandaran",
    # Jawa Tengah & DIY
    "G": "Pekalongan, Batang, Pemalang, Tegal, Brebes",
    "H": "Semarang, Salatiga, Kendal, Demak",
    "K": "Pati, Kudus, Jepara, Rembang, Blora",
    "R": "Banyumas, Cilacap, Purbalingga, Banjarnegara",
    "S": "Bojonegoro, Tuban, Lamongan",
    "AA": "Magelang, Temanggung, Wonosobo, Kebumen, Purworejo",
    "AB": "Yogyakarta, Sleman, Bantul, Kulon Progo, Gunung Kidul",
    "AD": "Solo, Boyolali, Klaten, Sukoharjo, Wonogiri, Sragen, Karanganyar",
    # Jawa Timur
    "L": "Surabaya",
    "M": "Madura (Bangkalan, Sampang, Pamekasan, Sumenep)",
    "N": "Malang, Batu, Lumajang, Probolinggo, Pasuruan",
    "P": "Besuki (Situbondo, Bondowoso, Jember, Banyuwangi)",
    "W": "Sidoarjo, Gresik",
    "AE": "Madiun, Ngawi, Magetan, Ponorogo, Pacitan",
    "AG": "Kediri, Tulungagung, Blitar, Trenggalek, Nganjuk",
    # Sumatera
    "BA": "Sumatera Barat",
    "BB": "Tapanuli (Sumatera Utara Bagian Selatan)",
    "BD": "Bengkulu",
    "BE": "Lampung",
    "BG": "Sumatera Selatan",
    "BH": "Jambi",
    "BK": "Sumatera Utara",
    "BL": "Aceh",
    "BM": "Riau",
    "BN": "Kepulauan Bangka Belitung",
    "BP": "Kepulauan Riau",
    # Kalimantan
    "DA": "Kalimantan Selatan",
    "DB": "Sulawesi Utara Bagian Selatan (Bolaang Mongondow)",
    "DC": "Sulawesi Barat",
    "DD": "Sulawesi Selatan",
    "DE": "Maluku",
    "DG": "Sulawesi Selatan (Gowa)",
    "DH": "NTT (Timor Barat)",
    "DK": "Bali",
    "DL": "Sulawesi Utara Kepulauan",
    "DM": "Gorontalo",
    "DN": "Sulawesi Tengah",
    "DR": "NTB (Lombok Barat)",
    "DS": "Papua",
    "DT": "Sulawesi Tenggara",
    "DW": "Sulawesi Selatan (Luwu)",
    "EA": "NTB (Sumbawa)",
    "ED": "NTT (Flores Timur)",
    "EB": "NTT (Flores Barat)",
    "KA": "Kalimantan Barat",
    "KB": "Kalimantan Barat",
    "KH": "Kalimantan Tengah",
    "KT": "Kalimantan Timur",
    "KU": "Kalimantan Utara",
    "KS": "Kalimantan Selatan",
    # Khusus
    "CD": "Korps Diplomatik",
    "CC": "Korps Konsuler",
}

# ─── Pola plat Indonesia ───────────────────────────────────────────────────────
# Format umum: [huruf wilayah] [angka 1-4] [huruf seri 1-3]
PLATE_PATTERN = re.compile(
    r"^([A-Z]{1,2})\s*(\d{1,4})\s*([A-Z]{1,3})$"
)

# ─── Warna plat berdasarkan seri akhir (heuristik umum) ──────────────────────
# Catatan: warna plat paling akurat dari deteksi warna, bukan dari teks.
# Ini hanya estimasi berdasarkan konteks.
PUBLIC_TRANSPORT_CODES = {
    # Angkutan umum sering pakai nomor seri tertentu, tapi tidak absolut.
    # Di sini gunakan heuristik berdasarkan prefix daerah + konteks
}


@dataclass
class VehicleInfo:
    """Informasi kendaraan hasil klasifikasi."""
    raw_text: str           # Teks mentah dari OCR
    plate_number: str       # Nomor plat yang sudah dinormalisasi
    region_code: str        # Kode wilayah (huruf depan)
    region_name: str        # Nama wilayah
    serial_number: str      # Nomor seri (angka)
    serial_suffix: str      # Huruf seri akhir
    vehicle_category: str   # Kategori: Pribadi / Umum / Dinas / Diplomatik / Tidak Dikenal
    vehicle_type: str       # Perkiraan tipe kendaraan
    is_valid: bool          # Apakah format plat valid
    confidence: float       # Kepercayaan OCR (0.0–1.0)

    def __str__(self):
        if not self.is_valid:
            return f"Plat tidak dikenali: '{self.raw_text}'"
        return (
            f"Nomor Plat : {self.plate_number}\n"
            f"Wilayah    : {self.region_name}\n"
            f"Kategori   : {self.vehicle_category}\n"
            f"Jenis      : {self.vehicle_type}"
        )


class VehicleClassifier:
    """Klasifikasi kendaraan berdasarkan nomor plat Indonesia."""

    def classify(self, ocr_text: str, ocr_confidence: float = 1.0) -> VehicleInfo:
        """
        Klasifikasi kendaraan dari teks OCR nomor plat.

        Args:
            ocr_text: teks mentah dari OCR
            ocr_confidence: kepercayaan hasil OCR (0.0–1.0)

        Returns:
            VehicleInfo dengan semua detail kendaraan
        """
        raw = ocr_text.strip().upper()
        normalized = self._normalize(raw)
        match = PLATE_PATTERN.match(normalized)

        if not match:
            return VehicleInfo(
                raw_text=raw,
                plate_number=raw,
                region_code="",
                region_name="Tidak Diketahui",
                serial_number="",
                serial_suffix="",
                vehicle_category="Tidak Dikenali",
                vehicle_type="Tidak Diketahui",
                is_valid=False,
                confidence=ocr_confidence,
            )

        region_code, serial_number, serial_suffix = match.groups()
        plate_number = f"{region_code} {serial_number} {serial_suffix}"

        # Cari wilayah (coba 2 huruf dulu, lalu 1 huruf)
        region_name = (
            REGION_MAP.get(region_code)
            or REGION_MAP.get(region_code[:1])
            or "Wilayah Tidak Diketahui"
        )

        # Tentukan kategori
        category, vtype = self._determine_category(region_code, serial_number, serial_suffix)

        return VehicleInfo(
            raw_text=raw,
            plate_number=plate_number,
            region_code=region_code,
            region_name=region_name,
            serial_number=serial_number,
            serial_suffix=serial_suffix,
            vehicle_category=category,
            vehicle_type=vtype,
            is_valid=True,
            confidence=ocr_confidence,
        )

    def _normalize(self, text: str) -> str:
        """Bersihkan dan normalisasi teks OCR."""
        # Hapus karakter selain huruf, angka, spasi
        text = re.sub(r"[^A-Z0-9 ]", "", text)
        # Normalisasi spasi
        text = re.sub(r"\s+", " ", text).strip()
        # Perbaiki OCR umum: 0 vs O, 1 vs I, dll. pada posisi yang sesuai
        # (heuristik sederhana)
        return text

    def _determine_category(
        self, code: str, number: str, suffix: str
    ) -> tuple:
        """
        Tentukan kategori dan jenis kendaraan.

        Returns:
            (category, vehicle_type)
        """
        # Korps diplomatik
        if code in ("CD", "CC"):
            return "Diplomatik / Konsuler", "Kendaraan Diplomatik"

        # Angka 1 digit biasanya kendaraan dinas pemerintah
        if len(number) == 1:
            return "Dinas Pemerintah", "Kendaraan Dinas"

        # Seri R = Motor
        if suffix.startswith("R"):
            return "Kendaraan Pribadi", "Sepeda Motor"

        # Nomor di atas 7000 sering angkutan umum (bus, angkot) — heuristik
        num_int = int(number) if number.isdigit() else 0
        if 7000 <= num_int <= 9999:
            return "Angkutan Umum", "Bus / Angkutan Kota"

        # Suffix huruf tertentu untuk angkutan umum (heuristik per daerah)
        if len(suffix) >= 2 and suffix[-1] in ("U",):
            return "Angkutan Umum", "Kendaraan Umum"

        # Default: kendaraan pribadi
        return "Kendaraan Pribadi", "Mobil / Motor Pribadi"

    @staticmethod
    def format_display(info: VehicleInfo) -> dict:
        """Format data untuk ditampilkan di UI."""
        return {
            "nomor_plat": info.plate_number if info.is_valid else info.raw_text,
            "wilayah": info.region_name,
            "kategori": info.vehicle_category,
            "jenis": info.vehicle_type,
            "valid": info.is_valid,
            "confidence": f"{info.confidence * 100:.1f}%",
        }
