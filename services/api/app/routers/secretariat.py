from __future__ import annotations

from datetime import datetime, timedelta
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import (
    Certificate,
    Circle,
    Document,
    Event,
    EventRegistration,
    Member,
    PaymentTransaction,
    SiteSetting,
    User,
)
from app.services import audit

router = APIRouter(prefix='/admin', tags=['secretariat'])

DEFAULT_EMAIL_TEMPLATES: dict[str, dict[str, Any]] = {
    'email_verification': {
        'key': 'email_verification',
        'name_bn': 'ইমেইল যাচাইকরণ',
        'name_en': 'Email Verification',
        'subject_bn': '[PGCB পোর্টাল] আপনার ইমেইল ঠিকানা যাচাই করুন',
        'subject_en': '[PGCB Portal] Verify Your Email Address',
        'body_bn': 'প্রিয় {{name}},\nপাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতি পোর্টালে নিবন্ধনের জন্য ধন্যবাদ। আপনার ইমেইল যাচাই করতে নিচের লিংকে ক্লিক করুন:\n{{verification_url}}',
        'body_en': 'Dear {{name}},\nThank you for registering on the PGCB Diploma Engineers Association Portal. Please verify your email address using the link below:\n{{verification_url}}',
        'placeholders': ['name', 'verification_url', 'expiry_hours'],
    },
    'password_reset': {
        'key': 'password_reset',
        'name_bn': 'পাসওয়ার্ড রিসেট',
        'name_en': 'Password Reset',
        'subject_bn': '[PGCB পোর্টাল] পাসওয়ার্ড রিসেট অনুরোধ',
        'subject_en': '[PGCB Portal] Password Reset Request',
        'body_bn': 'প্রিয় {{name}},\nআপনার পাসওয়ার্ড রিসেট করতে নিচের নিরাপদ লিংকটি ব্যবহার করুন:\n{{reset_url}}',
        'body_en': 'Dear {{name}},\nUse the secure link below to reset your portal password:\n{{reset_url}}',
        'placeholders': ['name', 'reset_url', 'ip_address'],
    },
    'membership_submitted': {
        'key': 'membership_submitted',
        'name_bn': 'সদস্যপদ আবেদন জমা সম্পন্ন',
        'name_en': 'Membership Application Submitted',
        'subject_bn': '[PGCB পোর্টাল] আপনার সদস্যপদ আবেদন গৃহীত হয়েছে',
        'subject_en': '[PGCB Portal] Membership Application Received',
        'body_bn': 'প্রিয় {{name}},\nআপনার সদস্যপদ আবেদন (রেফারেন্স: {{application_id}}) সফলভাবে জমা হয়েছে এবং প্রাথমিক যাচাইয়ের জন্য প্রেরিত হয়েছে।',
        'body_en': 'Dear {{name}},\nYour membership application (Ref: {{application_id}}) has been submitted and queued for eligibility review.',
        'placeholders': ['name', 'application_id', 'circle_name'],
    },
    'membership_under_review': {
        'key': 'membership_under_review',
        'name_bn': 'সদস্যপদ আবেদন পর্যালোচনাধীন',
        'name_en': 'Membership Under Review',
        'subject_bn': '[PGCB পোর্টাল] আপনার সদস্যপদ আবেদন পর্যালোচনাধীন রয়েছে',
        'subject_en': '[PGCB Portal] Your Membership Application is Under Review',
        'body_bn': 'প্রিয় {{name}},\nআপনার সদস্যপদ আবেদনটি বর্তমানে কেন্দ্রীয় সদস্যপদ যাচাই কমিটি কর্তৃক পর্যালোচনাধীন রয়েছে।',
        'body_en': 'Dear {{name}},\nYour membership application is currently under review by the Central Membership Verification Committee.',
        'placeholders': ['name', 'reviewer_note'],
    },
    'membership_approved': {
        'key': 'membership_approved',
        'name_bn': 'সদস্যপদ অনুমোদিত',
        'name_en': 'Membership Approved',
        'subject_bn': '[PGCB পোর্টাল] অভিনন্দন! আপনার সদস্যপদ অনুমোদিত হয়েছে ({{membership_id}})',
        'subject_en': '[PGCB Portal] Congratulations! Membership Approved ({{membership_id}})',
        'body_bn': 'প্রিয় {{name}},\nআপনার সদস্যপদ অনুমোদিত হয়েছে। আপনার অফিসিয়াল সদস্য আইডি: {{membership_id}}। আপনি এখন পোর্টাল থেকে ডিজিটাল আইডি কার্ড ও সনদপত্র ডাউনলোড করতে পারবেন।',
        'body_en': 'Dear {{name}},\nYour membership has been approved. Your official Membership ID is {{membership_id}}. You can now download your Digital ID Card and Certificate.',
        'placeholders': ['name', 'membership_id', 'validity_date', 'portal_url'],
    },
    'membership_rejected': {
        'key': 'membership_rejected',
        'name_bn': 'সদস্যপদ আবেদন সংশোধন/প্রত্যাখ্যান',
        'name_en': 'Membership Application Rejected / Needs Correction',
        'subject_bn': '[PGCB পোর্টাল] সদস্যপদ আবেদনের আপডেট',
        'subject_en': '[PGCB Portal] Membership Application Status Update',
        'body_bn': 'প্রিয় {{name}},\nআপনার সদস্যপদ আবেদনটি নিম্নোক্ত কারণে অনুমোদন করা সম্ভব হয়নি: {{reason}}। অনুগ্রহ করে তথ্য সংশোধন করে পুনরায় জমা দিন।',
        'body_en': 'Dear {{name}},\nYour membership application requires correction for the following reason: {{reason}}. Please update your documents and resubmit.',
        'placeholders': ['name', 'reason'],
    },
    'payment_receipt': {
        'key': 'payment_receipt',
        'name_bn': 'পেমেন্ট রসিদ',
        'name_en': 'Payment Receipt',
        'subject_bn': '[PGCB পোর্টাল] অফিসিয়াল পেমেন্ট রসিদ {{receipt_no}}',
        'subject_en': '[PGCB Portal] Official Payment Receipt {{receipt_no}}',
        'body_bn': 'প্রিয় {{name}},\nআপনার পেমেন্ট সফলভাবে যাচাইকৃত হয়েছে। রসিদ নম্বর: {{receipt_no}}, পরিমাণ: {{amount}} BDT, ট্রানজেকশন আইডি: {{transaction_id}}।',
        'body_en': 'Dear {{name}},\nYour payment has been verified. Receipt No: {{receipt_no}}, Amount: {{amount}} BDT, Transaction ID: {{transaction_id}}.',
        'placeholders': ['name', 'receipt_no', 'amount', 'transaction_id', 'verify_url'],
    },
    'renewal_reminder': {
        'key': 'renewal_reminder',
        'name_bn': 'সদস্যপদ নবায়ন অনুস্মারক',
        'name_en': 'Membership Renewal Reminder',
        'subject_bn': '[PGCB পোর্টাল] আপনার সদস্যপদ নবায়নের সময় হয়েছে',
        'subject_en': '[PGCB Portal] Membership Renewal Reminder',
        'body_bn': 'প্রিয় {{name}} ({{membership_id}}),\nআপনার সদস্যপদের মেয়াদ {{validity_date}} তারিখে শেষ হবে। অনুগ্রহ করে অনলাইনে নবায়ন সম্পন্ন করুন।',
        'body_en': 'Dear {{name}} ({{membership_id}}),\nYour membership expires on {{validity_date}}. Please complete your online renewal on the portal.',
        'placeholders': ['name', 'membership_id', 'validity_date', 'renewal_fee'],
    },
    'event_registration': {
        'key': 'event_registration',
        'name_bn': 'ইভেন্ট নিবন্ধন নিশ্চিতকরণ',
        'name_en': 'Event Registration Confirmation',
        'subject_bn': '[PGCB পোর্টাল] ইভেন্ট নিবন্ধন নিশ্চিতকরণ — {{event_title}}',
        'subject_en': '[PGCB Portal] Event Registration Confirmed — {{event_title}}',
        'body_bn': 'প্রিয় {{name}},\n"{{event_title}}" ইভেন্টে আপনার নিবন্ধন নিশ্চিত হয়েছে। তারিখ: {{event_date}}, স্থান: {{location}}।',
        'body_en': 'Dear {{name}},\nYour registration for "{{event_title}}" is confirmed. Date: {{event_date}}, Venue: {{location}}.',
        'placeholders': ['name', 'event_title', 'event_date', 'location', 'qr_code_url'],
    },
    'event_reminder': {
        'key': 'event_reminder',
        'name_bn': 'ইভেন্ট অনুস্মারক',
        'name_en': 'Event Reminder',
        'subject_bn': '[PGCB পোর্টাল] আগামীকাল ইভেন্ট অনুস্মারক — {{event_title}}',
        'subject_en': '[PGCB Portal] Upcoming Event Reminder — {{event_title}}',
        'body_bn': 'প্রিয় {{name}},\nস্মারক: "{{event_title}}" আগামী {{event_date}} তারিখে {{location}}-এ অনুষ্ঠিত হবে। আপনার ডিজিটাল পাস সাথে রাখুন।',
        'body_en': 'Dear {{name}},\nReminder: "{{event_title}}" will take place on {{event_date}} at {{location}}. Please bring your digital event pass.',
        'placeholders': ['name', 'event_title', 'event_date', 'location'],
    },
    'certificate_issued': {
        'key': 'certificate_issued',
        'name_bn': 'ডিজিটাল সনদপত্র ইস্যু',
        'name_en': 'Certificate Issued',
        'subject_bn': '[PGCB পোর্টাল] আপনার ডিজিটাল সনদপত্র ইস্যু হয়েছে ({{certificate_no}})',
        'subject_en': '[PGCB Portal] Digital Certificate Issued ({{certificate_no}})',
        'body_bn': 'প্রিয় {{name}},\nআপনার ডিজিটাল সনদপত্র ({{certificate_no}}) প্রস্তুত হয়েছে। যাচাই লিংক: {{verify_url}}',
        'body_en': 'Dear {{name}},\nYour digital certificate ({{certificate_no}}) has been issued. Verification URL: {{verify_url}}',
        'placeholders': ['name', 'certificate_no', 'verify_url'],
    },
    'security_alert': {
        'key': 'security_alert',
        'name_bn': 'নিরাপত্তা সতর্কবার্তা',
        'name_en': 'Security Alert',
        'subject_bn': '[PGCB পোর্টাল] আপনার অ্যাকাউন্টে নতুন নিরাপত্তা ইভেন্ট',
        'subject_en': '[PGCB Portal] Security Alert on Your Account',
        'body_bn': 'প্রিয় {{name}},\nআপনার অ্যাকাউন্টে একটি নিরাপত্তা কার্যক্রম ({{event_type}}) শনাক্ত হয়েছে। আইপি: {{ip_address}}, সময়: {{timestamp}}।',
        'body_en': 'Dear {{name}},\nA security event ({{event_type}}) was recorded on your account from IP {{ip_address}} at {{timestamp}}.',
        'placeholders': ['name', 'event_type', 'ip_address', 'timestamp'],
    },
}


