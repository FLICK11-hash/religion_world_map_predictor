#!/usr/bin/env python3
"""Check a local data/ directory against the committed provenance manifest.

    python scripts/verify_data.py

For every input listed in config/data_manifest.json, reports whether the file is present and
whether its SHA-256 matches the bytes the committed results were produced from. A mismatch is
not necessarily an error -- WPP and WRP are revised over time -- but it does mean results
produced from your files are not the committed results, and should not be reported as such.

Exit status: 0 if every required file is present and matches, 1 otherwise.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "config" / "data_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate(rel: str) -> Path | None:
    """Optional files may sit in data/raw/extra/ (current) or data/raw/step7/ (older layout)."""
    candidates = [ROOT / rel]
    if "/step7/" in rel:
        candidates.append(ROOT / rel.replace("/step7/", "/extra/"))
    return next((p for p in candidates if p.exists()), None)


def check(entries, label) -> tuple[int, int]:
    ok = bad = 0
    print(f"\n{label}")
    for item in entries:
        found = locate(item["path"])
        if found is None:
            status = "MISSING"
        elif sha256(found) == item["sha256"]:
            status, ok = "ok", ok + 1
        else:
            status = "DIFFERS"
        if status != "ok":
            bad += 1
        print(f"  {status:8} {item['path']}")
    return ok, bad


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf8"))
    r_ok, r_bad = check(manifest["required"], "Required")
    o_ok, o_bad = check(manifest["optional"], "Optional (the package degrades gracefully without these)")

    print("\nManual downloads (free Pew account; never committed)")
    for item in manifest["not_on_disk_manual"]:
        present = (ROOT / item["path"]).exists()
        print(f"  {'present' if present else 'absent':8} {item['path']}")
        if not present:
            print(f"           -> {item['consequence_if_absent']}")

    print(f"\nRequired {r_ok}/{r_ok + r_bad} match, optional {o_ok}/{o_ok + o_bad} match.")
    if r_bad:
        print("A required input is missing or differs: results will not match the committed results/.")
    return 1 if r_bad else 0


if __name__ == "__main__":
    sys.exit(main())
