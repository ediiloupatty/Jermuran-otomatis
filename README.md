# Panduan Implementasi Sistem Jemuran Otomatis Online
(Dengan Arduino + NodeMCU ESP8266)

## Daftar Isi
1. Pengenalan Sistem
2. Komponen yang Dibutuhkan
3. Persiapan Hardware
4. Instalasi Software
5. Upload Kode
6. Pengujian Sistem
7. Integrasi dengan Machine Learning
8. Troubleshooting
9. FAQ

## 1. Pengenalan Sistem

Sistem jemuran otomatis online ini terdiri dari dua modul utama:
- **Arduino UNO**: Menangani semua sensor (LDR dan sensor hujan) dan motor servo
- **NodeMCU ESP8266**: Menyediakan konektivitas internet dan antarmuka web

Kedua modul ini berkomunikasi melalui serial, di mana:
- Arduino mengirim data status dan sensor ke NodeMCU
- NodeMCU mengirim perintah kontrol ke Arduino berdasarkan input dari web

## 2. Komponen yang Dibutuhkan

- Arduino UNO
- NodeMCU ESP8266
- Sensor LDR (Light Dependent Resistor)
- Sensor Hujan
- Motor Servo
- LCD I2C 16x2 (yang sudah terpasang pada Arduino)
- Kabel jumper secukupnya
- Power supply untuk Arduino (5V)
- Power supply untuk NodeMCU (3.3V/5V)
- Resistor 10kΩ (untuk LDR, jika belum dipasang)

## 3. Persiapan Hardware

### Koneksi Arduino (sudah terpasang)
- LDR terhubung ke pin A0
- Sensor hujan terhubung ke pin A1
- Motor servo terhubung ke pin D9
- LCD I2C terhubung ke pin SDA/SCL

### Koneksi NodeMCU ke Arduino
1. Arduino TX → NodeMCU D2 (RX)
2. Arduino RX → NodeMCU D1 (TX)
3. Arduino GND → NodeMCU GND

**Catatan Penting:**
- Pastikan level tegangan cocok antara Arduino (5V) dan NodeMCU (3.3V).
- Jika menggunakan NodeMCU yang hanya menerima 3.3V pada pin input, gunakan pembagi tegangan untuk koneksi TX Arduino → RX NodeMCU.

Rangkaian pembagi tegangan sederhana:
```
Arduino TX --[ 2.2kΩ ]--------> NodeMCU RX
                       |
                       |
                    [ 3.3kΩ ]
                       |
                       V
                      GND
```

## 4. Instalasi Software

### Software yang Dibutuhkan
1. Arduino IDE
2. Library berikut untuk Arduino:
   - Wire.h (bawaan)
   - LiquidCrystal_I2C.h
   - Servo.h
   
3. Library berikut untuk NodeMCU:
   - ESP8266WiFi.h
   - ESP8266WebServer.h
   - ArduinoJson.h
   - SoftwareSerial.h

### Langkah Instalasi Library
1. Buka Arduino IDE
2. Pilih **Sketch > Include Library > Manage Libraries...**
3. Cari dan instal library-library berikut:
   - LiquidCrystal I2C by Frank de Brabander
   - ArduinoJson by Benoit Blanchon
   
