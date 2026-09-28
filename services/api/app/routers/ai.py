from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit_log
from app.core.deps import current_user, get_current_user
from app.core.rbac import has_permission, is_circle_scoped_admin, normalize_role, require_permission
from app.db.session import get_db
from app.models import (
    AIQueryLog,
    Certificate,
    Circle,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeFAQ,
    Member,
    MembershipApplication,
    MembershipRenewal,
    PaymentTransaction,
    User,
)
from app.services.knowledge_service import (
    can_user_access_document,
    ensure_default_knowledge_seeded,
    extract_text_from_file_bytes,
    ingest_knowledge_document,
    search_knowledge_base,
)

router = APIRouter(tags=['ai-intelligence'])

PROMPT_INJECTION_PATTERNS = [
    r'ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions',
    r'disregard\s+(?:all\s+)?(?:previous|system)\s+instructions',
    r'reveal\s+(?:your\s+)?system\s+prompt',
    r'drop\s+table\s+',
    r'delete\s+from\s+users',
    r'select\s+\*\s+from\s+users',
    r'union\s+select\s+',
    r'password_hash',
    r'jwt_secret',
    r'bypass\s+rbac',
    r'dump\s+(?:all\s+)?(?:nid|passwords|database)',
]


def _detect_prompt_injection(question: str) -> bool:
    q_low = question.lower()
    for pat in PROMPT_INJECTION_PATTERNS:
        if re.search(pat, q_low):
            return True
    return False


def _sanitize_pii(text: str) -> str:
    # Mask accidental 10/13/17 digit NID numbers or raw hashes if any appear in text
    return re.sub(r'\b\d{13,17}\b', '[REDACTED-NID]', text)


async def _optional_user(request: Request, db: Session) -> User | None:
    try:
        return await current_user(request, db, bearer_token=None)
    except Exception:
        return None


class KnowledgeDocCreateRequest(BaseModel):
    title_bn: str = Field(min_length=2, max_length=500)
    title_en: str | None = None
    category: str = 'MEMBERSHIP_GUIDELINES'
    version: str = '2026.1'
    raw_text: str = ''
    sections: list[dict[str, Any]] | None = None
    source_type: str = 'PDF'
    source_url: str | None = None
    access_level: str = 'PUBLIC'
    circle_id: int | None = None
    author: str = 'PGCB Secretariat'
    approval_status: str = 'PUBLISHED'
    is_current: bool = True
    supersedes_id: int | None = None
    publication_date: str | None = None
    effective_date: str | None = None


class SupersedeDocRequest(BaseModel):
    new_document_id: int


class AIAskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1500)
    mode: str = Field(default='PUBLIC')  # PUBLIC, MEMBER, ADMIN
    language: str = Field(default='en')
    circle_id: int | None = None
    include_historical: bool = False


class GenerateFAQRequest(BaseModel):
    document_id: int
    max_faqs: int = Field(default=5, ge=1, le=20)


class FAQUpdateRequest(BaseModel):
    question_bn: str | None = None
    question_en: str | None = None
    answer_bn: str | None = None
    answer_en: str | None = None
    status: str | None = None  # DRAFT, REVIEW, APPROVED, PUBLISHED, ARCHIVED


class ContentAssistRequest(BaseModel):
    title_bn: str = ''
    title_en: str | None = None
    content_bn: str = ''
    content_en: str | None = None
    entity_type: str = 'NOTICE'
    actions: list[str] = Field(
        default_factory=lambda: [
            'IMPROVE_WORDING',
            'TRANSLATE_BN_EN',
            'GENERATE_SUMMARY',
            'GENERATE_SEO',
            'GENERATE_NOTIFICATION',
        ]
    )


def _serialize_knowledge_doc(doc: KnowledgeDocument) -> dict[str, Any]:
    return {
        'id': doc.id,
        'title_bn': doc.title_bn,
        'title_en': doc.title_en,
        'category': doc.category,
        'version': doc.version,
        'is_current': doc.is_current,
        'supersedes_id': doc.supersedes_id,
        'superseded_by_id': doc.superseded_by_id,
        'publication_date': doc.publication_date.isoformat() if doc.publication_date else None,
        'effective_date': doc.effective_date.isoformat() if doc.effective_date else None,
        'author': doc.author,
        'approval_status': doc.approval_status,
        'source_type': doc.source_type,
        'source_url': doc.source_url,
        'access_level': doc.access_level,
        'circle_id': doc.circle_id,
        'chunk_count': doc.chunk_count,
        'created_at': doc.created_at.isoformat() if doc.created_at else None,
    }


@router.post('/admin/knowledge/documents')
def create_knowledge_document(
    payload: KnowledgeDocCreateRequest,
    user: User = Depends(require_permission('cms.write')),
    db: Session = Depends(get_db),
):
    pub_dt = None
    eff_dt = None
    if payload.publication_date:
        try:
            pub_dt = datetime.fromisoformat(payload.publication_date)
        except ValueError:
            pub_dt = datetime.utcnow()
    if payload.effective_date:
        try:
            eff_dt = datetime.fromisoformat(payload.effective_date)
        except ValueError:
            eff_dt = pub_dt

    doc = ingest_knowledge_document(
        db,
        title_bn=payload.title_bn,
        title_en=payload.title_en,
        category=payload.category,
        version=payload.version,
        raw_text=payload.raw_text,
        sections=payload.sections,
        source_type=payload.source_type,
        source_url=payload.source_url,
        access_level=payload.access_level,
        circle_id=payload.circle_id,
        author=payload.author,
        approval_status=payload.approval_status,
        is_current=payload.is_current,
        supersedes_id=payload.supersedes_id,
        publication_date=pub_dt,
        effective_date=eff_dt,
        created_by=user.id,
    )
    write_audit_log(
        db,
        actor_user_id=user.id,
        action='knowledge.document.ingest',
        entity_type='KnowledgeDocument',
        entity_id=str(doc.id),
        metadata={'title': doc.title_en or doc.title_bn, 'version': doc.version, 'access_level': doc.access_level},
    )
    db.commit()
    return _serialize_knowledge_doc(doc)


