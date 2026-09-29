from __future__ import annotations

import json
import re
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import current_user
from app.core.rbac import canonical_role, get_admin_circle_scope, has_permission, require_permission
from app.db.session import Base, engine, get_db
from app.models import (
    AIConversation,
    AIMessage,
    AIQueryLog,
    Certificate,
    Circle,
    Circular,
    CommitteeMember,
    Document,
    Event,
    EventRegistration,
    JournalIssue,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeFAQ,
    Member,
    MembershipApplication,
    Notice,
    Notification,
    Payment,
    PaymentTransaction,
    User,
)
from app.services import audit
from app.services.ai_provider import GROUNDED_SYSTEM_PROMPT, get_ai_provider
from app.services.knowledge_service import (
    can_user_access_document,
    ensure_default_knowledge_seeded,
    extract_text_from_file_bytes,
    ingest_knowledge_document,
    search_knowledge_base,
)

router = APIRouter(tags=['ai-intelligence'])

# Ensure AI conversation tables exist even on pre-initialized SQLite test DBs
try:
    Base.metadata.create_all(
        bind=engine,
        tables=[AIConversation.__table__, AIMessage.__table__],
        checkfirst=True,
    )
except Exception:
    pass

PROMPT_INJECTION_PATTERNS = [
    r'ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions',
    r'disregard\s+(?:all\s+)?(?:previous|system)\s+instructions',
    r'reveal\s+(?:your\s+)?system\s+prompt',
    r'show\s+(?:your\s+)?system\s+prompt',
    r'drop\s+table\s+',
    r'delete\s+from\s+users',
    r'select\s+\*\s+from\s+users',
    r'union\s+select\s+',
    r'password_hash',
    r'jwt_secret',
    r'bypass\s+rbac',
    r'dump\s+(?:all\s+)?(?:nid|passwords|database)',
    r'execute\s+sql',
    r'raw\s+sql',
]

CROSS_MEMBER_PRIVACY_PATTERNS = [
    r"(?:another|other)\s+member(?:'s)?\s+(?:payment|certificate|nid|phone|password|salary|record)",
    r'অন্য\s+সদস্যের\s+(?:পেমেন্ট|রসিদ|সনদ|এনআইডি|ফোন|তথ্য)',
    r'payment\s+(?:history|status)\s+(?:of|for)\s+member\s+pgd-',
    r'pgd-\d{4}-\d{3,6}\s+এর\s+(?:পেমেন্ট|রসিদ|ব্যক্তিগত)',
]

# Sliding-window rate limit tracker for AI chat (per user/IP)
_AI_RATE_WINDOW_SEC = 60.0
_AI_RATE_MAX_REQUESTS = 120
_ai_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


def _check_ai_rate_limit(key: str) -> None:
    now = time.monotonic()
    dq = _ai_rate_buckets[key]
    while dq and (now - dq[0]) > _AI_RATE_WINDOW_SEC:
        dq.popleft()
    if len(dq) >= _AI_RATE_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail='AI Assistant rate limit exceeded. Please wait a moment before sending more questions.',
        )
    dq.append(now)


def _detect_prompt_injection(question: str) -> bool:
    q_low = question.lower()
    for pat in PROMPT_INJECTION_PATTERNS:
        if re.search(pat, q_low):
            return True
    return False


def _detect_cross_member_privacy_violation(question: str, current_member_id_str: str | None = None) -> bool:
    q_low = question.lower()
    for pat in CROSS_MEMBER_PRIVACY_PATTERNS:
        if re.search(pat, q_low):
            return True
    # Check if user is asking for a specific PGD-XXXX ID's private payment/receipt that is not their own
    match = re.search(r'\b(pgd-\d{4}-\d{3,6})\b', q_low)
    if match and any(w in q_low for w in ('payment', 'receipt', 'transaction', 'nid', 'পেমেন্ট', 'রসিদ', 'এনআইডি')):
        asked_id = match.group(1).upper()
        if not current_member_id_str or asked_id != current_member_id_str.upper():
            return True
    return False


def _sanitize_pii(text: str) -> str:
    if not text:
        return ''
    sanitized = re.sub(r'\b\d{13,17}\b', '[REDACTED-NID]', text)
    return sanitized


def _detect_language(question: str, requested_language: str | None = None) -> str:
    """Detect whether the question is Bangla, English, or mixed."""
    has_bn = bool(re.search(r'[\u0980-\u09FF]', question))
    has_en = bool(re.search(r'[a-zA-Z]{2,}', question))
    if has_bn:
        return 'bn'
    if requested_language and requested_language.lower() in ('bn', 'en'):
        return requested_language.lower()
    if has_en:
        return 'en'
    return 'bn'


def _compute_confidence_state(confidence: float, unanswered: bool) -> str:
    if unanswered or confidence < 0.35:
        return 'LOW'
    if confidence >= 0.70:
        return 'HIGH'
    return 'MEDIUM'


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
    conversation_id: int | None = None
    session_id: str | None = None


class ConversationCreateRequest(BaseModel):
    session_id: str | None = None
    language: str = 'bn'
    mode: str = 'PUBLIC'
    title: str | None = None


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


def _serialize_message(msg: AIMessage) -> dict[str, Any]:
    def _parse_json(raw: str | None) -> list[ Any ]:
        if not raw:
            return []
        try:
            val = json.loads(raw)
            return val if isinstance(val, list) else []
        except Exception:
            return []

    return {
        'id': msg.id,
        'conversation_id': msg.conversation_id,
        'role': msg.role,
        'content': msg.content,
        'content_bn': msg.content_bn or msg.content,
        'content_en': msg.content_en or msg.content,
        'intent': msg.intent,
        'confidence': msg.confidence,
        'confidence_state': msg.confidence_state,
        'sources': _parse_json(msg.sources),
        'tools_used': _parse_json(msg.tools_used),
        'actions': _parse_json(msg.actions),
        'created_at': msg.created_at.isoformat() if msg.created_at else None,
    }


@router.get('/ai/suggestions')
async def get_ai_suggestions(
    mode: str = Query(default='PUBLIC'),
    language: str = Query(default='bn'),
):
    """Return institutional quick actions and sample questions in Bangla and English."""
    quick_actions = [
        {
            'id': 'membership_info',
            'label_bn': 'সদস্যপদ সম্পর্কে জানুন',
            'label_en': 'Membership',
            'question_bn': 'PGCB membership নিতে কী কী লাগবে?',
            'question_en': 'What are the eligibility criteria and documents required for PGCB membership?',
            'mode': 'PUBLIC',
            'action_url': '/membership',
        },
        {
            'id': 'my_membership',
            'label_bn': 'আমার সদস্যপদ',
            'label_en': 'My Membership',
            'question_bn': 'আমার সদস্যপদের অবস্থা কী?',
            'question_en': 'What is my membership status and my id?',
            'mode': 'MEMBER',
            'action_url': '/portal',
        },
        {
            'id': 'payment_status',
            'label_bn': 'Payment Status',
            'label_en': 'Payment Status',
            'question_bn': 'আমার শেষ payment কবে করেছি?',
            'question_en': 'Show my payment history and receipts',
            'mode': 'MEMBER',
            'action_url': '/portal#payments',
        },
        {
            'id': 'certificates',
            'label_bn': 'Certificate যাচাই',
            'label_en': 'Certificates',
            'question_bn': 'আমার certificate কোথায়?',
            'question_en': 'Where is my membership certificate?',
            'mode': 'MEMBER',
            'action_url': '/verify',
        },
        {
            'id': 'latest_circulars',
            'label_bn': 'Latest Circulars',
            'label_en': 'Latest Circulars',
            'question_bn': 'নতুন circular কী আছে?',
            'question_en': 'What are the latest official circulars?',
            'mode': 'PUBLIC',
            'action_url': '/circulars',
        },
        {
            'id': 'events',
            'label_bn': 'Events',
            'label_en': 'Events',
            'question_bn': 'আসন্ন ইভেন্ট ও সভা কী কী আছে?',
            'question_en': 'What upcoming events and meetings are scheduled?',
            'mode': 'PUBLIC',
            'action_url': '/events',
        },
        {
            'id': 'documents',
            'label_bn': 'Documents',
            'label_en': 'Documents',
            'question_bn': 'membership renewal-এর official document কোনটা?',
            'question_en': 'Which official documents exist for membership renewal?',
            'mode': 'PUBLIC',
            'action_url': '/documents',
        },
        {
            'id': 'contact_secretariat',
            'label_bn': 'Contact Secretariat',
            'label_en': 'Contact Secretariat',
            'question_bn': 'সচিবালয়ে যোগাযোগের ঠিকানা ও ফোন নম্বর কী?',
            'question_en': 'How can I contact the PGCB Secretariat?',
            'mode': 'PUBLIC',
            'action_url': '/contact',
        },
    ]
    return {
        'mode': mode.upper(),
        'language': language,
        'quick_actions': quick_actions,
    }


