"""Validate a PyInstaller --onedir build (PRD §14 Build Validation).

Fails (non-zero exit) if any required file/folder is missing or the executable
is too small, so the CI pipeline marks the build as failed.

Usage:
    python tools/validate_build.py <dist_dir>
"""
import os
import sys

EXE_NAME = "FaigueMitigation.exe"
MIN_EXE_BYTES = 500 * 1024  # a valid PyInstaller bootloader is well above this

REQUIRED_DIRS = ["models", "assets", "config", "storage", "_internal"]
REQUIRED_FILES = [
    EXE_NAME,
    "version.json",
    "README.txt",
    "LICENSE",
    os.path.join("models", "model_eye_mobilenet.h5"),
    os.path.join("models", "model_mouth_mobilenet.h5"),
    os.path.join("config", "config.json"),
]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate_build.py <dist_dir>")
        return 2
    dist = sys.argv[1]
    errors = []

    for d in REQUIRED_DIRS:
        if not os.path.isdir(os.path.join(dist, d)):
            errors.append(f"missing directory: {d}/")

    for f in REQUIRED_FILES:
        path = os.path.join(dist, f)
        if not os.path.isfile(path):
            errors.append(f"missing file: {f}")

    exe_path = os.path.join(dist, EXE_NAME)
    if os.path.isfile(exe_path):
        size = os.path.getsize(exe_path)
        if size < MIN_EXE_BYTES:
            errors.append(f"executable too small: {size} bytes")
        else:
            print(f"executable OK: {size / 1024:.0f} KB")

    if errors:
        print("BUILD VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("BUILD VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
