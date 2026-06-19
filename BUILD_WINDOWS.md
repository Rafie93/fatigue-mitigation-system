# Windows Packaging Guide

Builds the **Fatigue Mitigation System** into a Windows `.exe` distribution
using **PyInstaller (`--onedir`)**. Development is done on macOS; the actual
Windows build runs on a **GitHub Actions Windows runner**.

## Automated build (recommended)

The workflow `.github/workflows/windows-build.yml` runs on:

- **push to `main`** → build + upload artifact
- **push a `v*` tag** (e.g. `v1.2.0`) → build + create a **GitHub Release**
- **manual** via *Actions → Windows Build → Run workflow*

Pipeline steps (PRD §10): checkout → setup Python 3.12 (x64) → verify models →
install deps → run tests (`tools/ci_smoke.py`) → stamp `version.json` →
PyInstaller build → assemble dist → validate (`tools/validate_build.py`) →
zip + SHA256 → upload artifact → (on tag) release.

Artifact name: `FaigueMitigation_v<version>_Windows_x64.zip`.

> **Models must be in the repo.** `models/model_eye_mobilenet.h5` and
> `models/model_mouth_mobilenet.h5` are required at build time. They are tracked
> in git; the pipeline fails early if they are missing.

### Cutting a release

```bash
git tag v1.2.0
git push origin v1.2.0
```

## Local build (on a Windows machine)

```bat
python -m pip install -r requirements-build.txt
python tools/ci_smoke.py
pyinstaller --noconfirm --clean FaigueMitigation.spec
:: copy resources next to the exe
xcopy /E /I /Y models dist\FaigueMitigation\models
xcopy /E /I /Y assets dist\FaigueMitigation\assets
copy config\config.json dist\FaigueMitigation\config\
copy README.txt LICENSE CHANGELOG.md version.json dist\FaigueMitigation\
python tools/validate_build.py dist/FaigueMitigation
```

## Distribution layout

```
FaigueMitigation/
├── FaigueMitigation.exe
├── _internal/          # Python runtime + PySide6/TensorFlow/OpenCV
├── models/             # AI models (updatable without rebuild)
├── assets/             # icon.ico, logo.png, styles/, fonts/
├── config/config.json  # auto-created if missing
├── storage/            # logs, pending, screenshots, videos, cache
├── README.txt  LICENSE  CHANGELOG.md  version.json
```

The app uses a **portable** layout: `config/` and `storage/` live next to the
`.exe`, so no installation or admin rights are needed.