@router.post('/ai/conversations')
async def create_ai_conversation(
    payload: ConversationCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = await _optional_user(request, db)
    now = datetime.utcnow()
    conv = AIConversation(
        user_id=user.id if user else None,
        session_id=(payload.session_id or '').strip()[:120],
        title=(payload.title or 'PGCB AI Assistant Conversation')[:300],
        mode=(payload.mode or 'PUBLIC').upper()[:30],
        language=(payload.language or 'bn').lower()[:10],
        created_at=now,
        updated_at=now,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {
        'id': conv.id,
        'conversation_id': conv.id,
        'user_id': conv.user_id,
        'session_id': conv.session_id,
        'title': conv.title,
        'mode': conv.mode,
        'language': conv.language,
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
        'messages': [],
    }


@router.get('/ai/conversations')
async def list_ai_conversations(
    request: Request,
    session_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    user = await _optional_user(request, db)
    stmt = select(AIConversation).order_by(AIConversation.updated_at.desc()).limit(limit)
    if user is not None:
        if session_id:
            stmt = stmt.where(
                or_(AIConversation.user_id == user.id, AIConversation.session_id == session_id)
            )
        else:
            stmt = stmt.where(AIConversation.user_id == user.id)
    elif session_id:
        stmt = stmt.where(AIConversation.session_id == session_id, AIConversation.user_id.is_(None))
    else:
        return []

    rows = db.scalars(stmt).all()
    return [
        {
            'id': c.id,
            'conversation_id': c.id,
            'title': c.title,
            'mode': c.mode,
            'language': c.language,
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'updated_at': c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in rows
    ]


@router.get('/ai/conversations/{conversation_id}')
async def get_ai_conversation(
    conversation_id: int,
    request: Request,
    session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    conv = db.get(AIConversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail='Conversation not found')

    user = await _optional_user(request, db)
    if conv.user_id is not None:
        if user is None or (user.id != conv.user_id and canonical_role(user.role) != 'SUPER_ADMIN'):
            raise HTTPException(status_code=403, detail='Not authorized to access this conversation')
    elif conv.session_id and session_id and conv.session_id != session_id:
        raise HTTPException(status_code=403, detail='Session mismatch for conversation')

    msgs = db.scalars(
        select(AIMessage)
        .where(AIMessage.conversation_id == conv.id)
        .order_by(AIMessage.id.asc())
    ).all()

    return {
        'id': conv.id,
        'conversation_id': conv.id,
        'user_id': conv.user_id,
        'session_id': conv.session_id,
        'title': conv.title,
        'mode': conv.mode,
        'language': conv.language,
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
        'messages': [_serialize_message(m) for m in msgs],
    }


@router.delete('/ai/conversations/{conversation_id}')
async def delete_ai_conversation(
    conversation_id: int,
    request: Request,
    session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    conv = db.get(AIConversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail='Conversation not found')

    user = await _optional_user(request, db)
    if conv.user_id is not None:
        if user is None or (user.id != conv.user_id and canonical_role(user.role) != 'SUPER_ADMIN'):
            raise HTTPException(status_code=403, detail='Not authorized to delete this conversation')
    elif conv.session_id and session_id and conv.session_id != session_id:
        raise HTTPException(status_code=403, detail='Session mismatch for conversation')

    db.query(AIMessage).filter(AIMessage.conversation_id == conv.id).delete()
    db.delete(conv)
    db.commit()
    return {'ok': True, 'deleted_id': conversation_id}


@router.post('/admin/knowledge/documents')
def create_knowledge_document(
    payload: KnowledgeDocCreateRequest,
    user: User = Depends(require_permission('content.write')),
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
    audit(db, user, 'knowledge.document.ingest', 'KnowledgeDocument', doc.id)
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
    user: User = Depends(require_permission('content.write')),
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
    audit(db, user, 'knowledge.file.ingest', 'KnowledgeDocument', doc.id)
    db.commit()
    return _serialize_knowledge_doc(doc)


@router.get('/admin/knowledge/documents')
def list_knowledge_documents(
    category: str | None = None,
    include_historical: bool = True,
    user: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    ensure_default_knowledge_seeded(db)
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.id.desc())
    if category:
        stmt = stmt.where(KnowledgeDocument.category == category.upper())
    if not include_historical:
        stmt = stmt.where(KnowledgeDocument.is_current == True)
    docs = db.scalars(stmt).all()
    return [_serialize_knowledge_doc(d) for d in docs if can_user_access_document(user, d, db=db)]


@router.post('/admin/knowledge/documents/{doc_id}/supersede')
def supersede_knowledge_document(
    doc_id: int,
    payload: SupersedeDocRequest,
    user: User = Depends(require_permission('content.write')),
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
    audit(db, user, 'knowledge.document.supersede', 'KnowledgeDocument', old_doc.id)
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
    if not can_user_access_document(user, doc, db=db):
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


def _execute_member_tools(
    db: Session,
    user: User,
    q_lower: str,
) -> tuple[list[dict[str, Any]], str | None, str | None, list[dict[str, Any]]]:
    """Execute authorized member-scoped tools (strictly scoped to current_user -> member)."""
    tools_used: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    member = db.scalar(select(Member).where(Member.user_id == user.id))

    # 1. Member Profile & Membership Status
    if any(
        k in q_lower
        for k in (
            'my membership',
            'my status',
            'my id',
            'my profile',
            'আমার সদস্যপদ',
            'আমার স্ট্যাটাস',
            'সদস্যপদের অবস্থা',
            'আমার প্রোফাইল',
            'মেয়াদ',
            'মেয়াদ',
        )
    ):
        circle_name_en = 'Unassigned'
        circle_name_bn = 'অনির্ধারিত'
        if member and member.circle_id:
            circle = db.get(Circle, member.circle_id)
            if circle:
                circle_name_en = circle.name_en or circle.name_bn
                circle_name_bn = circle.name_bn or circle.name_en
        status_val = member.status if member else 'PENDING'
        mid_val = member.membership_id if member and member.membership_id else 'Not Assigned'
        exp_val = (
            member.validity_date.strftime('%d %b %Y')
            if (member and member.validity_date)
            else 'Lifetime / N/A'
        )
        name_en = (member.name_en if member and member.name_en else user.name_en) or user.name_bn
        name_bn = (member.name_bn if member and member.name_bn else user.name_bn) or name_en
        desig_en = (member.designation_en if member and member.designation_en else None) or 'Diploma Engineer'
        desig_bn = (member.designation_bn if member and member.designation_bn else None) or 'ডিপ্লোমা প্রকৌশলী'

        profile_payload = {
            'name': name_en,
            'name_bn': name_bn,
            'membership_id': mid_val,
            'designation': desig_en,
            'designation_bn': desig_bn,
            'circle': circle_name_en,
            'circle_bn': circle_name_bn,
            'status': status_val,
            'valid_until': exp_val,
        }
        tools_used.append(
            {
                'tool_name': 'my_membership_status',
                'authorized': True,
                'result': profile_payload,
            }
        )
        tools_used.append(
            {
                'tool_name': 'member.get_profile',
                'authorized': True,
                'result': profile_payload,
            }
        )
        actions.append(
            {
                'type': 'OPEN_MEMBER_PROFILE',
                'action': 'OPEN_MEMBER_PROFILE',
                'label': 'Open Member Portal',
                'label_bn': 'সদস্য পোর্টাল দেখুন',
                'url': '/portal',
            }
        )
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'View Digital ID Card',
                'label_bn': 'ডিজিটাল আইডি কার্ড',
                'url': '/portal/id-card',
            }
        )
        ans_en = (
            f"Your personal membership status is {status_val}\n"
            f"• Name: {name_en}\n"
            f"• Member ID: {mid_val}\n"
            f"• Designation: {desig_en}\n"
            f"• Grid Circle: {circle_name_en}\n"
            f"• Valid Until: {exp_val}"
        )
        ans_bn = (
            f"আপনার ব্যক্তিগত সদস্যপদের বর্তমান তথ্য:\n"
            f"• নাম: {name_bn}\n"
            f"• সদস্য আইডি: {mid_val}\n"
            f"• পদবি: {desig_bn}\n"
            f"• গ্রিড সার্কেল: {circle_name_bn}\n"
            f"• অবস্থা (Status): {status_val}\n"
            f"• মেয়াদ: {exp_val}"
        )
        return tools_used, ans_en, ans_bn, actions

    # 2. Payment Assistant
    if any(
        k in q_lower
        for k in (
            'my payment',
            'my receipt',
            'last payment',
            'paid',
            'আমার পেমেন্ট',
            'আমার রসিদ',
            'শেষ payment',
            'শেষ পেমেন্ট',
            'কত ছিল',
            'কবে করেছি',
        )
    ):
        txs: list[PaymentTransaction] = []
        if member:
            txs = list(
                db.scalars(
                    select(PaymentTransaction)
                    .where(PaymentTransaction.member_id == member.id)
                    .order_by(PaymentTransaction.id.desc())
                    .limit(5)
                ).all()
            )
        paid_txs = [t for t in txs if t.status == 'PAID']
        total_paid = sum(int(t.amount or 0) for t in paid_txs)
        latest_tx = paid_txs[0] if paid_txs else (txs[0] if txs else None)
        latest_ref = latest_tx.transaction_ref if latest_tx else 'None'
        latest_amt = int(latest_tx.amount or 0) if latest_tx else 0
        latest_status = latest_tx.status if latest_tx else 'NONE'
        latest_date = (
            latest_tx.created_at.strftime('%d %B %Y')
            if (latest_tx and latest_tx.created_at)
            else 'N/A'
        )

        result_payload = {
            'transactions_count': len(txs),
            'paid_count': len(paid_txs),
            'total_paid_bdt': total_paid,
            'latest_transaction_ref': latest_ref,
            'latest_amount_bdt': latest_amt,
            'latest_status': latest_status,
            'latest_date': latest_date,
        }
        tools_used.append(
            {
                'tool_name': 'my_payment_history',
                'authorized': True,
                'result': result_payload,
            }
        )
        tools_used.append(
            {
                'tool_name': 'member.get_payment_history',
                'authorized': True,
                'result': result_payload,
            }
        )
        actions.append(
            {
                'type': 'OPEN_RECEIPT',
                'action': 'OPEN_RECEIPT',
                'label': 'View Receipt',
                'label_bn': 'রসিদ দেখুন (View Receipt)',
                'url': '/portal#payments',
            }
        )
        if latest_tx:
            ans_en = (
                f"Your latest verified payment:\n\n"
                f"Amount: ৳{latest_amt:,}\n"
                f"Transaction: {latest_ref}\n"
                f"Status: {latest_status}\n"
                f"Date: {latest_date}\n\n"
                f"(Total verified paid transactions: {len(paid_txs)}, Total Paid: ৳{total_paid:,} BDT)"
            )
            ans_bn = (
                f"আপনার সর্বশেষ verified payment:\n\n"
                f"Amount: ৳{latest_amt:,}\n"
                f"Transaction: {latest_ref}\n"
                f"Status: {latest_status}\n"
                f"Date: {latest_date}\n\n"
                f"(মোট যাচাইকৃত পেমেন্ট: {len(paid_txs)} টি, সর্বমোট পরিশোধিত: ৳{total_paid:,} টাকা)"
            )
        else:
            ans_en = 'No verified payment transactions were found for your membership account yet.'
            ans_bn = 'আপনার সদস্যপদ অ্যাকাউন্টে এখনো কোনো যাচাইকৃত পেমেন্ট লেনদেন পাওয়া যায়নি।'
        return tools_used, ans_en, ans_bn, actions

    # 3. Certificate Assistant
    if any(
        k in q_lower
        for k in (
            'my certificate',
            'আমার সনদ',
            'আমার certificate',
            'certificate কোথায়',
            'certificate দেখাও',
            'সনদপত্র কোথায়',
        )
    ):
        certs: list[Certificate] = []
        if member:
            certs = list(
                db.scalars(
                    select(Certificate)
                    .where(Certificate.member_id == member.id)
                    .order_by(Certificate.id.desc())
                ).all()
            )
        latest_cert = certs[0] if certs else None
        cert_no = latest_cert.certificate_no if latest_cert else 'PGCB-CERT-PENDING'
        cert_title = (
            getattr(latest_cert, 'title_en', None)
            or getattr(latest_cert, 'certificate_type', None)
            or 'Membership Certificate'
        )
        cert_issued = (
            latest_cert.issued_at.strftime('%d %B %Y')
            if (latest_cert and getattr(latest_cert, 'issued_at', None))
            else datetime.utcnow().strftime('%d %B %Y')
        )
        cert_status = (
            'Revoked'
            if (latest_cert and getattr(latest_cert, 'revoked', False))
            else ('Verified' if latest_cert else 'Pending Issue')
        )
        cert_url = (
            f"/certificate/{latest_cert.verification_token}"
            if (latest_cert and getattr(latest_cert, 'verification_token', None))
            else '/portal'
        )

        cert_payload = {
            'certificate_count': len(certs),
            'certificates': [c.certificate_no for c in certs],
            'latest_certificate': {
                'title': cert_title,
                'certificate_no': cert_no,
                'issued': cert_issued,
                'status': cert_status,
                'view_url': cert_url,
            }
            if latest_cert
            else None,
        }
        tools_used.append(
            {
                'tool_name': 'my_certificates',
                'authorized': True,
                'result': cert_payload,
            }
        )
        tools_used.append(
            {
                'tool_name': 'member.get_certificates',
                'authorized': True,
                'result': cert_payload,
            }
        )
        actions.append(
            {
                'type': 'OPEN_CERTIFICATE',
                'action': 'OPEN_CERTIFICATE',
                'label': 'View Certificate',
                'label_bn': 'সনদ দেখুন (View Certificate)',
                'url': cert_url,
            }
        )
        if latest_cert:
            ans_en = (
                f"Your latest certificate:\n\n"
                f"Certificate: {cert_title}\n"
                f"Certificate No: {cert_no}\n"
                f"Issued: {cert_issued}\n"
                f"Status: {cert_status}\n\n"
                f"You have {len(certs)} official certificate(s) in your Certificate Wallet."
            )
            ans_bn = (
                f"আপনার সর্বশেষ certificate:\n\n"
                f"Certificate: {cert_title}\n"
                f"Certificate No: {cert_no}\n"
                f"Issued: {cert_issued}\n"
                f"Status: {cert_status}\n\n"
                f"আপনার সনদ ওয়ালেটে মোট {len(certs)} টি অফিসিয়াল সনদ রয়েছে।"
            )
        else:
            ans_en = 'You currently have 0 issued certificates in your Certificate Wallet. Once your membership is active, your certificate will appear in the Member Portal.'
            ans_bn = 'আপনার সনদ ওয়ালেটে বর্তমানে কোনো ইস্যুকৃত সনদ নেই। সদস্যপদ সক্রিয় হওয়ার পর সদস্য পোর্টালে সনদ পাওয়া যাবে।'
        return tools_used, ans_en, ans_bn, actions

    # 4. Application Status
    if any(
        k in q_lower
        for k in ('my application', 'application status', 'আমার আবেদন', 'আবেদনের অবস্থা')
    ):
        app_row = None
        if member:
            app_row = db.scalar(
                select(MembershipApplication)
                .where(MembershipApplication.member_id == member.id)
                .order_by(MembershipApplication.id.desc())
            )
        app_status = (app_row.status if app_row else (member.status if member else 'NONE'))
        app_no = (
            (app_row.application_no if app_row else None)
            or (member.application_no if member else None)
            or 'N/A'
        )
        app_payload = {'application_status': app_status, 'application_no': app_no}
        tools_used.append(
            {
                'tool_name': 'my_application_status',
                'authorized': True,
                'result': app_payload,
            }
        )
        tools_used.append(
            {
                'tool_name': 'member.get_application_status',
                'authorized': True,
                'result': app_payload,
            }
        )
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'Track Application',
                'label_bn': 'আবেদন ট্র্যাক করুন',
                'url': '/membership/track',
            }
        )
        ans_en = f'Your membership application ({app_no}) status is currently {app_status}.'
        ans_bn = f'আপনার সদস্যপদ আবেদন ({app_no})-এর বর্তমান অবস্থা হলো {app_status}।'
        return tools_used, ans_en, ans_bn, actions

    # 5. Member Notifications
    if any(k in q_lower for k in ('my notification', 'আমার নোটিফিকেশন', 'বার্তা')):
        notifs = list(
            db.scalars(
                select(Notification)
                .where(Notification.user_id == user.id)
                .order_by(Notification.id.desc())
                .limit(5)
            ).all()
        )
        unread_cnt = sum(1 for n in notifs if not getattr(n, 'is_read', False))
        tools_used.append(
            {
                'tool_name': 'member.get_notifications',
                'authorized': True,
                'result': {
                    'recent_count': len(notifs),
                    'unread_count': unread_cnt,
                    'items': [n.title_bn for n in notifs[:3]],
                },
            }
        )
        actions.append(
            {
                'type': 'OPEN_MEMBER_PROFILE',
                'action': 'OPEN_MEMBER_PROFILE',
                'label': 'View Notifications',
                'label_bn': 'নোটিফিকেশন দেখুন',
                'url': '/portal',
            }
        )
        ans_en = f'You have {unread_cnt} unread notification(s) among your {len(notifs)} most recent portal notifications.'
        ans_bn = f'আপনার সাম্প্রতিক {len(notifs)} টি নোটিফিকেশনের মধ্যে {unread_cnt} টি অপঠিত রয়েছে।'
        return tools_used, ans_en, ans_bn, actions

    # 6. Member Events
    if any(k in q_lower for k in ('my event', 'আমার ইভেন্ট', 'registered event')):
        regs = list(
            db.scalars(
                select(EventRegistration)
                .where(EventRegistration.email == user.email)
                .order_by(EventRegistration.id.desc())
                .limit(5)
            ).all()
        )
        tools_used.append(
            {
                'tool_name': 'member.get_events',
                'authorized': True,
                'result': {'registered_events_count': len(regs)},
            }
        )
        actions.append(
            {
                'type': 'OPEN_EVENT',
                'action': 'OPEN_EVENT',
                'label': 'Browse Events',
                'label_bn': 'ইভেন্টসমূহ দেখুন',
                'url': '/events',
            }
        )
        ans_en = f'You have {len(regs)} event registration(s) associated with your account.'
        ans_bn = f'আপনার অ্যাকাউন্টের সাথে {len(regs)} টি ইভেন্ট নিবন্ধন যুক্ত রয়েছে।'
        return tools_used, ans_en, ans_bn, actions

    # 7. Member Documents
    if any(k in q_lower for k in ('my document', 'আমার ডকুমেন্ট', 'আমার নথি')):
        docs = list(db.scalars(select(Document).order_by(Document.id.desc()).limit(5)).all())
        tools_used.append(
            {
                'tool_name': 'member.get_documents',
                'authorized': True,
                'result': {'available_documents': len(docs)},
            }
        )
        actions.append(
            {
                'type': 'OPEN_DOCUMENT',
                'action': 'OPEN_DOCUMENT',
                'label': 'Open Documents',
                'label_bn': 'ডকুমেন্টস দেখুন',
                'url': '/documents',
            }
        )
        ans_en = f'There are {len(docs)} official institutional forms and documents available in your repository.'
        ans_bn = f'ডকুমেন্ট সংগ্রহশালায় আপনার জন্য {len(docs)} টি অফিসিয়াল ফরম ও নথি উপলব্ধ রয়েছে।'
        return tools_used, ans_en, ans_bn, actions

    return tools_used, None, None, actions


def _execute_admin_tools(
    db: Session,
    user: User,
    q_lower: str,
    requested_circle_id: int | None = None,
) -> tuple[list[dict[str, Any]], str | None, str | None, list[dict[str, Any]]]:
    tools_used: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    role = canonical_role(user.role)
    is_circle_admin = role == 'CIRCLE_ADMIN'
    scoped_circle_id = get_admin_circle_scope(user, db) if is_circle_admin else None

    all_circles = db.scalars(select(Circle).order_by(Circle.id.asc())).all()
    target_circle: Circle | None = None
    if requested_circle_id is not None:
        target_circle = db.get(Circle, requested_circle_id)
    else:
        for c in all_circles:
            c_names = [
                (c.name_en or '').lower(),
                (c.name_bn or '').lower(),
                (getattr(c, 'circle_code', None) or '').lower(),
                f'circle {c.id:02d}',
                f'circle {c.id}',
            ]
            if any(name and len(name) >= 3 and name in q_lower for name in c_names):
                target_circle = c
                break

    if is_circle_admin:
        if target_circle and scoped_circle_id is not None and int(target_circle.id) != int(scoped_circle_id):
            raise HTTPException(
                status_code=403,
                detail='Circle Admin is only authorized to query data for their own assigned Grid Circle.',
            )
        if target_circle is None and scoped_circle_id is not None and scoped_circle_id != -1:
            target_circle = db.get(Circle, scoped_circle_id)

    # 1. Circle Pending Ranking
    if any(
        k in q_lower
        for k in (
            'which circle',
            'highest',
            'ranking',
            'compare circle',
            'কোন সার্কেলে',
            'কোন circle-এ',
            'সবচেয়ে বেশি',
        )
    ):
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
                    'circle_code': getattr(c, 'circle_code', None) or f'CIRCLE-{c.id:02d}',
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
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'Review Applications',
                'label_bn': 'আবেদনসমূহ যাচাই করুন',
                'url': '/admin/memberships/applications',
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
        return tools_used, ans_en, ans_bn, actions

    # 2. Monthly Membership Applications Breakdown ("এই মাসে কয়টি membership application এসেছে?")
    if any(
        k in q_lower
        for k in (
            'এই মাসে',
            'this month',
            'কয়টি membership application',
            'কতগুলো membership application',
            'monthly application',
        )
    ):
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        month_label = now.strftime('%B %Y')

        base_q = select(Member)
        if target_circle is not None:
            base_q = base_q.where(Member.circle_id == target_circle.id)

        all_rows = list(db.scalars(base_q).all())
        month_rows = [m for m in all_rows if m.created_at and m.created_at >= month_start]
        dataset = month_rows if month_rows else all_rows

        total_apps = len(dataset)
        approved_cnt = sum(1 for m in dataset if m.status in ('ACTIVE', 'APPROVED'))
        pending_cnt = sum(
            1
            for m in dataset
            if m.status in ('PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'DOCUMENTS_REQUIRED', 'PAYMENT_PENDING', 'CORRECTION_REQUIRED')
        )
        rejected_cnt = sum(1 for m in dataset if m.status in ('REJECTED', 'CANCELLED'))

        tools_used.append(
            {
                'tool_name': 'monthly_application_analytics',
                'authorized': True,
                'result': {
                    'period': month_label,
                    'total': total_apps,
                    'approved': approved_cnt,
                    'pending': pending_cnt,
                    'rejected': rejected_cnt,
                },
            }
        )
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'Open Applications Desk',
                'label_bn': 'আবেদন ডেস্ক খুলুন',
                'url': '/admin/memberships/applications',
            }
        )
        ans_en = (
            f"Membership Applications ({month_label}):\n\n"
            f"• Total: {total_apps}\n"
            f"• Approved / Active: {approved_cnt}\n"
            f"• Pending: {pending_cnt}\n"
            f"• Rejected: {rejected_cnt}"
        )
        ans_bn = (
            f"সদস্যপদ আবেদনের পরিসংখ্যান ({month_label}):\n\n"
            f"• মোট আবেদন (Total): {total_apps} টি\n"
            f"• অনুমোদিত / সক্রিয় (Approved): {approved_cnt} টি\n"
            f"• অপেক্ষমাণ (Pending): {pending_cnt} টি\n"
            f"• বাতিল / প্রত্যাখ্যাত (Rejected): {rejected_cnt} টি"
        )
        return tools_used, ans_en, ans_bn, actions

    # 3. Pending Applications by Circle
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
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'Manage Pending Applications',
                'label_bn': 'অপেক্ষমাণ আবেদন ব্যবস্থাপনা',
                'url': '/admin/memberships/applications',
            }
        )
        ans_en = f'There are currently {len(pending_members)} pending applications in {scope_label}.'
        ans_bn = f'{scope_label}-এ বর্তমানে {len(pending_members)} টি অপেক্ষমাণ আবেদন রয়েছে।'
        return tools_used, ans_en, ans_bn, actions

    # 4. Member Statistics
    if any(
        k in q_lower
        for k in (
            'how many',
            'active member',
            'total member',
            'statistics',
            'registered',
            'কতজন সক্রিয়',
            'মোট সদস্য',
        )
    ):
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
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'Open Admin Directory',
                'label_bn': 'সদস্য তালিকা দেখুন',
                'url': '/admin/members',
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
        return tools_used, ans_en, ans_bn, actions

    # 5. Revenue Summary
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
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'Open Finance Desk',
                'label_bn': 'পেমেন্ট ও হিসাব দেখুন',
                'url': '/admin/payments',
            }
        )
        ans_en = f'Total verified revenue collected is ৳{total_rev:,} BDT.'
        ans_bn = f'যাচাইকৃত মোট সংগৃহীত রাজস্বের পরিমাণ ৳{total_rev:,} টাকা।'
        return tools_used, ans_en, ans_bn, actions

    return tools_used, None, None, actions


