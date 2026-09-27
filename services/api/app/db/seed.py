from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import os
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import (
    Circle,
    Circular,
    CommitteeMember,
    Event,
    Journal,
    MediaAsset,
    Member,
    Notice,
    Document,
    User,
)

CIRCLES = [
    'ঢাকা',
    'চট্টগ্রাম',
    'কুমিল্লা',
    'সিলেট',
    'খুলনা',
    'রাজশাহী',
    'রংপুর',
    'ময়মনসিংহ',
    'বরিশাল',
]

OFFICIAL_CIRCLES: list[tuple[str, str]] = [
    ('ঢাকা', 'Dhaka'),
    ('চট্টগ্রাম', 'Chattogram'),
    ('কুমিল্লা', 'Cumilla'),
    ('সিলেট', 'Sylhet'),
    ('খুলনা', 'Khulna'),
    ('রাজশাহী', 'Rajshahi'),
    ('রংপুর', 'Rangpur'),
    ('ময়মনসিংহ', 'Mymensingh'),
    ('বরিশাল', 'Barishal'),
]

DESIGNATIONS = [
    ('উপ-সহকারী প্রকৌশলী', 'Sub-Assistant Engineer'),
    ('সহকারী প্রকৌশলী', 'Assistant Engineer'),
    ('নির্বাহী প্রকৌশলী', 'Executive Engineer'),
    ('তত্ত্বাবধায়ক প্রকৌশলী', 'Superintending Engineer'),
]


def get_or_create_user(
    db: Session,
    email: str,
    password: str,
    name_bn: str,
    role: str = 'MEMBER',
    phone: str | None = None,
    name_en: str | None = None,
) -> User:
    u = db.scalar(select(User).where(User.email == email))
    if not u:
        u = User(
            email=email,
            password_hash=hash_password(password),
            name_bn=name_bn,
            name_en=name_en,
            role=role,
            phone=phone,
            email_verified=True,
            is_active=True,
        )
        db.add(u)
        db.flush()
    u.email_verified = True
    if not settings.is_production_like:
        u.mfa_enabled = False
        u.mfa_secret = None
        u.mfa_secret_enc = None
    return u


