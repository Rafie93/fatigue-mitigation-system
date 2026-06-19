"""Stamp version.json from a version string (e.g. a Git tag) and build number.

Usage:
    python tools/gen_version.py <version> [build_number]

If <version> is omitted/empty the existing value is kept. A leading 'v' in the
version (from a tag like v1.2.0) is stripped automatically."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(ROOT, "version.json")


def main() -> int:
    with open(VERSION_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    version = sys.argv[1].strip().lstrip("v") if len(sys.argv) > 1 else ""
    if version:
        data["version"] = version
    if len(sys.argv) > 2 and sys.argv[2].strip().isdigit():
        data["build"] = int(sys.argv[2])

    with open(VERSION_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")

    print(f"version.json -> version={data['version']} build={data['build']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
