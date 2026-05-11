"""
utils/plate_parser.py
Utilitas tambahan: format, validasi, dan ekspor data plat.
"""

import re
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List
from core.classifier import VehicleInfo


def clean_plate_text(raw: str) -> str:
    """Bersihkan karakter tidak relevan dari output OCR."""
    # Hanya huruf kapital, angka, dan spasi
    cleaned = re.sub(r"[^A-Z0-9 ]", "", raw.upper().strip())
    return re.sub(r"\s+", " ", cleaned).strip()


def is_valid_indonesian_plate(text: str) -> bool:
    """Validasi apakah teks sesuai format plat Indonesia."""
    pattern = re.compile(r"^[A-Z]{1,2}\s?\d{1,4}\s?[A-Z]{1,3}$")
    return bool(pattern.match(text.strip()))


def format_plate_display(plate: str) -> str:
    """Format nomor plat dengan spasi yang benar (e.g., B 1234 CD)."""
    m = re.match(r"([A-Z]{1,2})\s*(\d{1,4})\s*([A-Z]{1,3})", plate.upper())
    if m:
        return f"{m.group(1)} {m.group(2)} {m.group(3)}"
    return plate


def export_to_csv(results: List[VehicleInfo], output_path: str = None) -> str:
    """
    Ekspor riwayat deteksi ke file CSV.

    Returns:
        Path file CSV yang dibuat.
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"hasil_deteksi_{timestamp}.csv"

    fieldnames = [
        "waktu", "nomor_plat", "wilayah", "kategori",
        "jenis", "akurasi", "valid"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for info in results:
            writer.writerow({
                "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "nomor_plat": info.plate_number,
                "wilayah": info.region_name,
                "kategori": info.vehicle_category,
                "jenis": info.vehicle_type,
                "akurasi": f"{info.confidence * 100:.1f}%",
                "valid": "Ya" if info.is_valid else "Tidak",
            })

    return output_path


def export_to_json(results: List[VehicleInfo], output_path: str = None) -> str:
    """Ekspor riwayat deteksi ke JSON."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"hasil_deteksi_{timestamp}.json"

    data = [
        {
            "nomor_plat": info.plate_number,
            "wilayah": info.region_name,
            "kategori": info.vehicle_category,
            "jenis": info.vehicle_type,
            "akurasi": info.confidence,
            "valid": info.is_valid,
        }
        for info in results
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return output_path
