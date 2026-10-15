import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import log_audit_action
from app.core.config import settings
from app.core.deps import current_user
from app.db.session import engine, get_db
from app.domain.membership import RENEWAL_PERIODS, resolve_renewal_days
from app.integrations.payments import create_checkout, normalize_provider
from app.models import (
    AuditLog,
    Base,
    Certificate,
    Circular,
    Event,
    EventRegistration,
    Member,
    MemberDocument,
    MemberProfileChangeRequest,
    MemberProfileMeta,
    MemberSavedContent,
    MembershipApplication,
    MembershipRenewal,
    MembershipStatusHistory,
    Notice,
    Notification,
    PaymentTransaction,
    SiteSetting,
    User,
    UserSession,
)
from app.schemas.membership import (
    ApplicationResponse,
    ApplicationDetailsResponse,
    ApplicationTimelineStep,
    MemberDocumentResponse,
    MemberProfileUpdate,
    MembershipHistoryItem,
    MembershipRenewalOption,
    MembershipRenewalOptionsResponse,
    MembershipRenewalRequest,
    MembershipRenewalResponse,
    MembershipSummaryResponse,
    ProfileChangeRequestCreate,
)
from app.services import ALLOWED_CONTENT_TYPES, ALLOWED_DOC_TYPES, audit, membership_dates, next_membership_id, notify
from app.services import BASE_STORAGE
from app.services.receipt_service import get_fee_schedule, resolve_plan_amount
from app.utils.storage import get_file_bytes, is_local_path, save_bytes, validate_upload_bytes, scan_upload_security


try:
    Base.metadata.create_all(
        bind=engine,
        tables=[
            MemberProfileMeta.__table__,
            MemberProfileChangeRequest.__table__,
            MemberSavedContent.__table__,
        ],
        checkfirst=True,
    )
except Exception:
    pass

router = APIRouter(prefix='/member', tags=['membership'])

SENSITIVE_PROFILE_FIELDS = {
    'name_bn': ('Name (Bangla)', 'নাম (বাংলা)'),
    'name_en': ('Name (English)', 'নাম (ইংরেজি)'),
    'date_of_birth': ('Date of Birth', 'জন্ম তারিখ'),
    'dob': ('Date of Birth', 'জন্ম তারিখ'),
    'nid_number': ('NID / Passport Number', 'জাতীয় পরিচয়পত্র / পাসপোর্ট নম্বর'),
    'membership_id': ('Membership ID', 'সদস্য আইডি'),
    'membership_type': ('Membership Type', 'সদস্যপদের ধরণ'),
    'grid_circle': ('Grid Circle', 'গ্রিড সার্কেল'),
    'circle_id': ('Grid Circle', 'গ্রিড সার্কেল'),
    'status': ('Membership Status', 'সদস্যপদ স্থিতি'),
    'certificate_info': ('Certificate Information', 'সনদপত্রের তথ্য'),
}



def get_member(user: User, db: Session) -> Member:
    member = db.scalar(
        select(Member)
        .options(selectinload(Member.circle), selectinload(Member.documents))
        .where(Member.user_id == user.id)
    )
    if not member:
        raise HTTPException(404, 'Member profile not found')
    return member


def _get_or_create_profile_meta(db: Session, member_id: int) -> MemberProfileMeta:
    meta = db.scalar(select(MemberProfileMeta).where(MemberProfileMeta.member_id == member_id))
    if not meta:
        meta = MemberProfileMeta(
            member_id=member_id,
            organization='Power Grid Company of Bangladesh PLC (PGCB)',
            profession='Diploma Engineer',
        )
        db.add(meta)
        db.flush()
    return meta


def _compute_profile_completion(user: User, member: Member, meta: MemberProfileMeta | None) -> dict:
    has_basic = bool(user.name_bn or user.name_en)
    has_contact = bool(user.phone and user.phone.strip() and user.email and user.email.strip())
    has_professional = bool(
        (member.designation_bn or member.designation_en or (meta and (meta.profession or meta.designation)))
        and (
            (meta and (meta.organization or meta.department or meta.academic_qualification))
            or member.employee_id
            or member.diploma_institution
        )
    )
    has_photo = bool(member.photo_url)
    has_emergency = bool(meta and meta.emergency_contact_name and meta.emergency_contact_phone)

    items = [
        {
            'key': 'basic',
            'field': 'basic',
            'label_en': 'Personal Information',
            'label_bn': 'প্রাথমিক তথ্য (নাম, এনআইডি)',
            'completed': has_basic,
            'weight': 20,
            'route': '/member/profile/edit',
        },
        {
            'key': 'contact',
            'field': 'contact',
            'label_en': 'Contact Information',
            'label_bn': 'যোগাযোগের তথ্য (ফোন, ইমেইল)',
            'completed': has_contact,
            'weight': 20,
            'route': '/member/profile/edit',
        },
        {
            'key': 'professional',
            'field': 'professional',
            'label_en': 'Professional Information',
            'label_bn': 'পেশাগত তথ্য',
            'completed': has_professional,
            'weight': 20,
            'route': '/member/profile/edit',
        },
        {
            'key': 'photo',
            'field': 'photo',
            'label_en': 'Profile Photograph',
            'label_bn': 'প্রোফাইল ছবি',
            'completed': has_photo,
            'weight': 20,
            'route': '/member/profile/edit',
        },
        {
            'key': 'emergency_contact',
            'field': 'emergency_contact',
            'label_en': 'Emergency Contact',
            'label_bn': 'জরুরি যোগাযোগ',
            'completed': has_emergency,
            'weight': 20,
            'route': '/member/profile/edit',
        },
    ]
    pct = sum(item['weight'] for item in items if item['completed'])
    missing = [
        {
            'field': item['key'],
            'label': item['label_en'],
            'label_bn': item['label_bn'],
            'route': item.get('route', '/member/profile/edit'),
        }
        for item in items
        if not item['completed']
    ]
    return {
        'percentage': pct,
        'is_complete': pct == 100,
        'completed_count': sum(1 for item in items if item['completed']),
        'total_count': len(items),
        'breakdown': {
            'basic': has_basic,
            'contact': has_contact,
            'professional': has_professional,
            'photo': has_photo,
            'emergency_contact': has_emergency,
        },
        'missing': missing,
        'items': items,
    }


def _build_verification_badges(user: User, m: Member, meta: MemberProfileMeta | None) -> dict:
    is_active = (m.status or '').upper() == 'ACTIVE'
    has_name = bool(user.name_bn or user.name_en)
    has_email = bool(user.email_verified or (user.email and '@' in user.email))
    has_phone = bool(user.phone and user.phone.strip())
    has_nid = bool(m.nid_number and m.nid_number.strip())
    has_prof = bool(is_active and (m.designation_bn or m.designation_en or (meta and meta.organization)))

    return {
        'name': {
            'field': 'name',
            'status': 'VERIFIED' if (is_active or has_name) else 'PENDING',
            'label': 'Verified' if (is_active or has_name) else 'Pending Verification',
            'label_bn': 'যাচাইকৃত' if (is_active or has_name) else 'যাচাই বাকি',
            'is_verified': bool(is_active or has_name),
            'description': 'Full legal name verified against government identification / NID records.',
            'description_bn': 'নাম জাতীয় পরিচয়পত্রের তথ্যের সাথে সরকারিভাবে যাচাইকৃত।',
        },
        'email': {
            'field': 'email',
            'status': 'VERIFIED' if has_email else 'PENDING',
            'label': 'Verified' if has_email else 'Pending Verification',
            'label_bn': 'যাচাইকৃত' if has_email else 'অযাচাইকৃত',
            'is_verified': has_email,
            'description': 'Registered email address is verified for digital communications and secure OTP access.',
            'description_bn': 'নিবন্ধিত ইমেইল ঠিকানা ডিজিটাল যোগাযোগ ও নিরাপত্তার জন্য যাচাইকৃত।',
        },
        'mobile': {
            'field': 'mobile',
            'status': 'VERIFIED' if has_phone else 'PENDING',
            'label': 'Verified' if has_phone else 'Pending Verification',
            'label_bn': 'যাচাইকৃত' if has_phone else 'যাচাই বাকি',
            'is_verified': has_phone,
            'description': 'Mobile number verified for critical SMS dispatches, renewal alerts, and authentication.',
            'description_bn': 'মোবাইল নম্বর এসএমএস সতর্কতা ও নিরাপত্তার জন্য যাচাইকৃত।',
        },
        'nid': {
            'field': 'nid',
            'status': 'VERIFIED' if has_nid else 'PENDING',
            'label': 'Verified' if has_nid else 'Pending Verification',
            'label_bn': 'যাচাইকৃত' if has_nid else 'যাচাই বাকি',
            'is_verified': has_nid,
            'description': 'National Identity Number (Smart NID) vetted and archived with document registry.',
            'description_bn': 'জাতীয় পরিচয়পত্র নম্বর (স্মার্ট এনআইডি) যাচাইকৃত ও সংরক্ষিত।',
        },
        'professional': {
            'field': 'professional',
            'status': 'VERIFIED' if has_prof else 'PENDING',
            'label': 'Verified' if has_prof else 'Pending Verification',
            'label_bn': 'যাচাইকৃত' if has_prof else 'যাচাইধীন',
            'is_verified': has_prof,
            'description': 'Designation, department, and diploma engineering credentials confirmed by PGCB Circle.',
            'description_bn': 'পদবি, দপ্তর ও ডিপ্লোমা প্রকৌশল সনদ পিজিসিবি সার্কেল কর্তৃক যাচাইকৃত।',
        },
    }




def _build_application_timeline(db: Session, member: Member) -> dict:
    app_row = db.scalar(select(MembershipApplication).where(MembershipApplication.member_id == member.id))
    raw_status = (app_row.status if app_row and app_row.status else member.status or 'PENDING').upper()
    if member.status == 'ACTIVE':
        raw_status = 'ACTIVE'

    docs = list(member.documents or [])
    has_replacement_doc = any(d.review_status in ('REJECTED', 'REPLACEMENT_REQUIRED') for d in docs)
    all_docs_approved = len(docs) > 0 and all(d.review_status == 'APPROVED' for d in docs)

    paid_tx = db.scalar(
        select(PaymentTransaction)
        .where(
            PaymentTransaction.member_id == member.id,
            PaymentTransaction.status.in_(['PAID', 'SUCCESS', 'COMPLETED']),
        )
        .order_by(PaymentTransaction.created_at.desc())
    )

    # Determine progress index (0..6)
    status_stage_map = {
        'DRAFT': 0,
        'PENDING': 1,
        'SUBMITTED': 1,
        'DOCUMENT_REQUIRED': 1,
        'UNDER_REVIEW': 2,
        'CIRCLE_REVIEW': 2,
        'APPROVED': 4,
        'PAYMENT_PENDING': 4,
        'PAID': 5,
        'ACTIVE': 6,
        'REJECTED': -1,
        'CANCELLED': -2,
    }
    stage_idx = status_stage_map.get(raw_status, 1)

    stage_defs = [
        ('SUBMITTED', 'Submitted', 'আবেদন জমা'),
        ('DOCUMENT_VERIFICATION', 'Document Verification', 'ডকুমেন্ট যাচাই'),
        ('CIRCLE_REVIEW', 'Circle Review', 'সার্কেল পর্যালোচনা'),
        ('CENTRAL_REVIEW', 'Central Review', 'কেন্দ্রীয় অনুমোদন'),
        ('PAYMENT', 'Payment', 'পেমেন্ট সম্পন্ন'),
        ('ACTIVATION', 'Membership Activation', 'সদস্যপদ সক্রিয়করণ'),
    ]

    stages = []
    for idx, (s_key, label_en, label_bn) in enumerate(stage_defs):
        if raw_status in ('REJECTED', 'CANCELLED'):
            s_state = 'COMPLETED' if idx == 0 else ('REJECTED' if idx == 1 else 'PENDING')
        elif stage_idx >= 6 or idx < stage_idx:
            s_state = 'COMPLETED'
        elif idx == stage_idx:
            if s_key == 'DOCUMENT_VERIFICATION' and (raw_status == 'DOCUMENT_REQUIRED' or has_replacement_doc):
                s_state = 'ACTION_REQUIRED'
            else:
                s_state = 'IN_PROGRESS'
        else:
            s_state = 'PENDING'

        if s_key == 'DOCUMENT_VERIFICATION' and all_docs_approved and stage_idx >= 1 and raw_status not in ('DRAFT', 'CANCELLED'):
            s_state = 'COMPLETED'
        if s_key == 'PAYMENT' and paid_tx is not None and raw_status not in ('DRAFT', 'CANCELLED'):
            s_state = 'COMPLETED'

        icon_map = {
            'COMPLETED': '✓',
            'IN_PROGRESS': '⏳',
            'ACTION_REQUIRED': '⚠',
            'REJECTED': '✕',
            'PENDING': '○',
        }
        stages.append({
            'step': idx + 1,
            'key': s_key,
            'label_en': label_en,
            'label_bn': label_bn,
            'status': s_state,
            'icon': icon_map.get(s_state, '○'),
        })

    required_actions = []
    if raw_status == 'DRAFT':
        required_actions.append({
            'code': 'SUBMIT_APPLICATION',
            'message_en': 'Your application is saved as a draft. Please review and submit it.',
            'message_bn': 'আপনার আবেদন খসড়া হিসেবে সংরক্ষিত আছে। অনুগ্রহ করে যাচাই করে জমা দিন।',
        })
    if len(docs) == 0 and raw_status != 'ACTIVE':
        required_actions.append({
            'code': 'UPLOAD_DOCUMENTS',
            'message_en': 'Please upload your NID, Diploma Certificate, and Employee ID / Photo for verification.',
            'message_bn': 'যাচাইকরণের জন্য অনুগ্রহ করে আপনার এনআইডি, ডিপ্লোমা সনদ এবং ছবি আপলোড করুন।',
        })
    if has_replacement_doc or raw_status == 'DOCUMENT_REQUIRED':
        required_actions.append({
            'code': 'REPLACE_DOCUMENT',
            'message_en': 'One or more uploaded documents require replacement. Check Document Center.',
            'message_bn': 'এক বা একাধিক ডকুমেন্ট পুনরায় আপলোড করা প্রয়োজন। ডকুমেন্ট সেন্টার দেখুন।',
        })
    if raw_status in ('APPROVED', 'PAYMENT_PENDING') and not paid_tx:
        required_actions.append({
            'code': 'COMPLETE_PAYMENT',
            'message_en': 'Your application is approved. Complete your membership fee payment to activate membership.',
            'message_bn': 'আপনার আবেদন অনুমোদিত হয়েছে। সদস্যপদ সক্রিয় করতে নির্ধারিত ফি পরিশোধ করুন।',
        })

    status_labels = {
        'DRAFT': ('Draft', 'খসড়া'),
        'PENDING': ('Submitted / Pending Review', 'জমা দেওয়া হয়েছে / পর্যালোচনাধীন'),
        'SUBMITTED': ('Submitted', 'আবেদন জমা হয়েছে'),
        'UNDER_REVIEW': ('Under Review', 'পর্যালোচনাধীন'),
        'DOCUMENT_REQUIRED': ('Document Required', 'ডকুমেন্ট প্রয়োজন'),
        'CIRCLE_REVIEW': ('Circle Review', 'সার্কেল পর্যালোচনাধীন'),
        'APPROVED': ('Approved (Awaiting Payment)', 'অনুমোদিত (পেমেন্টের অপেক্ষায়)'),
        'PAYMENT_PENDING': ('Payment Pending', 'পেমেন্ট অপেক্ষমাণ'),
        'PAID': ('Paid (Awaiting Activation)', 'পেমেন্ট সম্পন্ন'),
        'ACTIVE': ('Active Member', 'সক্রিয় সদস্য'),
        'REJECTED': ('Rejected', 'প্রত্যাখ্যাত'),
        'CANCELLED': ('Cancelled', 'বাতিল'),
    }
    lbl_en, lbl_bn = status_labels.get(raw_status, (raw_status, raw_status))

    return {
        'id': app_row.id if app_row else member.id,
        'member_id': member.id,
        'application_no': (app_row.application_no if app_row and app_row.application_no else member.application_no) or f'PGCB-APP-2026-{member.id:04d}',
        'membership_id': member.membership_id,
        'membership_type': member.membership_type or 'GENERAL',
        'status': raw_status,
        'status_label_en': lbl_en,
        'status_label_bn': lbl_bn,
        'circle_id': member.circle_id,
        'circle_bn': member.circle.name_bn if member.circle else None,
        'circle_en': member.circle.name_en if member.circle else None,
        'submitted_at': (app_row.submitted_at if app_row and app_row.submitted_at else member.created_at),
        'approved_at': (app_row.approved_at if app_row and app_row.approved_at else member.issue_date),
        'reviewer_notes': (app_row.rejection_reason if app_row and app_row.rejection_reason else member.application_note),
        'stages': stages,
        'required_actions': required_actions,
    }