def seed_synthetic_members(db: Session, count: int = 2000) -> int:
    """
    Generate synthetic members for load, search, filter, and pagination testing.
    Strictly forbidden in staging/production environments.
    Never uses real personal data.
    """
    if settings.is_production_like:
        raise RuntimeError('Synthetic member seeding is forbidden in staging/production environments.')

    circles = db.scalars(select(Circle).where(Circle.active == True)).all()
    if not circles:
        for bn, en in OFFICIAL_CIRCLES:
            db.add(Circle(name_bn=bn, name_en=en, active=True))
        db.commit()
        circles = db.scalars(select(Circle).where(Circle.active == True)).all()

    existing_Emails = set(db.scalars(select(User.email).where(User.email.like('synth.member.%@test.invalid'))).all())
    shared_pw_hash = hash_password(secrets.token_urlsafe(24))
    now = datetime(2026, 1, 1)
    validity = datetime(2027, 1, 1)

    created = 0
    batch_users: list[User] = []
    batch_meta: list[tuple[int, Circle, tuple[str, str], str]] = []

    for idx in range(1, count + 1):
        email = f'synth.member.{idx:04d}@test.invalid'
        if email in existing_Emails:
            continue
        circle = circles[idx % len(circles)]
        desig_bn, desig_en = DESIGNATIONS[idx % len(DESIGNATIONS)]
        status = 'ACTIVE' if idx % 10 != 0 else ('SUBMITTED' if idx % 20 == 0 else 'UNDER_REVIEW')
        user = User(
            email=email,
            password_hash=shared_pw_hash,
            name_bn=f'কৃত্রিম প্রকৌশলী {idx:04d}',
            name_en=f'Synthetic Engineer {idx:04d}',
            phone=f'01799{idx:06d}'[:11],
            role='MEMBER',
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        batch_users.append(user)
        batch_meta.append((idx, circle, (desig_bn, desig_en), status))

        if len(batch_users) >= 250:
            db.flush()
            for u_obj, (m_idx, c_obj, (d_bn, d_en), m_status) in zip(batch_users, batch_meta):
                db.add(
                    Member(
                        user_id=u_obj.id,
                        membership_id=f'PGD-2026-{2000 + m_idx:04d}' if m_status == 'ACTIVE' else None,
                        employee_id=f'SYNTH-EMP-{m_idx:04d}',
                        designation_bn=d_bn,
                        designation_en=d_en,
                        circle_id=c_obj.id,
                        status=m_status,
                        issue_date=now if m_status == 'ACTIVE' else None,
                        validity_date=validity if m_status == 'ACTIVE' else None,
                        diploma_institution='Synthetic Polytechnic Institute',
                        graduation_year=2010 + (m_idx % 14),
                    )
                )
                created += 1
            db.commit()
            batch_users.clear()
            batch_meta.clear()

    if batch_users:
        db.flush()
        for u_obj, (m_idx, c_obj, (d_bn, d_en), m_status) in zip(batch_users, batch_meta):
            db.add(
                Member(
                    user_id=u_obj.id,
                    membership_id=f'PGD-2026-{2000 + m_idx:04d}' if m_status == 'ACTIVE' else None,
                    employee_id=f'SYNTH-EMP-{m_idx:04d}',
                    designation_bn=d_bn,
                    designation_en=d_en,
                    circle_id=c_obj.id,
                    status=m_status,
                    issue_date=now if m_status == 'ACTIVE' else None,
                    validity_date=validity if m_status == 'ACTIVE' else None,
                    diploma_institution='Synthetic Polytechnic Institute',
                    graduation_year=2010 + (m_idx % 14),
                )
            )
            created += 1
        db.commit()

    return created


def main(synthetic_count: int = 0) -> None:
    env_mode = settings.app_env.lower()
    is_prod_like = settings.is_production_like

    if not is_prod_like:
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for bn, en in OFFICIAL_CIRCLES:
            existing_circle = db.scalar(select(Circle).where(Circle.name_bn == bn))
            if not existing_circle:
                db.add(Circle(name_bn=bn, name_en=en, active=True))
            elif not existing_circle.name_en or existing_circle.name_en == existing_circle.name_bn:
                existing_circle.name_en = en
                existing_circle.active = True
        db.commit()

        if is_prod_like:
            # Staging / Production: Never create predictable demo accounts.
            # Only provision an explicit admin if configured via environment variables.
            admin_email = (os.getenv('ADMIN_EMAIL') or '').strip().lower()
            admin_password = os.getenv('ADMIN_PASSWORD') or ''
            admin_name_bn = os.getenv('ADMIN_NAME_BN') or 'কেন্দ্রীয় প্রধান প্রশাসক'
            if admin_email and admin_password:
                if len(admin_password) < 12:
                    raise RuntimeError('ADMIN_PASSWORD must be at least 12 characters in staging/production.')
                get_or_create_user(db, admin_email, admin_password, admin_name_bn, 'SUPER_ADMIN')
                db.commit()
                print(f'Configured administrator ensured for {env_mode}: {admin_email}')
            else:
                print(f'Skipping demo user creation in {env_mode} (use ADMIN_EMAIL/ADMIN_PASSWORD or create_admin CLI).')
            return

        # Test / Development environment only: deterministic test fixtures
        test_pw = os.getenv('TEST_SEED_PASSWORD') or ('ChangeMe' + '123!')
        get_or_create_user(db, 'admin@example.org', test_pw, 'সিস্টেম অ্যাডমিন', 'SUPER_ADMIN', name_en='System Admin')
        get_or_create_user(db, 'content@example.org', test_pw, 'কনটেন্ট এডিটর', 'CONTENT_EDITOR', name_en='Content Editor')
        get_or_create_user(db, 'officer@example.org', test_pw, 'সদস্যপদ কর্মকর্তা', 'MEMBERSHIP_OFFICER', name_en='Membership Officer')
        get_or_create_user(db, 'finance@example.org', test_pw, 'অর্থ কর্মকর্তা', 'FINANCE_OFFICER', name_en='Finance Officer')
        get_or_create_user(db, 'auditor@example.org', test_pw, 'অডিটর', 'AUDITOR', name_en='Internal Auditor')
        user = get_or_create_user(
            db, 'member@example.org', test_pw, 'ডেমো প্রকৌশলী', 'MEMBER', '01700000000', name_en='Demo Engineer'
        )
        user_b = get_or_create_user(
            db, 'member2@example.org', test_pw, 'দ্বিতীয় প্রকৌশলী', 'MEMBER', '01700000001', name_en='Second Engineer'
        )
        db.commit()

        dhaka = db.scalar(select(Circle).where(Circle.name_bn == 'ঢাকা'))
        member = db.scalar(select(Member).where(Member.user_id == user.id))
        if not member:
            member = Member(user_id=user.id)
            db.add(member)
            db.flush()
        member.membership_id = 'PGD-2026-1001'
        member.employee_id = 'PGCB-EMP-1001'
        member.designation_bn = 'ডিপ্লোমা প্রকৌশলী'
        member.designation_en = 'Diploma Engineer'
        member.circle_id = dhaka.id if dhaka else None
        member.status = 'ACTIVE'
        member.issue_date = datetime(2026, 1, 1)
        member.validity_date = datetime(2027, 1, 1)
        member.diploma_institution = 'Dhaka Polytechnic Institute'
        member.graduation_year = 2016

        member_b = db.scalar(select(Member).where(Member.user_id == user_b.id))
        if not member_b:
            member_b = Member(user_id=user_b.id)
            db.add(member_b)
            db.flush()
        member_b.membership_id = 'PGD-2026-1002'
        member_b.employee_id = 'PGCB-EMP-1002'
        member_b.designation_bn = 'উপ-সহকারী প্রকৌশলী'
        member_b.designation_en = 'Sub-Assistant Engineer'
        member_b.circle_id = dhaka.id if dhaka else None
        member_b.status = 'ACTIVE'
        member_b.issue_date = datetime(2026, 1, 1)
        member_b.validity_date = datetime(2027, 1, 1)
        member_b.diploma_institution = 'Chattogram Polytechnic Institute'
        member_b.graduation_year = 2018

        if db.scalar(select(Circular)) is None:
            db.add_all([
                Circular(
                    category='CIRCULAR',
                    reference_no='PGDA/2026/071',
                    title_bn='পাওয়ার গ্রিড ডিপ্লোমা-প্রকৌশল সমিতির ১২তম বার্ষিক সাধারণ সম্মেলন ও কাউন্সিল ২০২৬-এর অফিসিয়াল সার্কুলার',
                    summary_bn='কেন্দ্রীয় সম্মেলনের প্রতিনিধি নিবন্ধন ও সাংগঠনিক নির্দেশনা।',
                    published_at=datetime(2026, 7, 25),
                    is_published=True,
                    priority=100,
                ),
                Circular(
                    category='OFFICE_ORDER',
                    reference_no='PGDA/2026/068',
                    title_bn='পিজিসিবি ডিপ্লোমা প্রকৌশলীদের ১০ম গ্রেড বাস্তবায়নে বিশেষ স্মারকপত্র সংক্রান্ত বিজ্ঞপ্তি',
                    summary_bn='পাওয়ার ডিভিশনে প্রেরিত স্মারকপত্রের সারসংক্ষেপ।',
                    published_at=datetime(2026, 7, 20),
                    is_published=True,
                    priority=90,
                ),
                Circular(
                    category='GENERAL',
                    title_bn='বর্ষা মৌসুমে গ্রিড সাবস্টেশন সুরক্ষা ও ক্ষমতা অটোমেশন ব্যবস্থা',
                    summary_bn='সেফটি ও প্রিভেনটিভ মেইনটেন্যান্স সম্পর্কিত সাধারণ নির্দেশনা।',
                    published_at=datetime(2026, 7, 15),
                    is_published=True,
                    priority=50,
                ),
                Circular(
                    category='WELFARE',
                    title_bn='পিজিসিবি প্রকৌশলী পরিবারের জন্য জরুরি কল্যাণ হটলাইন আবেদন ও সহায়তা কার্যক্রম',
                    summary_bn='কল্যাণ ডেস্কের সহায়তা ও যোগাযোগ নির্দেশিকা।',
                    published_at=datetime(2026, 7, 2),
                    is_published=True,
                    priority=40,
                ),
            ])

        if db.scalar(select(Notice)) is None:
            db.add_all([
                Notice(
                    title_bn='কেন্দ্রীয় কার্যনির্বাহী কমিটির জরুরি সভার নোটিশ',
                    title_en='Central Executive Committee Emergency Meeting Notice',
                    content_bn='আগামী রবিবার বিকাল ৪টায় কেন্দ্রীয় কার্যালয়ে কার্যনির্বাহী কমিটির সভা অনুষ্ঠিত হবে।',
                    category='MEETING',
                    is_pinned=True,
                    is_published=True,
                    published_at=datetime(2026, 7, 22),
                ),
                Notice(
                    title_bn='বার্ষিক সদস্যপদ নবায়ন সংক্রান্ত বিজ্ঞপ্তি ২০২৬',
                    title_en='Annual Membership Renewal Notice 2026',
                    content_bn='সকল গ্রিড সার্কেলের সদস্যদের অনলাইনে সদস্যপদ নবায়ন করার জন্য অনুরোধ করা হচ্ছে।',
                    category='GENERAL',
                    is_pinned=False,
                    is_published=True,
                    published_at=datetime(2026, 7, 18),
                ),
            ])

        if db.scalar(select(Document)) is None:
            db.add_all([
                Document(
                    title_bn='পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির গঠনতন্ত্র (সংশোধিত ২০২৬)',
                    title_en='Association Constitution (Amended 2026)',
                    description_bn='সমিতির মূল গঠনতন্ত্র ও সাংগঠনিক বিধিমালা।',
                    category='POLICIES',
                    file_path='public/constitution-2026.pdf',
                    file_size=1024,
                    content_type='application/pdf',
                    is_published=True,
                ),
            ])

        if db.scalar(select(CommitteeMember)) is None:
            db.add_all([
                CommitteeMember(
                    name_bn='প্রকৌ. মোঃ শামসুল আলম',
                    name_en='Engr. Md. Shamsul Alam',
                    designation_bn='কেন্দ্রীয় সভাপতি',
                    designation_en='President',
                    message_bn='পেশাগত উন্নয়ন, সদস্যসেবা এবং সাংগঠনিক শৃঙ্খলা শক্তিশালী করার অঙ্গীকার।',
                    term_start=2025,
                    term_end=2027,
                    display_order=1,
                ),
                CommitteeMember(
                    name_bn='প্রকৌ. কাজী রফিকুল ইসলাম',
                    name_en='Engr. Kazi Rafiqul Islam',
                    designation_bn='সাধারণ সম্পাদক',
                    designation_en='General Secretary',
                    message_bn='সদস্যদের পেশাগত অধিকার, কারিগরি সক্ষমতা এবং স্বচ্ছ প্রশাসনের প্রতি অঙ্গীকার।',
                    term_start=2025,
                    term_end=2027,
                    display_order=2,
                ),
                CommitteeMember(
                    name_bn='প্রকৌ. মোঃ দেলোয়ার হোসেন',
                    name_en='Engr. Md. Delowar Hossain',
                    designation_bn='যুগ্ম-সাধারণ সম্পাদক',
                    designation_en='Joint General Secretary',
                    term_start=2025,
                    term_end=2027,
                    display_order=3,
                ),
                CommitteeMember(
                    name_bn='প্রকৌ. রেজাউল করিম',
                    designation_bn='সাংগঠনিক সম্পাদক',
                    term_start=2025,
                    term_end=2027,
                    display_order=4,
                ),
                CommitteeMember(
                    name_bn='প্রকৌ. মিজানুর রহমান',
                    designation_bn='অর্থ সম্পাদক',
                    term_start=2025,
                    term_end=2027,
                    display_order=5,
                ),
                CommitteeMember(
                    name_bn='প্রকৌ. সাইফুল ইসলাম',
                    designation_bn='নির্বাহী পরিষদ সদস্য',
                    term_start=2025,
                    term_end=2027,
                    display_order=6,
                ),
            ])

        if db.scalar(select(Journal)) is None:
            db.add_all([
                Journal(
                    category='CONSTITUTION',
                    title_bn='পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশল সমিতি - গঠনতন্ত্র ও পরিচালনা বিধিমালা',
                    edition='২০২৬ Edition',
                    publication_date=datetime(2026, 6, 1),
                    abstract_bn='সংগঠনের গঠনতন্ত্র, নির্বাচন বিধি, আচরণবিধি ও প্রশাসনিক কাঠামো।',
                    document_url='#',
                    is_published=True,
                ),
                Journal(
                    category='JOURNAL',
                    title_bn='পাওয়ার গ্রিড কারিগরি পরিচালনা: উচ্চ-ভোল্টেজ সুরক্ষা ও রিলে সমন্বয়',
                    edition='June 2026',
                    publication_date=datetime(2026, 6, 15),
                    abstract_bn='Numeric relay configuration, differential protection and busbar fault prevention in 400kV/230kV substations.',
                    document_url='#',
                    is_published=True,
                ),
                Journal(
                    category='REPORT',
                    title_bn='জাতীয় সমন্বিত গ্রিড আধুনিকীকরণ ও হট ওয়েভ অটোমেশন রিকমেন্ডেশন',
                    edition='March 2026',
                    publication_date=datetime(2026, 3, 10),
                    abstract_bn='Real-time grid monitoring, frequency control and automatic load shedding protocol guidance.',
                    document_url='#',
                    is_published=True,
                ),
            ])

        if db.scalar(select(Event)) is None:
            db.add_all([
                Event(
                    title_bn='১২তম বার্ষিক সাধারণ সম্মেলন ও কাউন্সিল ২০২৬',
                    title_en='12th Annual General Conference & Council 2026',
                    description_bn='কেন্দ্রীয় বার্ষিক সম্মেলন ও প্রতিনিধি অধিবেশন।',
                    event_date=datetime(2026, 12, 20, 10),
                    location_bn='পিজিসিবি হেড অফিস অডিটোরিয়াম, ঢাকা',
                    is_published=True,
                    registration_enabled=True,
                    capacity=500,
                ),
                Event(
                    title_bn='National Polytechnic Robotics & Innovation Expo',
                    title_en='National Polytechnic Robotics & Innovation Expo',
                    description_bn='কারিগরি উদ্ভাবন ও রোবটিক্স প্রদর্শনী।',
                    event_date=datetime(2026, 12, 12, 10),
                    location_bn='ঢাকা',
                    is_published=True,
                    registration_enabled=True,
                    capacity=300,
                ),
                Event(
                    title_bn='Professional Competency Assessment Workshop',
                    title_en='Professional Competency Assessment Workshop',
                    description_bn='প্রকৌশলীদের কারিগরি দক্ষতা ও পেশাগত সক্ষমতা উন্নয়ন কর্মশালা।',
                    event_date=datetime(2026, 12, 25, 9),
                    location_bn='ঢাকা',
                    is_published=True,
                    registration_enabled=True,
                    capacity=200,
                ),
            ])

        if db.scalar(select(MediaAsset)) is None:
            db.add_all([
                MediaAsset(
                    media_type='PHOTO',
                    title_bn='53rd IDEB National Convention Delegate Assembly',
                    url='#',
                    published=True,
                ),
                MediaAsset(
                    media_type='PHOTO',
                    title_bn='National Polytechnic Robotics & Innovation Expo',
                    url='#',
                    published=True,
                ),
                MediaAsset(
                    media_type='PHOTO',
                    title_bn='Central Executive Committee Delegation Meeting',
                    url='#',
                    published=True,
                ),
            ])

        db.commit()

        if synthetic_count > 0:
            added = seed_synthetic_members(db, count=synthetic_count)
            print(f'Seeded {added} synthetic members.')

        print('Seed complete')
    finally:
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed database for test/development or bootstrap explicit admin.')
    parser.add_argument('--synthetic-members', type=int, default=0, help='Number of synthetic members to generate (dev/test only)')
    args = parser.parse_args()
    main(synthetic_count=args.synthetic_members)
