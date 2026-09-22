#!/usr/bin/env python3
"""
PGCB Organization Portal - Persistent Disk Upload & Persistence Verification CLI
Validates that file uploads are written to disk, paths are contained within
the storage root, and readbacks preserve exact binary and SHA-256 integrity.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

# Add project paths to sys.path
_script_dir = Path(__file__).resolve().parent
_api_dir = _script_dir.parent if _script_dir.name == "scripts" and _script_dir.parent.name == "api" else _script_dir.parent / "services" / "api"
_repo_root = _api_dir.parent.parent if _api_dir.name == "api" else _script_dir.parent

for path in (_repo_root, _api_dir):
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.storage.disk import DiskStorageBackend, safe_name


def verify_storage_persistence(target_root: Path | str | None = None) -> bool:
    print("=" * 70)
    print(" PGCB PORTAL PERSISTENT DISK UPLOAD & STORAGE VERIFICATION")
    print("=" * 70)

    if target_root:
        root_path = Path(target_root).resolve()
    else:
        root_path = Path(os.getenv("STORAGE_ROOT", "/var/data/uploads" if os.getenv("APP_ENV") == "production" else "./storage")).resolve()

    print(f"[*] Target Storage Root : {root_path}")
    print(f"[*] Environment         : {os.getenv('APP_ENV', 'development')}")

    backend = DiskStorageBackend(root_path)

    # 1. Test Directory Structure Initialization
    print("\n[STEP 1] Initializing persistent disk root & subdirectories...")
    try:
        backend.ensure_root_exists()
        for sub in ("public", "members", "cards", "certificates"):
            sub_path = root_path / sub
            if not sub_path.exists():
                print(f"  [-] Missing expected subdirectory: {sub_path}")
                return False
            print(f"  [+] Subdirectory verified: {sub}/")
        print("  [+] Root structure check PASSED.")
    except Exception as exc:
        print(f"  [!] Failed to initialize storage root: {exc}")
        return False

    # 2. Test Member Document Upload Persistence
    print("\n[STEP 2] Testing member document write & readback...")
    sample_pdf = b"%PDF-1.4\n%PGCB Automated Storage Persistence Canary\n%%EOF"
    sample_pdf_hash = hashlib.sha256(sample_pdf).hexdigest()
    test_member_id = 99999
    doc_filename = "canary_verification_cert.pdf"

    try:
        saved_path_str = backend.save(sample_pdf, f"members/{test_member_id}", doc_filename)
        saved_path = Path(saved_path_str)
        print(f"  [+] Saved file path : {saved_path}")

        if not saved_path.exists():
            print(f"  [-] ERROR: File was reported saved but does not exist on disk!")
            return False

        read_content = backend.read(saved_path_str)
        read_hash = hashlib.sha256(read_content).hexdigest()

        if read_hash != sample_pdf_hash:
            print(f"  [-] ERROR: SHA-256 mismatch! Upload: {sample_pdf_hash} | Read: {read_hash}")
            return False

        print(f"  [+] SHA-256 match   : {read_hash}")
        print("  [+] Member document persistence PASSED.")

        # Cleanup test canary
        backend.delete(saved_path_str)
        if saved_path.exists():
            print(f"  [!] Warning: Failed to clean up canary file {saved_path}")
        else:
            print("  [+] Cleanup verified.")
    except Exception as exc:
        print(f"  [-] Member document test failed: {exc}")
        return False

    # 3. Test Public Asset Persistence
    print("\n[STEP 3] Testing public asset write & readback...")
    sample_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    sample_png_hash = hashlib.sha256(sample_png).hexdigest()
    asset_filename = "canary_public_banner.png"

    try:
        saved_asset_str = backend.save(sample_png, "public", asset_filename)
        saved_asset_path = Path(saved_asset_str)
        print(f"  [+] Saved asset path: {saved_asset_path}")

        read_asset = backend.read(saved_asset_str)
        if hashlib.sha256(read_asset).hexdigest() != sample_png_hash:
            print("  [-] ERROR: Public asset hash mismatch!")
            return False

        print("  [+] Public asset persistence PASSED.")
        backend.delete(saved_asset_str)
    except Exception as exc:
        print(f"  [-] Public asset test failed: {exc}")
        return False

    # 4. Test Path Traversal Protection
    print("\n[STEP 4] Testing path traversal security defenses...")
    malicious_paths = [
        "../../etc/passwd",
        "../secret.txt",
        "/etc/shadow",
        "members/../../root_breach.txt",
    ]

    for attack in malicious_paths:
        try:
            backend._resolve_candidate(attack)
            print(f"  [-] SECURITY FLAW: Path traversal was NOT rejected: {attack}")
            return False
        except (ValueError, Exception):
            print(f"  [+] Attack rejected successfully: {attack}")

    print("  [+] Path traversal defenses PASSED.")

    # 5. Summary
    print("\n" + "=" * 70)
    print(" RESULT: ALL PERSISTENT DISK UPLOAD CHECKS PASSED (100% SUCCESS)")
    print("=" * 70)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify PGCB Portal persistent disk uploads")
    parser.add_argument("--storage-root", help="Custom storage root path to test", default=None)
    args = parser.parse_args()

    success = verify_storage_persistence(args.storage_root)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