@router.post('/admin/knowledge/ingest-file')
async def ingest_knowledge_file(
    file: UploadFile = File(...),
    title_bn: str = Form(...),
    title_en: str = Form(''),
    category: str = Form('MEMBERSHIP_GUIDELINES'),
    version: str = Form('2026.1'),
    access_level: str = Form('PUBLIC'),
    circle_id: int | None = Form(None),
    supersedes_id: int | None = Form(None),
    user: User = Depends(require_permission('cms.write')),
    db: Session = Depends(get_db),
):
    raw_bytes = await file.read()
    fname = file.filename or 'document.pdf'
    ext = fname.rsplit('.', 1)[-1].upper() if '.' in fname else 'PDF'
    extracted_text = extract_text_from_file_bytes(raw_bytes, fname)

    doc = ingest_knowledge_document(
        db,
        title_bn=title_bn,
        title_en=title_en or title_bn,
        category=category,
        version=version,
        raw_text=extracted_text,
        source_type=ext if ext in ('PDF', 'DOCX', 'TXT', 'MD') else 'PDF',
        access_level=access_level,
        circle_id=circle_id,
        supersedes_id=supersedes_id,
        created_by=user.id,
    )
    write_audit_log(
        db,
        actor_user_id=user.id,
        action='knowledge.file.ingest',
        entity_type='KnowledgeDocument',
        entity_id=str(doc.id),
        metadata={'filename': fname, 'chunks': doc.chunk_count},
    )
    db.commit()
    return _serialize_knowledge_doc(doc)


@router.get('/admin/knowledge/documents')
def list_knowledge_documents(
    category: str | None = None,
    include_historical: bool = True,
    user: User = Depends(require_permission('cms.read')),
    db: Session = Depends(get_db),
):
    ensure_default_knowledge_seeded(db)
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.id.desc())
    if category:
        stmt = stmt.where(KnowledgeDocument.category == category.upper())
    if not include_historical:
        stmt = stmt.where(KnowledgeDocument.is_current == True)
    docs = db.scalars(stmt).all()
    return [_serialize_knowledge_doc(d) for d in docs if can_user_access_document(user, d)]


@router.post('/admin/knowledge/documents/{doc_id}/supersede')
def supersede_knowledge_document(
    doc_id: int,
    payload: SupersedeDocRequest,
    user: User = Depends(require_permission('cms.write')),
    db: Session = Depends(get_db),
):
    old_doc = db.get(KnowledgeDocument, doc_id)
    new_doc = db.get(KnowledgeDocument, payload.new_document_id)
    if not old_doc or not new_doc:
        raise HTTPException(status_code=404, detail='Knowledge document not found')

    old_doc.is_current = False
    old_doc.approval_status = 'SUPERSEDED'
    old_doc.superseded_by_id = new_doc.id
    new_doc.supersedes_id = old_doc.id
    new_doc.is_current = True
    new_doc.approval_status = 'PUBLISHED'
    write_audit_log(
        db,
        actor_user_id=user.id,
        action='knowledge.document.supersede',
        entity_type='KnowledgeDocument',
        entity_id=str(old_doc.id),
        metadata={'superseded_by_id': new_doc.id},
    )
    db.commit()
    return {
        'ok': True,
        'superseded_document': _serialize_knowledge_doc(old_doc),
        'current_document': _serialize_knowledge_doc(new_doc),
    }


