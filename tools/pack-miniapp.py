#!/usr/bin/env python3
"""Pack a mini-app folder into <appId>-<version>.miniapp and print its index.json entry.

Usage: python tools/pack-miniapp.py <folder> [-o output_dir]
"""
import argparse
import hashlib
import json
import os
import sys
import zipfile

MAX_COMPRESSED = 10 * 1024 * 1024
ALLOWED_EXT = {
    "html", "htm", "js", "mjs", "css", "json", "png", "jpg", "jpeg", "gif",
    "webp", "svg", "ico", "woff", "woff2", "ttf", "otf", "txt", "map",
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("-o", "--out", default=".")
    args = p.parse_args()

    src = os.path.abspath(args.folder)
    manifest = json.load(open(os.path.join(src, "manifest.json"), encoding="utf-8"))
    app_id, version, vcode = manifest["appId"], manifest["version"], manifest["versionCode"]
    entry = manifest.get("entry", "index.html")
    if not os.path.isfile(os.path.join(src, entry)):
        sys.exit(f"entry file missing: {entry}")

    name = f"{app_id}-{version}.miniapp"
    out = os.path.join(args.out, name)
    os.makedirs(args.out, exist_ok=True)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(src):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, src).replace("\\", "/")
                ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                if ext not in ALLOWED_EXT:
                    sys.exit(f"forbidden extension: {rel}")
                z.write(full, rel)

    size = os.path.getsize(out)
    if size > MAX_COMPRESSED:
        os.remove(out)
        sys.exit(f"package too large: {size}")
    sha = hashlib.sha256(open(out, "rb").read()).hexdigest()
    entry_json = {
        "appId": app_id,
        "name": manifest["name"],
        "version": version,
        "versionCode": vcode,
        "type": manifest.get("type", "app"),
        "iconUrl": None,
        "packageUrl": name,
        "sha256": sha,
        "sizeBytes": size,
    }
    print(f"packed: {out} ({size} bytes)")
    print(json.dumps(entry_json, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
