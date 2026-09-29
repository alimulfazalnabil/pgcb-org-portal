"""
Institutional Membership Domain Service for PGCB Organization Portal.
Handles membership applications, state machine transitions, ID assignment, and notifications.
"""

from datetime import datetime, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Member, User, Notification
from app.services import audit, notify, next_membership_id, membership_dates
from app.services.email import EmailService

APPLICATION_STATES: tuple[str, ...] = (
    'DRAFT',
    'SUBMITTED',
    'UNDER_REVIEW',
    'CORRECTION_REQUIRED',
    'APPROVED',
    'PAYMENT_PENDING',
    'ACTIVE',
    'REJECTED',
    'CANCELLED',
)

VALID_APPLICATION_TRANSITIONS: dict[str, set[str]] = {
    'DRAFT': {'DRAFT', 'SUBMITTED', 'PENDING', 'CANCELLED'},
    'PENDING': {
        'SUBMITTED',
        'UNDER_REVIEW',
        'CORRECTION_REQUIRED',
        'DOCUMENTS_REQUIRED',
        'APPROVED',
        'PAYMENT_PENDING',
        'ACTIVE',
        'REJECTED',
        'CANCELLED',
    },
    'SUBMITTED': {
        'SUBMITTED',
        'UNDER_REVIEW',
        'CORRECTION_REQUIRED',
        'DOCUMENTS_REQUIRED',
        'APPROVED',
        'PAYMENT_PENDING',
        'ACTIVE',
        'REJECTED',
        'CANCELLED',
    },
    'UNDER_REVIEW': {
        'UNDER_REVIEW',
        'CORRECTION_REQUIRED',
        'DOCUMENTS_REQUIRED',
        'APPROVED',
        'PAYMENT_PENDING',
        'ACTIVE',
        'REJECTED',
        'CANCELLED',
    },
    'CORRECTION_REQUIRED': {
        'CORRECTION_REQUIRED',
        'DOCUMENTS_REQUIRED',
        'SUBMITTED',
        'UNDER_REVIEW',
        'APPROVED',
        'PAYMENT_PENDING',
        'ACTIVE',
        'REJECTED',
        'CANCELLED',
    },
    'DOCUMENTS_REQUIRED': {
        'CORRECTION_REQUIRED',
        'DOCUMENTS_REQUIRED',
        'SUBMITTED',
        'UNDER_REVIEW',
        'APPROVED',
        'PAYMENT_PENDING',
        'ACTIVE',
        'REJECTED',
        'CANCELLED',
    },
    'APPROVED': {'APPROVED', 'PAYMENT_PENDING', 'ACTIVE', 'REJECTED', 'CANCELLED'},
    'PAYMENT_PENDING': {'PAYMENT_PENDING', 'ACTIVE', 'REJECTED', 'CANCELLED'},
    'ACTIVE': {'ACTIVE', 'SUSPENDED', 'EXPIRED', 'REVOKED'},
    'SUSPENDED': {'SUSPENDED', 'ACTIVE', 'REVOKED'},
    'REJECTED': {'REJECTED', 'SUBMITTED', 'UNDER_REVIEW'},
    'CANCELLED': {'CANCELLED', 'DRAFT', 'SUBMITTED'},
}


def validate_application_transition(current_status: str | None, next_status: str) -> bool:
    cur = (current_status or 'DRAFT').strip().upper()
    nxt = (next_status or '').strip().upper()
    allowed = VALID_APPLICATION_TRANSITIONS.get(cur)
    if allowed is None:
        return False
    return nxt in allowed


def transition_application_status(member: Member, next_status: str) -> str:
    cur = (member.status or 'DRAFT').strip().upper()
    nxt = next_status.strip().upper()
    if not validate_application_transition(cur, nxt):
        raise ValueError(f'Illegal application state transition: {cur} -> {nxt}')
    member.status = nxt
    return nxt