class EmailTemplateUpdate(BaseModel):
    subject_bn: str = Field(min_length=3, max_length=300)
    subject_en: str = Field(min_length=3, max_length=300)
    body_bn: str = Field(min_length=10, max_length=10000)
    body_en: str = Field(min_length=10, max_length=10000)


def _compute_data_quality(db: Session) -> dict[str, Any]:
    now = datetime.utcnow()
    users = db.scalars(select(User)).all()
    members = db.scalars(select(Member)).all()
    active_circle_ids = set(db.scalars(select(Circle.id).where(Circle.active == True)).all())
    user_by_id = {u.id: u for u in users}

    issues: list[dict[str, Any]] = []

    # 1. Duplicate NID number
    nid_counts: dict[str, list[Member]] = {}
    for m in members:
        nid_val = getattr(m, 'nid_number', None) or getattr(m, 'nid_hash', None)
        if nid_val:
            nid_counts.setdefault(str(nid_val).strip(), []).append(m)
    duplicate_nid_count = 0
    for _, group in nid_counts.items():
        if len(group) > 1:
            duplicate_nid_count += len(group)
            for m in group:
                issues.append({
                    'category': 'duplicate_nid',
                    'severity': 'HIGH',
                    'member_id': m.id,
                    'user_id': m.user_id,
                    'membership_id': m.membership_id,
                    'detail': f'Duplicate NID shared across {len(group)} member records',
                })

    # 2. Duplicate mobile phone
    phone_counts: dict[str, list[User]] = {}
    for u in users:
        if u.phone and u.phone.strip():
            phone_counts.setdefault(u.phone.strip(), []).append(u)
    duplicate_mobile_count = 0
    for phone, group in phone_counts.items():
        if len(group) > 1:
            duplicate_mobile_count += len(group)
            for u in group:
                issues.append({
                    'category': 'duplicate_mobile',
                    'severity': 'MEDIUM',
                    'user_id': u.id,
                    'email': u.email,
                    'detail': f'Duplicate mobile phone {phone} shared across {len(group)} accounts',
                })

    # 3. Duplicate email (case-insensitive)
    email_counts: dict[str, list[User]] = {}
    for u in users:
        if u.email:
            email_counts.setdefault(u.email.strip().lower(), []).append(u)
    duplicate_email_count = sum(len(g) for g in email_counts.values() if len(g) > 1)

    # 4. Duplicate membership ID
    mid_counts: dict[str, list[Member]] = {}
    for m in members:
        if m.membership_id:
            mid_counts.setdefault(m.membership_id.strip().upper(), []).append(m)
    duplicate_membership_id_count = 0
    for mid, group in mid_counts.items():
        if len(group) > 1:
            duplicate_membership_id_count += len(group)
            for m in group:
                issues.append({
                    'category': 'duplicate_membership_id',
                    'severity': 'HIGH',
                    'member_id': m.id,
                    'membership_id': m.membership_id,
                    'detail': f'Duplicate membership ID {mid}',
                })

    # 5. Missing documents, expired membership, invalid circle, incomplete profile
    missing_documents_count = 0
    expired_membership_count = 0
    invalid_circle_count = 0
    incomplete_profile_count = 0
    affected_member_ids: set[int] = set()

    for m in members:
        u = user_by_id.get(m.user_id)
        has_docs = bool(m.photo_url) and len(getattr(m, 'documents', []) or []) > 0
        if not has_docs:
            missing_documents_count += 1
            affected_member_ids.add(m.id)
            issues.append({
                'category': 'missing_documents',
                'severity': 'LOW',
                'member_id': m.id,
                'user_id': m.user_id,
                'membership_id': m.membership_id,
                'detail': 'Missing profile photo or verification document attachments',
            })
        if m.status == 'EXPIRED' or (m.validity_date and m.validity_date < now):
            expired_membership_count += 1
            affected_member_ids.add(m.id)
            issues.append({
                'category': 'expired_membership',
                'severity': 'MEDIUM',
                'member_id': m.id,
                'user_id': m.user_id,
                'membership_id': m.membership_id,
                'detail': f'Membership expired on {m.validity_date.date().isoformat() if m.validity_date else "unknown"}',
            })
        if m.circle_id is not None and m.circle_id not in active_circle_ids:
            invalid_circle_count += 1
            affected_member_ids.add(m.id)
            issues.append({
                'category': 'invalid_circle',
                'severity': 'HIGH',
                'member_id': m.id,
                'user_id': m.user_id,
                'detail': f'Assigned circle_id={m.circle_id} is not an active PGCB grid circle',
            })
        if not m.employee_id or not m.designation_bn or not m.circle_id or not (u and u.phone):
            incomplete_profile_count += 1
            affected_member_ids.add(m.id)
            issues.append({
                'category': 'incomplete_profile',
                'severity': 'LOW',
                'member_id': m.id,
                'user_id': m.user_id,
                'membership_id': m.membership_id,
                'detail': 'Profile missing employee_id, designation_bn, circle_id, or phone number',
            })

    summary = {
        'duplicate_nid': duplicate_nid_count,
        'duplicate_mobile': duplicate_mobile_count,
        'duplicate_email': duplicate_email_count,
        'duplicate_membership_id': duplicate_membership_id_count,
        'missing_documents': missing_documents_count,
        'expired_membership': expired_membership_count,
        'invalid_circle': invalid_circle_count,
        'incomplete_profile': incomplete_profile_count,
    }
    records_requiring_attention = len(affected_member_ids) + duplicate_nid_count + duplicate_mobile_count
    return {
        'records_requiring_attention': records_requiring_attention,
        'total_members_scanned': len(members),
        'total_users_scanned': len(users),
        'summary': summary,
        'issues': issues[:200],
        'generated_at': now.isoformat(),
    }


