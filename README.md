# Fatigue Detection System — Desktop

Aplikasi desktop (PySide6) untuk mendeteksi kantuk pengemudi secara real-time
menggunakan model Deep Learning **MobileNetV2** (mata + mulut). Dibangun dengan arsitektur **MVVM**.

## Fitur (v1.1)

- Splash screen dengan loading model AI di background thread
- Home Dashboard (status Kamera / Backend / AI Model / Device / Pending Events)
- Detection Window dengan live preview di dalam GUI (QLabel) + overlay status
- Configuration Manager tersimpan ke `config/config.json`
- Event History (Micro Sleep / Fatigue / Yawn)
- Pengiriman event ke backend REST + penyimpanan **pending** saat offline + retry otomatis
- Status bar (Camera, Backend, FPS, CPU, RAM)
- Kamera **tidak aktif** saat aplikasi dibuka — hanya aktif setelah **Start Camera**

## Fitur Baru (v1.2)

- **Multi Camera Support** — deteksi semua kamera, pilih dari dropdown di Home /
  Settings, tombol **Refresh Camera**, ganti kamera tanpa restart (saat idle)
- **Multiple Camera Types** — Integrated / USB / Virtual / **RTSP** / **HTTP MJPEG**
  (set tipe + URL di Settings → Camera)
- **Automatic Event Video Recording** — circular buffer (10 dtk sebelum +
  20 dtk sesudah event) → `storage/videos/<tanggal>/`
- **Automatic Screenshot** — snapshot dengan overlay (time/status/camera/event/confidence)
  → `storage/screenshots/<tanggal>/`
- **Theme Manager** — Light / Dark / Follow System, berubah tanpa restart
- **System Tray** — tutup window = tetap berjalan di background; menu tray
  (Open / Start / Stop / Settings / History / About / Exit) + notifikasi alert.
  Keluar hanya via **Tray → Exit**

## Struktur

```
FatigueDesktop/
├── app.py / main.py        # entry point
├── ui/                     # View (PySide6)
│   ├── splash.py  home.py  detection.py  settings.py
│   ├── event_history.py  about.py  main_window.py  theme.py
├── viewmodels/             # ViewModel
│   └── detection_viewmodel.py
├── services/               # Services
│   ├── camera_service.py   detection_service.py  backend_service.py
│   ├── config_service.py   event_service.py  system_monitor.py  paths.py
├── models/                 # model_eye_mobilenet.h5, model_mouth_mobilenet.h5
├── config/config.json      # konfigurasi tersimpan
├── pending/  logs/  assets/
└── storage/                # v1.2 — screenshots/  videos/  cache/
```

Service v1.2 tambahan: `camera_discovery.py` (scan & build sumber kamera),
`recorder_service.py` (VideoRecorder circular buffer + ScreenshotSaver),
`theme_manager.py` (light/dark/system).

## Menjalankan (development)

```bash
pip install -r requirements.txt
python app.py
```

Atur Backend API URL & Device Token di halaman **Configuration**, lalu **Save**.
Nilai konfigurasi juga di-mirror ke environment variable (`Fatigue_API_URL`, dst.)
agar kompatibel dengan kode deteksi versi sebelumnya.

## Packaging (Phase 5)

Setelah stabil, paketkan menjadi executable dengan PyInstaller, sertakan folder
`models/` sebagai data. Contoh:

```bash
pyinstaller --noconfirm --windowed --name FatigueDesktop \
  --add-data "models:models" app.py
```

<!-- ADD IMAGE SAMPLE THIS FROM ASSET ss.png -->
## RESULT RUN DETECTTION
![image](https://github.com/Rafie93/fatigue-mitigation-system/blob/main/assets/ss.png)