class MembershipService:
    @staticmethod
    def submit_application(
        db: Session,
        user: User,
        data: dict,
        ip: str | None = None,
    ) -> Member:
        member = db.scalar(select(Member).where(Member.user_id == user.id))
        if not member:
            member = Member(user_id=user.id)
            db.add(member)
            db.flush()

        if data.get('name_bn'):
            user.name_bn = data['name_bn']
        if data.get('name_en'):
            user.name_en = data['name_en']
        if data.get('phone'):
            user.phone = data['phone']

        member.employee_id = data.get('employee_id', member.employee_id)
        member.designation_bn = data.get('designation_bn', member.designation_bn)
        member.designation_en = data.get('designation_en', member.designation_en)
        member.circle_id = data.get('circle_id', member.circle_id)
        member.diploma_institution = data.get('diploma_institution', member.diploma_institution)
        member.graduation_year = data.get('graduation_year', member.graduation_year)
        member.nid_number = data.get('nid_number', member.nid_number)
        member.membership_type = data.get('membership_type', member.membership_type or 'REGULAR')

        if not member.application_no:
            year = datetime.utcnow().year
            member.application_no = f"PGCB-APP-{year}-{member.id:05d}"

        member.status = 'SUBMITTED'
        member.created_at = member.created_at or datetime.utcnow()

        audit(db, user, 'SUBMIT_MEMBERSHIP_APPLICATION', 'MEMBER', member.id, ip)
        notify(
            db,
            user.id,
            'আবেদন সফলভাবে জমা হয়েছে',
            f'আপনার সদস্যপদ আবেদন নং {member.application_no} পর্যালোচনার জন্য জমা দেওয়া হয়েছে।',
            'MEMBERSHIP',
        )

        EmailService.send_application_received(
            to_email=user.email,
            applicant_name=user.name_bn or user.name_en or 'প্রকৌশলী',
            application_no=member.application_no,
        )

        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def review_application(
        db: Session,
        admin_user: User,
        member_id: int,
        action: str,
        note: str | None = None,
        ip: str | None = None,
    ) -> Member:
        member = db.get(Member, member_id)
        if not member:
            raise HTTPException(404, 'Member not found')

        action = action.upper()
        user = db.get(User, member.user_id) if member.user_id else None

        if action == 'APPROVE':
            member.status = 'ACTIVE'
            if not member.membership_id:
                member.membership_id = next_membership_id(db)
            issue, validity = membership_dates()
            member.issue_date = member.issue_date or issue
            member.validity_date = validity

            audit(db, admin_user, 'APPROVE_MEMBER', 'MEMBER', member.id, ip)
            if user:
                notify(
                    db,
                    user.id,
                    'সদস্যপদ অনুমোদিত হয়েছে',
                    f'অভিনন্দন! আপনার সদস্যপদ অনুমোদন করা হয়েছে। সদস্য আইডি: {member.membership_id}',
                    'MEMBERSHIP',
                )
                EmailService.send_application_approved(
                    to_email=user.email,
                    applicant_name=user.name_bn or user.name_en or 'প্রকৌশলী',
                    membership_id=member.membership_id,
                )

        elif action == 'REJECT':
            member.status = 'REJECTED'
            audit(db, admin_user, 'REJECT_MEMBER', 'MEMBER', member.id, ip)
            if user:
                notify(
                    db,
                    user.id,
                    'সদস্যপদ আবেদন প্রত্যাখ্যাত',
                    note or 'আপনার সদস্যপদ আবেদনটি পর্যালোচনার পর অনুমোদন করা সম্ভব হয়নি।',
                    'MEMBERSHIP',
                )
                EmailService.send_application_rejected(
                    to_email=user.email,
                    applicant_name=user.name_bn or user.name_en or 'প্রকৌশলী',
                    reason=note or 'নথিপত্র অসম্পূর্ণ বা যাচাইকরণে অসঙ্গতি পাওয়া গেছে।',
                )

        elif action in ('REVIEW', 'UNDER_REVIEW'):
            member.status = 'UNDER_REVIEW'
            audit(db, admin_user, 'MOVE_TO_REVIEW_MEMBER', 'MEMBER', member.id, ip)
            if user:
                notify(
                    db,
                    user.id,
                    'আবেদন পর্যালোচনাধীন রয়েছে',
                    'আপনার আবেদনটি সচিবালয় কর্তৃক পর্যালোচনা করা হচ্ছে।',
                    'MEMBERSHIP',
                )

        elif action in ('CORRECTION_REQUIRED', 'REQUEST_CORRECTION', 'DOCUMENTS_REQUIRED'):
            member.status = 'CORRECTION_REQUIRED' if action == 'CORRECTION_REQUIRED' else 'DOCUMENTS_REQUIRED'
            audit(db, admin_user, 'REQUEST_CORRECTION_MEMBER', 'MEMBER', member.id, ip)
            if user:
                notify(
                    db,
                    user.id,
                    'সদস্যপদ আবেদনে সংশোধন প্রয়োজন',
                    note or 'আপনার সদস্যপদ আবেদনের তথ্য/নথিপত্র সংশোধন করে পুনরায় জমা দিন।',
                    'MEMBERSHIP',
                )

        elif action in ('PAYMENT_PENDING', 'APPROVE_FOR_PAYMENT'):
            member.status = 'PAYMENT_PENDING'
            audit(db, admin_user, 'APPROVE_PAYMENT_PENDING_MEMBER', 'MEMBER', member.id, ip)
            if user:
                notify(
                    db,
                    user.id,
                    'সদস্যপদ আবেদন অনুমোদিত — ফি পরিশোধ করুন',
                    note or 'আপনার সদস্যপদ আবেদন অনুমোদিত হয়েছে। সদস্যপদ সক্রিয় করতে নির্ধারিত ফি পরিশোধ করুন।',
                    'MEMBERSHIP',
                )

        elif action in ('CANCEL', 'CANCELLED'):
            member.status = 'CANCELLED'
            audit(db, admin_user, 'CANCEL_MEMBER_APPLICATION', 'MEMBER', member.id, ip)

        elif action == 'SUSPEND':
            member.status = 'SUSPENDED'
            audit(db, admin_user, 'SUSPEND_MEMBER', 'MEMBER', member.id, ip)
            if user:
                notify(
                    db,
                    user.id,
                    'সদস্যপদ স্থগিত করা হয়েছে',
                    'আপনার সদস্যপদ সাময়িকভাবে স্থগিত করা হয়েছে। সচিবালয়ের সাথে যোগাযোগ করুন।',
                    'MEMBERSHIP',
                )

        elif action in ('REACTIVATE', 'ACTIVATE'):
            member.status = 'ACTIVE'
            audit(db, admin_user, 'REACTIVATE_MEMBER', 'MEMBER', member.id, ip)
            if user:
                notify(
                    db,
                    user.id,
                    'সদস্যপদ পুনরায় সক্রিয়',
                    'আপনার সদস্যপদ পুনরায় সক্রিয় করা হয়েছে।',
                    'MEMBERSHIP',
                )

        else:
            raise HTTPException(400, f'Invalid review action: {action}')

        db.commit()
        db.refresh(member)
        return member