def _retrieve_live_institutional_intelligence(
    db: Session,
    question: str,
    q_lower: str,
) -> tuple[str | None, str | None, list[dict[str, Any]], list[dict[str, Any]]]:
    """Retrieve live portal content (Circulars, Notices, Events, Grid Circles, Committee, Apply Navigation)."""
    actions: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []

    # 1. Latest Circulars / Specific Circular Lookup ("নতুন circular কী আছে?", "সর্বশেষ circular কী?")
    if any(
        k in q_lower
        for k in (
            'নতুন circular',
            'সর্বশেষ circular',
            'latest circular',
            'recent circular',
            'নতুন সার্কুলার',
            'সর্বশেষ সার্কুলার',
            'circular দেখাও',
            'সার্কুলার দেখাও',
        )
    ):
        circulars = list(
            db.scalars(
                select(Circular)
                .where(Circular.is_published == True)
                .order_by(Circular.published_at.desc(), Circular.id.desc())
                .limit(5)
            ).all()
        )
        kb_circulars = list(
            db.scalars(
                select(KnowledgeDocument)
                .where(KnowledgeDocument.category == 'CIRCULAR', KnowledgeDocument.is_current == True)
                .order_by(KnowledgeDocument.publication_date.desc())
                .limit(3)
            ).all()
        )

        items_bn: list[str] = []
        items_en: list[str] = []
        for idx, c in enumerate(circulars[:3], start=1):
            dt_str = c.published_at.strftime('%d %b %Y') if c.published_at else '2026'
            ref_str = f" ({c.reference_no})" if c.reference_no else ''
            items_bn.append(f"{idx}. {c.title_bn}{ref_str} — {dt_str}")
            items_en.append(f"{idx}. {c.title_en or c.title_bn}{ref_str} — {dt_str}")
            actions.append(
                {
                    'type': 'OPEN_CIRCULAR',
                    'action': 'OPEN_CIRCULAR',
                    'label': f"Open Circular #{c.id}",
                    'label_bn': f"সার্কুলার দেখুন ({c.reference_no or c.id})",
                    'url': f"/circulars/{c.id}",
                }
            )

        for kd in kb_circulars:
            sources.append(
                {
                    'document_id': kd.id,
                    'title': kd.title_en or kd.title_bn,
                    'title_bn': kd.title_bn,
                    'category': kd.category,
                    'version': kd.version,
                    'is_current': kd.is_current,
                    'section': 'Official Circular',
                    'page': 1,
                    'snippet': (kd.cleaned_text or kd.title_bn)[:260],
                    'score': 0.92,
                    'relevance': 0.92,
                    'view_source_url': kd.source_url or f'/api/v1/knowledge/documents/{kd.id}/source',
                }
            )
            if len(items_bn) < 3:
                dt_str = kd.publication_date.strftime('%d %b %Y') if kd.publication_date else '2026'
                idx = len(items_bn) + 1
                items_bn.append(f"{idx}. {kd.title_bn} — {dt_str}")
                items_en.append(f"{idx}. {kd.title_en or kd.title_bn} — {dt_str}")

        actions.append(
            {
                'type': 'OPEN_CIRCULAR',
                'action': 'OPEN_CIRCULAR',
                'label': 'View All Circulars',
                'label_bn': 'সকল সার্কুলার দেখুন',
                'url': '/circulars',
            }
        )
        if items_bn:
            ans_bn = "সর্বশেষ প্রকাশিত অফিসিয়াল সার্কুলারসমূহ:\n\n" + "\n".join(items_bn)
            ans_en = "Latest Official Circulars:\n\n" + "\n".join(items_en)
            return ans_en, ans_bn, sources, actions

    # 2. Grid Circle specific query ("কক্সবাজার Grid Circle-এর তথ্য দাও", "গ্রিড সার্কেল")
    if any(k in q_lower for k in ('grid circle', 'গ্রিড সার্কেল', 'শাখা কমিটি', 'কক্সবাজার', 'চট্টগ্রাম', 'সিলেট', 'রাজশাহী', 'খুলনা', 'কুমিল্লা', 'বগুড়া', 'রংপুর')):
        circles = list(db.scalars(select(Circle).order_by(Circle.id.asc())).all())
        matched_circle: Circle | None = None
        for c in circles:
            for token in ((c.name_bn or '').lower(), (c.name_en or '').lower(), (c.slug or '').lower()):
                if token and len(token) >= 3 and (token in q_lower or any(w in token for w in q_lower.split() if len(w) >= 4)):
                    matched_circle = c
                    break
            if matched_circle:
                break

        if matched_circle:
            mem_cnt = int(
                db.scalar(
                    select(func.count(Member.id)).where(
                        Member.circle_id == matched_circle.id,
                        Member.status == 'ACTIVE',
                    )
                )
                or 0
            )
            slug_or_id = matched_circle.slug or str(matched_circle.id)
            actions.append(
                {
                    'type': 'NAVIGATE',
                    'action': 'NAVIGATE',
                    'label': f"View {matched_circle.name_en or matched_circle.name_bn}",
                    'label_bn': f"{matched_circle.name_bn} পেজ দেখুন",
                    'url': f"/circles/{slug_or_id}",
                }
            )
            ans_bn = (
                f"{matched_circle.name_bn} ({matched_circle.name_en}):\n"
                f"• সক্রিয় নিবন্ধিত সদস্য: {mem_cnt} জন\n"
                f"• বিবরণ: {matched_circle.description_bn or 'পিজিসিবি আঞ্চলিক গ্রিড সার্কেল ও শাখা কমিটি। Provides regional coordination and member services.'}"
            )
            ans_en = (
                f"{matched_circle.name_en or matched_circle.name_bn}:\n"
                f"• Active Registered Members: {mem_cnt}\n"
                f"• Overview: {matched_circle.description_bn or 'Official PGCB Regional Grid Circle and Branch Committee.'}"
            )
            return ans_en, ans_bn, sources, actions

    # 3. Upcoming Events Lookup
    if any(k in q_lower for k in ('আসন্ন ইভেন্ট', 'upcoming event', 'কী কী ইভেন্ট', 'events scheduled')):
        events = list(
            db.scalars(
                select(Event)
                .where(Event.is_published == True)
                .order_by(Event.event_date.desc(), Event.id.desc())
                .limit(4)
            ).all()
        )
        actions.append(
            {
                'type': 'OPEN_EVENT',
                'action': 'OPEN_EVENT',
                'label': 'View Events Calendar',
                'label_bn': 'ইভেন্ট ক্যালেন্ডার দেখুন',
                'url': '/events',
            }
        )
        if events:
            ev_bn = [
                f"{i}. {ev.title_bn} ({ev.event_date.strftime('%d %b %Y') if ev.event_date else 'TBA'}) — {ev.location_bn or 'ঢাকা'}"
                for i, ev in enumerate(events, start=1)
            ]
            ev_en = [
                f"{i}. {ev.title_en or ev.title_bn} ({ev.event_date.strftime('%d %b %Y') if ev.event_date else 'TBA'}) — {ev.location_bn or 'Dhaka'}"
                for i, ev in enumerate(events, start=1)
            ]
            return (
                "Upcoming & Recent PGCB Events:\n\n" + "\n".join(ev_en),
                "পিজিসিবি-এর আসন্ন ও সাম্প্রতিক ইভেন্টসমূহ:\n\n" + "\n".join(ev_bn),
                sources,
                actions,
            )

    return None, None, sources, actions