4. Untuk ESP8266, tambahkan URL board manager:
   - Buka **File > Preferences**
   - Pada "Additional Boards Manager URLs" tambahkan: `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
   - Pilih **Tools > Board > Boards Manager...**
   - Cari "ESP8266" dan instal versi terbaru

## 5. Upload Kode

### Langkah Upload Kode Arduino
1. Hubungkan Arduino ke komputer via USB
2. Buka kode Arduino yang sudah ada (yang ada di file upload)
3. Pilih board "Arduino UNO" di **Tools > Board**
4. Pilih port yang sesuai di **Tools > Port**
5. Klik "Upload"

### Langkah Upload Kode NodeMCU
1. Lepaskan Arduino dari komputer
2. Hubungkan NodeMCU ke komputer via USB
3. Buka kode NodeMCU yang sudah dibuat
4. Edit konfigurasi WiFi (SSID dan password)
5. Pilih board "NodeMCU 1.0 (ESP-12E Module)" di **Tools > Board**
6. Pilih port yang sesuai di **Tools > Port**
7. Klik "Upload"

## 6. Pengujian Sistem

### Langkah Uji Coba
1. Hubungkan kedua modul sesuai skema (Arduino TX → NodeMCU D2, Arduino RX → NodeMCU D1, GND → GND)
2. Sambungkan power ke Arduino dan NodeMCU
3. Tunggu sampai NodeMCU terhubung ke WiFi (cek Serial Monitor)
4. Catat alamat IP yang muncul di Serial Monitor
5. Buka browser di laptop/handphone dan akses alamat IP tersebut
6. Anda akan melihat halaman kontrol jemuran otomatis

### Pengujian Fungsionalitas
1. **Tes Pembacaan Sensor**
   - Pantau nilai LDR dan sensor hujan di halaman web
   - Bandingkan dengan nilai di LCD Arduino
   
2. **Tes Kontrol Manual**
   - Klik tombol "Buka Jemuran" dan lihat apakah servo bergerak
   - Klik tombol "Tutup Jemuran" dan lihat apakah servo bergerak
   
3. **Tes Otomatis**
   - Tutupi sensor LDR untuk mensimulasikan kondisi gelap
   - Basahi sensor hujan untuk mensimulasikan kondisi hujan
   - Amati apakah jemuran bergerak secara otomatis

## 7. Integrasi dengan Machine Learning

Karena mata kuliah Anda adalah Machine Learning, berikut beberapa ide untuk mengintegrasikan ML ke dalam sistem:

### 1. Prediksi Cuaca Berbasis ML
1. Kumpulkan data historis dari sensor (LDR dan hujan)
2. Buat model ML sederhana untuk memprediksi hujan/cerah beberapa jam ke depan
3. Tambahkan fitur prediksi ini ke halaman web

### 2. Pengenalan Pola Penggunaan
1. Rekam pola manual override dari pengguna
2. Buat model ML untuk memprediksi kapan pengguna biasanya menjemur

### 3. Optimasi Pengeringan
1. Gunakan data dari sensor untuk memprediksi waktu pengeringan optimal
2. Buat model ML yang belajar dari waktu pengeringan sebelumnya

### Implementasi ML di NodeMCU
Karena NodeMCU memiliki keterbatasan komputasi, Anda dapat:
1. Implementasikan model ML sederhana di NodeMCU (TinyML)
2. Atau gunakan cloud service untuk pemrosesan ML, dengan NodeMCU hanya mengirim data dan menerima hasil

## 8. Troubleshooting

### Masalah Koneksi Serial
- **Arduino dan NodeMCU tidak berkomunikasi**
  - Periksa kembali koneksi kabel (TX → RX, RX → TX)
  - Pastikan level tegangan sesuai (gunakan pembagi tegangan jika perlu)
  - Coba menukar pin RX/TX jika komunikasi masih gagal

### Masalah WiFi
- **NodeMCU tidak terhubung ke WiFi**
  - Periksa SSID dan password
  - Pastikan router dalam jangkauan
  - Coba restart NodeMCU

### Masalah Servo
- **Servo tidak bergerak**
  - Periksa koneksi servo ke Arduino
  - Pastikan power supply Arduino cukup untuk menjalankan servo
  - Coba tes servo dengan kode sederhana untuk memastikan servo berfungsi

### Masalah Web Interface
- **Tidak bisa mengakses web interface**
  - Pastikan perangkat berada dalam jaringan WiFi yang sama
  - Coba akses IP dengan browser berbeda
  - Periksa firewall yang mungkin memblokir koneksi

## 9. FAQ

### Q: Apakah sistem tetap bekerja jika internet mati?
A: Ya, kontrol otomatis oleh Arduino tetap berfungsi meskipun NodeMCU kehilangan koneksi internet. Namun, akses remote melalui web tidak akan berfungsi hingga koneksi internet kembali.

### Q: Berapa lama sistem dapat beroperasi?
A: Selama power supply tersedia, sistem dapat beroperasi tanpa batasan waktu. Tidak perlu koneksi ke laptop setelah setup awal.

### Q: Bisakah saya menambahkan sensor lain?
A: Ya, Anda dapat menambahkan sensor lain ke Arduino, kemudian diatur untuk mengirim data tambahan melalui komunikasi serial ke NodeMCU.

### Q: Bagaimana cara mengubah threshold sensor?
A: Ubah nilai `LDR_THRESHOLD` dan `RAIN_THRESHOLD` di kode Arduino, kemudian upload ulang ke Arduino.

### Q: Bisakah saya mengakses sistem dari luar jaringan rumah?
A: Ya, tetapi memerlukan konfigurasi tambahan seperti port forwarding di router atau menggunakan layanan seperti MQTT/IoT platform.
