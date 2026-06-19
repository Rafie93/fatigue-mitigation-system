============================================================
 Fatigue Mitigation System - Windows Edition
============================================================

Aplikasi deteksi kelelahan perawat berbasis AI
MobileNetV2. Tidak memerlukan instalasi Python.

------------------------------------------------------------
 CARA MENJALANKAN
------------------------------------------------------------
1. Ekstrak seluruh isi file .zip ke sebuah folder
   (contoh: C:\FatigueMitigation).
2. Klik dua kali "FaigueMitigation.exe".
3. Splash screen akan tampil saat model AI dimuat.
4. Home Dashboard akan terbuka. Kamera TIDAK langsung aktif.
5. Tekan "Start Camera" untuk memulai deteksi.

CATATAN: Jangan memindahkan FaigueMitigation.exe keluar dari
folder hasil ekstrak. Seluruh folder (models, _internal, dll)
harus tetap berada di lokasi yang sama.

------------------------------------------------------------
 STRUKTUR FOLDER
------------------------------------------------------------
  FaigueMitigation.exe   -> aplikasi utama
  _internal/             -> runtime Python + library (jangan diubah)
  models/                -> model AI (.h5) - dapat diperbarui
  assets/                -> ikon & logo
  config/config.json     -> konfigurasi (dibuat otomatis bila kosong)
  storage/               -> logs, pending, screenshots, videos, cache
  version.json           -> informasi versi
  README.txt, LICENSE, CHANGELOG.md

------------------------------------------------------------
 KONFIGURASI
------------------------------------------------------------
Buka menu "Configuration" di dalam aplikasi untuk mengatur:
  - Sumber kamera (Integrated/USB/RTSP/HTTP) & pemilihan device
  - Backend API URL + Device Token
  - Parameter deteksi mata & menguap
  - Recording & screenshot otomatis
  - Tema (Light/Dark/Follow System) & System Tray

Token backend & password TIDAK disimpan di dalam executable;
seluruhnya berada pada config/config.json.

------------------------------------------------------------
 PERSYARATAN SISTEM
------------------------------------------------------------
  - Windows 10 / Windows 11 (64-bit)
  - Webcam (atau kamera RTSP/HTTP)
  - RAM minimal 4 GB (disarankan 8 GB)

------------------------------------------------------------
 DUKUNGAN
------------------------------------------------------------
  https://github.com/Rafie93/fatigue-mitigation-system
============================================================
