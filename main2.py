import cv2

# 1. Load file XML
# Pastikan file ini ada di folder yang sama
plate_cascade = cv2.CascadeClassifier('haarcascade_russian_plate_number.xml')

# 2. Inisialisasi Kamera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Konversi ke grayscale untuk proses deteksi
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 3. Deteksi Plat Nomor
    # scaleFactor dan minNeighbors bisa disesuaikan untuk akurasi
    plates = plate_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    for (x, y, w, h) in plates:
        # Membuat Frame Kotak di sekitar plat
        # Warna (0, 255, 0) adalah hijau, ketebalan garis 2
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Tambahkan label kecil di atas frame (Opsional, hanya tulisan "PLAT")
        cv2.rectangle(frame, (x, y - 25), (x + 60, y), (0, 255, 0), -1)
        cv2.putText(frame, "PLAT", (x + 5, y - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # 4. Tampilkan Hasil
    cv2.imshow('Deteksi Plat Nomor (Frame Only)', frame)

    # Keluar dengan menekan tombol 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()