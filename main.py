import cv2
import numpy as np
import pytesseract

# ========== Deteksi Plat via MSER + Grouping Teks ==========
def detect_plate_mser(frame):
    """
    Deteksi wilayah plat menggunakan MSER dan clustering geometri karakter.
    Mengembalikan citra plat hasil crop, atau None jika tidak ditemukan.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Inisialisasi MSER
    mser = cv2.MSER_create(
        _delta=5,              # step size saat thresholding
        _min_area=30,          # filter region terlalu kecil (noise)
        _max_area=500,         # filter terlalu besar (bukan karakter)
        _max_variation=0.25,   # stabilitas region
        _min_diversity=0.2
    )
    
    regions, _ = mser.detectRegions(gray)
    
    if not regions:
        return None
    
    # Ambil bounding box tiap region
    bboxes = [cv2.boundingRect(r) for r in regions]
    
    # Filter berdasarkan aspek rasio khas karakter plat (0.2 - 1.0, karakter tidak terlalu pipih)
    char_bboxes = []
    for (x, y, w, h) in bboxes:
        aspect = w / h if h != 0 else 0
        if 0.2 < aspect < 1.0 and h > 10:  # tinggi minimal 10px
            char_bboxes.append((x, y, w, h))
    
    if len(char_bboxes) < 3:
        return None  # minimal 3 karakter untuk jadi plat
    
    # Kelompokkan karakter yang berdekatan (satu baris plat)
    # Urutkan berdasarkan x
    char_bboxes.sort(key=lambda b: b[0])
    
    groups = []
    current_group = [char_bboxes[0]]
    for i in range(1, len(char_bboxes)):
        prev = current_group[-1]
        curr = char_bboxes[i]
        # Jika jarak horizontal < 2x lebar karakter sebelumnya (longgar)
        if curr[0] - (prev[0] + prev[2]) < 2 * prev[2]:
            current_group.append(curr)
        else:
            groups.append(current_group)
            current_group = [curr]
    groups.append(current_group)
    
    # Pilih grup dengan karakter terbanyak
    best_group = max(groups, key=len)
    if len(best_group) < 3:
        return None
    
    # Hitung bounding box gabungan
    x_min = min(b[0] for b in best_group)
    y_min = min(b[1] for b in best_group)
    x_max = max(b[0] + b[2] for b in best_group)
    y_max = max(b[1] + b[3] for b in best_group)
    
    # Tambah padding
    pad_x = int((x_max - x_min) * 0.2)
    pad_y = int((y_max - y_min) * 0.3)
    x1 = max(0, x_min - pad_x)
    y1 = max(0, y_min - pad_y)
    x2 = min(frame.shape[1], x_max + pad_x)
    y2 = min(frame.shape[0], y_max + pad_y)
    
    plate = frame[y1:y2, x1:x2]
    if plate.size == 0:
        return None
    return plate, (x1, y1, x2 - x1, y2 - y1)

# ========== Klasifikasi warna plat (sama seperti sebelumnya) ==========
COLOR_RANGES = {
    "PUTIH":  (np.array([0, 0, 180]),   np.array([180, 40, 255])),
    "KUNING": (np.array([15, 100, 100]), np.array([35, 255, 255])),
    "MERAH":  (np.array([0, 100, 100]),  np.array([10, 255, 255])),
    "MERAH2": (np.array([160, 100, 100]), np.array([180, 255, 255])),
    "HIJAU":  (np.array([40, 100, 100]), np.array([80, 255, 255])),
    "HITAM":  (np.array([0, 0, 0]),      np.array([180, 255, 70])),
}

def classify_plate_type(plate_img):
    hsv = cv2.cvtColor(plate_img, cv2.COLOR_BGR2HSV)
    total = plate_img.shape[0] * plate_img.shape[1]
    scores = {}
    for name in ["PUTIH","KUNING","MERAH","HIJAU","HITAM"]:
        if name == "MERAH":
            m1 = cv2.inRange(hsv, COLOR_RANGES["MERAH"][0], COLOR_RANGES["MERAH"][1])
            m2 = cv2.inRange(hsv, COLOR_RANGES["MERAH2"][0], COLOR_RANGES["MERAH2"][1])
            mask = cv2.bitwise_or(m1, m2)
        else:
            mask = cv2.inRange(hsv, COLOR_RANGES[name][0], COLOR_RANGES[name][1])
        scores[name] = cv2.countNonZero(mask) / total
    best = max(scores, key=scores.get)
    return best if scores[best] > 0.3 else "TIDAK DIKETAHUI"

# ========== OCR ==========
def ocr_plate(plate_img):
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    # Adaptive threshold agar kontras maksimal
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    try:
        text = pytesseract.image_to_string(thresh, config=custom_config).strip().replace(' ', '')
    except:
        text = ""
    return text

# ========== Loop Utama ==========
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera tidak tersedia.")
        return

    print("Deteksi Plat Otomatis (MSER) berjalan... Tekan 'q' untuk keluar.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (640, 480))
        display = frame.copy()

        result = detect_plate_mser(frame)
        if result is not None:
            plate_img, (x, y, w, h) = result
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

            plat_type = classify_plate_type(plate_img)
            plate_text = ocr_plate(plate_img)

            label = f"{plate_text} | {plat_type}"
            cv2.putText(display, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(display, "Plat tidak terdeteksi", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Deteksi Plat Otomatis", display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()