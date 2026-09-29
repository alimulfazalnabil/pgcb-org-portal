#!/usr/bin/env python3
"""
Official PGCB Diprokous (2026-2028 Term) Member & Voter List Importer.

Supports:
  1. Validating the 1,457-member official dataset in dry-run mode (default, keeps synthetic test DB untouched):
       python scripts/import_official_member_list.py --dry-run
  2. Importing all 20 Branch Committees / Grid Circles and 1,457 official members into PostgreSQL/SQLite:
       python scripts/import_official_member_list.py --apply
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import secrets
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DEFAULT_JSON_PATH = ROOT_DIR / "data" / "pgcb_members_official_2026_2028.json"
DEFAULT_CSV_PATH = ROOT_DIR / "data" / "pgcb_members_official_2026_2028.csv"
DEFAULT_SQL_PATH = ROOT_DIR / "data" / "pgcb_members_official_2026_2028.sql"


def load_official_dataset(json_path: Path = DEFAULT_JSON_PATH) -> dict:
    if not json_path.exists():
        raise FileNotFoundError(f"Official member dataset not found at: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_dataset(data: dict) -> dict:
    members = data.get("members", [])
    circles = data.get("circles", [])

    seen_membership_ids: set[str] = set()
    seen_diprokous_nos: set[str] = set()
    seen_employee_ids: set[str] = set()
    seen_emails: set[str] = set()
    errors: list[str] = []

    for idx, m in enumerate(members, start=1):
        mid = m.get("membership_id", "")
        dip_no = str(m.get("diprokous_member_no", ""))
        emp_id = str(m.get("employee_id", ""))
        email = str(m.get("email", "")).lower()

        if not mid.startswith("PGD-2026-"):
            errors.append(f"Row {idx}: invalid membership_id {mid!r}")
        if mid in seen_membership_ids:
            errors.append(f"Row {idx}: duplicate membership_id {mid!r}")
        seen_membership_ids.add(mid)

        if not dip_no.isdigit():
            errors.append(f"Row {idx}: non-numeric diprokous_member_no {dip_no!r}")
        if dip_no in seen_diprokous_nos:
            errors.append(f"Row {idx}: duplicate diprokous_member_no {dip_no!r}")
        seen_diprokous_nos.add(dip_no)

        if not emp_id.isdigit():
            errors.append(f"Row {idx}: non-numeric employee_id {emp_id!r}")
        if emp_id in seen_employee_ids:
            errors.append(f"Row {idx}: duplicate employee_id {emp_id!r}")
        seen_employee_ids.add(emp_id)

        if "@" not in email:
            errors.append(f"Row {idx}: invalid email {email!r}")
        if email in seen_emails:
            errors.append(f"Row {idx}: duplicate email {email!r}")
        seen_emails.add(email)

    return {
        "valid": len(errors) == 0 and len(members) == 1457 and len(circles) == 20,
        "total_members": len(members),
        "total_circles": len(circles),
        "unique_membership_ids": len(seen_membership_ids),
        "unique_diprokous_member_nos": len(seen_diprokous_nos),
        "unique_employee_ids": len(seen_employee_ids),
        "unique_emails": len(seen_emails),
        "errors": errors,
    }


def apply_to_database(data: dict) -> dict:
    from sqlalchemy import select
    from app.core.security import hash_password
    from app.db.session import SessionLocal
    from app.models import Circle, GridCircle, Member, Membership, User

    circles_data = data.get("circles", [])
    members_data = data.get("members", [])

    db = SessionLocal()
    created_circles = 0
    created_users = 0
    updated_members = 0
    created_members = 0

    try:
        circle_map: dict[str, int] = {}
        for c_item in circles_data:
            bn = c_item["circle_name_bn"]
            en = c_item["circle_name_en"]
            code = c_item["circle_code"]
            reg = c_item.get("region", "Bangladesh")

            circle_row = db.scalar(select(Circle).where(Circle.name_bn == bn))
            if not circle_row:
                circle_row = Circle(
                    name_bn=bn,
                    name_en=en,
                    description_bn=f"আওতাধীন শাখা কমিটি: {bn} ({en})",
                    active=True,
                )
                db.add(circle_row)
                db.flush()
                created_circles += 1
            circle_map[bn] = circle_row.id

            gc_row = db.scalar(select(GridCircle).where(GridCircle.code == code))
            if not gc_row:
                db.add(
                    GridCircle(
                        code=code,
                        name_bn=bn,
                        name_en=en,
                        region=reg,
                        is_active=True,
                    )
                )

        default_pwd_hash = hash_password(secrets.token_urlsafe(24))
        issue_dt = datetime(2026, 1, 1, 0, 0, 0)
        valid_dt = datetime(2028, 12, 31, 23, 59, 59)

        for m_item in members_data:
            email = m_item["email"].strip().lower()
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(
                    email=email,
                    password_hash=default_pwd_hash,
                    name_bn=m_item["name_bn"],
                    name_en=m_item.get("name_en"),
                    role="MEMBER",
                    mfa_enabled=False,
                    email_verified=True,
                    is_active=True,
                )
                db.add(user)
                db.flush()
                created_users += 1
            else:
                user.name_bn = m_item["name_bn"]
                if m_item.get("name_en"):
                    user.name_en = m_item["name_en"]

            c_id = circle_map.get(m_item["circle_name_bn"])
            note = f"ডিপ্রকৌস সদস্য নম্বর: {m_item['diprokous_member_no']} | কর্মস্থল: {m_item['workplace']}"

            conflict = db.scalar(
                select(Member).where(
                    (Member.membership_id == m_item["membership_id"])
                    | (Member.application_no == m_item["application_no"])
                )
            )
            if conflict and conflict.user_id != user.id:
                conflict.membership_id = f"DEMO-{conflict.id}-{conflict.membership_id}"
                if conflict.application_no == m_item["application_no"]:
                    conflict.application_no = f"DEMO-{conflict.id}-{conflict.application_no}"
                db.flush()

            member = db.scalar(select(Member).where(Member.user_id == user.id))
            if not member:
                member = Member(
                    user_id=user.id,
                    membership_id=m_item["membership_id"],
                    membership_type="GENERAL",
                    application_no=m_item["application_no"],
                    designation_bn=m_item["designation_bn"],
                    designation_en=m_item["designation_en"],
                    employee_id=m_item["employee_id"],
                    current_address=m_item["workplace"],
                    circle_id=c_id,
                    status="ACTIVE",
                    application_note=note,
                    issue_date=issue_dt,
                    validity_date=valid_dt,
                )
                db.add(member)
                db.flush()
                created_members += 1
            else:
                member.membership_id = m_item["membership_id"]
                member.application_no = m_item["application_no"]
                member.designation_bn = m_item["designation_bn"]
                member.designation_en = m_item["designation_en"]
                member.employee_id = m_item["employee_id"]
                member.current_address = m_item["workplace"]
                member.circle_id = c_id
                member.status = "ACTIVE"
                member.application_note = note
                member.issue_date = issue_dt
                member.validity_date = valid_dt
                updated_members += 1

            mem_rec = db.scalar(select(Membership).where(Membership.membership_id == m_item["membership_id"]))
            if not mem_rec:
                db.add(
                    Membership(
                        member_id=member.id,
                        membership_id=m_item["membership_id"],
                        membership_type="GENERAL",
                        status="ACTIVE",
                        issue_date=issue_dt,
                        validity_date=valid_dt,
                    )
                )

        db.commit()
        return {
            "applied": True,
            "created_circles": created_circles,
            "created_users": created_users,
            "created_members": created_members,
            "updated_members": updated_members,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Official PGCB Diprokous 1,457-Member Importer")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON_PATH, help="Path to official JSON dataset")
    parser.add_argument("--apply", action="store_true", help="Commit all 1,457 members to the database")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Validate dataset without modifying DB (default)")
    args = parser.parse_args()

    data = load_official_dataset(args.json)
    report = validate_dataset(data)

    print("======================================================================")
    print("PGCB Diprokous Official Voter/Member List (2026-2028) Validation")
    print("======================================================================")
    print(f"Document Title : {data.get('document_title_bn')}")
    print(f"Total Pages    : {data.get('total_pages')}")
    print(f"Total Circles  : {report['total_circles']}")
    print(f"Total Members  : {report['total_members']}")
    print(f"Unique PGD IDs : {report['unique_membership_ids']} (PGD-2026-0001 .. PGD-2026-1457)")
    print(f"Unique Dip Nos : {report['unique_diprokous_member_nos']}")
    print(f"Unique Emp IDs : {report['unique_employee_ids']}")
    print(f"Unique Emails  : {report['unique_emails']}")
    print(f"CSV Dataset    : {DEFAULT_CSV_PATH}")
    print(f"JSON Dataset   : {DEFAULT_JSON_PATH}")
    print(f"SQL Dataset    : {DEFAULT_SQL_PATH}")

    if not report["valid"]:
        print("\n[ERROR] Validation errors detected:")
        for err in report["errors"][:20]:
            print(f"  - {err}")
        return 1

    print("\n[OK] All 1,457 member records and 20 Branch Committees passed strict validation.")

    if args.apply:
        print("\n[APPLY] Importing 20 Branch Committees and 1,457 members into database...")
        db_res = apply_to_database(data)
        print(f"[DONE] Import result: {json.dumps(db_res, ensure_ascii=False)}")
    else:
        print("\n[DRY-RUN] Synthetic test database left untouched (pass --apply to import into DB).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
