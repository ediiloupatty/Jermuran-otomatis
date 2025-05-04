# Sistem Jemuran Otomatis Online

Sistem jemuran otomatis berbasis Arduino dan NodeMCU dengan kemampuan prediksi cuaca menggunakan machine learning.

## Daftar Isi
1. [Pengenalan Sistem](#1-pengenalan-sistem)
2. [Komponen yang Dibutuhkan](#2-komponen-yang-dibutuhkan)
3. [Persiapan Hardware](#3-persiapan-hardware)
4. [Instalasi Software](#4-instalasi-software)
5. [Upload Kode](#5-upload-kode)
6. [Pengujian Sistem](#6-pengujian-sistem)
7. [Integrasi dengan Machine Learning](#7-integrasi-dengan-machine-learning)
8. [Troubleshooting](#8-troubleshooting)
9. [FAQ](#9-faq)

## 1. Pengenalan Sistem

Sistem jemuran otomatis online ini terdiri dari dua modul utama:
- **Arduino UNO**: Menangani semua sensor (LDR dan sensor hujan) dan motor servo
- **NodeMCU ESP8266**: Menyediakan konektivitas internet dan antarmuka web

Kedua modul ini berkomunikasi melalui serial, di mana:
- Arduino mengirim data status dan sensor ke NodeMCU
- NodeMCU mengirim perintah kontrol ke Arduino berdasarkan input dari web

![Diagram Wiring](path/to/wiring-diagram.png)

## 2. Komponen yang Dibutuhkan

- Arduino UNO
- NodeMCU ESP8266
- Sensor LDR (Light Dependent Resistor)
- Sensor Hujan
- Motor Servo
- LCD I2C 16x2
- Kabel jumper secukupnya
- Power supply untuk Arduino (5V)
- Power supply untuk NodeMCU (3.3V/5V)
- Resistor 10kΩ (untuk LDR, jika belum dipasang)

## 3. Persiapan Hardware

### Koneksi Arduino
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

4. Software untuk Flask:
   - Flask
   - SQLite3
   - Requests
   - Scikit-learn
   - Numpy
   - Joblib

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

5. Untuk Flask dan library Python, jalankan:
   ```
   pip install flask requests scikit-learn numpy joblib
   ```

## 5. Upload Kode

### Langkah Upload Kode Arduino
1. Hubungkan Arduino ke komputer via USB
2. Buka kode Arduino yang sudah ada
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

Sistem ini menggunakan model Decision Tree Classifier untuk memprediksi kondisi cuaca berdasarkan data sensor yang dikumpulkan. Implementasi ML berada di sisi server (Flask application) yang menerima data dari NodeMCU.

### Arsitektur Model ML
- **Model**: Decision Tree Classifier dengan parameter yang dioptimalkan untuk menghindari overfitting
- **Fitur Input**: Data time series dari sensor LDR dan hujan
- **Output**: Prediksi cuaca (hujan/tidak hujan) dengan tingkat kepercayaan

### Proses Pengolahan Data
1. **Pengumpulan Data**:
   - Data dari sensor (LDR dan hujan) dikumpulkan tiap 3 detik
   - Data disimpan dalam database SQLite (sensor_data.db)

2. **Preprocessing Data**:
   - Data diskalakan menggunakan MinMaxScaler (rentang 0-1)
   - Data diformat dalam bentuk time series dengan window size 3
   - Target diubah menjadi kategorikal (1 = hujan, 0 = tidak hujan)

3. **Pelatihan Model**:
   - Data dibagi menjadi training (80%) dan testing (20%)
   - Model dilatih dengan parameter yang dioptimalkan:
     ```python
     DecisionTreeClassifier(
         max_depth=3,
         min_samples_split=5,
         min_samples_leaf=3,
         class_weight='balanced'
     )
     ```
   - Model disimpan menggunakan Joblib

4. **Prediksi**:
   - Model menggunakan data terbaru (window size - 1) untuk memprediksi cuaca
   - Hasil prediksi mencakup probabilitas kejadian hujan (0-1)

### Fitur Machine Learning
1. **Auto Training**:
   - Sistem secara otomatis melatih ulang model setiap 30 menit
   - Pelatihan hanya dilakukan jika jumlah data mencukupi

2. **Weather Prediction API**:
   - Endpoint `/predict-weather` memberikan prediksi cuaca
   - Response berisi status prediksi (akan hujan/tidak) dan probabilitas

3. **Integrasi dengan Auto Mode**:
   - Prediksi cuaca dapat digunakan untuk pengambilan keputusan otomatis
   - Sistem akan secara otomatis menutup jemuran jika terdeteksi potensi hujan

### Cara Melatih Model Secara Manual
1. Buka halaman settings dari web interface
2. Klik tombol "Train Model"
3. Tunggu hingga proses training selesai
4. Accuracy model akan ditampilkan setelah training selesai

### Cara Melihat Prediksi Cuaca
1. Buka halaman dashboard atau realtime monitoring
2. Cek panel "Weather Prediction"
3. Sistem akan menampilkan prediksi cuaca beserta tingkat kepercayaan

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

### Masalah Machine Learning
- **Error saat Training Model**
  - Pastikan jumlah data cukup (minimum 13 data untuk window size 3)
  - Periksa format data dalam database
  - Pastikan library scikit-learn dan numpy terinstal

- **Prediksi Tidak Akurat**
  - Kumpulkan lebih banyak data untuk training
  - Coba sesuaikan parameter model (max_depth, min_samples_split)
  - Periksa nilai sensor apakah sudah terkalibrasi dengan baik

## 9. FAQ

### Q: Apakah sistem tetap bekerja jika internet mati?
A: Ya, kontrol otomatis oleh Arduino tetap berfungsi meskipun NodeMCU kehilangan koneksi internet. Namun, akses remote melalui web tidak akan berfungsi hingga koneksi internet kembali.

### Q: Berapa lama sistem dapat beroperasi?
A: Selama power supply tersedia, sistem dapat beroperasi tanpa batasan waktu. Tidak perlu koneksi ke laptop setelah setup awal.

### Q: Bisakah saya menambahkan sensor lain?
A: Ya, Anda dapat menambahkan sensor lain ke Arduino, kemudian diatur untuk mengirim data tambahan melalui komunikasi serial ke NodeMCU.

### Q: Bagaimana cara mengubah threshold sensor?
A: Ubah nilai `LDR_THRESHOLD` dan `RAIN_THRESHOLD` di halaman settings web interface atau langsung di kode Arduino.

### Q: Bisakah saya mengakses sistem dari luar jaringan rumah?
A: Ya, tetapi memerlukan konfigurasi tambahan seperti port forwarding di router atau menggunakan layanan seperti MQTT/IoT platform.

### Q: Bagaimana akurasi prediksi cuaca?
A: Akurasi prediksi bergantung pada jumlah dan kualitas data yang dikumpulkan. Dengan data yang cukup, sistem dapat mencapai akurasi di atas 70%.

### Q: Berapa lama waktu yang dibutuhkan untuk melatih model?
A: Proses pelatihan model biasanya membutuhkan waktu 1-2 detik tergantung jumlah data yang tersedia.

### Q: Apa yang terjadi jika prediksi cuaca salah?
A: Sistem memiliki mode manual yang memungkinkan pengguna mengontrol jemuran secara langsung jika prediksi otomatis tidak akurat.
