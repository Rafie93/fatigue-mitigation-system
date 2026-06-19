# Fatigue Detection System — Desktop

Aplikasi desktop (PySide6) untuk mendeteksi kantuk pengemudi secara real-time
menggunakan model Deep Learning **MobileNetV2** (mata + mulut). Dibangun
mengikuti PRD v1.1 dengan arsitektur **MVVM**.

## Fitur

- Splash screen dengan loading model AI di background thread
- Home Dashboard (status Kamera / Backend / AI Model / Device / Pending Events)
- Detection Window dengan live preview di dalam GUI (QLabel) + overlay status
- Configuration Manager (5 kategori) tersimpan ke `config/config.json`
- Event History (Micro Sleep / Fatigue / Yawn)
- Pengiriman event ke backend REST + penyimpanan **pending** saat offline + retry otomatis
- Status bar (Camera, Backend, FPS, CPU, RAM)
- Kamera **tidak aktif** saat aplikasi dibuka — hanya aktif setelah **Start Camera**

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
```

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