@router.get('/knowledge/documents/{doc_id}/source')
async def get_knowledge_document_source(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    ensure_default_knowledge_seeded(db)
    doc = db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Knowledge document not found')

    user = await _optional_user(request, db)
    if not can_user_access_document(user, doc):
        if user is None:
            raise HTTPException(status_code=401, detail='Authentication required to view this document source')
        raise HTTPException(status_code=403, detail='Insufficient permissions to view this document source')

    chunks = db.scalars(
        select(KnowledgeChunk)
        .where(KnowledgeChunk.document_id == doc.id)
        .order_by(KnowledgeChunk.chunk_index.asc())
    ).all()

    return {
        **_serialize_knowledge_doc(doc),
        'sections': [
            {
                'chunk_id': c.id,
                'section': c.section_title,
                'page': c.page_number,
                'content': _sanitize_pii(c.content),
            }
            for c in chunks
        ],
    }


@router.get('/knowledge/search')
@router.get('/public/knowledge/search')
async def semantic_document_search(
    request: Request,
    q: str = Query(..., min_length=1),
    category: str | None = None,
    document_type: str | None = None,
    year: int | None = None,
    circle_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    include_historical: bool = False,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    user = await _optional_user(request, db)
    return search_knowledge_base(
        db,
        query=q,
        user=user,
        category=category,
        document_type=document_type,
        year=year,
        circle_id=circle_id,
        date_from=date_from,
        date_to=date_to,
        include_historical=include_historical,
        limit=limit,
    )


def _execute_member_tools(db: Session, user: User, q_lower: str) -> tuple[list[dict[str, Any]], str | None, str | None]:
    tools_used: list[dict[str, Any]] = []
    member = db.get(Member, user.member_id) if user.member_id else None
    if not member:
        member = db.scalar(select(Member).where(Member.email == user.email))

    # 1. Personal membership status / expiry / ID
    if any(k in q_lower for k in ('my membership', 'my status', 'my id', 'আমার সদস্যপদ', 'আমার স্ট্যাটাস', 'মেয়াদ')):
        circle_name = 'Unassigned'
        if member and member.circle_id:
            circle = db.get(Circle, member.circle_id)
            if circle:
                circle_name = circle.name_en or circle.name_bn
        status_val = member.status if member else 'PENDING'
        mid_val = (member.membership_number or member.membership_id) if member else 'Not Assigned'
        exp_val = member.validity_date.strftime('%d %b %Y') if (member and member.validity_date) else 'Lifetime / N/A'
        tools_used.append(
            {
                'tool_name': 'my_membership_status',
                'authorized': True,
                'result': {
                    'membership_id': mid_val,
                    'status': status_val,
                    'valid_until': exp_val,
                    'circle': circle_name,
                },
            }
        )
        ans_en = f'Your personal membership status is {status_val} (Member ID: {mid_val}, Grid Circle: {circle_name}, Valid Until: {exp_val}).'
        ans_bn = f'আপনার ব্যক্তিগত সদস্যপদ স্ট্যাটাস হলো {status_val} (সদস্য আইডি: {mid_val}, গ্রিড সার্কেল: {circle_name}, মেয়াদ: {exp_val})।'
        return tools_used, ans_en, ans_bn

    # 2. Personal payment history
    if any(k in q_lower for k in ('my payment', 'my receipt', 'paid', 'আমার পেমেন্ট', 'আমার রসিদ')):
        txs = []
        if member:
            txs = db.scalars(
                select(PaymentTransaction)
                .where(PaymentTransaction.member_id == member.id)
                .order_by(PaymentTransaction.id.desc())
                .limit(5)
            ).all()
        paid_txs = [t for t in txs if t.status == 'PAID']
        total_paid = sum(int(t.amount or 0) for t in paid_txs)
        latest_ref = txs[0].transaction_ref if txs else 'None'
        tools_used.append(
            {
                'tool_name': 'my_payment_history',
                'authorized': True,
                'result': {
                    'transactions_count': len(txs),
                    'paid_count': len(paid_txs),
                    'total_paid_bdt': total_paid,
                    'latest_transaction_ref': latest_ref,
                },
            }
        )
        ans_en = f'You have {len(paid_txs)} verified paid transactions totaling {total_paid:,} BDT (Latest Ref: {latest_ref}).'
        ans_bn = f'আপনার মোট {len(paid_txs)} টি যাচাইকৃত পেমেন্ট রয়েছে যার সর্বমোট পরিমাণ ৳{total_paid:,} টাকা (সর্বশেষ রেফারেন্স: {latest_ref})।'
        return tools_used, ans_en, ans_bn

    # 3. Personal certificates
    if any(k in q_lower for k in ('my certificate', 'আমার সনদ')):
        certs = []
        if member:
            certs = db.scalars(select(Certificate).where(Certificate.member_id == member.id)).all()
        tools_used.append(
            {
                'tool_name': 'my_certificates',
                'authorized': True,
                'result': {
                    'certificate_count': len(certs),
                    'certificates': [c.certificate_no for c in certs],
                },
            }
        )
        ans_en = f'You currently have {len(certs)} official certificate(s) in your Certificate Wallet.'
        ans_bn = f'আপনার সনদ ওয়ালেটে বর্তমানে {len(certs)} টি অফিসিয়াল সনদ রয়েছে।'
        return tools_used, ans_en, ans_bn

    # 4. Personal application status
    if any(k in q_lower for k in ('my application', 'application status', 'আমার আবেদন')):
        app_row = None
        if member:
            app_row = db.scalar(
                select(MembershipApplication)
                .where(MembershipApplication.member_id == member.id)
                .order_by(MembershipApplication.id.desc())
            )
        app_status = app_row.status if app_row else (member.status if member else 'NONE')
        tools_used.append(
            {
                'tool_name': 'my_application_status',
                'authorized': True,
                'result': {'application_status': app_status},
            }
        )
        ans_en = f'Your membership application status is currently {app_status}.'
        ans_bn = f'আপনার সদস্যপদ আবেদনের বর্তমান অবস্থা হলো {app_status}।'
        return tools_used, ans_en, ans_bn

    return tools_used, None, None


def _execute_admin_tools(
    db: Session,
    user: User,
    q_lower: str,
    requested_circle_id: int | None = None,
) -> tuple[list[dict[str, Any]], str | None, str | None]:
    tools_used: list[dict[str, Any]] = []
    role = normalize_role(user.role)
    is_circle_admin = is_circle_scoped_admin(role)

    # Detect if query mentions a specific circle by name or code (e.g. "Dhaka", "Chattogram", "Circle 01", "Circle 02")
    all_circles = db.scalars(select(Circle).order_by(Circle.id.asc())).all()
    target_circle: Circle | None = None
    if requested_circle_id is not None:
        target_circle = db.get(Circle, requested_circle_id)
    else:
        for c in all_circles:
            c_names = [
                (c.name_en or '').lower(),
                (c.name_bn or '').lower(),
                (c.code or '').lower(),
                f'circle {c.id:02d}',
                f'circle {c.id}',
            ]
            if any(name and len(name) >= 3 and name in q_lower for name in c_names):
                target_circle = c
                break

    # Enforce strict Circle-Level Data Isolation for CIRCLE_ADMIN
    if is_circle_admin:
        if target_circle and user.circle_id is not None and int(target_circle.id) != int(user.circle_id):
            raise HTTPException(
                status_code=403,
                detail='Circle Admin is only authorized to query data for their own assigned Grid Circle.',
            )
        if target_circle is None and user.circle_id is not None:
            target_circle = db.get(Circle, user.circle_id)

    # Tool 1: "Which Circles have the highest number of pending applications?"
    if any(k in q_lower for k in ('which circle', 'highest', 'ranking', 'compare circle', 'কোন সার্কেলে')):
        if is_circle_admin:
            raise HTTPException(
                status_code=403,
                detail='Circle Admin cannot run cross-circle comparison queries.',
            )
        ranking: list[dict[str, Any]] = []
        for c in all_circles:
            pending_cnt = db.scalar(
                select(func.count(Member.id)).where(
                    Member.circle_id == c.id,
                    Member.status.in_(['PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'DOCUMENTS_REQUIRED', 'PAYMENT_PENDING']),
                )
            ) or 0
            active_cnt = db.scalar(
                select(func.count(Member.id)).where(Member.circle_id == c.id, Member.status == 'ACTIVE')
            ) or 0
            ranking.append(
                {
                    'circle_id': c.id,
                    'circle_code': c.code or f'CIRCLE-{c.id:02d}',
                    'circle_name_en': c.name_en or c.name_bn,
                    'circle_name_bn': c.name_bn,
                    'pending_applications': int(pending_cnt),
                    'active_members': int(active_cnt),
                }
            )
        ranking.sort(key=lambda r: (r['pending_applications'], r['active_members']), reverse=True)
        top_circle = ranking[0] if ranking else {'circle_name_en': 'N/A', 'pending_applications': 0}
        tools_used.append(
            {
                'tool_name': 'circles_pending_ranking',
                'authorized': True,
                'result': {'ranking': ranking[:5]},
            }
        )
        ans_en = (
            f"Based on authorized database records, {top_circle['circle_name_en']} currently has the highest number "
            f"of pending applications ({top_circle['pending_applications']})."
        )
        ans_bn = (
            f"প্রামাণ্য ডাটাবেজ অনুযায়ী বর্তমানে {top_circle.get('circle_name_bn', top_circle['circle_name_en'])}-এ "
            f"সর্বোচ্চ সংখ্যক অপেক্ষমাণ আবেদন রয়েছে ({top_circle['pending_applications']} টি)।"
        )
        return tools_used, ans_en, ans_bn

    # Tool 2: Pending applications (optionally scoped to a Circle)
    if any(k in q_lower for k in ('pending application', 'pending member', 'অপেক্ষমাণ আবেদন', 'পেন্ডিং')):
        stmt = select(Member).where(
            Member.status.in_(['PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'DOCUMENTS_REQUIRED', 'PAYMENT_PENDING'])
        )
        if target_circle is not None:
            stmt = stmt.where(Member.circle_id == target_circle.id)
        pending_members = db.scalars(stmt.order_by(Member.id.desc()).limit(25)).all()
        scope_label = (target_circle.name_en or target_circle.name_bn) if target_circle else 'All Grid Circles'
        tools_used.append(
            {
                'tool_name': 'pending_applications_by_circle',
                'authorized': True,
                'result': {
                    'scope': scope_label,
                    'circle_id': target_circle.id if target_circle else None,
                    'pending_count': len(pending_members),
                    'applications': [
                        {
                            'member_id': m.id,
                            'name_en': m.name_en or m.name_bn,
                            'status': m.status,
                            'circle_id': m.circle_id,
                        }
                        for m in pending_members[:10]
                    ],
                },
            }
        )
        ans_en = f'There are currently {len(pending_members)} pending applications in {scope_label}.'
        ans_bn = f'{scope_label}-এ বর্তমানে {len(pending_members)} টি অপেক্ষমাণ আবেদন রয়েছে।'
        return tools_used, ans_en, ans_bn

    # Tool 3: Member statistics ("How many active members are currently registered?")
    if any(k in q_lower for k in ('how many', 'active member', 'total member', 'statistics', 'registered', 'কতজন সক্রিয়', 'মোট সদস্য')):
        base_stmt = select(func.count(Member.id))
        active_stmt = select(func.count(Member.id)).where(Member.status == 'ACTIVE')
        pending_stmt = select(func.count(Member.id)).where(
            Member.status.in_(['PENDING', 'SUBMITTED', 'UNDER_REVIEW'])
        )
        now = datetime.utcnow()
        expiring_stmt = select(func.count(Member.id)).where(
            Member.status == 'ACTIVE',
            Member.validity_date.is_not(None),
            Member.validity_date <= now + timedelta(days=30),
        )

        if target_circle is not None:
            base_stmt = base_stmt.where(Member.circle_id == target_circle.id)
            active_stmt = active_stmt.where(Member.circle_id == target_circle.id)
            pending_stmt = pending_stmt.where(Member.circle_id == target_circle.id)
            expiring_stmt = expiring_stmt.where(Member.circle_id == target_circle.id)

        total_cnt = int(db.scalar(base_stmt) or 0)
        active_cnt = int(db.scalar(active_stmt) or 0)
        pending_cnt = int(db.scalar(pending_stmt) or 0)
        expiring_cnt = int(db.scalar(expiring_stmt) or 0)
        scope_label = (target_circle.name_en or target_circle.name_bn) if target_circle else 'PGCB Organization-wide'

        tools_used.append(
            {
                'tool_name': 'member_statistics',
                'authorized': True,
                'result': {
                    'scope': scope_label,
                    'circle_id': target_circle.id if target_circle else None,
                    'total_members': total_cnt,
                    'active_members': active_cnt,
                    'pending_members': pending_cnt,
                    'expiring_next_30_days': expiring_cnt,
                },
            }
        )
        ans_en = (
            f'According to {scope_label} records, there are currently {active_cnt} active members registered '
            f'(Total: {total_cnt}, Pending: {pending_cnt}, Expiring in 30 days: {expiring_cnt}).'
        )
        ans_bn = (
            f'{scope_label} রেকর্ড অনুযায়ী বর্তমানে {active_cnt} জন সক্রিয় সদস্য নিবন্ধিত রয়েছেন '
            f'(মোট: {total_cnt}, অপেক্ষমাণ: {pending_cnt}, ৩০ দিনে মেয়াদোত্তীর্ণ: {expiring_cnt})।'
        )
        return tools_used, ans_en, ans_bn

    # Tool 4: Revenue / financial summary
    if any(k in q_lower for k in ('revenue', 'finance', 'collection', 'রাজস্ব', 'আয়', 'তহবিল')):
        if not has_permission(user.role, 'finance.read'):
            raise HTTPException(status_code=403, detail='Finance permission required for revenue intelligence.')
        total_rev = int(
            db.scalar(
                select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
                    PaymentTransaction.status == 'PAID'
                )
            )
            or 0
        )
        tools_used.append(
            {
                'tool_name': 'financial_revenue_summary',
                'authorized': True,
                'result': {'total_verified_revenue_bdt': total_rev},
            }
        )
        ans_en = f'Total verified revenue collected is ৳{total_rev:,} BDT.'
        ans_bn = f'যাচাইকৃত মোট সংগৃহীত রাজস্বের পরিমাণ ৳{total_rev:,} টাকা।'
        return tools_used, ans_en, ans_bn

    return tools_used, None, None


@router.post('/ai/ask')
@router.post('/ai/chat')
async def ask_ai_assistant(
    payload: AIAskRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    t0 = time.perf_counter()
    ensure_default_knowledge_seeded(db)

    question = payload.question.strip()
    q_lower = question.lower()
    mode = (payload.mode or 'PUBLIC').strip().upper()
    if mode not in ('PUBLIC', 'MEMBER', 'ADMIN'):
        raise HTTPException(status_code=400, detail='Invalid assistant mode. Must be PUBLIC, MEMBER, or ADMIN.')

    user = await _optional_user(request, db)
    user_role = normalize_role(user.role) if user else 'PUBLIC'

    # 1. Prompt-Injection & Security Guardrail
    if _detect_prompt_injection(question):
        elapsed_ms = max(1, int((time.perf_counter() - t0) * 1000))
        log_item = AIQueryLog(
            user_id=user.id if user else None,
            user_role=user_role,
            assistant_mode=mode,
            question=question[:500],
            question_category='SECURITY_BLOCKED',
            answer_preview='Prompt injection or unauthorized data access attempt blocked.',
            confidence=0.0,
            unanswered=True,
            security_flagged=True,
            documents_searched=0,
            sources_cited='[]',
            tools_called='[]',
            response_time_ms=elapsed_ms,
            token_count=len(question.split()),
            estimated_cost_usd=0.0,
        )
        db.add(log_item)
        write_audit_log(
            db,
            actor_user_id=user.id if user else None,
            action='ai.security.prompt_injection_blocked',
            entity_type='AIQueryLog',
            entity_id='security',
            metadata={'mode': mode, 'question_excerpt': question[:120]},
        )
        db.commit()
        return {
            'question': question,
            'mode': mode,
            'status': 'BLOCKED_SECURITY',
            'security_flagged': True,
            'unanswered': True,
            'confidence': 0.0,
            'answer': (
                'This request was blocked by PGCB AI Security Guardrails. '
                'The assistant cannot bypass access controls, execute raw SQL, or disclose internal system prompts/credentials.'
            ),
            'answer_bn': (
                'পিজিসিবি এআই নিরাপত্তা নীতিমালার কারণে এই অনুরোধটি ব্লক করা হয়েছে। '
                'সহকারী কোনো অবস্থাতেই অ্যাক্সেস কন্ট্রোল উপেক্ষা বা গোপন তথ্য প্রকাশ করতে পারে না।'
            ),
            'sources': [],
            'tools_used': [],
            'fallback_actions': [
                {'action': 'CONTACT_SECRETARIAT', 'label': 'Contact Secretariat', 'url': '/contact'},
            ],
        }

    # 2. Enforce Mode & RBAC Authorization
    if mode == 'MEMBER':
        if user is None:
            raise HTTPException(status_code=401, detail='Authentication required for Member AI Assistant.')
    elif mode == 'ADMIN':
        if user is None:
            raise HTTPException(status_code=401, detail='Authentication required for Admin AI Assistant.')
        if user_role == 'MEMBER':
            raise HTTPException(status_code=403, detail='Admin role required for Admin AI Assistant.')

    # If PUBLIC mode user asks for another member's private records or admin stats, block if it requires auth
    if mode == 'PUBLIC' and any(
        k in q_lower for k in ('my payment history', 'my personal application', 'pending applications from')
    ):
        raise HTTPException(
            status_code=403,
            detail='Public Assistant can only access public institutional information. Please sign in for member or admin tools.',
        )

    tools_used: list[dict[str, Any]] = []
    tool_ans_en: str | None = None
    tool_ans_bn: str | None = None

    if mode == 'MEMBER' and user is not None:
        tools_used, tool_ans_en, tool_ans_bn = _execute_member_tools(db, user, q_lower)
    elif mode == 'ADMIN' and user is not None:
        tools_used, tool_ans_en, tool_ans_bn = _execute_admin_tools(
            db, user, q_lower, requested_circle_id=payload.circle_id
        )

    # 3. Knowledge Base Semantic Retrieval (scoped to user's permission level; PUBLIC mode forces user=None)
    retrieval_user = None if mode == 'PUBLIC' else user
    kb_search = search_knowledge_base(
        db,
        query=question,
        user=retrieval_user,
        circle_id=payload.circle_id,
        include_historical=payload.include_historical,
        limit=4,
    )
    passages = kb_search['results']
    docs_searched = kb_search['documents_searched']

    sources: list[dict[str, Any]] = [
        {
            'document_id': p['document_id'],
            'title': p['title'],
            'title_bn': p['title_bn'],
            'category': p['category'],
            'version': p['version'],
            'is_current': p['is_current'],
            'section': p['section'],
            'page': p['page'],
            'snippet': _sanitize_pii(p['snippet']),
            'score': p['score'],
            'view_source_url': p['view_source_url'],
        }
        for p in passages
    ]

    # Determine category for usage monitoring
    if any(k in q_lower for k in ('renew', 'নবায়ন', 'নবায়ন', 'fee', 'ফি', 'pay')):
        q_category = 'RENEWAL_AND_FEES'
    elif any(k in q_lower for k in ('constitution', 'rule', 'গঠনতন্ত্র', 'বিধিমালা')):
        q_category = 'CONSTITUTION_AND_RULES'
    elif any(k in q_lower for k in ('active member', 'pending', 'how many', 'circle')):
        q_category = 'ADMIN_ANALYTICS'
    elif any(k in q_lower for k in ('certificate', 'verify', 'id card', 'সনদ')):
        q_category = 'VERIFICATION'
    else:
        q_category = 'GENERAL'

    # 4. Synthesize Grounded Response or Safe "No Answer" Fallback
    if tool_ans_en:
        confidence = 0.96
        unanswered = False
        answer_en = tool_ans_en
        answer_bn = tool_ans_bn or tool_ans_en
        if sources:
            top_src = sources[0]
            answer_en += f" (Reference: {top_src['title']}, {top_src['section']}, Page {top_src['page']})"
    elif sources and sources[0]['score'] >= 0.25:
        top = sources[0]
        confidence = float(top['score'])
        unanswered = False
        citation_str = f"Source: {top['title']} | {top['section']} | Page {top['page']}"
        answer_en = (
            f"According to {top['title']} ({top['section']}, Page {top['page']}): "
            f"{_sanitize_pii(top['snippet'])} [{citation_str}]"
        )
        answer_bn = (
            f"{top['title_bn']} ({top['section']}, পৃষ্ঠা {top['page']}) অনুযায়ী: "
            f"{_sanitize_pii(top['snippet'])}"
        )
    else:
        # Safe "No Answer" Fallback — never hallucinate institutional policy
        confidence = 0.0
        unanswered = True
        sources = []
        answer_en = "I couldn't find an authoritative PGCB document supporting that answer."
        answer_bn = 'এই প্রশ্নের উত্তরের সমর্থনে কোনো প্রামাণ্য পিজিসিবি নথি পাওয়া যায়নি।'

    fallback_actions = [
        {
            'action': 'CONTACT_SECRETARIAT',
            'label': 'Contact Secretariat',
            'label_bn': 'সচিবালয়ে যোগাযোগ করুন',
            'url': '/contact',
        },
        {
            'action': 'SUBMIT_INQUIRY',
            'label': 'Submit Inquiry',
            'label_bn': 'অনুসন্ধান জমা দিন',
            'url': '/contact#inquiry',
        },
        {
            'action': 'SEARCH_DOCUMENTS',
            'label': 'Search Documents',
            'label_bn': 'নথিপত্র অনুসন্ধান করুন',
            'url': '/search',
        },
    ]

    elapsed_ms = max(1, int((time.perf_counter() - t0) * 1000))
    tokens_est = len(question.split()) + len(answer_en.split())
    cost_est = round(tokens_est * 0.000002, 6)

    log_entry = AIQueryLog(
        user_id=user.id if user else None,
        user_role=user_role,
        assistant_mode=mode,
        question=question[:500],
        question_category=q_category,
        answer_preview=answer_en[:480],
        confidence=confidence,
        unanswered=unanswered,
        security_flagged=False,
        documents_searched=docs_searched,
        sources_cited=json.dumps([{'id': s['document_id'], 'title': s['title']} for s in sources]),
        tools_called=json.dumps([t['tool_name'] for t in tools_used]),
        response_time_ms=elapsed_ms,
        token_count=tokens_est,
        estimated_cost_usd=cost_est,
    )
    db.add(log_entry)
    if tools_used:
        write_audit_log(
            db,
            actor_user_id=user.id if user else None,
            action='ai.tool.executed',
            entity_type='AIQueryLog',
            entity_id=mode,
            metadata={'tools': [t['tool_name'] for t in tools_used], 'role': user_role},
        )
    db.commit()

    return {
        'question': question,
        'mode': mode,
        'role': user_role,
        'status': 'UNANSWERED' if unanswered else 'ANSWERED',
        'unanswered': unanswered,
        'security_flagged': False,
        'confidence': confidence,
        'answer': answer_en if payload.language == 'en' else answer_bn,
        'answer_en': answer_en,
        'answer_bn': answer_bn,
        'sources': sources,
        'tools_used': tools_used,
        'fallback_actions': fallback_actions if unanswered else [],
        'response_time_ms': elapsed_ms,
    }


@router.post('/admin/ai/generate-faqs')
def generate_smart_faqs(
    payload: GenerateFAQRequest,
    user: User = Depends(require_permission('cms.write')),
    db: Session = Depends(get_db),
):
    ensure_default_knowledge_seeded(db)
    doc = db.get(KnowledgeDocument, payload.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Knowledge document not found')

    chunks = db.scalars(
        select(KnowledgeChunk)
        .where(KnowledgeChunk.document_id == doc.id)
        .order_by(KnowledgeChunk.chunk_index.asc())
        .limit(payload.max_faqs)
    ).all()

    created_faqs: list[dict[str, Any]] = []
    for ch in chunks:
        sec_label = ch.section_title or 'General Provision'
        q_en = f"What does {doc.title_en or doc.title_bn} specify regarding {sec_label}?"
        q_bn = f"{doc.title_bn}-এর '{sec_label}' ধারায় কী উল্লেখ আছে?"
        faq = KnowledgeFAQ(
            document_id=doc.id,
            question_bn=q_bn,
            question_en=q_en,
            answer_bn=ch.content,
            answer_en=ch.content,
            category=doc.category,
            section_ref=sec_label,
            page_ref=ch.page_number,
            status='DRAFT',
        )
        db.add(faq)
        db.flush()
        created_faqs.append(
            {
                'id': faq.id,
                'document_id': faq.document_id,
                'question_bn': faq.question_bn,
                'question_en': faq.question_en,
                'answer_bn': faq.answer_bn,
                'answer_en': faq.answer_en,
                'section_ref': faq.section_ref,
                'page_ref': faq.page_ref,
                'status': faq.status,
            }
        )

    write_audit_log(
        db,
        actor_user_id=user.id,
        action='ai.faq.generate_drafts',
        entity_type='KnowledgeDocument',
        entity_id=str(doc.id),
        metadata={'generated_count': len(created_faqs)},
    )
    db.commit()
    return {
        'document_id': doc.id,
        'document_title': doc.title_en or doc.title_bn,
        'generated_count': len(created_faqs),
        'status': 'DRAFT',
        'requires_admin_approval': True,
        'faqs': created_faqs,
    }


@router.get('/admin/ai/faqs')
def list_admin_faqs(
    status: str | None = None,
    user: User = Depends(require_permission('cms.read')),
    db: Session = Depends(get_db),
):
    stmt = select(KnowledgeFAQ).order_by(KnowledgeFAQ.id.desc())
    if status:
        stmt = stmt.where(KnowledgeFAQ.status == status.upper())
    rows = db.scalars(stmt).all()
    return [
        {
            'id': r.id,
            'document_id': r.document_id,
            'question_bn': r.question_bn,
            'question_en': r.question_en,
            'answer_bn': r.answer_bn,
            'answer_en': r.answer_en,
            'category': r.category,
            'section_ref': r.section_ref,
            'page_ref': r.page_ref,
            'status': r.status,
            'approved_by': r.approved_by,
            'published_at': r.published_at.isoformat() if r.published_at else None,
        }
        for r in rows
    ]


@router.patch('/admin/ai/faqs/{faq_id}')
def update_or_approve_faq(
    faq_id: int,
    payload: FAQUpdateRequest,
    user: User = Depends(require_permission('cms.write')),
    db: Session = Depends(get_db),
):
    faq = db.get(KnowledgeFAQ, faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail='FAQ not found')

    if payload.question_bn is not None:
        faq.question_bn = payload.question_bn
    if payload.question_en is not None:
        faq.question_en = payload.question_en
    if payload.answer_bn is not None:
        faq.answer_bn = payload.answer_bn
    if payload.answer_en is not None:
        faq.answer_en = payload.answer_en

    if payload.status is not None:
        target_status = payload.status.upper()
        if target_status not in ('DRAFT', 'REVIEW', 'APPROVED', 'PUBLISHED', 'ARCHIVED'):
            raise HTTPException(status_code=400, detail='Invalid FAQ status')
        if target_status == 'PUBLISHED' and not has_permission(user.role, 'cms.publish'):
            raise HTTPException(status_code=403, detail='Only authorized publishers/admins can publish FAQs')
        faq.status = target_status
        if target_status in ('APPROVED', 'PUBLISHED'):
            faq.approved_by = user.id
        if target_status == 'PUBLISHED':
            faq.published_at = datetime.utcnow()

    write_audit_log(
        db,
        actor_user_id=user.id,
        action='ai.faq.update',
        entity_type='KnowledgeFAQ',
        entity_id=str(faq.id),
        metadata={'status': faq.status},
    )
    db.commit()
    db.refresh(faq)
    return {
        'id': faq.id,
        'document_id': faq.document_id,
        'question_bn': faq.question_bn,
        'question_en': faq.question_en,
        'answer_bn': faq.answer_bn,
        'answer_en': faq.answer_en,
        'status': faq.status,
        'approved_by': faq.approved_by,
        'published_at': faq.published_at.isoformat() if faq.published_at else None,
    }


@router.get('/public/faqs')
def list_published_faqs(category: str | None = None, db: Session = Depends(get_db)):
    stmt = select(KnowledgeFAQ).where(KnowledgeFAQ.status == 'PUBLISHED').order_by(KnowledgeFAQ.id.asc())
    if category:
        stmt = stmt.where(KnowledgeFAQ.category == category.upper())
    rows = db.scalars(stmt).all()
    return [
        {
            'id': r.id,
            'document_id': r.document_id,
            'question_bn': r.question_bn,
            'question_en': r.question_en,
            'answer_bn': r.answer_bn,
            'answer_en': r.answer_en,
            'category': r.category,
            'section_ref': r.section_ref,
            'page_ref': r.page_ref,
        }
        for r in rows
    ]


@router.post('/admin/ai/content-assist')
def ai_content_assist(
    payload: ContentAssistRequest,
    user: User = Depends(require_permission('cms.write')),
    db: Session = Depends(get_db),
):
    title_bn = payload.title_bn.strip()
    title_en = (payload.title_en or '').strip()
    content_bn = payload.content_bn.strip()
    content_en = (payload.content_en or '').strip()

    improved_bn = f"অফিসিয়াল বিজ্ঞপ্তি: {content_bn}" if content_bn and not content_bn.startswith('অফিসিয়াল') else content_bn
    improved_en = (
        f"Official Notice ({payload.entity_type.upper()}): {content_en or title_en or title_bn}"
    )
    summary_bn = (content_bn[:180] + '...') if len(content_bn) > 180 else (content_bn or title_bn)
    summary_en = (content_en[:180] + '...') if len(content_en) > 180 else (content_en or title_en or title_bn)

    slug_words = re.findall(r'[a-z0-9]+', (title_en or 'pgcb-official-notice').lower())
    suggested_slug = '-'.join(slug_words[:8]) or 'pgcb-official-update'

    write_audit_log(
        db,
        actor_user_id=user.id,
        action='ai.cms.content_assist',
        entity_type=payload.entity_type,
        entity_id='draft',
        metadata={'actions': payload.actions},
    )
    db.commit()

    return {
        'entity_type': payload.entity_type,
        'requires_human_review': True,
        'auto_published': False,
        'suggestions': {
            'improved_wording': {
                'title_bn': title_bn,
                'title_en': title_en or f'PGCB Official {payload.entity_type.title()}',
                'content_bn': improved_bn,
                'content_en': improved_en,
            },
            'translation': {
                'bn_to_en': content_en or f'[Translated Summary] {title_en or title_bn}: {summary_en}',
                'en_to_bn': content_bn or f'[বাংলা অনুবাদ] {title_bn}: {summary_bn}',
            },
            'summary': {
                'summary_bn': summary_bn,
                'summary_en': summary_en,
            },
            'seo_metadata': {
                'meta_title': f"{title_en or title_bn} | PGCB Portal",
                'meta_description': summary_en or summary_bn,
                'suggested_slug': suggested_slug,
                'robots': 'index,follow',
            },
            'notification_draft': {
                'title_bn': f"নতুন {payload.entity_type}: {title_bn}",
                'body_bn': summary_bn,
            },
        },
    }


@router.get('/admin/ai/analytics')
def get_ai_usage_analytics(
    user: User = Depends(require_permission('reports.read')),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    logs = db.scalars(select(AIQueryLog).order_by(AIQueryLog.id.desc())).all()
    questions_today = sum(1 for l in logs if l.created_at and l.created_at >= today_start)
    total_questions = len(logs)
    documents_searched = sum(int(l.documents_searched or 0) for l in logs)
    unanswered_count = sum(1 for l in logs if l.unanswered)
    security_blocked = sum(1 for l in logs if l.security_flagged)
    avg_ms = (sum(int(l.response_time_ms or 0) for l in logs) / total_questions) if total_questions else 0.0
    total_tokens = sum(int(l.token_count or 0) for l in logs)
    total_cost = round(sum(float(l.estimated_cost_usd or 0.0) for l in logs), 6)

    by_category: dict[str, int] = {}
    source_counter: dict[str, int] = {}
    for l in logs:
        cat = l.question_category or 'GENERAL'
        by_category[cat] = by_category.get(cat, 0) + 1
        if l.sources_cited:
            try:
                cited = json.loads(l.sources_cited)
                for item in cited:
                    title = item.get('title') or f"Doc #{item.get('id')}"
                    source_counter[title] = source_counter.get(title, 0) + 1
            except Exception:
                pass

    top_sources = [
        {'title': title, 'citations': cnt}
        for title, cnt in sorted(source_counter.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    return {
        'questions_today': questions_today,
        'total_questions': total_questions,
        'documents_searched': documents_searched,
        'unanswered': unanswered_count,
        'security_blocked': security_blocked,
        'avg_response_time_sec': round(avg_ms / 1000.0, 3),
        'failure_rate': round((unanswered_count / total_questions), 4) if total_questions else 0.0,
        'total_tokens': total_tokens,
        'estimated_cost_usd': total_cost,
        'by_category': by_category,
        'top_source_documents': top_sources,
    }


@router.get('/admin/analytics/intelligence')
def get_admin_intelligence_dashboard(
    user: User = Depends(require_permission('reports.read')),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    role = normalize_role(user.role)
    circle_filter = user.circle_id if is_circle_scoped_admin(role) else None

    members_stmt = select(func.count(Member.id))
    active_stmt = select(func.count(Member.id)).where(Member.status == 'ACTIVE')
    pending_stmt = select(func.count(Member.id)).where(
        Member.status.in_(['PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'DOCUMENTS_REQUIRED', 'PAYMENT_PENDING'])
    )
    expiring_stmt = select(func.count(Member.id)).where(
        Member.status == 'ACTIVE',
        Member.validity_date.is_not(None),
        Member.validity_date <= now + timedelta(days=30),
    )
    apps_month_stmt = select(func.count(MembershipApplication.id)).where(
        MembershipApplication.submitted_at >= month_start
    )

    if circle_filter is not None:
        members_stmt = members_stmt.where(Member.circle_id == circle_filter)
        active_stmt = active_stmt.where(Member.circle_id == circle_filter)
        pending_stmt = pending_stmt.where(Member.circle_id == circle_filter)
        expiring_stmt = expiring_stmt.where(Member.circle_id == circle_filter)

    members_total = int(db.scalar(members_stmt) or 0)
    active_members = int(db.scalar(active_stmt) or 0)
    pending_members = int(db.scalar(pending_stmt) or 0)
    expiring_30d = int(db.scalar(expiring_stmt) or 0)
    apps_this_month = int(db.scalar(apps_month_stmt) or 0)

    revenue_month = int(
        db.scalar(
            select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
                PaymentTransaction.status == 'PAID',
                PaymentTransaction.created_at >= month_start,
            )
        )
        or 0
    )

    circles = db.scalars(select(Circle).order_by(Circle.id.asc())).all()
    circles_by_pending: list[dict[str, Any]] = []
    for c in circles:
        if circle_filter is not None and int(c.id) != int(circle_filter):
            continue
        p_cnt = int(
            db.scalar(
                select(func.count(Member.id)).where(
                    Member.circle_id == c.id,
                    Member.status.in_(['PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'DOCUMENTS_REQUIRED', 'PAYMENT_PENDING']),
                )
            )
            or 0
        )
        a_cnt = int(
            db.scalar(select(func.count(Member.id)).where(Member.circle_id == c.id, Member.status == 'ACTIVE')) or 0
        )
        circles_by_pending.append(
            {
                'circle_id': c.id,
                'circle_code': c.code or f'CIRCLE-{c.id:02d}',
                'circle_name_en': c.name_en or c.name_bn,
                'circle_name_bn': c.name_bn,
                'pending_applications': p_cnt,
                'active_members': a_cnt,
            }
        )
    circles_by_pending.sort(key=lambda x: x['pending_applications'], reverse=True)

    return {
        'members': members_total,
        'active': active_members,
        'pending': pending_members,
        'expiring_next_30_days': expiring_30d,
        'applications_this_month': apps_this_month,
        'revenue_this_month': revenue_month,
        'revenue_this_month_formatted': f'৳{revenue_month:,}',
        'circles_by_pending_applications': circles_by_pending,
    }