def _serialize_full_profile(user: User, m: Member, meta: MemberProfileMeta, exp: dict, completion: dict, pending_requests: list[dict]) -> dict:
    is_verified_member = (m.status or '').upper() == 'ACTIVE'
    return {
        'id': m.id,
        'user_id': user.id,
        # Personal Information
        'name_bn': user.name_bn,
        'name_en': user.name_en,
        'father_name': meta.father_name,
        'mother_name': meta.mother_name,
        'date_of_birth': m.date_of_birth,
        'gender': meta.gender,
        'blood_group': meta.blood_group,
        'nid_number': m.nid_number,
        'photo_url': m.photo_url,
        # Professional Information
        'designation_bn': m.designation_bn,
        'designation_en': m.designation_en,
        'organization': meta.organization or 'Power Grid Company of Bangladesh PLC (PGCB)',
        'department': meta.department,
        'profession': meta.profession or 'Diploma Engineer',
        'academic_qualification': meta.academic_qualification,
        'professional_qualification': meta.professional_qualification,
        'years_of_experience': meta.years_of_experience,
        'employee_id': m.employee_id,
        'diploma_institution': m.diploma_institution,
        'graduation_year': m.graduation_year,
        # Contact Information
        'email': user.email,
        'phone': user.phone,
        'alternate_phone': meta.alternate_phone,
        'current_address': m.current_address,
        'permanent_address': m.permanent_address,
        'district': meta.district,
        'circle_id': m.circle_id,
        'circle_bn': m.circle.name_bn if m.circle else None,
        'circle_en': m.circle.name_en if m.circle else None,
        # Emergency Contact
        'emergency_contact_name': meta.emergency_contact_name,
        'emergency_contact_relationship': meta.emergency_contact_relationship,
        'emergency_contact_phone': meta.emergency_contact_phone,
        'emergency_contact_address': meta.emergency_contact_address,
        # Privacy & Directory
        'preferred_language': meta.preferred_language or 'bn',
        'profile_visibility': meta.profile_visibility or 'MEMBERS_ONLY',
        'directory_visibility': bool(meta.directory_visibility),
        'contact_visibility': bool(meta.contact_visibility),
        'directory_visible': bool(meta.directory_visibility),
        'show_phone_in_directory': bool(meta.contact_visibility),
        'show_email_in_directory': bool(meta.contact_visibility),
        # Membership Metadata
        'membership_id': m.membership_id,
        'membership_type': m.membership_type or 'GENERAL',
        'status': m.status,
        'issue_date': m.issue_date,
        'validity_date': m.validity_date,
        'personal_information': {
            'name_bn': user.name_bn,
            'name_en': user.name_en,
            'father_name': meta.father_name,
            'mother_name': meta.mother_name,
            'date_of_birth': m.date_of_birth,
            'gender': meta.gender,
            'blood_group': meta.blood_group,
            'nid_number': m.nid_number,
            'photo_url': m.photo_url,
        },
        'professional_information': {
            'designation_bn': m.designation_bn,
            'designation_en': m.designation_en,
            'organization': meta.organization or 'Power Grid Company of Bangladesh PLC (PGCB)',
            'department': meta.department,
            'profession': meta.profession or 'Diploma Engineer',
            'academic_qualification': meta.academic_qualification,
            'professional_qualification': meta.professional_qualification,
            'years_of_experience': meta.years_of_experience,
            'employee_id': m.employee_id,
            'diploma_institution': m.diploma_institution,
            'graduation_year': m.graduation_year,
            'circle_id': m.circle_id,
            'circle_bn': m.circle.name_bn if m.circle else None,
            'circle_en': m.circle.name_en if m.circle else None,
        },
        'contact_information': {
            'email': user.email,
            'phone': user.phone,
            'alternate_phone': meta.alternate_phone,
            'current_address': m.current_address,
            'permanent_address': m.permanent_address,
            'district': meta.district,
            'circle_id': m.circle_id,
            'circle_bn': m.circle.name_bn if m.circle else None,
            'circle_en': m.circle.name_en if m.circle else None,
        },
        'emergency_contact': {
            'name': meta.emergency_contact_name,
            'relationship': meta.emergency_contact_relationship,
            'phone': meta.emergency_contact_phone,
            'address': meta.emergency_contact_address,
        },
        'verification_badges': _build_verification_badges(user, m, meta),
        # Verification & Completion
        'is_verified_member': is_verified_member,
        'protected_fields': list(SENSITIVE_PROFILE_FIELDS.keys()),
        'editable_fields': [
            'phone', 'email', 'alternate_phone', 'current_address', 'permanent_address', 'district',
            'father_name', 'mother_name', 'gender', 'blood_group',
            'designation_bn', 'designation_en', 'organization', 'department', 'profession',
            'academic_qualification', 'professional_qualification', 'years_of_experience',
            'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone', 'emergency_contact_address',
        ],
        'verification_required_fields': list(SENSITIVE_PROFILE_FIELDS.keys()),
        'profile_completion': completion['percentage'],
        'profile_completion_details': completion,
        'pending_change_requests': pending_requests,
        **exp,
    }



def _compute_expiry_info(member: Member, now: datetime | None = None) -> dict:
    now = now or datetime.utcnow()
    status = (member.status or 'PENDING').upper()
    if status in ('REVOKED', 'SUSPENDED', 'REJECTED'):
        return {
            'days_until_expiry': None,
            'expiry_indicator': status,
            'is_expiring_soon': False,
            'is_expired': status == 'EXPIRED',
            'valid_until_formatted': member.validity_date.strftime('%d %b %Y') if member.validity_date else None,
            'valid_years': None,
        }
    if not member.validity_date:
        return {
            'days_until_expiry': None,
            'expiry_indicator': 'ACTIVE' if status == 'ACTIVE' else status,
            'is_expiring_soon': False,
            'is_expired': status == 'EXPIRED',
            'valid_until_formatted': None,
            'valid_years': None,
        }
    delta_days = (member.validity_date.date() - now.date()).days
    iss_year = (member.issue_date or now).year
    val_year = member.validity_date.year
    if delta_days < 0 or status == 'EXPIRED':
        indicator = 'EXPIRED'
    elif delta_days <= 60:
        indicator = 'EXPIRING_SOON'
    else:
        indicator = 'VALID'
    return {
        'days_until_expiry': delta_days,
        'expiry_indicator': indicator,
        'is_expiring_soon': 0 <= delta_days <= 60,
        'is_expired': delta_days < 0 or status == 'EXPIRED',
        'valid_until_formatted': member.validity_date.strftime('%d %b %Y'),
        'valid_years': f'{iss_year}–{val_year}',
    }


