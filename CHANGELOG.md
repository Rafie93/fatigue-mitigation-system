# Changelog

All notable changes to the Fatigue Mitigation System are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-06-19

### Added
- **Windows packaging**: PyInstaller (`--onedir`) build, automated via GitHub
  Actions on a Windows runner, producing a ready-to-run `.zip` distribution.
- **Multi camera support** with device discovery, selection and refresh.
- **Multiple camera types**: integrated / USB / virtual / RTSP / HTTP MJPEG.
- **Automatic event video recording** (circular buffer, pre + post event).
- **Automatic screenshots** with information overlay.
- **Theme manager**: light / dark / follow system.
- **System tray**: keep monitoring in the background + desktop notifications.
- Portable storage layout (`storage/logs|pending|screenshots|videos|cache`).

## [1.1.0]

### Added
- Splash screen, Home dashboard, Detection window, Configuration manager,
  Event history, backend event sending with pending-event retry, status bar.
- MVVM architecture (View / ViewModel / Services).

## [1.0.0]

### Added
- Initial MobileNetV2 eye/mouth fatigue detection script.
