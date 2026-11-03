#!/usr/bin/env python3
"""
Dedicated Administrator Bootstrap Utility for PGCB Organization Portal.
Usage:
    python -m app.scripts.create_admin --email admin@example.org --password MyStrongPassword123! --name "System Admin"
Or via environment variables:
    ADMIN_EMAIL=admin@example.org ADMIN_PASSWORD=Secret ADMIN_NAME="Admin" python -m app.scripts.create_admin
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure services/api is on sys.path for direct execution (e.g., cPanel Setup Python App)
_API_DIR = Path(__file__).resolve().parent.parent.parent
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from sqlalchemy import select
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User

UNSAFE_PASSWORDS = {
    "secret",
    "admin",
    "admin123",
    "password",
    "password123",
    "changeme",
    "changeme123!",
    "mystrongpassword123!",
    "12345678",
    "123456789",
    "1234567890",
    "root",
    "toor",
    "pgcb123",
    "pgcb2026",
}


def validate_admin_credentials(email: str, password: str, is_prod: bool = False) -> None:
    """Validate administrator email and password against unsafe defaults and production constraints."""
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError(f"Invalid administrator email address: '{email}'")

    domain = email.split("@")[-1].lower().strip()
    if is_prod and domain in ("example.com", "example.org", "test.com", "localhost"):
        raise ValueError(f"Unsafe placeholder email domain '@{domain}' rejected in production/staging.")

    clean_pw = (password or "").strip()
    if clean_pw.lower() in UNSAFE_PASSWORDS:
        raise ValueError(
            "Unsafe default password rejected. Please choose a strong, unique password."
        )

    min_len = 12 if is_prod else 8
    if len(clean_pw) < min_len:
        raise ValueError(
            f"Admin password too short ({len(clean_pw)} chars). Must be at least {min_len} characters."
        )


def bootstrap_admin(
    email: str,
    password: str,
    name: str = "System Admin",
    force_reset_password: bool = False,
) -> User:
    email = email.lower().strip()
    validate_admin_credentials(email, password, is_prod=settings.is_production_like)

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            # Preserve existing administrator password unless explicitly requested
            if force_reset_password:
                print(f"[*] User {email} already exists. Explicit password reset requested; updating password...")
                user.password_hash = hash_password(password)
            else:
                print(f"[*] User {email} already exists. Retaining existing password. Ensuring SUPER_ADMIN role and active status...")

            user.role = "SUPER_ADMIN"
            user.is_active = True
            user.email_verified = True
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            print(f"[✓] Administrator {email} validated and active.")
            return user

        print(f"[*] Creating new SUPER_ADMIN user: {email}...")
        new_admin = User(
            email=email,
            password_hash=hash_password(password),
            name_bn=name,
            name_en=name,
            role="SUPER_ADMIN",
            is_active=True,
            email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print(f"[✓] Administrator {email} created successfully.")
        return new_admin


def main():
    parser = argparse.ArgumentParser(description="Create or ensure a PGCB Portal SUPER_ADMIN")
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL"), help="Admin email address")
    parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"), help="Admin password")
    parser.add_argument("--name", default=os.getenv("ADMIN_NAME", "সিস্টেম অ্যাডমিন"), help="Admin display name")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        default=os.getenv("RESET_ADMIN_PASSWORD", "").lower() in ("true", "1", "yes"),
        help="Explicitly reset password if user already exists",
    )

    args = parser.parse_args()

    if not args.email or not args.password:
        print("[!] Error: --email and --password are required (or set ADMIN_EMAIL & ADMIN_PASSWORD env vars).", file=sys.stderr)
        sys.exit(1)

    try:
        bootstrap_admin(
            args.email,
            args.password,
            args.name,
            force_reset_password=args.reset_password,
        )
    except ValueError as exc:
        print(f"[!] Validation Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[!] Bootstrap Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