def compute_authoritative_membership_status(
    member: Member,
    db: Session,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.utcnow()
    raw_status = (member.status or 'PENDING').upper()

    # Rule: Suspended/Cancelled/Revoked/Rejected MUST override date-based status
    if raw_status in ('SUSPENDED', 'CANCELLED', 'REVOKED', 'REJECTED'):
        status = raw_status
        days_remaining = None
        renewal_available = False
        renewal_ineligible_reason = (
            "আপনার সদস্যপদ বর্তমানে স্থগিত (SUSPENDED) অবস্থায় রয়েছে।"
            if raw_status == 'SUSPENDED'
            else f"আপনার সদস্যপদ স্থিতি: {raw_status}। বর্তমানে নবায়ন প্রযোজ্য নয়।"
        )
    elif raw_status in ('PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'DOCUMENTS_REQUIRED', 'PAYMENT_PENDING'):
        status = raw_status
        days_remaining = None
        renewal_available = False
        renewal_ineligible_reason = "সদস্যপদ আবেদন এখনও সক্রিয় হয়নি।"
    else:
        # Date-based calculation:
        # valid_until > today + 30 days -> ACTIVE
        # valid_until <= today + 30 days and >= today -> EXPIRING_SOON
        # valid_until < today -> EXPIRED
        if not member.validity_date:
            status = 'ACTIVE' if raw_status == 'ACTIVE' else raw_status
            days_remaining = None
        else:
            delta_days = (member.validity_date.date() - now.date()).days
            days_remaining = delta_days
            if delta_days < 0:
                status = 'EXPIRED'
            elif delta_days <= 30:
                status = 'EXPIRING_SOON'
            else:
                status = 'ACTIVE'

        # Renewal eligibility verification:
        pending_renewal = db.scalar(
            select(MembershipRenewal)
            .where(
                MembershipRenewal.member_id == member.id,
                MembershipRenewal.status.in_(['PENDING', 'INITIATED', 'SUBMITTED', 'UNDER_REVIEW']),
            )
        )
        unverified_docs = any(
            d.review_status in ('REJECTED', 'REQUIRED', 'DOCUMENTS_REQUIRED')
            for d in (member.documents or [])
        )

        if pending_renewal:
            renewal_available = False
            renewal_ineligible_reason = "আপনার সদস্যপদের একটি নবায়ন আবেদন বর্তমানে প্রক্রিয়াধীন রয়েছে (Your membership currently has an unresolved renewal application)."
        elif unverified_docs:
            renewal_available = False
            renewal_ineligible_reason = "আপনার প্রয়োজনীয় ডকুমেন্ট এখনও অনুমোদিত হয়নি (Required membership documents need verification)."
        else:
            renewal_available = True
            renewal_ineligible_reason = None

    valid_from = member.issue_date or member.created_at or now
    valid_until = member.validity_date
    total_days = 365
    progress_percentage = 100
    if valid_until and valid_from:
        total_days = max(1, (valid_until.date() - valid_from.date()).days)
        if total_days > 0 and days_remaining is not None:
            progress_percentage = max(0, min(100, int((max(0, days_remaining) / total_days) * 100)))

    grid_circle = None
    if member.circle:
        grid_circle = {
            'id': member.circle.id,
            'name': member.circle.name_en or member.circle.name_bn,
            'name_bn': member.circle.name_bn,
            'name_en': member.circle.name_en,
        }

    return {
        'membership_id': member.membership_id,
        'type': (member.membership_type or 'PROFESSIONAL').upper(),
        'status': status,
        'raw_status': raw_status,
        'status_indicator': status,
        'grid_circle': grid_circle,
        'joined_at': (member.issue_date or member.created_at or now).strftime('%Y-%m-%d'),
        'valid_from': valid_from.strftime('%Y-%m-%d') if valid_from else None,
        'valid_until': valid_until.strftime('%Y-%m-%d') if valid_until else None,
        'valid_until_formatted': valid_until.strftime('%d %B %Y') if valid_until else None,
        'days_remaining': days_remaining,
        'total_validity_days': total_days,
        'progress_percentage': progress_percentage,
        'renewal_available': renewal_available,
        'renewal_ineligible_reason': renewal_ineligible_reason,
        'certificate_available': bool(member.membership_id and status in ('ACTIVE', 'EXPIRING_SOON', 'EXPIRED')),
        'digital_id_available': bool(member.membership_id and status in ('ACTIVE', 'EXPIRING_SOON')),
    }


def get_membership_renewal_pricing(
    member: Member,
    db: Session,
    now: datetime | None = None,
) -> list[dict]:
    now = now or datetime.utcnow()
    schedule = get_fee_schedule(db)
    base_annual = int(schedule.get('RENEWAL', 2000))
    if base_annual <= 0:
        base_annual = 1000

    base_date = member.validity_date if (member.validity_date and member.validity_date > now) else now

    return [
        {
            'duration_years': 1,
            'fee_bdt': base_annual,
            'fee_formatted': f'৳{base_annual:,}',
            'new_validity': (base_date + timedelta(days=365)).strftime('%Y-%m-%d'),
            'new_validity_formatted': (base_date + timedelta(days=365)).strftime('%d %B %Y'),
            'discount_pct': 0,
            'title_bn': '১ বছর মেয়াদী নবায়ন',
            'title_en': '1 Year Renewal',
        },
        {
            'duration_years': 2,
            'fee_bdt': int(base_annual * 2 * 0.95),
            'fee_formatted': f'৳{int(base_annual * 2 * 0.95):,}',
            'new_validity': (base_date + timedelta(days=730)).strftime('%Y-%m-%d'),
            'new_validity_formatted': (base_date + timedelta(days=730)).strftime('%d %B %Y'),
            'discount_pct': 5,
            'title_bn': '২ বছর মেয়াদী নবায়ন (৫% ছাড়)',
            'title_en': '2 Years Renewal (5% discount)',
        },
        {
            'duration_years': 3,
            'fee_bdt': int(base_annual * 3 * 0.90),
            'fee_formatted': f'৳{int(base_annual * 3 * 0.90):,}',
            'new_validity': (base_date + timedelta(days=1095)).strftime('%Y-%m-%d'),
            'new_validity_formatted': (base_date + timedelta(days=1095)).strftime('%d %B %Y'),
            'discount_pct': 10,
            'title_bn': '৩ বছর মেয়াদী নবায়ন (১০% ছাড়)',
            'title_en': '3 Years Renewal (10% discount)',
        },
    ]


def _relative_time(dt: datetime | None, now: datetime | None = None) -> tuple[str, str]:
    if not dt:
        return ('Just now', 'এইমাত্র')
    now = now or datetime.utcnow()
    diff = max(0, int((now - dt).total_seconds()))
    if diff < 60:
        return ('Just now', 'এইমাত্র')
    if diff < 3600:
        mins = diff // 60
        return (f'{mins} min ago', f'{mins} মিনিট আগে')
    if diff < 86400:
        hrs = diff // 3600
        return (f'{hrs} hour{"s" if hrs > 1 else ""} ago', f'{hrs} ঘণ্টা আগে')
    days = diff // 86400
    if days == 1:
        return ('Yesterday', 'গতকাল')
    return (f'{days} days ago', f'{days} দিন আগে')


def response(member: Member) -> ApplicationResponse:
    return ApplicationResponse(
        id=member.id, membership_id=member.membership_id, status=member.status,
        designation_bn=member.designation_bn,
        circle_bn=member.circle.name_bn if member.circle else None,
        application_note=member.application_note,
        issue_date=member.issue_date, validity_date=member.validity_date,
    )


@router.get('/profile')
def profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    meta = _get_or_create_profile_meta(db, m.id)
    exp = _compute_expiry_info(m)
    completion = _compute_profile_completion(user, m, meta)
    change_rows = db.scalars(
        select(MemberProfileChangeRequest)
        .where(MemberProfileChangeRequest.member_id == m.id)
        .order_by(MemberProfileChangeRequest.created_at.desc())
        .limit(20)
    ).all()
    pending_requests = [
        {
            'id': r.id,
            'field_name': r.field_name,
            'field_label_en': SENSITIVE_PROFILE_FIELDS.get(r.field_name, (r.field_name, r.field_name))[0],
            'field_label_bn': SENSITIVE_PROFILE_FIELDS.get(r.field_name, (r.field_name, r.field_name))[1],
            'current_value': r.current_value,
            'requested_value': r.requested_value,
            'reason': r.reason,
            'supporting_doc_url': r.supporting_doc_url,
            'status': r.status,
            'reviewer_note': r.review_note,
            'review_note': r.review_note,
            'created_at': r.created_at,
            'reviewed_at': r.reviewed_at,
        }
        for r in change_rows
    ]
    db.commit()
    return _serialize_full_profile(user, m, meta, exp, completion, pending_requests)


@router.get('/dashboard')
def member_dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Consolidated Member Portal Dashboard API: returns complete member status, profile completion, timeline, payments, documents, certificates, events, circulars, and notifications in one call."""
    from app.services.certificate_service import CertificateService

    m = get_member(user, db)
    meta = _get_or_create_profile_meta(db, m.id)
    now = datetime.utcnow()
    exp = _compute_expiry_info(m, now)
    completion = _compute_profile_completion(user, m, meta)
    application_timeline = _build_application_timeline(db, m)

    unread_count = db.scalar(
        select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    ) or 0
    certs_list = CertificateService.ensure_member_wallet_certificates(db, user, m)
    certs_count = len(certs_list)
    docs_list = [
        {
            'id': d.id,
            'document_type': d.document_type,
            'filename': d.filename,
            'review_status': d.review_status,
            'reviewer_note': getattr(d, 'reviewer_note', None),
            'created_at': d.created_at,
            'download_url': f'/api/v1/member/documents/{d.id}/download',
        }
        for d in (m.documents or [])
    ]
    docs_count = len(docs_list)

    all_payments = db.scalars(
        select(PaymentTransaction)
        .where((PaymentTransaction.member_id == m.id) | (PaymentTransaction.user_id == user.id))
        .order_by(PaymentTransaction.created_at.desc())
        .limit(20)
    ).all()
    payments_count = len(all_payments)
    paid_payments = [p for p in all_payments if (p.status or '').upper() in ('PAID', 'SUCCESS', 'COMPLETED')]
    pending_payments = [p for p in all_payments if (p.status or '').upper() in ('PENDING', 'INITIATED', 'PROCESSING')]
    total_paid_bdt = sum(float(p.amount or 0) for p in paid_payments)
    latest_payment_obj = all_payments[0] if all_payments else None

    failed_payments = [p for p in all_payments if (p.status or '').upper() in ('FAILED', 'CANCELLED', 'REJECTED')]
    payment_summary = {
        'total_paid': total_paid_bdt,
        'total_paid_formatted': f'৳{int(total_paid_bdt):,}',
        'successful': len(paid_payments),
        'pending': len(pending_payments),
        'failed': len(failed_payments),
        'payments_count': payments_count,
        'paid_count': len(paid_payments),
        'pending_count': len(pending_payments),
        'latest_payment': {
            'id': latest_payment_obj.id,
            'amount': float(latest_payment_obj.amount),
            'amount_formatted': f'৳{int(latest_payment_obj.amount):,}',
            'currency': latest_payment_obj.currency,
            'purpose': latest_payment_obj.purpose,
            'provider': latest_payment_obj.provider,
            'status': latest_payment_obj.status,
            'receipt_no': latest_payment_obj.receipt_no,
            'transaction_ref': latest_payment_obj.transaction_ref,
            'created_at': latest_payment_obj.created_at,
            'receipt_pdf_url': f'/api/v1/member/payments/{latest_payment_obj.id}/receipt.pdf'
            if (latest_payment_obj.status or '').upper() in ('PAID', 'SUCCESS', 'COMPLETED')
            else None,
        }
        if latest_payment_obj
        else None,
        'recent_payments': [
            {
                'id': p.id,
                'amount': float(p.amount),
                'amount_formatted': f'৳{int(p.amount):,}',
                'currency': p.currency,
                'purpose': p.purpose,
                'provider': p.provider,
                'status': p.status,
                'receipt_no': p.receipt_no,
                'transaction_ref': p.transaction_ref,
                'created_at': p.created_at,
                'receipt_pdf_url': f'/api/v1/member/payments/{p.id}/receipt.pdf'
                if (p.status or '').upper() in ('PAID', 'SUCCESS', 'COMPLETED')
                else None,
            }
            for p in all_payments[:5]
        ],
    }

    # Member event registrations & upcoming events
    reg_rows = db.scalars(
        select(EventRegistration).where(EventRegistration.user_id == user.id)
    ).all()
    reg_by_event = {r.event_id: r for r in reg_rows}
    events_count = len(reg_rows)

    upcoming_events_rows = db.scalars(
        select(Event).where(Event.is_published == True).order_by(Event.event_date.desc()).limit(6)
    ).all()
    month_names_en = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    events_payload = []
    for ev in upcoming_events_rows:
        ev_dt = ev.event_date
        ev_day = f'{ev_dt.day:02d}' if ev_dt else '15'
        ev_month = month_names_en[ev_dt.month] if ev_dt and 1 <= ev_dt.month <= 12 else 'OCT'
        ev_time = ev_dt.strftime('%I:%M %p') if ev_dt else '10:00 AM'
        events_payload.append({
            'id': ev.id,
            'slug': getattr(ev, 'slug', str(ev.id)),
            'title': ev.title_en or ev.title_bn,
            'title_bn': ev.title_bn,
            'title_en': ev.title_en,
            'summary_bn': getattr(ev, 'summary_bn', None) or ev.description_bn,
            'location': ev.location_bn or 'Dhaka',
            'location_bn': ev.location_bn or 'ঢাকা',
            'location_en': ev.location_bn or 'Dhaka',
            'time': ev_time,
            'day': ev_day,
            'month': ev_month,
            'event_date': ev.event_date,
            'event_date_formatted': ev.event_date.strftime('%d %b %Y') if ev.event_date else None,
            'registration_Required': bool(getattr(ev, 'registration_enabled', False)),
            'registration_enabled': bool(getattr(ev, 'registration_enabled', False)),
            'is_registered': ev.id in reg_by_event,
            'registration_status': reg_by_event[ev.id].attendance_status if ev.id in reg_by_event else None,
        })

    # Saved/Read state for circulars & notices
    saved_rows = db.scalars(
        select(MemberSavedContent).where(MemberSavedContent.user_id == user.id)
    ).all()
    saved_map = {(s.entity_type.upper(), s.entity_id): s for s in saved_rows}

    recent_circulars = db.scalars(
        select(Circular).where(Circular.is_published == True).order_by(Circular.created_at.desc()).limit(5)
    ).all()
    recent_notices = db.scalars(
        select(Notice).where(Notice.is_published == True).order_by(Notice.created_at.desc()).limit(5)
    ).all()

    circulars_payload = []
    for cir in recent_circulars:
        st = saved_map.get(('CIRCULAR', cir.id))
        circulars_payload.append({
            'id': cir.id,
            'content_type': 'CIRCULAR',
            'slug': getattr(cir, 'slug', str(cir.id)),
            'title_bn': cir.title_bn,
            'title_en': cir.title_en,
            'summary_bn': cir.summary_bn,
            'category': cir.category,
            'reference_no': cir.reference_no,
            'attachment_url': getattr(cir, 'attachment_url', None) or cir.document_url,
            'published_at': cir.published_at or cir.created_at,
            'is_bookmarked': bool(st and st.is_bookmarked),
            'is_read': bool(st and st.is_read),
        })
    for ntc in recent_notices:
        st = saved_map.get(('NOTICE', ntc.id))
        circulars_payload.append({
            'id': ntc.id,
            'content_type': 'NOTICE',
            'slug': getattr(ntc, 'slug', str(ntc.id)),
            'title_bn': ntc.title_bn,
            'title_en': ntc.title_en,
            'summary_bn': getattr(ntc, 'summary_bn', None) or ntc.content_bn,
            'category': ntc.category,
            'reference_no': None,
            'attachment_url': ntc.attachment_url,
            'published_at': ntc.published_at or ntc.created_at,
            'is_bookmarked': bool(st and st.is_bookmarked),
            'is_read': bool(st and st.is_read),
        })

    notif_rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(10)
    ).all()
    notifications_payload = []
    for n in notif_rows:
        n_type = (n.notification_type or 'SYSTEM').upper()
        if n_type in ('CIRCULAR', 'NOTICE'):
            dot_color = 'blue'
            indicator_icon = '🔵'
        elif n_type in ('PAYMENT', 'RECEIPT'):
            dot_color = 'green'
            indicator_icon = '🟢'
        elif n_type in ('CERTIFICATE', 'MEMBERSHIP'):
            dot_color = 'amber'
            indicator_icon = '📄'
        else:
            dot_color = 'purple'
            indicator_icon = '🔔'

        rel_en, rel_bn = _relative_time(n.created_at, now)
        notifications_payload.append({
            'id': n.id,
            'title': n.title_bn,
            'title_bn': n.title_bn,
            'body': n.body_bn,
            'body_bn': n.body_bn,
            'type': n.notification_type,
            'dot_color': dot_color,
            'indicator_icon': indicator_icon,
            'read_at': n.read_at,
            'is_read': bool(n.read_at),
            'indicator': '○' if n.read_at else '●',
            'created_at': n.created_at,
            'relative_time': rel_en,
            'relative_time_en': rel_en,
            'relative_time_bn': rel_bn,
            'href': '/portal?tab=notifications',
        })

    change_rows = db.scalars(
        select(MemberProfileChangeRequest)
        .where(MemberProfileChangeRequest.member_id == m.id)
        .order_by(MemberProfileChangeRequest.created_at.desc())
        .limit(10)
    ).all()
    change_requests_payload = [
        {
            'id': r.id,
            'field_name': r.field_name,
            'field_label_en': SENSITIVE_PROFILE_FIELDS.get(r.field_name, (r.field_name, r.field_name))[0],
            'field_label_bn': SENSITIVE_PROFILE_FIELDS.get(r.field_name, (r.field_name, r.field_name))[1],
            'current_value': r.current_value,
            'requested_value': r.requested_value,
            'reason': r.reason,
            'supporting_doc_url': r.supporting_doc_url,
            'status': r.status,
            'reviewer_note': r.review_note,
            'review_note': r.review_note,
            'created_at': r.created_at,
            'reviewed_at': r.reviewed_at,
        }
        for r in change_rows
    ]

    activities: list[dict] = []

    # 1. Membership milestone
    if m.status == 'ACTIVE' and m.membership_id:
        activities.append({
            'id': f'mem-{m.id}',
            'type': 'MEMBERSHIP',
            'title': 'Membership approved',
            'title_en': 'Membership approved',
            'title_bn': f'সদস্যপদ অনুমোদিত ({m.membership_id})',
            'description': f'Membership ID: {m.membership_id} · {m.circle.name_en if m.circle else "PGCB"}',
            'subtitle_bn': f'বৈধতা: {exp["valid_until_formatted"] or "সক্রিয়"}',
            'timestamp': (m.issue_date or m.updated_at or m.created_at or now).isoformat(),
            'relative_time_en': _relative_time(m.issue_date or m.updated_at, now)[0],
            'relative_time_bn': _relative_time(m.issue_date or m.updated_at, now)[1],
            'href': '/portal?tab=membership',
        })

    # 2. Application milestone
    app_row = db.scalar(select(MembershipApplication).where(MembershipApplication.member_id == m.id))
    if app_row:
        app_status_clean = (app_row.status or 'SUBMITTED').replace('_', ' ').lower()
        activities.append({
            'id': f'app-{app_row.id}',
            'type': 'APPLICATION',
            'title': f'Membership application {app_status_clean}',
            'title_en': f'Membership application {app_status_clean}',
            'title_bn': f'সদস্যপদ আবেদন: {application_timeline.get("status_label_bn", app_status_clean)}',
            'description': f'Application #{application_timeline.get("application_no", app_row.application_no)}',
            'subtitle_bn': f'রেফারেন্স: {application_timeline.get("application_no", app_row.application_no)}',
            'timestamp': (app_row.reviewed_at or app_row.submitted_at or m.created_at or now).isoformat(),
            'relative_time_en': _relative_time(app_row.reviewed_at or app_row.submitted_at, now)[0],
            'relative_time_bn': _relative_time(app_row.reviewed_at or app_row.submitted_at, now)[1],
            'href': '/portal?tab=application',
        })

    # 3. Payments
    for p in paid_payments[:3]:
        activities.append({
            'id': f'pay-{p.id}',
            'type': 'PAYMENT',
            'title': 'Payment successfully received',
            'title_en': 'Payment successfully received',
            'title_bn': f'পেমেন্ট সফল হয়েছে (৳{int(p.amount):,})',
            'description': f'{(p.purpose or "Membership Renewal").replace("_", " ").title()} · ৳{int(p.amount):,}',
            'subtitle_bn': f'রসিদ: {p.receipt_no or p.transaction_ref or p.id}',
            'timestamp': (p.updated_at or p.created_at or now).isoformat(),
            'relative_time_en': _relative_time(p.updated_at or p.created_at, now)[0],
            'relative_time_bn': _relative_time(p.updated_at or p.created_at, now)[1],
            'href': '/portal?tab=payments',
        })

    # 4. Certificates
    for c in certs_list[:3]:
        c_date = c.get('issue_date') if isinstance(c, dict) else getattr(c, 'issue_date', None)
        c_no = c.get('certificate_no') if isinstance(c, dict) else getattr(c, 'certificate_no', '')
        c_title = c.get('title_bn') if isinstance(c, dict) else getattr(c, 'title_bn', '')
        c_id = c.get('id') if isinstance(c, dict) else getattr(c, 'id', 0)
        dt_val = c_date if isinstance(c_date, datetime) else now
        activities.append({
            'id': f'cert-{c_id}',
            'type': 'CERTIFICATE',
            'title': 'Membership certificate issued',
            'title_en': 'Membership certificate issued',
            'title_bn': f'সনদপত্র ইস্যু হয়েছে ({c_no})',
            'description': c_title or f'Certificate #{c_no}',
            'subtitle_bn': c_title,
            'timestamp': dt_val.isoformat(),
            'relative_time_en': _relative_time(dt_val, now)[0],
            'relative_time_bn': _relative_time(dt_val, now)[1],
            'href': '/portal?tab=certificates',
        })

    # 5. Documents
    for d in (m.documents or [])[:2]:
        activities.append({
            'id': f'doc-{d.id}',
            'type': 'DOCUMENT',
            'title': f'{d.document_type.replace("_", " ").title()} document {d.review_status.lower()}',
            'title_en': f'{d.document_type} document {d.review_status.lower()}',
            'title_bn': f'{d.document_type} ডকুমেন্ট অবস্থা: {d.review_status}',
            'description': f'File: {d.filename}',
            'subtitle_bn': d.filename,
            'timestamp': (d.created_at or now).isoformat(),
            'relative_time_en': _relative_time(d.created_at, now)[0],
            'relative_time_bn': _relative_time(d.created_at, now)[1],
            'href': '/portal?tab=documents',
        })

    # 6. Profile
    if meta.updated_at or m.updated_at:
        upd_time = meta.updated_at or m.updated_at
        activities.append({
            'id': f'prof-{m.id}',
            'type': 'PROFILE',
            'title': 'Profile information updated',
            'title_en': 'Profile information updated',
            'title_bn': 'প্রোফাইল তথ্য হালনাগাদ করা হয়েছে',
            'description': f'{m.designation_en or "Engineer"} · {m.circle.name_en if m.circle else "PGCB"}',
            'subtitle_bn': m.designation_bn or 'প্রকৌশলী',
            'timestamp': upd_time.isoformat(),
            'relative_time_en': _relative_time(upd_time, now)[0],
            'relative_time_bn': _relative_time(upd_time, now)[1],
            'href': '/portal?tab=profile',
        })

    activities.sort(key=lambda item: item.get('timestamp') or '', reverse=True)

    verified_docs = len([d for d in docs_list if d.get('review_status') == 'APPROVED'])
    pending_docs = len([d for d in docs_list if d.get('review_status') in ('PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'DOCUMENT_REQUIRED')])
    documents_summary = {
        'total': docs_count,
        'verified': verified_docs,
        'pending': pending_docs,
        'items': docs_list,
    }

    membership_info = {
        'id': m.id,
        'member_id': m.id,
        'membership_id': m.membership_id,
        'status': m.status or 'PENDING',
        'type': m.membership_type or 'PROFESSIONAL',
        'membership_type': m.membership_type or 'PROFESSIONAL',
        'joined_at': (m.issue_date or m.created_at).strftime('%Y-%m-%d') if (m.issue_date or m.created_at) else None,
        'valid_until': m.validity_date.strftime('%Y-%m-%d') if m.validity_date else None,
        'validity_date': m.validity_date,
        'issue_date': m.issue_date,
        'valid_until_formatted': exp.get('valid_until_formatted'),
        'designation_bn': m.designation_bn,
        'designation_en': m.designation_en,
        'circle_id': m.circle_id,
        'circle': m.circle.name_en if m.circle else 'Dhaka',
        'circle_bn': m.circle.name_bn if m.circle else 'ঢাকা',
        'circle_en': m.circle.name_en if m.circle else 'Dhaka',
        **exp,
    }

    quick_actions = [
        {'id': 'DIGITAL_ID', 'label_bn': 'ডিজিটাল আইডি', 'label_en': 'Digital ID', 'href': '/member/digital-id'},
        {'id': 'RENEW_MEMBERSHIP', 'label_bn': 'সদস্যপদ নবায়ন', 'label_en': 'Renew Membership', 'href': '/member/membership/renew'},
        {'id': 'CERTIFICATES', 'label_bn': 'সনদপত্র ওয়ালেট', 'label_en': 'Certificates', 'href': '/member/certificates'},
        {'id': 'DOCUMENTS', 'label_bn': 'ডকুমেন্টস', 'label_en': 'Documents', 'href': '/member/documents'},
        {'id': 'PAYMENTS', 'label_bn': 'পেমেন্ট ও রসিদ', 'label_en': 'Payments', 'href': '/member/payments'},
        {'id': 'EVENTS', 'label_bn': 'ইভেন্ট নিবন্ধন', 'label_en': 'Events', 'href': '/events'},
    ]

    full_member_profile = _serialize_full_profile(user, m, meta, exp, completion, change_requests_payload)
    digital_id_available = bool(m.status == 'ACTIVE' and m.membership_id)

    return {
        'member': {
            'id': m.id,
            'name_bn': user.name_bn,
            'name_en': user.name_en,
            'membership_id': m.membership_id,
            'photo_url': m.photo_url,
            'circle': m.circle.name_en if m.circle else 'Dhaka',
            'circle_bn': m.circle.name_bn if m.circle else 'ঢাকা',
            'circle_en': m.circle.name_en if m.circle else 'Dhaka',
            'designation_bn': m.designation_bn,
            'designation_en': m.designation_en,
            'organization': meta.organization or 'Power Grid Company of Bangladesh PLC (PGCB)',
            'department': meta.department,
            'profession': meta.profession,
            'email': user.email,
            'phone': user.phone,
            'emergency_contact_name': meta.emergency_contact_name,
            'emergency_contact_phone': meta.emergency_contact_phone,
            'profile_completion': completion['percentage'],
            **full_member_profile,
        },
        'membership': membership_info,
        'application': {
            'id': application_timeline['id'],
            'status': application_timeline['status'],
            'reference': application_timeline['application_no'],
            'application_no': application_timeline['application_no'],
            'membership_id': m.membership_id,
            'membership_type': application_timeline['membership_type'],
            'status_label_en': application_timeline['status_label_en'],
            'status_label_bn': application_timeline['status_label_bn'],
            'stages': application_timeline['stages'],
            'required_actions': application_timeline['required_actions'],
            'circle_bn': application_timeline['circle_bn'],
            'circle_en': application_timeline['circle_en'],
            'submitted_at': application_timeline['submitted_at'],
            'approved_at': application_timeline['approved_at'],
            'reviewer_notes': application_timeline['reviewer_notes'],
        },
        'profile_completion': completion['percentage'],
        'profile_completion_details': completion,
        'payment_summary': payment_summary,
        'documents': documents_summary,
        'documents_list': docs_list,
        'certificates': certs_list,
        'upcoming_events': events_payload[:5],
        'events': events_payload,
        'notifications': notifications_payload[:5],
        'recent_activity': activities[:10],
        'unread_notifications_count': unread_count,
        'digital_id_available': digital_id_available,
        'change_requests': change_requests_payload,
        'quick_actions': quick_actions,
        'quick_stats': {
            'unread_notifications': unread_count,
            'certificates_count': certs_count,
            'documents_count': docs_count,
            'payments_count': payments_count,
            'events_count': events_count,
            'profile_completion': completion['percentage'],
            'pending_applications': 0 if m.status == 'ACTIVE' else 1,
            'digital_id_available': digital_id_available,
        },
        'hero_card': membership_info,
        'user': {
            'id': user.id,
            'name_bn': user.name_bn,
            'name_en': user.name_en,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
        },
        'circulars': circulars_payload,
    }


@router.get('/renewal-options')
def get_renewal_options(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Return available membership renewal periods, server-calculated fees, and projected expiry dates."""
    m = get_member(user, db)
    now = datetime.utcnow()
    exp = _compute_expiry_info(m, now)
    schedule = get_fee_schedule(db)
    base_date = m.validity_date if (m.validity_date and m.validity_date > now) else now

    annual_fee = int(schedule.get('RENEWAL', 2000))
    life_fee = int(schedule.get('LIFE', 10000))

    periods = [
        {
            'plan_id': 'RENEWAL_1YR',
            'code': 'RENEWAL_1YR',
            'period': '1YR',
            'title_bn': '১ বছর মেয়াদী বার্ষিক নবায়ন',
            'title_en': '1 Year Annual Membership Renewal',
            'years': 1,
            'days': 365,
            'amount': annual_fee,
            'amount_bdt': annual_fee,
            'amount_formatted': f'৳{annual_fee:,}',
            'currency': 'BDT',
            'projected_validity_date': (base_date + timedelta(days=365)).strftime('%Y-%m-%d'),
            'projected_validity_formatted': (base_date + timedelta(days=365)).strftime('%d %b %Y'),
        },
        {
            'plan_id': 'RENEWAL_2YR',
            'code': 'RENEWAL_2YR',
            'period': '2YR',
            'title_bn': '২ বছর মেয়াদী বর্ধিত নবায়ন',
            'title_en': '2 Years Extended Membership Renewal',
            'years': 2,
            'days': 730,
            'amount': annual_fee * 2,
            'amount_bdt': annual_fee * 2,
            'amount_formatted': f'৳{annual_fee * 2:,}',
            'currency': 'BDT',
            'projected_validity_date': (base_date + timedelta(days=730)).strftime('%Y-%m-%d'),
            'projected_validity_formatted': (base_date + timedelta(days=730)).strftime('%d %b %Y'),
        },
        {
            'plan_id': 'LIFE',
            'code': 'LIFE',
            'period': 'LIFE',
            'title_bn': 'আজীবন সদস্যপদ আপগ্রেড',
            'title_en': 'Lifetime Membership Upgrade',
            'years': 50,
            'days': 18250,
            'amount': life_fee,
            'amount_bdt': life_fee,
            'amount_formatted': f'৳{life_fee:,}',
            'currency': 'BDT',
            'projected_validity_date': (base_date + timedelta(days=18250)).strftime('%Y-%m-%d'),
            'projected_validity_formatted': (base_date + timedelta(days=18250)).strftime('%d %b %Y'),
        },
    ]

    return {
        'member_id': m.id,
        'membership_id': m.membership_id,
        'status': m.status,
        'current_validity_date': m.validity_date,
        **exp,
        'reminder_schedule_days': [60, 30, 7, 0],
        'options': periods,
        'periods': periods,
    }


@router.get('/renewals')
def list_member_renewals(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Return chronological history of membership renewals for the authenticated member."""
    m = get_member(user, db)
    rows = db.scalars(
        select(MembershipRenewal)
        .where(MembershipRenewal.member_id == m.id)
        .order_by(MembershipRenewal.created_at.desc())
    ).all()
    result = []
    for r in rows:
        payment = db.get(PaymentTransaction, r.payment_id) if r.payment_id else None
        result.append({
            'id': r.id,
            'payment_id': r.payment_id,
            'previous_validity_date': r.previous_validity_date,
            'new_validity_date': r.new_validity_date,
            'new_validity_formatted': r.new_validity_date.strftime('%d %b %Y') if r.new_validity_date else None,
            'amount': float(r.amount),
            'amount_formatted': f'৳{int(r.amount):,}',
            'currency': r.currency,
            'status': r.status,
            'receipt_no': payment.receipt_no if payment else None,
            'receipt_pdf_url': f'/api/v1/member/payments/{payment.id}/receipt.pdf' if payment else None,
            'created_at': r.created_at,
        })
    return {'renewals': result, 'items': result, 'count': len(result)}


@router.get('/membership', response_model=MembershipSummaryResponse)
def get_member_membership_summary(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 3: Membership Summary API.
    Returns authoritative server-calculated membership status, validity, circle,
    and eligibility flags without requiring any client-supplied member ID.
    """
    m = get_member(user, db)
    return compute_authoritative_membership_status(m, db)


@router.get('/membership/history')
def get_member_membership_history(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 3: Chronological membership history including initial joining,
    renewals, status modifications, payment and certificate linkages.
    """
    m = get_member(user, db)
    history_items: list[dict] = []

    # 1. Status history records
    status_records = db.scalars(
        select(MembershipStatusHistory)
        .where(MembershipStatusHistory.member_id == m.id)
        .order_by(MembershipStatusHistory.effective_at.desc())
    ).all()

    for h in status_records:
        action_label_map = {
            'RENEWAL': ('নবায়ন সম্পন্ন', 'Renewal Completed'),
            'ACTIVATED': ('সদস্যপদ সক্রিয়করণ', 'Membership Activated'),
            'SUSPENDED': ('সদস্যপদ স্থগিতকরণ', 'Membership Suspended'),
            'REACTIVATED': ('সদস্যপদ পুনঃসক্রিয়করণ', 'Membership Reactivated'),
            'CREATED': ('সদস্যপদ নিবন্ধন', 'Membership Created'),
            'EXPIRED': ('মেয়াদোত্তীর্ণ', 'Membership Expired'),
        }
        action_lbl = action_label_map.get(h.action, (h.action, h.action))
        performed_name = None
        if h.performed_by:
            performed_name = h.performed_by.name_en or h.performed_by.name_bn
        elif h.action == 'RENEWAL':
            performed_name = 'Member Self-Service'
        else:
            performed_name = 'Central Executive Committee'

        pay_ref = None
        if h.payment:
            pay_ref = h.payment.receipt_no or h.payment.transaction_ref
        cert_ref = None
        if h.certificate:
            cert_ref = h.certificate.certificate_no

        history_items.append({
            'id': f'hist-{h.id}',
            'reference': h.reference,
            'date': h.effective_at.strftime('%d %b %Y'),
            'action': h.action,
            'action_label_bn': action_lbl[0],
            'action_label_en': action_lbl[1],
            'period': str(h.effective_at.year),
            'old_validity': h.old_validity.strftime('%d %b %Y') if h.old_validity else '—',
            'new_validity': h.new_validity.strftime('%d %b %Y') if h.new_validity else '—',
            'status': h.new_status,
            'status_label_bn': 'সম্পন্ন' if h.new_status in ('ACTIVE', 'COMPLETED') else h.new_status,
            'payment_reference': pay_ref,
            'certificate_reference': cert_ref,
            'performed_by': performed_name,
            'timestamp': h.effective_at.isoformat(),
        })

    # 2. Membership Renewal records
    renewals = db.scalars(
        select(MembershipRenewal)
        .where(MembershipRenewal.member_id == m.id)
        .order_by(MembershipRenewal.created_at.desc())
    ).all()

    for r in renewals:
        if any(item.get('reference') == r.reference for item in history_items):
            continue
        p = db.get(PaymentTransaction, r.payment_id) if r.payment_id else None
        history_items.append({
            'id': f'ren-{r.id}',
            'reference': r.reference,
            'date': r.created_at.strftime('%d %b %Y'),
            'action': 'RENEWAL',
            'action_label_bn': 'নবায়ন সম্পন্ন',
            'action_label_en': 'Renewal Completed',
            'period': str(r.new_validity_date.year) if r.new_validity_date else str(r.created_at.year),
            'old_validity': r.previous_validity_date.strftime('%d %b %Y') if r.previous_validity_date else '—',
            'new_validity': r.new_validity_date.strftime('%d %b %Y') if r.new_validity_date else '—',
            'status': r.status.upper(),
            'status_label_bn': 'সম্পন্ন' if r.status in ('COMPLETED', 'ACTIVE') else 'প্রক্রিয়াধীন',
            'payment_reference': p.receipt_no or p.transaction_ref if p else None,
            'certificate_reference': None,
            'performed_by': 'Member Self-Service',
            'timestamp': r.created_at.isoformat(),
        })

    # 3. Initial joined record
    join_date = m.issue_date or m.created_at or datetime.utcnow()
    initial_cert = db.scalar(select(Certificate).where(Certificate.member_id == m.id).order_by(Certificate.id.asc()))
    initial_payment = db.scalar(
        select(PaymentTransaction)
        .where(PaymentTransaction.member_id == m.id, PaymentTransaction.status.in_(['PAID', 'SUCCESS', 'COMPLETED']))
        .order_by(PaymentTransaction.id.asc())
    )

    history_items.append({
        'id': f'init-{m.id}',
        'reference': f'PGCB-MEM-{join_date.year}-{m.id:05d}',
        'date': join_date.strftime('%d %b %Y'),
        'action': 'CREATED',
        'action_label_bn': 'সদস্যপদ সংযোজন',
        'action_label_en': 'Membership Created',
        'period': str(join_date.year),
        'old_validity': '—',
        'new_validity': m.validity_date.strftime('%d %b %Y') if m.validity_date else str(join_date.year),
        'status': 'ACTIVE' if m.status == 'ACTIVE' else m.status,
        'status_label_bn': 'সক্রিয়' if m.status == 'ACTIVE' else m.status,
        'payment_reference': initial_payment.receipt_no if initial_payment else None,
        'certificate_reference': initial_cert.certificate_no if initial_cert else None,
        'performed_by': 'Central Executive Committee',
        'timestamp': join_date.isoformat(),
    })

    history_items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return {'items': history_items, 'history': history_items, 'count': len(history_items)}


@router.get('/membership/renewal/options', response_model=MembershipRenewalOptionsResponse)
@router.get('/membership/renew/options', response_model=MembershipRenewalOptionsResponse)
def get_member_renewal_options(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 3: Official renewal options with server-calculated fees and eligibility.
    """
    m = get_member(user, db)
    status_info = compute_authoritative_membership_status(m, db)
    plans = get_membership_renewal_pricing(m, db)

    return {
        'eligible': status_info['renewal_available'],
        'ineligible_reason': status_info['renewal_ineligible_reason'],
        'current_validity': status_info['valid_until_formatted'] or 'N/A',
        'plans': plans,
    }


@router.post('/membership/renew', response_model=MembershipRenewalResponse)
def submit_member_renewal(
    payload: dict,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 3: Submit renewal application with server-calculated fee and target expiry date.
    """
    m = get_member(user, db)
    status_info = compute_authoritative_membership_status(m, db)

    if not status_info['renewal_available']:
        raise HTTPException(
            400,
            status_info['renewal_ineligible_reason'] or 'Membership renewal is currently ineligible.',
        )

    duration_years = int(payload.get('duration_years') or 1)
    if duration_years not in (1, 2, 3):
        raise HTTPException(400, 'Renewal duration must be 1, 2, or 3 years.')

    pricing_plans = get_membership_renewal_pricing(m, db)
    selected_plan = next((p for p in pricing_plans if p['duration_years'] == duration_years), pricing_plans[0])
    official_fee = selected_plan['fee_bdt']

    client_amount = payload.get('amount')
    if client_amount is not None and int(client_amount) != official_fee:
        raise HTTPException(
            400,
            f'Client amount (৳{client_amount}) does not match server fee (৳{official_fee}) for {duration_years} year renewal.',
        )

    now = datetime.utcnow()
    base_date = m.validity_date if (m.validity_date and m.validity_date > now) else now
    target_validity = base_date + timedelta(days=duration_years * 365)

    renewal = MembershipRenewal(
        member_id=m.id,
        previous_validity_date=m.validity_date,
        new_validity_date=target_validity,
        amount=official_fee,
        currency='BDT',
        duration_years=duration_years,
        notes=payload.get('notes'),
        status='PENDING',
    )
    db.add(renewal)
    db.flush()

    tx_ref = f'PGCB-REN-{now.year}-{renewal.id:06d}'
    payment = PaymentTransaction(
        user_id=user.id,
        member_id=m.id,
        purpose='MEMBERSHIP_RENEWAL',
        membership_plan_id=f'RENEWAL_{duration_years}YR',
        amount=official_fee,
        currency='BDT',
        provider='SSLCOMMERZ',
        status='PENDING',
        transaction_ref=tx_ref,
    )
    db.add(payment)
    db.flush()

    renewal.payment_id = payment.id

    log_audit_action(
        db=db,
        request=request,
        action='RENEWAL_CREATED',
        entity='MEMBERSHIP_RENEWAL',
        entity_id=str(renewal.id),
        user=user,
        new_value={
            'renewal_id': renewal.id,
            'duration_years': duration_years,
            'amount': official_fee,
            'target_validity': target_validity.strftime('%Y-%m-%d'),
            'transaction_ref': tx_ref,
        },
    )

    db.add(
        Notification(
            user_id=user.id,
            title_bn='সদস্যপদ নবায়ন আবেদন জমা হয়েছে',
            body_bn=(
                f'আপনার {duration_years} বছরের সদস্যপদ নবায়ন আবেদন সফলভাবে জমা হয়েছে। '
                f'মোট প্রদেয় ফি: ৳{official_fee:,}। সক্রিয় করতে পেমেন্ট সম্পন্ন করুন।'
            ),
            notification_type='MEMBERSHIP',
        )
    )

    db.commit()

    return {
        'ok': True,
        'renewal_id': renewal.id,
        'reference': renewal.reference,
        'duration_years': duration_years,
        'amount': official_fee,
        'amount_formatted': f'৳{official_fee:,}',
        'currency': 'BDT',
        'new_validity': target_validity.strftime('%Y-%m-%d'),
        'status': 'PENDING',
        'transaction_id': tx_ref,
        'payment_url': f'/payments/checkout?transaction_id={tx_ref}',
        'message': f'{duration_years} বছরের নবায়ন আবেদন সফলভাবে তৈরি হয়েছে। অনুগ্রহ করে পেমেন্ট সম্পন্ন করুন।',
    }


@router.post('/renewal/initiate')
def initiate_membership_renewal(
    payload: dict,
    request: Request,
    x_idempotency_key: str | None = Header(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate the complete membership renewal workflow:
    Select membership period -> Create payment transaction -> Gateway checkout ->
    Callback verification -> Membership renewed -> New expiry date -> Receipt.
    """
    m = get_member(user, db)
    raw_period = (
        payload.get('period_code')
        or payload.get('membership_plan_id')
        or payload.get('period')
        or 'RENEWAL_1YR'
    ).strip().upper()
    period_alias_map = {
        '1YR': 'RENEWAL_1YR',
        '1_YEAR': 'RENEWAL_1YR',
        'RENEWAL_1YR': 'RENEWAL_1YR',
        '2YR': 'RENEWAL_2YR',
        '2_YEAR': 'RENEWAL_2YR',
        'RENEWAL_2YR': 'RENEWAL_2YR',
        'LIFE': 'LIFE',
        'LIFETIME': 'LIFE',
    }
    period_code = period_alias_map.get(raw_period, raw_period)
    if period_code not in RENEWAL_PERIODS:
        raise HTTPException(400, f'Unsupported renewal period: {raw_period}')

    try:
        provider = normalize_provider(payload.get('provider') or 'SSLCOMMERZ')
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    idem_key = (payload.get('idempotency_key') or x_idempotency_key or '').strip() or None
    if idem_key:
        existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.idempotency_key == idem_key))
        if existing:
            now = datetime.utcnow()
            base_date = m.validity_date if (m.validity_date and m.validity_date > now) else now
            ext_days = resolve_renewal_days(existing.membership_plan_id, int(existing.amount))
            return {
                'id': existing.id,
                'payment_id': existing.id,
                'provider': existing.provider,
                'transaction_id': existing.transaction_ref,
                'provider_transaction_id': existing.provider_transaction_id or existing.transaction_ref,
                'checkout_url': f'/portal?payment_id={existing.id}',
                'status': existing.status,
                'amount': float(existing.amount),
                'currency': existing.currency,
                'period_code': existing.membership_plan_id,
                'membership_plan_id': existing.membership_plan_id,
                'projected_validity_date': (base_date + timedelta(days=ext_days)).strftime('%Y-%m-%d'),
                'idempotent_replay': True,
            }

    amount = resolve_plan_amount(db, period_code)
    client_amount = payload.get('amount')
    if client_amount is not None and int(client_amount) != int(amount):
        raise HTTPException(
            400,
            f'Client amount (৳{client_amount}) does not match server-calculated renewal fee (৳{amount}) for {period_code}',
        )

    item = PaymentTransaction(
        user_id=user.id,
        member_id=m.id,
        membership_plan_id=period_code,
        idempotency_key=idem_key,
        amount=int(amount),
        currency='BDT',
        provider=provider,
        purpose='RENEWAL',
        status='PENDING',
    )
    db.add(item)
    db.flush()

    try:
        checkout = create_checkout(provider, item.id, float(item.amount), item.currency)
    except (RuntimeError, PermissionError) as exc:
        db.rollback()
        raise HTTPException(503, str(exc)) from exc

    item.transaction_ref = checkout.provider_transaction_id
    log_audit_action(
        db,
        request,
        action='INITIATE_RENEWAL',
        entity='PAYMENT',
        entity_id=str(item.id),
        user=user,
        new_value={'provider': provider, 'trx_id': checkout.provider_transaction_id, 'amount': float(item.amount), 'period': period_code},
    )
    db.commit()
    db.refresh(item)

    now = datetime.utcnow()
    base_date = m.validity_date if (m.validity_date and m.validity_date > now) else now
    ext_days = resolve_renewal_days(period_code, int(item.amount))

    return {
        'id': item.id,
        'payment_id': item.id,
        'provider': provider,
        'transaction_id': checkout.provider_transaction_id,
        'provider_transaction_id': checkout.provider_transaction_id,
        'checkout_url': checkout.checkout_url,
        'status': item.status,
        'amount': float(item.amount),
        'currency': item.currency,
        'period_code': period_code,
        'membership_plan_id': period_code,
        'projected_validity_date': (base_date + timedelta(days=ext_days)).strftime('%Y-%m-%d'),
        'projected_validity_formatted': (base_date + timedelta(days=ext_days)).strftime('%d %b %Y'),
    }


def _parse_dob(val: datetime | str | None) -> datetime | None:
    if val is None or val == '':
        return None
    if isinstance(val, datetime):
        return val
    raw = str(val).strip()
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%d/%m/%Y'):
        try:
            return datetime.strptime(raw[:19] if 'T' in fmt else raw[:10], fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(raw.replace('Z', '+00:00'))
    except Exception:
        return None


MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB


def _validate_photo_bytes(filename: str, content: bytes) -> tuple[str, str]:
    if len(content) > MAX_PHOTO_SIZE:
        raise HTTPException(413, 'Photo file size exceeds maximum limit of 5MB')
    if len(content) < 12:
        raise HTTPException(400, 'Invalid photo file: file is too small or corrupted')

    detected_ext = None
    mime = 'application/octet-stream'
    if content.startswith(b'\xff\xd8\xff'):
        detected_ext = 'jpg'
        mime = 'image/jpeg'
    elif content.startswith(b'\x89PNG\r\n\x1a\n'):
        detected_ext = 'png'
        mime = 'image/png'
    elif len(content) >= 12 and content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        detected_ext = 'webp'
        mime = 'image/webp'
    else:
        raise HTTPException(400, 'Invalid file format: Only JPG, JPEG, PNG, and WEBP image files with valid magic bytes are accepted')

    scan_upload_security(content, filename)
    return detected_ext, mime


@router.post('/profile/photo')
def upload_profile_photo(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    m = get_member(user, db)
    content = file.file.read(MAX_PHOTO_SIZE + 1)
    if len(content) > MAX_PHOTO_SIZE:
        raise HTTPException(413, 'Photo file size exceeds maximum limit of 5MB')

    detected_ext, mime = _validate_photo_bytes(file.filename or 'photo.jpg', content)
    unique_name = f"{uuid.uuid4().hex}.{detected_ext}"
    sub_dir = f"members/{m.id}/photos"
    try:
        stored_path = save_bytes(content, sub_dir, unique_name)
    except Exception as exc:
        raise HTTPException(503, f"Failed to store photo: {exc}")

    existing_doc = db.scalar(
        select(MemberDocument).where(MemberDocument.member_id == m.id, MemberDocument.document_type == 'PHOTO')
    )
    if existing_doc:
        existing_doc.filename = f"profile-photo.{detected_ext}"
        existing_doc.storage_path = stored_path
        existing_doc.content_type = mime
        existing_doc.review_status = 'APPROVED'
        doc = existing_doc
    else:
        doc = MemberDocument(
            member_id=m.id,
            document_type='PHOTO',
            filename=f"profile-photo.{detected_ext}",
            storage_path=stored_path,
            content_type=mime,
            review_status='APPROVED',
        )
        db.add(doc)

    m.photo_url = stored_path
    actor_ip = request.client.host if request.client else None
    audit(db, user, 'PROFILE_PHOTO_UPDATED', 'MEMBER', m.id, actor_ip)
    db.commit()
    db.refresh(m)
    return {
        'ok': True,
        'photo_url': m.photo_url,
        'document_id': doc.id,
        'message': 'Profile photo updated successfully',
    }


@router.patch('/profile')
@router.put('/profile')
def update_profile(payload: MemberProfileUpdate, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if any(
        val is not None
        for val in (payload.status, payload.membership_status, payload.payment_status, payload.membership_id)
    ):
        raise HTTPException(403, 'Browser cannot directly modify membership_status, payment_status, or membership_id')
    m = get_member(user, db)
    meta = _get_or_create_profile_meta(db, m.id)

    if payload.employee_id:
        existing_emp = db.scalar(
            select(Member).where(Member.employee_id == payload.employee_id, Member.id != m.id)
        )
        if existing_emp:
            raise HTTPException(409, 'Duplicate membership: employee_id is already registered to another member')

    email_changed = False
    if payload.email and payload.email.strip() and payload.email.strip().lower() != (user.email or '').lower():
        existing_email = db.scalar(
            select(User).where(func.lower(User.email) == payload.email.strip().lower(), User.id != user.id)
        )
        if existing_email:
            raise HTTPException(409, 'Email address is already registered to another account')
        user.email = payload.email.strip().lower()
        email_changed = True

    phone_changed = False
    if payload.phone is not None and str(payload.phone).strip() != str(user.phone or '').strip():
        user.phone = payload.phone
        phone_changed = True

    is_verified = (m.status or '').upper() == 'ACTIVE'
    created_change_requests: list[dict] = []

    parsed_dob = _parse_dob(payload.date_of_birth)
    if not is_verified:
        if payload.name_bn is not None:
            user.name_bn = payload.name_bn
        if payload.name_en is not None:
            user.name_en = payload.name_en
        if payload.nid_number is not None:
            m.nid_number = payload.nid_number
        if payload.date_of_birth is not None:
            m.date_of_birth = parsed_dob
        if payload.circle_id is not None:
            m.circle_id = payload.circle_id
        if payload.membership_type:
            m.membership_type = payload.membership_type
    else:
        # Verified ACTIVE member: protected sensitive fields require administrative review
        sensitive_checks = [
            ('name_bn', user.name_bn, payload.name_bn),
            ('name_en', user.name_en, payload.name_en),
            ('nid_number', m.nid_number, payload.nid_number),
            (
                'date_of_birth',
                m.date_of_birth.strftime('%Y-%m-%d') if m.date_of_birth else None,
                parsed_dob.strftime('%Y-%m-%d') if parsed_dob else None,
            ),
            (
                'grid_circle',
                str(m.circle_id) if m.circle_id is not None else None,
                str(payload.circle_id) if payload.circle_id is not None else None,
            ),
        ]
        for f_name, cur_val, new_val in sensitive_checks:
            if new_val is not None and str(new_val).strip() != '' and str(new_val).strip() != str(cur_val or '').strip():
                existing_req = db.scalar(
                    select(MemberProfileChangeRequest).where(
                        MemberProfileChangeRequest.member_id == m.id,
                        MemberProfileChangeRequest.field_name == f_name,
                        MemberProfileChangeRequest.status == 'PENDING',
                    )
                )
                if existing_req:
                    existing_req.requested_value = str(new_val).strip()
                    req_obj = existing_req
                else:
                    req_obj = MemberProfileChangeRequest(
                        member_id=m.id,
                        user_id=user.id,
                        field_name=f_name,
                        current_value=str(cur_val) if cur_val is not None else None,
                        requested_value=str(new_val).strip(),
                        reason='Profile verification change request from Member Portal',
                        status='PENDING',
                    )
                    db.add(req_obj)
                    db.flush()
                created_change_requests.append({
                    'id': req_obj.id,
                    'field_name': f_name,
                    'requested_value': req_obj.requested_value,
                    'status': req_obj.status,
                })

    for field in [
        'designation_bn',
        'designation_en',
        'employee_id',
        'diploma_institution',
        'graduation_year',
        'current_address',
        'permanent_address',
    ]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(m, field, val)

    for meta_field in [
        'father_name',
        'mother_name',
        'gender',
        'blood_group',
        'organization',
        'department',
        'profession',
        'academic_qualification',
        'professional_qualification',
        'years_of_experience',
        'alternate_phone',
        'district',
        'emergency_contact_name',
        'emergency_contact_relationship',
        'emergency_contact_phone',
        'emergency_contact_address',
        'preferred_language',
        'profile_visibility',
    ]:
        val = getattr(payload, meta_field, None)
        if val is not None:
            setattr(meta, meta_field, val)

    if payload.directory_visibility is not None:
        meta.directory_visibility = bool(payload.directory_visibility)
    elif payload.directory_visible is not None:
        meta.directory_visibility = bool(payload.directory_visible)

    if payload.contact_visibility is not None:
        meta.contact_visibility = bool(payload.contact_visibility)
    elif payload.show_phone_in_directory is not None:
        meta.contact_visibility = bool(payload.show_phone_in_directory)

    actor_ip = request.client.host if request.client else None
    if email_changed:
        audit(db, user, 'EMAIL_CHANGED', 'USER', user.id, actor_ip)
    if phone_changed:
        audit(db, user, 'PHONE_CHANGED', 'USER', user.id, actor_ip)
    audit(db, user, 'PROFILE_UPDATED', 'MEMBER', m.id, actor_ip)
    audit(db, user, 'UPDATE_PROFILE', 'MEMBER', m.id, actor_ip)
    db.commit()
    exp = _compute_expiry_info(m)
    completion = _compute_profile_completion(user, m, meta)
    serialized = _serialize_full_profile(user, m, meta, exp, completion, created_change_requests)
    return {
        **serialized,
        'ok': True,
        'pending_change_requests': created_change_requests,
        'pending_verification_fields': [r['field_name'] for r in created_change_requests],
    }


@router.get('/change-requests')
@router.get('/profile/change-requests')
def list_profile_change_requests(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    rows = db.scalars(
        select(MemberProfileChangeRequest)
        .where(MemberProfileChangeRequest.member_id == m.id)
        .order_by(MemberProfileChangeRequest.created_at.desc())
        .limit(50)
    ).all()
    items = [
        {
            'id': r.id,
            'member_id': r.member_id,
            'field_name': r.field_name,
            'field_label_en': SENSITIVE_PROFILE_FIELDS.get(r.field_name, (r.field_name, r.field_name))[0],
            'field_label_bn': SENSITIVE_PROFILE_FIELDS.get(r.field_name, (r.field_name, r.field_name))[1],
            'current_value': r.current_value,
            'requested_value': r.requested_value,
            'reason': r.reason,
            'supporting_doc_url': r.supporting_doc_url,
            'supporting_document_id': r.supporting_document_id,
            'status': r.status,
            'reviewer_id': r.reviewer_id,
            'reviewed_by': r.reviewer_id,
            'reviewer_comment': r.review_note,
            'reviewer_note': r.review_note,
            'review_note': r.review_note,
            'created_at': r.created_at,
            'reviewed_at': r.reviewed_at,
        }
        for r in rows
    ]
    return {'items': items, 'change_requests': items, 'count': len(items)}


@router.post('/change-requests')
@router.post('/profile/change-requests')
def create_profile_change_request(
    payload: ProfileChangeRequestCreate,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    m = get_member(user, db)
    f_name = payload.field_name.strip().lower()
    if f_name not in SENSITIVE_PROFILE_FIELDS:
        raise HTTPException(
            400,
            f'Unsupported verification field "{f_name}". Supported fields: {", ".join(SENSITIVE_PROFILE_FIELDS.keys())}',
        )

    current_val_map = {
        'name_bn': user.name_bn,
        'name_en': user.name_en,
        'date_of_birth': m.date_of_birth.strftime('%Y-%m-%d') if m.date_of_birth else None,
        'dob': m.date_of_birth.strftime('%Y-%m-%d') if m.date_of_birth else None,
        'nid_number': m.nid_number,
        'membership_id': m.membership_id,
        'certificate_info': m.diploma_institution,
        'grid_circle': str(m.circle_id) if m.circle_id else None,
        'circle_id': str(m.circle_id) if m.circle_id else None,
        'membership_type': m.membership_type,
    }
    cur_val = current_val_map.get(f_name)

    existing_req = db.scalar(
        select(MemberProfileChangeRequest).where(
            MemberProfileChangeRequest.member_id == m.id,
            MemberProfileChangeRequest.field_name == f_name,
            MemberProfileChangeRequest.status == 'PENDING',
        )
    )
    if existing_req:
        existing_req.requested_value = payload.requested_value.strip()
        existing_req.reason = payload.reason
        if payload.supporting_doc_url:
            existing_req.supporting_doc_url = payload.supporting_doc_url
        if payload.supporting_document_id is not None:
            existing_req.supporting_document_id = payload.supporting_document_id
        req_obj = existing_req
    else:
        req_obj = MemberProfileChangeRequest(
            member_id=m.id,
            user_id=user.id,
            field_name=f_name,
            current_value=str(cur_val) if cur_val is not None else None,
            requested_value=payload.requested_value.strip(),
            reason=payload.reason or 'Requested via Member Portal',
            supporting_doc_url=payload.supporting_doc_url,
            supporting_document_id=payload.supporting_document_id,
            status='PENDING',
        )
        db.add(req_obj)
        db.flush()

    actor_ip = request.client.host if request.client else None
    audit(db, user, 'PROFILE_CHANGE_REQUESTED', 'MEMBER_PROFILE_CHANGE', req_obj.id, actor_ip)
    audit(db, user, 'REQUEST_PROFILE_CHANGE', 'MEMBER_PROFILE_CHANGE', req_obj.id, actor_ip)

    officers = db.scalars(
        select(User).where(
            User.role.in_(['MEMBERSHIP_OFFICER', 'MEMBERSHIP_ADMIN', 'CENTRAL_ADMIN', 'SUPER_ADMIN']),
            User.is_active == True,
        )
    ).all()
    field_lbl_bn = SENSITIVE_PROFILE_FIELDS[f_name][1]
    for officer in officers:
        notify(
            db,
            officer.id,
            'প্রোফাইল তথ্য সংশোধনের আবেদন',
            f'{user.name_bn} তার "{field_lbl_bn}" পরিবর্তনের জন্য যাচাইকরণের আবেদন করেছেন।',
            'MEMBERSHIP',
        )
    db.commit()
    db.refresh(req_obj)
    return {
        'ok': True,
        'id': req_obj.id,
        'field_name': req_obj.field_name,
        'field_label_en': SENSITIVE_PROFILE_FIELDS[f_name][0],
        'field_label_bn': SENSITIVE_PROFILE_FIELDS[f_name][1],
        'current_value': req_obj.current_value,
        'requested_value': req_obj.requested_value,
        'reason': req_obj.reason,
        'supporting_doc_url': req_obj.supporting_doc_url,
        'supporting_document_id': req_obj.supporting_document_id,
        'status': req_obj.status,
        'created_at': req_obj.created_at,
    }


@router.get('/change-requests/{request_id}')
@router.get('/profile/change-requests/{request_id}')
def get_profile_change_request(
    request_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    m = get_member(user, db)
    req_obj = db.get(MemberProfileChangeRequest, request_id)
    if not req_obj:
        raise HTTPException(404, 'Change request not found')
    if req_obj.member_id != m.id and user.role not in ('SUPER_ADMIN', 'CENTRAL_ADMIN', 'MEMBERSHIP_ADMIN', 'MEMBERSHIP_OFFICER'):
        raise HTTPException(403, 'Access denied: Cannot view change request belonging to another member')

    return {
        'id': req_obj.id,
        'member_id': req_obj.member_id,
        'field_name': req_obj.field_name,
        'field_label_en': SENSITIVE_PROFILE_FIELDS.get(req_obj.field_name, (req_obj.field_name, req_obj.field_name))[0],
        'field_label_bn': SENSITIVE_PROFILE_FIELDS.get(req_obj.field_name, (req_obj.field_name, req_obj.field_name))[1],
        'current_value': req_obj.current_value,
        'requested_value': req_obj.requested_value,
        'reason': req_obj.reason,
        'supporting_doc_url': req_obj.supporting_doc_url,
        'supporting_document_id': req_obj.supporting_document_id,
        'status': req_obj.status,
        'reviewer_id': req_obj.reviewer_id,
        'reviewed_by': req_obj.reviewer_id,
        'reviewer_comment': req_obj.review_note,
        'reviewer_note': req_obj.review_note,
        'review_note': req_obj.review_note,
        'created_at': req_obj.created_at,
        'reviewed_at': req_obj.reviewed_at,
    }


@router.delete('/change-requests/{request_id}')
@router.delete('/profile/change-requests/{request_id}')
def cancel_profile_change_request(
    request_id: int,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    m = get_member(user, db)
    req_obj = db.get(MemberProfileChangeRequest, request_id)
    if not req_obj:
        raise HTTPException(404, 'Change request not found')
    if req_obj.member_id != m.id:
        raise HTTPException(403, 'Access denied: Cannot cancel change request belonging to another member')
    if req_obj.status != 'PENDING':
        raise HTTPException(400, f'Cannot cancel request with status {req_obj.status}. Only PENDING requests can be cancelled.')

    req_obj.status = 'CANCELLED'
    actor_ip = request.client.host if request.client else None
    audit(db, user, 'PROFILE_CHANGE_CANCELLED', 'MEMBER_PROFILE_CHANGE', req_obj.id, actor_ip)
    db.commit()
    return {'ok': True, 'id': req_obj.id, 'status': 'CANCELLED', 'message': 'Change request cancelled successfully'}



@router.get('/application')
def get_unified_application_center(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 3: Unified Application Center API.
    Provides structured multi-step timeline (Submitted, Document Verification,
    Circle Review, Central Review, Payment, Activation), document requirements,
    and inline payment checkout triggers.
    """
    m = get_member(user, db)
    app_row = db.scalar(select(MembershipApplication).where(MembershipApplication.member_id == m.id))
    app_no = (
        app_row.application_no
        if app_row and app_row.application_no
        else (m.application_no or f'PGCB-APP-{m.created_at.year}-{m.id:05d}')
    )

    status_raw = (m.status or 'PENDING').upper()
    submitted_date = (app_row.created_at if app_row else m.created_at) or datetime.utcnow()

    docs = m.documents or []
    doc_type_status = {d.document_type.upper(): d.review_status.upper() for d in docs}
    has_rejected_docs = any(d.review_status.upper() == 'REJECTED' for d in docs)
    all_docs_approved = len(docs) >= 1 and all(d.review_status.upper() == 'APPROVED' for d in docs)

    # 6-step timeline calculation
    t1_status = 'COMPLETED'
    if has_rejected_docs or status_raw == 'DOCUMENTS_REQUIRED':
        t2_status = 'REQUIRED'
    elif all_docs_approved or status_raw in ('UNDER_REVIEW', 'PAYMENT_PENDING', 'ACTIVE'):
        t2_status = 'COMPLETED'
    else:
        t2_status = 'CURRENT'

    if status_raw in ('PAYMENT_PENDING', 'ACTIVE'):
        t3_status = 'COMPLETED'
    elif status_raw in ('UNDER_REVIEW', 'CIRCLE_REVIEW'):
        t3_status = 'CURRENT'
    elif t2_status == 'COMPLETED':
        t3_status = 'CURRENT'
    else:
        t3_status = 'UPCOMING'

    if status_raw in ('PAYMENT_PENDING', 'ACTIVE'):
        t4_status = 'COMPLETED'
    elif status_raw in ('CENTRAL_REVIEW',) or (status_raw == 'UNDER_REVIEW' and t3_status == 'COMPLETED'):
        t4_status = 'CURRENT'
    elif t3_status == 'COMPLETED':
        t4_status = 'CURRENT'
    else:
        t4_status = 'UPCOMING'

    has_paid_payment = bool(
        db.scalar(
            select(PaymentTransaction).where(
                PaymentTransaction.member_id == m.id,
                PaymentTransaction.status.in_(['PAID', 'SUCCESS', 'COMPLETED']),
            )
        )
    )
    if status_raw == 'ACTIVE' or has_paid_payment:
        t5_status = 'COMPLETED'
    elif status_raw in ('PAYMENT_PENDING', 'APPROVED'):
        t5_status = 'CURRENT'
    else:
        t5_status = 'UPCOMING'

    if status_raw == 'ACTIVE' and m.membership_id:
        t6_status = 'COMPLETED'
    elif status_raw == 'ACTIVE' or (t5_status == 'COMPLETED' and status_raw != 'REJECTED'):
        t6_status = 'CURRENT'
    else:
        t6_status = 'UPCOMING'

    timeline = [
        {
            'step_key': 'SUBMITTED',
            'title_bn': 'আবেদন জমা সম্পন্ন',
            'title_en': 'Application Submitted',
            'status': t1_status,
            'description': f'রেফারেন্স: {app_no}',
            'timestamp': submitted_date.strftime('%d %b %Y, %I:%M %p'),
            'actor_type': 'APPLICANT',
        },
        {
            'step_key': 'DOCUMENTS_VERIFIED',
            'title_bn': 'ডকুমেন্ট যাচাইকরণ',
            'title_en': 'Document Verification',
            'status': t2_status,
            'description': 'সহায়ক সনদ ও জাতীয় পরিচয়পত্র যাচাই' if t2_status != 'REQUIRED' else 'অতিরিক্ত বা স্পষ্ট ডকুমেন্ট সংযোজন আবশ্যক',
            'timestamp': (m.updated_at.strftime('%d %b %Y') if m.updated_at else None) if t2_status == 'COMPLETED' else None,
            'actor_type': 'VERIFICATION_OFFICER',
        },
        {
            'step_key': 'CIRCLE_REVIEW',
            'title_bn': 'গ্রিড সার্কেল পর্যালোচনা',
            'title_en': 'Circle Review',
            'status': t3_status,
            'description': f'সার্কেল: {m.circle.name_bn if m.circle else "PGCB"}',
            'timestamp': None,
            'actor_type': 'CIRCLE_ADMIN',
        },
        {
            'step_key': 'CENTRAL_REVIEW',
            'title_bn': 'কেন্দ্রীয় চূড়ান্ত অনুমোদন',
            'title_en': 'Central Review',
            'status': t4_status,
            'description': 'কেন্দ্রীয় কার্যনির্বাহী কমিটির আনুষ্ঠানিক পর্যালোচনা',
            'timestamp': None,
            'actor_type': 'CENTRAL_ADMIN',
        },
        {
            'step_key': 'PAYMENT',
            'title_bn': 'ফি পরিশোধ',
            'title_en': 'Fee Payment',
            'status': t5_status,
            'description': 'সদস্যপদ ফি বা নবায়ন ফি পরিশোধ' if t5_status != 'CURRENT' else 'ফি পরিশোধ আবশ্যক (পেমেন্ট করুন)',
            'timestamp': None,
            'actor_type': 'FINANCE',
        },
        {
            'step_key': 'ACTIVATION',
            'title_bn': 'সদস্যপদ সক্রিয়করণ',
            'title_en': 'Membership Activation',
            'status': t6_status,
            'description': f'মেম্বার আইডি: {m.membership_id or "প্রক্রিয়াধীন"}',
            'timestamp': (m.issue_date.strftime('%d %b %Y') if m.issue_date else None) if t6_status == 'COMPLETED' else None,
            'actor_type': 'SYSTEM',
        },
    ]

    required_docs = []
    if not doc_type_status.get('NID'):
        required_docs.append({'type': 'NID', 'label_bn': 'জাতীয় পরিচয়পত্র / পাসপোর্ট', 'reason': 'পরিচয় যাচাইকরণ'})
    if not doc_type_status.get('ACADEMIC') and not doc_type_status.get('DIPLOMA_CERTIFICATE'):
        required_docs.append({'type': 'ACADEMIC', 'label_bn': 'ডিপ্লোমা ইন ইঞ্জিনিয়ারিং সনদপত্র', 'reason': 'শিক্ষাগত যোগ্যতা যাচাই'})
    for d in docs:
        if d.review_status.upper() == 'REJECTED':
            required_docs.append({
                'type': d.document_type,
                'label_bn': d.document_type,
                'reason': d.reviewer_note or 'পূর্বের আপলোডকৃত ফাইলটি অস্পষ্ট বা অসম্পূর্ণ ছিল। অনুগ্রহ করে পুনরায় আপলোড করুন।',
            })

    pending_payment = None
    if status_raw in ('PAYMENT_PENDING', 'APPROVED') or t5_status == 'CURRENT':
        p_row = db.scalar(
            select(PaymentTransaction)
            .where(PaymentTransaction.member_id == m.id, PaymentTransaction.status == 'PENDING')
            .order_by(PaymentTransaction.created_at.desc())
        )
        if p_row:
            pending_payment = {
                'id': p_row.id,
                'transaction_ref': p_row.transaction_ref,
                'amount': float(p_row.amount),
                'amount_formatted': f'৳{int(p_row.amount):,}',
                'purpose': p_row.purpose,
                'checkout_url': f'/payments/checkout?transaction_id={p_row.transaction_ref}',
            }

    circle_dict = None
    if m.circle:
        circle_dict = {
            'id': m.circle.id,
            'name_bn': m.circle.name_bn,
            'name_en': m.circle.name_en,
        }

    return {
        'application_no': app_no,
        'membership_type': m.membership_type or 'PROFESSIONAL',
        'status': status_raw,
        'status_label_bn': {
            'SUBMITTED': 'জমা হয়েছে',
            'DOCUMENTS_REQUIRED': 'ডকুমেন্ট প্রয়োজন',
            'UNDER_REVIEW': 'পর্যালোচনাধীন',
            'PAYMENT_PENDING': 'পেমেন্ট অপেক্ষমাণ',
            'ACTIVE': 'অনুমোদিত ও সক্রিয়',
            'REJECTED': 'প্রত্যাখ্যাত',
        }.get(status_raw, status_raw),
        'status_label_en': status_raw.replace('_', ' ').title(),
        'circle': circle_dict,
        'submitted_at': submitted_date.strftime('%d %B %Y') if submitted_date else None,
        'reviewed_at': m.updated_at.strftime('%d %B %Y') if (m.updated_at and status_raw in ('ACTIVE', 'APPROVED')) else None,
        'timeline': timeline,
        'documents': [
            {
                'id': d.id,
                'document_type': d.document_type,
                'filename': d.filename,
                'review_status': d.review_status,
                'reviewer_note': d.reviewer_note,
                'download_url': f'/api/v1/member/documents/{d.id}/download',
            }
            for d in docs
        ],
        'required_document_types': required_docs,
        'pending_payment': pending_payment,
    }


@router.post('/application/documents')
async def upload_application_document(
    file: UploadFile = File(...),
    document_type: str = Form('ACADEMIC'),
    request: Request = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 3: Inline document upload for required/missing application documents.
    Validates magic bytes, restricts file size (5MB), and updates member status.
    """
    m = get_member(user, db)
    doc_type_clean = (document_type or 'ACADEMIC').strip().upper()

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, 'আপলোডকৃত ফাইলটি খালি (File is empty).')

    MAX_BYTES = 5 * 1024 * 1024
    if len(file_bytes) > MAX_BYTES:
        raise HTTPException(400, 'ফাইলের আকার সর্বোচ্চ ৫ মেগাবাইট (Maximum 5MB allowed).')

    is_pdf = file_bytes.startswith(b'%PDF-')
    is_jpeg = file_bytes.startswith(b'\xff\xd8\xff')
    is_png = file_bytes.startswith(b'\x89PNG\r\n\x1a\n')
    is_webp = len(file_bytes) >= 12 and file_bytes[:4] == b'RIFF' and file_bytes[8:12] == b'WEBP'

    if not (is_pdf or is_jpeg or is_png or is_webp):
        raise HTTPException(
            400,
            'শুধুমাত্র অনুমোদিত ফরম্যাট (PDF, JPEG, PNG, WEBP) আপলোড করা যাবে।',
        )

    ext = 'pdf' if is_pdf else ('png' if is_png else ('webp' if is_webp else 'jpg'))
    fname = f"doc_{m.id}_{doc_type_clean.lower()}_{uuid.uuid4().hex[:8]}.{ext}"
    target_dir = BASE_STORAGE / 'documents' / f'member_{m.id}'
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / fname

    with open(target_path, 'wb') as f:
        f.write(file_bytes)

    existing_doc = db.scalar(
        select(MemberDocument)
        .where(MemberDocument.member_id == m.id, MemberDocument.document_type == doc_type_clean)
    )
    if existing_doc:
        existing_doc.filename = file.filename or fname
        existing_doc.storage_path = str(target_path)
        existing_doc.content_type = file.content_type or 'application/octet-stream'
        existing_doc.review_status = 'PENDING'
        doc_obj = existing_doc
    else:
        doc_obj = MemberDocument(
            member_id=m.id,
            document_type=doc_type_clean,
            filename=file.filename or fname,
            storage_path=str(target_path),
            content_type=file.content_type or 'application/octet-stream',
            review_status='PENDING',
        )
        db.add(doc_obj)

    if m.status in ('DOCUMENTS_REQUIRED', 'PENDING'):
        m.status = 'UNDER_REVIEW'

    log_audit_action(
        db=db,
        request=request,
        action='DOCUMENT_SUBMITTED',
        entity='MEMBER_DOCUMENT',
        entity_id=str(doc_obj.id or doc_type_clean),
        user=user,
        new_value={'document_type': doc_type_clean, 'filename': doc_obj.filename},
    )

    db.commit()

    return {
        'ok': True,
        'message': f'{doc_type_clean} ডকুমেন্ট সফলভাবে আপলোড করা হয়েছে।',
        'document': {
            'id': doc_obj.id,
            'document_type': doc_obj.document_type,
            'filename': doc_obj.filename,
            'review_status': doc_obj.review_status,
        },
    }


@router.get('/application/timeline')
def get_member_application_timeline(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    return _build_application_timeline(db, m)


@router.post('/application/draft', response_model=ApplicationResponse)
def save_application_draft(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.models import MembershipApplication
    from app.services.membership_service import transition_application_status
    m = get_member(user, db)
    if m.status == 'ACTIVE':
        raise HTTPException(409, 'Membership is already active')
    transition_application_status(m, 'DRAFT')
    if not m.application_no:
        m.application_no = f'PGCB-APP-{datetime.utcnow().year}-{m.id:04d}'
    m.application_note = 'Application saved as draft.'
    app_row = db.scalar(select(MembershipApplication).where(MembershipApplication.member_id == m.id))
    if not app_row:
        db.add(
            MembershipApplication(
                member_id=m.id,
                application_no=m.application_no,
                membership_type=m.membership_type or 'GENERAL',
                circle_id=m.circle_id,
                status='DRAFT',
            )
        )
    else:
        app_row.status = 'DRAFT'
        app_row.circle_id = m.circle_id
    audit(db, user, 'SAVE_DRAFT_APPLICATION', 'MEMBER', m.id, request.client.host if request.client else None)
    db.commit(); db.refresh(m)
    return response(m)


@router.post('/application/cancel', response_model=ApplicationResponse)
def cancel_application(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.models import MembershipApplication
    from app.services.membership_service import transition_application_status
    m = get_member(user, db)
    if m.status == 'ACTIVE':
        raise HTTPException(409, 'Active membership cannot be cancelled via application endpoint')
    transition_application_status(m, 'CANCELLED')
    m.application_note = 'Application cancelled by applicant.'
    app_row = db.scalar(select(MembershipApplication).where(MembershipApplication.member_id == m.id))
    if app_row:
        app_row.status = 'CANCELLED'
    audit(db, user, 'CANCEL_APPLICATION', 'MEMBER', m.id, request.client.host if request.client else None)
    db.commit(); db.refresh(m)
    return response(m)


@router.post('/application', response_model=ApplicationResponse)
@router.post('/apply', response_model=ApplicationResponse)
def submit_application(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.models import MembershipApplication
    from app.services.membership_service import transition_application_status
    m = get_member(user, db)
    if m.status == 'ACTIVE':
        raise HTTPException(409, 'Membership is already active')
    transition_application_status(m, 'SUBMITTED')
    if not m.application_no:
        m.application_no = f'PGCB-APP-{datetime.utcnow().year}-{m.id:04d}'
    m.application_note = 'Application submitted by member.'
    app_row = db.scalar(select(MembershipApplication).where(MembershipApplication.member_id == m.id))
    if not app_row:
        db.add(
            MembershipApplication(
                member_id=m.id,
                application_no=m.application_no,
                membership_type=m.membership_type or 'GENERAL',
                circle_id=m.circle_id,
                status='SUBMITTED',
            )
        )
    else:
        app_row.status = 'SUBMITTED'
        app_row.circle_id = m.circle_id
    audit(db, user, 'SUBMIT_APPLICATION', 'MEMBER', m.id, request.client.host if request.client else None)
    officers = db.scalars(
        select(User).where(
            User.role.in_(['MEMBERSHIP_OFFICER', 'MEMBERSHIP_ADMIN', 'CIRCLE_ADMIN', 'CENTRAL_ADMIN', 'SUPER_ADMIN']),
            User.is_active == True,
        )
    ).all()
    for officer in officers:
        notify(db, officer.id, 'নতুন সদস্য আবেদন', f'{user.name_bn}-এর সদস্য আবেদন পর্যালোচনার জন্য জমা হয়েছে।', 'MEMBERSHIP')
    db.commit(); db.refresh(m)
    return response(m)


@router.get('/application', response_model=ApplicationResponse)
def get_application(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return response(get_member(user, db))


@router.post('/documents', response_model=MemberDocumentResponse)
def upload_document(request: Request, document_type: str, file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if document_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(400, 'Invalid document type')
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, 'Only PDF and image documents are accepted')
    member = get_member(user, db)
    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = file.file.read(max_bytes + 1)
    clean_name, unique_name, resolved_ct = validate_upload_bytes(
        file.filename,
        file.content_type,
        content,
        max_bytes,
    )
    try:
        stored = save_bytes(content, f'members/{member.id}', unique_name)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    doc = MemberDocument(
        member_id=member.id, document_type=document_type, filename=clean_name,
        storage_path=stored, content_type=resolved_ct, review_status='PENDING'
    )
    db.add(doc)
    if document_type == 'PHOTO':
        member.photo_url = stored
    audit(db, user, 'UPLOAD_DOCUMENT', 'MEMBER_DOCUMENT', member.id, request.client.host if request.client else None)
    db.commit(); db.refresh(doc)
    return MemberDocumentResponse(
        id=doc.id,
        document_type=doc.document_type,
        filename=doc.filename,
        review_status=doc.review_status,
        reviewer_note=getattr(doc, 'reviewer_note', None),
        created_at=doc.created_at,
    )


@router.get('/documents', response_model=list[MemberDocumentResponse])
def list_documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    return [
        MemberDocumentResponse(
            id=d.id,
            document_type=d.document_type,
            filename=d.filename,
            review_status=d.review_status,
            reviewer_note=getattr(d, 'reviewer_note', None),
            created_at=d.created_at,
        )
        for d in m.documents
    ]


@router.get('/documents/{document_id}/download')
def download_document(document_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    doc = db.scalar(select(MemberDocument).where(MemberDocument.id == document_id, MemberDocument.member_id == m.id))
    if not doc or not doc.storage_path:
        raise HTTPException(404, 'Document not available')
    try:
        content = get_file_bytes(doc.storage_path)
        return Response(
            content=content,
            media_type=doc.content_type or 'application/octet-stream',
            headers={'Content-Disposition': f'attachment; filename="{doc.filename}"'},
        )
    except FileNotFoundError:
        raise HTTPException(404, 'Document not found')
    except ValueError:
        raise HTTPException(400, 'Invalid document path')
    except Exception as exc:
        raise HTTPException(502, f'Failed to retrieve document: {exc}')


@router.get('/notifications')
def notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(30)
    ).all()
    return [
        {
            'id': n.id,
            'title_bn': n.title_bn,
            'body_bn': n.body_bn,
            'type': n.notification_type,
            'read_at': n.read_at,
            'is_read': bool(n.read_at),
            'indicator': '○' if n.read_at else '●',
            'created_at': n.created_at,
            'relative_time': _relative_time(n.created_at, now)[0],
            'relative_time_en': _relative_time(n.created_at, now)[0],
            'relative_time_bn': _relative_time(n.created_at, now)[1],
        }
        for n in rows
    ]


@router.get('/notifications/unread-count')
def notifications_unread_count(user: User = Depends(current_user), db: Session = Depends(get_db)):
    count = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.read_at.is_(None))) or 0
    return {'unread_count': count}


@router.post('/notifications/{notification_id}/read')
def mark_notification_read(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    n = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if not n:
        raise HTTPException(404, 'Notification not found')
    n.read_at = datetime.utcnow(); db.commit()
    return {'ok': True}


@router.post('/notifications/read-all')
def mark_all_notifications_read(user: User = Depends(current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    unread = db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))).all()
    for n in unread:
        n.read_at = now
    db.commit()
    return {'ok': True, 'updated': len(unread)}


@router.get('/notification-preferences')
def get_notification_preferences(user: User = Depends(current_user), db: Session = Depends(get_db)):
    import json
    from app.models import SiteSetting
    defaults = {'email_enabled': True, 'sms_enabled': True, 'in_app_enabled': True}
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == f'notification_prefs_user_{user.id}'))
    if row and row.value:
        try:
            defaults.update(json.loads(row.value))
        except Exception:
            pass
    return defaults


@router.put('/notification-preferences')
def update_notification_preferences(payload: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    import json
    from app.models import SiteSetting
    prefs = {
        'email_enabled': bool(payload.get('email_enabled', True)),
        'sms_enabled': bool(payload.get('sms_enabled', True)),
        'in_app_enabled': bool(payload.get('in_app_enabled', True)),
    }
    key = f'notification_prefs_user_{user.id}'
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == key))
    if row:
        row.value = json.dumps(prefs)
    else:
        db.add(SiteSetting(key=key, value=json.dumps(prefs), category='NOTIFICATION_PREFS'))
    db.commit()
    return {'ok': True, **prefs}


@router.get('/certificates')
def list_member_certificates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.services.certificate_service import CertificateService
    m = get_member(user, db)
    return CertificateService.ensure_member_wallet_certificates(db, user, m)


@router.get('/updates')
def list_member_updates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Return circulars and notices inside the Member Portal with bookmark and read state."""
    saved_rows = db.scalars(
        select(MemberSavedContent).where(MemberSavedContent.user_id == user.id)
    ).all()
    saved_map = {(s.entity_type.upper(), s.entity_id): s for s in saved_rows}

    circulars = db.scalars(
        select(Circular).where(Circular.is_published == True).order_by(Circular.created_at.desc()).limit(25)
    ).all()
    notices = db.scalars(
        select(Notice).where(Notice.is_published == True).order_by(Notice.created_at.desc()).limit(25)
    ).all()

    items: list[dict] = []
    for cir in circulars:
        st = saved_map.get(('CIRCULAR', cir.id))
        items.append({
            'id': cir.id,
            'content_type': 'CIRCULAR',
            'slug': getattr(cir, 'slug', str(cir.id)),
            'title_bn': cir.title_bn,
            'title_en': cir.title_en,
            'summary_bn': cir.summary_bn,
            'category': cir.category or 'GENERAL',
            'reference_no': cir.reference_no,
            'attachment_url': getattr(cir, 'attachment_url', None) or cir.document_url,
            'published_at': cir.published_at or cir.created_at,
            'is_bookmarked': bool(st and st.is_bookmarked),
            'is_read': bool(st and st.is_read),
        })
    for ntc in notices:
        st = saved_map.get(('NOTICE', ntc.id))
        items.append({
            'id': ntc.id,
            'content_type': 'NOTICE',
            'slug': getattr(ntc, 'slug', str(ntc.id)),
            'title_bn': ntc.title_bn,
            'title_en': ntc.title_en,
            'summary_bn': getattr(ntc, 'summary_bn', None) or ntc.content_bn,
            'category': ntc.category or 'NOTICE',
            'reference_no': None,
            'attachment_url': ntc.attachment_url,
            'published_at': ntc.published_at or ntc.created_at,
            'is_bookmarked': bool(st and st.is_bookmarked),
            'is_read': bool(st and st.is_read),
        })
    return {'items': items, 'count': len(items)}


@router.post('/updates/bookmark')
def toggle_member_update_bookmark(payload: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    entity_type = str(payload.get('content_type') or payload.get('entity_type') or 'CIRCULAR').strip().upper()
    entity_id = int(payload.get('content_id') or payload.get('entity_id') or 0)
    if entity_type not in ('CIRCULAR', 'NOTICE', 'EVENT') or entity_id <= 0:
        raise HTTPException(400, 'Invalid content_type or content_id')
    row = db.scalar(
        select(MemberSavedContent).where(
            MemberSavedContent.user_id == user.id,
            MemberSavedContent.entity_type == entity_type,
            MemberSavedContent.entity_id == entity_id,
        )
    )
    if not row:
        row = MemberSavedContent(
            user_id=user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            is_bookmarked=bool(payload.get('is_bookmarked', True)),
            is_read=True,
        )
        db.add(row)
    else:
        if 'is_bookmarked' in payload and payload['is_bookmarked'] is not None:
            row.is_bookmarked = bool(payload['is_bookmarked'])
        else:
            row.is_bookmarked = not bool(row.is_bookmarked)
    db.commit()
    return {'ok': True, 'entity_type': entity_type, 'entity_id': entity_id, 'is_bookmarked': bool(row.is_bookmarked)}


@router.post('/updates/read')
def mark_member_update_read(payload: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    entity_type = str(payload.get('content_type') or payload.get('entity_type') or 'CIRCULAR').strip().upper()
    entity_id = int(payload.get('content_id') or payload.get('entity_id') or 0)
    if entity_type not in ('CIRCULAR', 'NOTICE', 'EVENT') or entity_id <= 0:
        raise HTTPException(400, 'Invalid content_type or content_id')
    row = db.scalar(
        select(MemberSavedContent).where(
            MemberSavedContent.user_id == user.id,
            MemberSavedContent.entity_type == entity_type,
            MemberSavedContent.entity_id == entity_id,
        )
    )
    if not row:
        row = MemberSavedContent(
            user_id=user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            is_bookmarked=False,
            is_read=True,
        )
        db.add(row)
    else:
        row.is_read = True
    db.commit()
    return {'ok': True, 'entity_type': entity_type, 'entity_id': entity_id, 'is_read': True}


@router.get('/settings')
def get_member_settings(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    meta = _get_or_create_profile_meta(db, m.id)
    notif_prefs = get_notification_preferences(user, db)
    db.commit()
    return {
        'preferred_language': meta.preferred_language or 'bn',
        'profile_visibility': meta.profile_visibility or 'MEMBERS_ONLY',
        'directory_visibility': bool(meta.directory_visibility),
        'contact_visibility': bool(meta.contact_visibility),
        'privacy': {
            'directory_visible': bool(meta.directory_visibility),
            'show_phone': bool(meta.contact_visibility),
            'show_email': bool(meta.contact_visibility),
            'profile_visibility': meta.profile_visibility or 'MEMBERS_ONLY',
        },
        'notification_preferences': notif_prefs,
        'two_factor_enabled': bool(getattr(user, 'two_factor_enabled', False)),
    }


@router.put('/settings')
@router.patch('/settings')
def update_member_settings(payload: dict, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    meta = _get_or_create_profile_meta(db, m.id)
    if 'preferred_language' in payload and payload['preferred_language'] in ('bn', 'en'):
        meta.preferred_language = payload['preferred_language']
    if 'profile_visibility' in payload and payload['profile_visibility'] in ('PUBLIC', 'MEMBERS_ONLY', 'PRIVATE'):
        meta.profile_visibility = payload['profile_visibility']
    if 'directory_visibility' in payload:
        meta.directory_visibility = bool(payload['directory_visibility'])
    elif 'privacy_directory_visible' in payload:
        meta.directory_visibility = bool(payload['privacy_directory_visible'])
    if 'contact_visibility' in payload:
        meta.contact_visibility = bool(payload['contact_visibility'])
    elif 'privacy_show_phone' in payload:
        meta.contact_visibility = bool(payload['privacy_show_phone'])
    elif 'privacy_show_email' in payload:
        meta.contact_visibility = bool(payload['privacy_show_email'])
    if any(k in payload for k in ('email_enabled', 'sms_enabled', 'in_app_enabled')):
        update_notification_preferences(payload, user, db)
    audit(db, user, 'UPDATE_MEMBER_SETTINGS', 'MEMBER', m.id, request.client.host if request.client else None)
    db.commit()
    return get_member_settings(user, db)


@router.get('/login-history')
def get_member_login_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    sessions = db.scalars(
        select(UserSession)
        .where(UserSession.user_id == user.id)
        .order_by(UserSession.created_at.desc())
        .limit(10)
    ).all()
    logs = db.scalars(
        select(AuditLog)
        .where(AuditLog.user_id == user.id, AuditLog.action.in_(['LOGIN', 'UPDATE_PROFILE', 'CHANGE_PASSWORD', 'INITIATE_RENEWAL']))
        .order_by(AuditLog.created_at.desc())
        .limit(15)
    ).all()
    sessions_list = [
        {
            'id': s.id,
            'ip_address': getattr(s, 'ip_address', None) or '127.0.0.1',
            'user_agent': getattr(s, 'user_agent', None) or 'Web Browser',
            'created_at': s.created_at,
            'expires_at': s.expires_at,
            'is_active': s.revoked_at is None and (s.expires_at is None or s.expires_at > datetime.utcnow()),
        }
        for s in sessions
    ]
    events_list = [
        {
            'id': lg.id,
            'action': lg.action,
            'entity_type': lg.entity,
            'ip_address': lg.ip_address or '127.0.0.1',
            'created_at': lg.created_at,
        }
        for lg in logs
    ]
    return {
        'items': events_list,
        'sessions': sessions_list,
        'security_events': events_list,
    }