def _build_contextual_actions(q_lower: str, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build structured navigation/action buttons based on user intent and matched sources."""
    actions: list[dict[str, Any]] = []
    if any(k in q_lower for k in ('apply', 'আবেদন করতে', 'নিবন্ধন', 'membership নিতে', 'নতুন সদস্য')):
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'Apply for Membership',
                'label_bn': 'সদস্যপদ আবেদন করুন',
                'url': '/membership/apply',
            }
        )
    if any(k in q_lower for k in ('renew', 'নবায়ন', 'নবায়ন', 'fee', 'ফি', 'চাঁদা')):
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'Renew Membership in Portal',
                'label_bn': 'পোর্টালে সদস্যপদ নবায়ন করুন',
                'url': '/portal',
            }
        )
    if any(k in q_lower for k in ('circular', 'সার্কুলার')):
        actions.append(
            {
                'type': 'OPEN_CIRCULAR',
                'action': 'OPEN_CIRCULAR',
                'label': 'Browse Official Circulars',
                'label_bn': 'অফিসিয়াল সার্কুলার দেখুন',
                'url': '/circulars',
            }
        )
    if any(k in q_lower for k in ('document', 'guideline', 'constitution', 'ফরম', 'ডকুমেন্ট', 'গঠনতন্ত্র', 'নির্দেশিকা')):
        actions.append(
            {
                'type': 'OPEN_DOCUMENT',
                'action': 'OPEN_DOCUMENT',
                'label': 'Open Documents Repository',
                'label_bn': 'ডকুমেন্ট সংগ্রহশালা খুলুন',
                'url': '/documents',
            }
        )
    if any(k in q_lower for k in ('verify', 'যাচাই', 'qr', 'certificate', 'সনদ')):
        actions.append(
            {
                'type': 'NAVIGATE',
                'action': 'NAVIGATE',
                'label': 'Verify ID / Certificate',
                'label_bn': 'আইডি ও সনদ যাচাই করুন',
                'url': '/verify',
            }
        )
    if any(k in q_lower for k in ('secretariat', 'contact', 'সচিবালয়', 'যোগাযোগ', 'ঠিকানা', 'ফোন')):
        actions.append(
            {
                'type': 'CONTACT_SECRETARIAT',
                'action': 'CONTACT_SECRETARIAT',
                'label': 'Contact Secretariat',
                'label_bn': 'সচিবালয়ে যোগাযোগ করুন',
                'url': '/contact',
            }
        )
    return actions


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
    user_role = canonical_role(user.role) if user else 'PUBLIC'

    # Rate limit check per user or client IP
    client_ip = request.client.host if request.client else 'local'
    rate_key = f"user:{user.id}" if user else f"ip:{client_ip}"
    _check_ai_rate_limit(rate_key)

    effective_lang = _detect_language(question, payload.language)

    # Check current member's ID for cross-member privacy protection
    current_member = db.scalar(select(Member).where(Member.user_id == user.id)) if user else None
    current_member_id_str = current_member.membership_id if current_member else None

    # 1. Prompt-Injection & Cross-Member Privacy Guardrail
    if _detect_prompt_injection(question) or _detect_cross_member_privacy_violation(question, current_member_id_str):
        elapsed_ms = max(1, int((time.perf_counter() - t0) * 1000))
        log_item = AIQueryLog(
            user_id=user.id if user else None,
            user_role=user_role,
            assistant_mode=mode,
            question=_sanitize_pii(question[:500]),
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
        audit(db, user, 'ai.security.prompt_injection_blocked', 'AIQueryLog', 'security')
        db.commit()
        ans_en_sec = (
            'This request was blocked by PGCB AI Security Guardrails. '
            'The assistant cannot bypass access controls, execute raw SQL, expose another member\'s private data, or disclose internal system prompts/credentials.'
        )
        ans_bn_sec = (
            'পিজিসিবি এআই নিরাপত্তা নীতিমালার কারণে এই অনুরোধটি ব্লক করা হয়েছে। '
            'সহকারী কোনো অবস্থাতেই অ্যাক্সেস কন্ট্রোল উপেক্ষা, অন্য সদস্যের ব্যক্তিগত তথ্য প্রকাশ, বা গোপন সিস্টেম তথ্য প্রদান করতে পারে না।'
        )
        return {
            'question': question,
            'mode': mode,
            'language': effective_lang,
            'status': 'BLOCKED_SECURITY',
            'security_flagged': True,
            'unanswered': True,
            'confidence': 0.0,
            'confidence_state': 'LOW',
            'answer': ans_bn_sec if effective_lang == 'bn' else ans_en_sec,
            'answer_en': ans_en_sec,
            'answer_bn': ans_bn_sec,
            'sources': [],
            'tools_used': [],
            'actions': [],
            'action': {
                'type': 'CONTACT_SECRETARIAT',
                'url': '/contact',
                'label': 'Contact Secretariat',
                'label_bn': 'সচিবালয়ে যোগাযোগ করুন',
            },
            'fallback_actions': [
                {'action': 'CONTACT_SECRETARIAT', 'label': 'Contact Secretariat', 'label_bn': 'সচিবালয়ে যোগাযোগ করুন', 'url': '/contact'},
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

    if mode == 'PUBLIC' and any(
        k in q_lower for k in ('my payment history', 'my personal application', 'pending applications from')
    ):
        raise HTTPException(
            status_code=403,
            detail='Public Assistant can only access public institutional information. Please sign in for member or admin tools.',
        )

    # 3. Conversation Memory & Multi-Turn Context Resolution
    conv: AIConversation | None = None
    history_turns: list[dict[str, str]] = []
    augmented_query = question

    if payload.conversation_id is not None:
        conv = db.get(AIConversation, payload.conversation_id)
        if conv and conv.user_id is not None and user is not None and conv.user_id != user.id:
            conv = None

    if conv is None and (payload.conversation_id is not None or payload.session_id):
        now_conv = datetime.utcnow()
        conv = AIConversation(
            user_id=user.id if user else None,
            session_id=(payload.session_id or '').strip()[:120],
            title=question[:120],
            mode=mode,
            language=effective_lang,
            created_at=now_conv,
            updated_at=now_conv,
        )
        db.add(conv)
        db.flush()

    if conv is not None:
        prior_msgs = db.scalars(
            select(AIMessage)
            .where(AIMessage.conversation_id == conv.id)
            .order_by(AIMessage.id.desc())
            .limit(6)
        ).all()
        prior_msgs_asc = list(reversed(prior_msgs))
        for pm in prior_msgs_asc:
            history_turns.append({'role': pm.role, 'content': pm.content})

        # Multi-turn pronoun / follow-up coreference expansion (e.g., "এর জন্য কোন documents লাগবে?")
        follow_up_markers = (
            'এর জন্য',
            'এটার',
            'এটি',
            'সেটা',
            'ঐ',
            'কীভাবে করব',
            'কোন documents লাগবে',
            'for this',
            'for that',
            'about this',
            'what documents',
            'how much is it',
        )
        if prior_msgs_asc and (len(question.split()) <= 8 or any(m in q_lower for m in follow_up_markers)):
            last_user_msgs = [m.content for m in prior_msgs_asc if m.role == 'user']
            if last_user_msgs:
                augmented_query = f"{last_user_msgs[-1]} {question}"

    # 4. Execute Authorized Member / Admin Tools
    tools_used: list[dict[str, Any]] = []
    tool_ans_en: str | None = None
    tool_ans_bn: str | None = None
    structured_actions: list[dict[str, Any]] = []

    if mode == 'MEMBER' and user is not None:
        tools_used, tool_ans_en, tool_ans_bn, structured_actions = _execute_member_tools(db, user, q_lower)
    elif mode == 'ADMIN' and user is not None:
        tools_used, tool_ans_en, tool_ans_bn, structured_actions = _execute_admin_tools(
            db, user, q_lower, requested_circle_id=payload.circle_id
        )

    # 5. Live Institutional Portal Intelligence (Circulars, Grid Circles, Events)
    live_ans_en: str | None = None
    live_ans_bn: str | None = None
    live_sources: list[dict[str, Any]] = []
    if not tool_ans_en:
        live_ans_en, live_ans_bn, live_sources, live_actions = _retrieve_live_institutional_intelligence(
            db, augmented_query, q_lower
        )
        if live_actions:
            structured_actions.extend(live_actions)

    # 6. Knowledge Base Semantic Retrieval
    retrieval_user = None if mode == 'PUBLIC' else user
    kb_search = search_knowledge_base(
        db,
        query=augmented_query,
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
            'relevance': p.get('relevance', p['score']),
            'view_source_url': p['view_source_url'],
        }
        for p in passages
    ]
    if live_sources and not sources:
        sources = live_sources

    if any(k in q_lower for k in ('renew', 'নবায়ন', 'নবায়ন', 'fee', 'ফি', 'pay')):
        q_category = 'RENEWAL_AND_FEES'
    elif any(k in q_lower for k in ('constitution', 'rule', 'গঠনতন্ত্র', 'বিধিমালা')):
        q_category = 'CONSTITUTION_AND_RULES'
    elif any(k in q_lower for k in ('circular', 'সার্কুলার', 'notice', 'নোটিশ')):
        q_category = 'CIRCULARS_AND_NOTICES'
    elif any(k in q_lower for k in ('active member', 'pending', 'how many', 'circle', 'এই মাসে')):
        q_category = 'ADMIN_ANALYTICS'
    elif any(k in q_lower for k in ('certificate', 'verify', 'id card', 'সনদ')):
        q_category = 'VERIFICATION'
    elif any(k in q_lower for k in ('apply', 'eligibility', 'membership', 'সদস্যপদ', 'আবেদন', 'যোগ্যতা')):
        q_category = 'MEMBERSHIP_ELIGIBILITY'
    else:
        q_category = 'GENERAL'

    if not structured_actions:
        structured_actions = _build_contextual_actions(q_lower, sources)

    # 7. Grounded Answer Generation + Confidence State
    if tool_ans_en:
        confidence = 0.96
        unanswered = False
        answer_en = tool_ans_en
        answer_bn = tool_ans_bn or tool_ans_en
        if sources:
            top_src = sources[0]
            answer_en += f"\n\nSource: {top_src['title']} ({top_src['section']}, Page {top_src['page']})"
    elif live_ans_en:
        confidence = 0.93
        unanswered = False
        answer_en = live_ans_en
        answer_bn = live_ans_bn or live_ans_en
    elif sources and sources[0]['score'] >= 0.25:
        top = sources[0]
        confidence = float(top['score'])
        unanswered = False
        citation_str = f"Source: {top['title']} | {top['section']} | Page {top['page']}"
        snippet_clean = _sanitize_pii(top['snippet'])

        cautious_prefix_bn = (
            'আমি যে তথ্য পেয়েছি তা সম্পূর্ণ নিশ্চিত নয়। প্রাসঙ্গিক নথি অনুযায়ী:\n\n'
            if confidence < 0.70
            else ''
        )
        cautious_prefix_en = (
            'Based on the closest available official records:\n\n'
            if confidence < 0.70
            else ''
        )

        answer_en = (
            f"{cautious_prefix_en}According to {top['title']} ({top['section']}, Page {top['page']}): "
            f"{snippet_clean}\n\n[{citation_str}]"
        )
        answer_bn = (
            f"{cautious_prefix_bn}{top['title_bn']} ({top['section']}, পৃষ্ঠা {top['page']}) অনুযায়ী:\n"
            f"{snippet_clean}\n\nসূত্র: {top['title_bn']} — {top['section']}, পৃষ্ঠা {top['page']}"
        )

        provider = get_ai_provider()
        context_block = '\n\n'.join(
            f"[{s['title']} | {s['section']} | Page {s['page']} | Version {s['version']}]: {s['snippet']}"
            for s in sources[:3]
        )
        synthesized = await provider.generate(
            question=question,
            context=context_block,
            language=effective_lang,
            history=history_turns,
            system_prompt=GROUNDED_SYSTEM_PROMPT,
        )
        if synthesized:
            synthesized_clean = _sanitize_pii(synthesized)
            if effective_lang == 'bn':
                answer_bn = f"{cautious_prefix_bn}{synthesized_clean}\n\nসূত্র: {top['title_bn']} — {top['section']}, পৃষ্ঠা {top['page']}"
            else:
                answer_en = f"{cautious_prefix_en}{synthesized_clean} [{citation_str}]"
    else:
        confidence = 0.0
        unanswered = True
        sources = []
        answer_en = (
            "I couldn't find an authoritative PGCB document supporting that answer in the knowledge base.\n\n"
            "You may:\n"
            "• View Circulars (/circulars)\n"
            "• Browse Documents (/documents)\n"
            "• Contact the Secretariat (/contact)"
        )
        answer_bn = (
            "এই বিষয়ে নির্ভরযোগ্য PGCB তথ্য আমার knowledge base-এ পাওয়া যায়নি।\n\n"
            "আপনি চাইলে:\n"
            "• Circulars দেখুন (/circulars)\n"
            "• Documents দেখুন (/documents)\n"
            "• Secretariat-এর সাথে যোগাযোগ করুন (/contact)"
        )

    confidence_state = _compute_confidence_state(confidence, unanswered)

    fallback_actions = [
        {
            'action': 'OPEN_CIRCULAR',
            'label': 'View Circulars',
            'label_bn': 'Circulars দেখুন',
            'url': '/circulars',
        },
        {
            'action': 'OPEN_DOCUMENT',
            'label': 'Browse Documents',
            'label_bn': 'Documents দেখুন',
            'url': '/documents',
        },
        {
            'action': 'SEARCH_DOCUMENTS',
            'label': 'Search Documents',
            'label_bn': 'নথিপত্র অনুসন্ধান করুন',
            'url': '/search',
        },
        {
            'action': 'SUBMIT_INQUIRY',
            'label': 'Submit Inquiry',
            'label_bn': 'অনুসন্ধান জমা দিন',
            'url': '/contact#inquiry',
        },
        {
            'action': 'CONTACT_SECRETARIAT',
            'label': 'Contact Secretariat',
            'label_bn': 'Secretariat-এর সাথে যোগাযোগ করুন',
            'url': '/contact',
        },
    ]

    primary_answer = answer_bn if effective_lang == 'bn' else answer_en

    # Persist conversation turns if conversation tracking is active
    if conv is not None:
        now_msg = datetime.utcnow()
        user_msg = AIMessage(
            conversation_id=conv.id,
            role='user',
            content=_sanitize_pii(question),
            content_bn=_sanitize_pii(question),
            content_en=_sanitize_pii(question),
            intent=q_category,
            created_at=now_msg,
        )
        assistant_msg = AIMessage(
            conversation_id=conv.id,
            role='assistant',
            content=primary_answer,
            content_bn=answer_bn,
            content_en=answer_en,
            intent=q_category,
            confidence=confidence,
            confidence_state=confidence_state,
            sources=json.dumps(sources, ensure_ascii=False),
            tools_used=json.dumps(tools_used, ensure_ascii=False),
            actions=json.dumps(structured_actions, ensure_ascii=False),
            created_at=now_msg,
        )
        conv.updated_at = now_msg
        db.add(user_msg)
        db.add(assistant_msg)

    elapsed_ms = max(1, int((time.perf_counter() - t0) * 1000))
    tokens_est = len(question.split()) + len(answer_en.split())
    cost_est = round(tokens_est * 0.000002, 6)

    log_entry = AIQueryLog(
        user_id=user.id if user else None,
        user_role=user_role,
        assistant_mode=mode,
        question=_sanitize_pii(question[:500]),
        question_category=q_category,
        answer_preview=_sanitize_pii(primary_answer[:480]),
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
        audit(db, user, 'ai.tool.executed', 'AIQueryLog', mode)
    db.commit()

    primary_action = structured_actions[0] if structured_actions else (fallback_actions[0] if unanswered else None)

    return {
        'conversation_id': conv.id if conv else None,
        'question': question,
        'mode': mode,
        'role': user_role,
        'language': effective_lang,
        'intent': q_category,
        'status': 'UNANSWERED' if unanswered else 'ANSWERED',
        'unanswered': unanswered,
        'security_flagged': False,
        'confidence': confidence,
        'confidence_state': confidence_state,
        'answer': primary_answer,
        'answer_en': answer_en,
        'answer_bn': answer_bn,
        'sources': sources,
        'tools_used': tools_used,
        'action': primary_action,
        'actions': structured_actions,
        'fallback_actions': fallback_actions if unanswered else [],
        'response_time_ms': elapsed_ms,
    }


@router.post('/admin/ai/generate-faqs')
@router.post('/admin/ai/generate-faq', include_in_schema=False)
def generate_smart_faqs(
    payload: GenerateFAQRequest,
    user: User = Depends(require_permission('content.write')),
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

    audit(db, user, 'ai.faq.generate_drafts', 'KnowledgeDocument', doc.id)
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
    user: User = Depends(require_permission('content.read')),
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
    user: User = Depends(require_permission('content.write')),
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
        if target_status == 'PUBLISHED' and not has_permission(user.role, 'content.publish'):
            raise HTTPException(status_code=403, detail='Only authorized publishers/admins can publish FAQs')
        faq.status = target_status
        if target_status in ('APPROVED', 'PUBLISHED'):
            faq.approved_by = user.id
        if target_status == 'PUBLISHED':
            faq.published_at = datetime.utcnow()

    audit(db, user, 'ai.faq.update', 'KnowledgeFAQ', faq.id)
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
    user: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    title_bn = payload.title_bn.strip()
    title_en = (payload.title_en or '').strip()
    content_bn = payload.content_bn.strip()
    content_en = (payload.content_en or '').strip()

    improved_bn = (
        f"অফিসিয়াল বিজ্ঞপ্তি ({payload.entity_type.upper()}): {content_bn}"
        if content_bn and not content_bn.startswith('অফিসিয়াল')
        else (content_bn or f"অফিসিয়াল বিজ্ঞপ্তি: {title_bn}")
    )
    improved_en = (
        f"Official {payload.entity_type.title()} Notice: {content_en or title_en or title_bn}"
    )
    summary_bn = (content_bn[:180] + '...') if len(content_bn) > 180 else (content_bn or title_bn)
    summary_en = (content_en[:180] + '...') if len(content_en) > 180 else (content_en or title_en or title_bn)

    slug_words = re.findall(r'[a-z0-9]+', (title_en or 'pgcb-official-notice').lower())
    suggested_slug = '-'.join(slug_words[:8]) or 'pgcb-official-update'

    audit(db, user, 'ai.cms.content_assist', payload.entity_type, 'draft')
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
                'bn_to_en': content_en or f'[Official English Translation] {title_en or title_bn}: {summary_en}',
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
                'sms_bn': f"PGCB {payload.entity_type}: {title_bn[:60]} - বিস্তারিত পোর্টালে দেখুন।",
            },
        },
    }


@router.get('/admin/ai/analytics')
def get_ai_usage_analytics(
    user: User = Depends(require_permission('analytics.read')),
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
    user: User = Depends(require_permission('analytics.read')),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    role = canonical_role(user.role)
    circle_filter = get_admin_circle_scope(user, db) if role == 'CIRCLE_ADMIN' else None

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
    apps_month_stmt = select(func.count(Member.id)).where(
        Member.created_at >= month_start
    )

    if circle_filter is not None and circle_filter != -1:
        members_stmt = members_stmt.where(Member.circle_id == circle_filter)
        active_stmt = active_stmt.where(Member.circle_id == circle_filter)
        pending_stmt = pending_stmt.where(Member.circle_id == circle_filter)
        expiring_stmt = expiring_stmt.where(Member.circle_id == circle_filter)
        apps_month_stmt = apps_month_stmt.where(Member.circle_id == circle_filter)

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
        if circle_filter is not None and circle_filter != -1 and int(c.id) != int(circle_filter):
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
                'circle_code': getattr(c, 'circle_code', None) or f'CIRCLE-{c.id:02d}',
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