@router.get('/data-quality')
def get_data_quality_report(
    _: User = Depends(require_permission('member.read')),
    db: Session = Depends(get_db),
):
    return _compute_data_quality(db)


@router.get('/analytics/executive')
def get_executive_analytics(
    _: User = Depends(require_permission('analytics.read')),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    soon = now + timedelta(days=30)

    members = db.scalars(select(Member)).all()
    circles = db.scalars(select(Circle).order_by(Circle.id.asc())).all()
    payments = db.scalars(select(PaymentTransaction)).all()
    events = db.scalars(select(Event).order_by(Event.event_date.desc())).all()
    registrations = db.scalars(select(EventRegistration)).all()
    certificates = db.scalars(select(Certificate)).all()
    documents = db.scalars(select(Document).order_by(Document.download_count.desc())).all()

    total_members = len(members)
    active_members = sum(1 for m in members if m.status == 'ACTIVE')
    pending_members = sum(1 for m in members if m.status in ('SUBMITTED', 'UNDER_REVIEW', 'APPROVED_PENDING_PAYMENT'))
    expiring_members = sum(
        1 for m in members if m.validity_date and now <= m.validity_date <= soon and m.status == 'ACTIVE'
    )

    paid_statuses = {'PAID', 'COMPLETED', 'SUCCESS'}
    paid_payments = [p for p in payments if (p.status or '').upper() in paid_statuses]
    total_revenue_bdt = sum(int(p.amount or 0) for p in paid_payments)

    dq = _compute_data_quality(db)

    # Members by circle
    members_by_circle = []
    for c in circles:
        c_members = [m for m in members if m.circle_id == c.id]
        members_by_circle.append({
            'circle_id': c.id,
            'name_bn': c.name_bn,
            'name_en': c.name_en or c.name_bn,
            'total_members': len(c_members),
            'active_members': sum(1 for m in c_members if m.status == 'ACTIVE'),
            'pending_members': sum(1 for m in c_members if m.status in ('SUBMITTED', 'UNDER_REVIEW')),
        })

    # Membership status breakdown
    status_counts: dict[str, int] = {}
    for m in members:
        st = m.status or 'DRAFT'
        status_counts[st] = status_counts.get(st, 0) + 1

    # Revenue by month
    revenue_by_month_map: dict[str, int] = {}
    payment_method_map: dict[str, dict[str, int]] = {}
    for p in paid_payments:
        dt = p.completed_at or p.created_at or now
        month_key = dt.strftime('%Y-%m')
        revenue_by_month_map[month_key] = revenue_by_month_map.get(month_key, 0) + int(p.amount or 0)
        prov = (p.provider or 'MANUAL').upper()
        entry = payment_method_map.setdefault(prov, {'count': 0, 'amount_bdt': 0})
        entry['count'] += 1
        entry['amount_bdt'] += int(p.amount or 0)

    revenue_by_month = [
        {'month': k, 'revenue_bdt': v} for k, v in sorted(revenue_by_month_map.items())
    ]
    payment_method_breakdown = [
        {'provider': k, 'count': v['count'], 'amount_bdt': v['amount_bdt']}
        for k, v in sorted(payment_method_map.items())
    ]

    # Application conversion
    submitted_or_beyond = sum(1 for m in members if m.status != 'DRAFT')
    conversion_rate_pct = round((active_members / submitted_or_beyond) * 100.0, 1) if submitted_or_beyond else 0.0

    # Event attendance
    regs_by_event: dict[int, list[EventRegistration]] = {}
    for r in registrations:
        regs_by_event.setdefault(r.event_id, []).append(r)
    event_attendance = []
    for e in events[:20]:
        e_regs = regs_by_event.get(e.id, [])
        reg_count = len(e_regs)
        checked_in = sum(
            1 for r in e_regs if getattr(r, 'attendance_status', '') == 'CHECKED_IN' or getattr(r, 'checked_in_at', None) is not None
        )
        event_attendance.append({
            'event_id': e.id,
            'title_bn': e.title_bn,
            'event_date': e.event_date.isoformat() if e.event_date else None,
            'registered_count': reg_count,
            'checked_in_count': checked_in,
            'attendance_rate_pct': round((checked_in / reg_count) * 100.0, 1) if reg_count else 0.0,
        })

    # Certificate issuance
    cert_by_type: dict[str, int] = {}
    revoked_certs = 0
    for c in certificates:
        t = 'EVENT' if c.event_registration_id else 'MEMBERSHIP'
        cert_by_type[t] = cert_by_type.get(t, 0) + 1
        if (c.status or '').upper() == 'REVOKED':
            revoked_certs += 1

    document_downloads = [
        {
            'id': d.id,
            'title_bn': d.title_bn,
            'category': d.category,
            'download_count': d.download_count or 0,
        }
        for d in documents[:20]
    ]

    return {
        'kpis': {
            'total_members': total_members,
            'active_members': active_members,
            'pending_members': pending_members,
            'expiring_members': expiring_members,
            'total_revenue_bdt': total_revenue_bdt,
            'total_events': len(events),
            'total_certificates': len(certificates),
            'records_requiring_attention': dq['records_requiring_attention'],
        },
        'members_by_circle': members_by_circle,
        'membership_status_breakdown': status_counts,
        'revenue_by_month': revenue_by_month,
        'payment_method_breakdown': payment_method_breakdown,
        'application_conversion': {
            'total_applications': submitted_or_beyond,
            'approved_members': active_members,
            'conversion_rate_pct': conversion_rate_pct,
        },
        'event_attendance': event_attendance,
        'certificate_issuance': {
            'total_issued': len(certificates),
            'revoked_count': revoked_certs,
            'by_type': cert_by_type,
        },
        'document_downloads': document_downloads,
        'generated_at': now.isoformat(),
    }


@router.get('/email-templates')
def list_email_templates(
    _: User = Depends(require_permission('settings.manage')),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(SiteSetting).where(SiteSetting.key.like('email_template:%'))).all()
    overrides: dict[str, dict[str, Any]] = {}
    for r in rows:
        k = r.key.split(':', 1)[1]
        try:
            overrides[k] = json.loads(r.value or '{}')
            overrides[k]['updated_at'] = r.updated_at.isoformat() if r.updated_at else None
        except Exception:
            continue

    items = []
    for key, default_tpl in DEFAULT_EMAIL_TEMPLATES.items():
        merged = {**default_tpl, **overrides.get(key, {})}
        items.append(merged)
    return {'total': len(items), 'items': items}


@router.put('/email-templates/{template_key}')
def update_email_template(
    template_key: str,
    payload: EmailTemplateUpdate,
    request: Request,
    admin: User = Depends(require_permission('settings.manage')),
    db: Session = Depends(get_db),
):
    key = template_key.strip().lower()
    if key not in DEFAULT_EMAIL_TEMPLATES:
        raise HTTPException(404, f'Unknown email template key: {key}')
    setting_key = f'email_template:{key}'
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == setting_key))
    data = {
        **DEFAULT_EMAIL_TEMPLATES[key],
        'subject_bn': payload.subject_bn.strip(),
        'subject_en': payload.subject_en.strip(),
        'body_bn': payload.body_bn.strip(),
        'body_en': payload.body_en.strip(),
    }
    if not row:
        row = SiteSetting(key=setting_key, value=json.dumps(data, ensure_ascii=False), category='EMAIL_TEMPLATES')
        db.add(row)
    else:
        row.value = json.dumps(data, ensure_ascii=False)
    audit(db, admin, 'UPDATE_EMAIL_TEMPLATE', 'SiteSetting', None, request.client.host if request.client else None)
    db.commit()
    db.refresh(row)
    return {**data, 'updated_at': row.updated_at.isoformat() if row.updated_at else None}
