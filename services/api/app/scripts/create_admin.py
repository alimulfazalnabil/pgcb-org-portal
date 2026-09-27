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

from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User


def bootstrap_admin(email: str, password: str, name: str = "System Admin"):
    email = email.lower().strip()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            print(f"[*] User {email} already exists. Updating role to SUPER_ADMIN and activating...")
            user.role = "SUPER_ADMIN"
            user.is_active = True
            user.email_verified = True
            user.password_hash = hash_password(password)
            user.updated_at = datetime.utcnow()
            db.commit()
            print(f"[✓] Administrator {email} updated successfully.")
            return

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
        print(f"[✓] Administrator {email} created successfully.")


def main():
    parser = argparse.ArgumentParser(description="Create or update a PGCB Portal SUPER_ADMIN")
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL"), help="Admin email address")
    parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"), help="Admin password")
    parser.add_argument("--name", default=os.getenv("ADMIN_NAME", "সিস্টেম অ্যাডমিন"), help="Admin display name")

    args = parser.parse_args()

    if not args.email or not args.password:
        print("[!] Error: --email and --password are required (or set ADMIN_EMAIL & ADMIN_PASSWORD env vars).")
        sys.exit(1)

    if len(args.password) < 8:
        print("[!] Error: Admin password must be at least 8 characters long.")
        sys.exit(1)

    bootstrap_admin(args.email, args.password, args.name)


if __name__ == "__main__":
    main()
