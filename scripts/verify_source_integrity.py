#!/usr/bin/env python3
"""Verify preserved source files against SOURCE_MANIFEST.csv SHA-256 hashes."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SOURCE_MANIFEST.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    failures = 0
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["classification"] != "preserved_source":
                continue
            p = ROOT / row["public_path"]
            actual = sha256(p) if p.exists() else "MISSING"
            ok = actual == row["sha256"]
            print(("OK  " if ok else "FAIL") + f" {row['public_path']}  {actual}")
            failures += 0 if ok else 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
