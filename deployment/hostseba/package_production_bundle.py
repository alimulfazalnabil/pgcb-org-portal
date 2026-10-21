#!/usr/bin/env python3
"""
HostSeba Production Deployment Packaging Script
Creates a clean, production-ready deployment archive excluding dev/test artifacts,
local databases, and credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

EXCLUDE_PATTERNS = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".coverage",
    "htmlcov",
    "pgcb_portal.db",
    "test_*.db",
    ".env",
    "storage",
    "tests",
    "playwright-report",
    "test-results",
}


def should_exclude(rel_path: Path) -> bool:
    for part in rel_path.parts:
        if part in EXCLUDE_PATTERNS:
            return True
        if part.endswith(".pyc") or part.endswith(".pyo"):
            return True
        if part == ".env":
            return True
        if part.endswith(".db"):
            return True
    return False


def build_package(output_format: str = "zip", dist_dir: Path | None = None) -> tuple[Path, str]:
    if dist_dir is None:
        dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    archive_base = dist_dir / "pgcb-portal-hostseba-v1.1"

    files_to_pack: list[tuple[Path, str]] = []

    # Paths to include
    targets = [
        ("services/api", REPO_ROOT / "services" / "api"),
        ("apps/web", REPO_ROOT / "apps" / "web"),
        ("deployment/hostseba", REPO_ROOT / "deployment" / "hostseba"),
    ]

    for prefix, target_dir in targets:
        if not target_dir.exists():
            continue
        for root, dirs, files in os.walk(target_dir):
            root_path = Path(root)
            rel_to_repo = root_path.relative_to(REPO_ROOT)
            if should_exclude(rel_to_repo):
                dirs.clear()
                continue
            # Filter dirs in-place
            dirs[:] = [d for d in dirs if not should_exclude(rel_to_repo / d)]
            for file in files:
                file_path = root_path / file
                file_rel = file_path.relative_to(REPO_ROOT)
                if should_exclude(file_rel):
                    continue
                arcname = str(file_rel).replace("\\", "/")
                files_to_pack.append((file_path, arcname))

    if output_format.lower() == "zip":
        archive_path = dist_dir / "pgcb-portal-hostseba-v1.1.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path, arcname in sorted(files_to_pack, key=lambda x: x[1]):
                zf.write(file_path, arcname)
    else:
        archive_path = dist_dir / "pgcb-portal-hostseba-v1.1.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tf:
            for file_path, arcname in sorted(files_to_pack, key=lambda x: x[1]):
                tf.add(file_path, arcname=arcname)

    # Compute SHA-256
    sha256 = hashlib.sha256()
    with open(archive_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    digest = sha256.hexdigest()

    return archive_path, digest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HostSeba production bundle")
    parser.add_argument("--format", choices=["zip", "tar.gz"], default="zip", help="Archive format")
    args = parser.parse_args()

    print(f"Building HostSeba production deployment bundle ({args.format})...")
    archive_path, digest = build_package(args.format)
    size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"[+] Archive created : {archive_path}")
    print(f"[+] Archive size    : {size_mb:.2f} MB")
    print(f"[+] SHA-256 Checksum: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
