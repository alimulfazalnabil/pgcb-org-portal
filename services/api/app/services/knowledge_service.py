from __future__ import annotations

import hashlib
import io
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import canonical_role, get_admin_circle_scope
from app.models import (
    Circular,
    Document,
    Event,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeFAQ,
    Notice,
    User,
)

EMBEDDING_DIM = 64

# Domain concept expansion for bilingual semantic matching (English <-> Bangla + synonyms)
SEMANTIC_SYNONYM_GROUPS: list[set[str]] = [
    {
        'renew', 'renewal', 'renewing', 'extend', 'validity', 'expire', 'expiry', 'annual',
        'নবায়ন', 'নবায়ন', 'মেয়াদ', 'মেয়াদ', 'বার্ষিক',
    },
    {
        'fee', 'fees', 'pay', 'payment', 'cost', 'price', 'amount', 'charge', 'bdt', 'taka',
        'ফি', 'চাঁদা', 'টাকা', 'পেমেন্ট', 'কত',
    },
    {
        'member', 'membership', 'join', 'apply', 'application', 'register', 'registration', 'eligibility',
        'সদস্য', 'সদস্যপদ', 'আবেদন', 'নিবন্ধন', 'যোগ্যতা',
    },
    {
        'constitution', 'rule', 'rules', 'regulation', 'regulations', 'bylaw', 'guideline', 'guidelines',
        'গঠনতন্ত্র', 'বিধিমালা', 'নীতিমালা', 'নিয়মাবলী', 'নিয়মাবলী', 'নির্দেশিকা',
    },
    {
        'certificate', 'card', 'id', 'verify', 'verification', 'qr', 'digital',
        'সনদ', 'পরিচয়পত্র', 'পরিচয়পত্র', 'আইডি', 'যাচাই', 'ডিজিটাল',
    },
    {
        'circle', 'circles', 'grid', 'dhaka', 'chattogram', 'division', 'regional',
        'সার্কেল', 'গ্রিড', 'ঢাকা', 'চট্টগ্রাম', 'বিভাগ',
    },
    {
        'welfare', 'benefit', 'benefits', 'fund', 'support', 'voting', 'vote',
        'কল্যাণ', 'তহবিল', 'সুবিধা', 'ভোটাধিকার',
    },
]

STOPWORDS = {
    'the', 'is', 'are', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'and', 'or', 'how', 'do', 'i',
    'need', 'much', 'my', 'what', 'can', 'from', 'with', 'by', 'at', 'be', 'this', 'that', 'it',
    'কিভাবে', 'কীভাবে', 'কী', 'কি', 'জন্য', 'করতে', 'চাই', 'করব', 'হলে',
}


def extract_text_from_file_bytes(content: bytes, filename: str = '') -> str:
    fname = (filename or '').lower()

    # 1. DOCX extraction (ZIP archive with word/document.xml)
    if fname.endswith('.docx') or content[:4] == b'PK\x03\x04':
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                if 'word/document.xml' in zf.namelist():
                    xml_bytes = zf.read('word/document.xml')
                    root = ET.fromstring(xml_bytes)
                    texts: list[str] = []
                    for elem in root.iter():
                        if elem.tag.endswith('}t') and elem.text:
                            texts.append(elem.text)
                        elif elem.tag.endswith('}p'):
                            texts.append('\n')
                    extracted = ''.join(texts).strip()
                    if extracted:
                        return extracted
        except Exception:
            pass

    # 2. PDF extraction
    if fname.endswith('.pdf') or content.startswith(b'%PDF'):
        raw_str = content.decode('latin-1', errors='ignore')
        # Extract literal strings inside parentheses (...) used by PDF text operators
        literals = re.findall(r'\(([^\(\)]{2,400})\)', raw_str)
        cleaned_literals = [
            lit for lit in literals
            if not lit.startswith(('PDF-', 'Identity', 'Adobe'))
            and any(ch.isalpha() for ch in lit)
        ]
        if cleaned_literals:
            return '\n'.join(cleaned_literals)

    # 3. Plain UTF-8 / fallback text
    return content.decode('utf-8', errors='ignore').strip()


def clean_text(raw: str | None) -> str:
    if not raw:
        return ''
    text = raw.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def compute_semantic_tokens(text: str) -> list[str]:
    lowered = text.lower()
    raw_words = re.findall(r'[\w\u0980-\u09FF]+', lowered)
    tokens: list[str] = []
    seen: set[str] = set()

    for w in raw_words:
        if len(w) < 2 or w in STOPWORDS:
            continue
        if w not in seen:
            seen.add(w)
            tokens.append(w)
        # Stem common suffixes
        for suffix in ('ing', 'ed', 'es', 's', 'tion'):
            if len(w) > len(suffix) + 3 and w.endswith(suffix):
                stem = w[:-len(suffix)]
                if stem not in seen:
                    seen.add(stem)
                    tokens.append(stem)

    # Synonym concept expansion
    token_set = set(tokens)
    for idx, group in enumerate(SEMANTIC_SYNONYM_GROUPS):
        if token_set & group:
            concept_tag = f'__concept_{idx}__'
            if concept_tag not in seen:
                seen.add(concept_tag)
                tokens.append(concept_tag)
            for syn in group:
                if syn not in seen:
                    seen.add(syn)
                    tokens.append(syn)

    return tokens


def compute_embedding_vector(text: str) -> list[float]:
    import os
    import urllib.request

    openai_key = os.getenv('OPENAI_API_KEY', '').strip()
    if openai_key and os.getenv('AI_USE_OPENAI_EMBEDDINGS', '').lower() == 'true':
        try:
            emb_model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small').strip()
            req = urllib.request.Request(
                'https://api.openai.com/v1/embeddings',
                data=json.dumps({
                    'input': text[:4000],
                    'model': emb_model,
                    'dimensions': EMBEDDING_DIM,
                }).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {openai_key}',
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                payload = json.loads(resp.read().decode('utf-8'))
            data = payload.get('data') or []
            if data and isinstance(data[0].get('embedding'), list):
                return [round(float(x), 6) for x in data[0]['embedding'][:EMBEDDING_DIM]]
        except Exception:
            pass

    tokens = compute_semantic_tokens(text)
    vec = [0.0] * EMBEDDING_DIM
    if not tokens:
        return vec

    for tok in tokens:
        weight = 2.5 if tok.startswith('__concept_') else 1.0
        digest = hashlib.sha256(tok.encode('utf-8')).digest()
        bucket = digest[0] % EMBEDDING_DIM
        sign = 1.0 if (digest[1] % 2 == 0) else -1.0
        vec[bucket] += sign * weight

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [round(v / norm, 6) for v in vec]
    return vec


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(0.0, min(1.0, dot))


def chunk_document_text(
    cleaned_text: str,
    sections: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []

    if sections:
        for idx, sec in enumerate(sections):
            content = clean_text(sec.get('content') or sec.get('text') or '')
            if not content:
                continue
            chunks.append(
                {
                    'chunk_index': idx,
                    'section_title': sec.get('section') or sec.get('section_title') or f'Section {idx + 1}',
                    'page_number': int(sec.get('page') or sec.get('page_number') or (idx + 1)),
                    'content': content,
                }
            )
        if chunks:
            return chunks

    if not cleaned_text:
        return []

    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', cleaned_text) if p.strip()]
    current_section = 'Section 1: General Provisions'
    current_page = 1

    for idx, para in enumerate(paragraphs):
        page_match = re.search(r'\[(?:Page|পৃষ্ঠা)\s*(\d+)\]', para, flags=re.IGNORECASE)
        if page_match:
            current_page = int(page_match.group(1))
            para = re.sub(r'\[(?:Page|পৃষ্ঠা)\s*\d+\]', '', para, flags=re.IGNORECASE).strip()

        sec_match = re.match(r'^((?:Section|ধারা|অধ্যায়)\s+[^\n:]{1,80})(?:[:\-]\s*(.*))?$', para, flags=re.IGNORECASE | re.DOTALL)
        if sec_match:
            header_line = para.split('\n', 1)[0].strip()
            current_section = header_line[:160]

        if not para:
            continue

        chunks.append(
            {
                'chunk_index': idx,
                'section_title': current_section,
                'page_number': current_page,
                'content': para,
            }
        )

    return chunks


def ingest_knowledge_document(
    db: Session,
    *,
    title_bn: str,
    title_en: str | None = None,
    category: str = 'MEMBERSHIP_GUIDELINES',
    version: str = '2026.1',
    raw_text: str = '',
    sections: list[dict[str, Any]] | None = None,
    source_type: str = 'PDF',
    source_url: str | None = None,
    source_entity_id: int | None = None,
    access_level: str = 'PUBLIC',
    circle_id: int | None = None,
    author: str = 'PGCB Secretariat',
    approval_status: str = 'PUBLISHED',
    is_current: bool = True,
    supersedes_id: int | None = None,
    publication_date: datetime | None = None,
    effective_date: datetime | None = None,
    created_by: int | None = None,
) -> KnowledgeDocument:
    now = datetime.utcnow()
    cleaned = clean_text(raw_text)
    if not cleaned and sections:
        cleaned = '\n\n'.join(
            f"{s.get('section') or s.get('section_title') or 'Section'}: {s.get('content') or s.get('text') or ''}"
            for s in sections
        )

    doc = KnowledgeDocument(
        title_bn=title_bn,
        title_en=title_en or title_bn,
        category=category.upper(),
        version=version,
        is_current=is_current,
        supersedes_id=supersedes_id,
        publication_date=publication_date or now,
        effective_date=effective_date or publication_date or now,
        author=author,
        approval_status=approval_status.upper(),
        source_type=source_type.upper(),
        source_url=source_url,
        source_entity_id=source_entity_id,
        access_level=access_level.upper(),
        circle_id=circle_id,
        raw_text=raw_text or cleaned,
        cleaned_text=cleaned,
        chunk_count=0,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    db.add(doc)
    db.flush()

    if not doc.source_url:
        doc.source_url = f'/api/v1/knowledge/documents/{doc.id}/source'

    # Handle version superseding
    if supersedes_id:
        old_doc = db.get(KnowledgeDocument, supersedes_id)
        if old_doc and old_doc.id != doc.id:
            old_doc.is_current = False
            old_doc.approval_status = 'SUPERSEDED'
            old_doc.superseded_by_id = doc.id
            old_doc.updated_at = now

    chunk_dicts = chunk_document_text(cleaned, sections=sections)
    for ch in chunk_dicts:
        combined_for_embed = f"{doc.title_bn} {doc.title_en or ''} {ch['section_title']} {ch['content']}"
        tokens = compute_semantic_tokens(combined_for_embed)
        embedding = compute_embedding_vector(combined_for_embed)
        db.add(
            KnowledgeChunk(
                document_id=doc.id,
                chunk_index=ch['chunk_index'],
                section_title=ch['section_title'],
                page_number=ch['page_number'],
                content=ch['content'],
                tokens_json=json.dumps(tokens, ensure_ascii=False),
                embedding_json=json.dumps(embedding),
                created_at=now,
            )
        )

    doc.chunk_count = len(chunk_dicts)
    db.commit()
    db.refresh(doc)
    return doc


def can_user_access_document(user: User | None, doc: KnowledgeDocument, db: Session | None = None) -> bool:
    level = (doc.access_level or 'PUBLIC').upper()

    if user is None:
        return level == 'PUBLIC'

    role = canonical_role(user.role)
    if role == 'SUPER_ADMIN':
        return True

    if role in ('CENTRAL_ADMIN', 'ADMIN', 'SECRETARIAT_ADMIN', 'FINANCE_OFFICER', 'MEMBERSHIP_OFFICER', 'CONTENT_PUBLISHER', 'AUDITOR'):
        return level in ('PUBLIC', 'MEMBER', 'CIRCLE_ADMIN', 'CENTRAL_ADMIN')

    if role == 'CIRCLE_ADMIN':
        if level in ('PUBLIC', 'MEMBER'):
            return True
        if level == 'CIRCLE_ADMIN':
            if doc.circle_id is None:
                return True
            scoped_cid = get_admin_circle_scope(user, db) if db is not None else getattr(user, 'circle_id', None)
            return scoped_cid is not None and scoped_cid != -1 and int(doc.circle_id) == int(scoped_cid)
        return False

    # Regular authenticated MEMBER / CONTENT_EDITOR / etc.
    return level in ('PUBLIC', 'MEMBER')


def ensure_default_knowledge_seeded(db: Session) -> None:
    count = db.scalar(select(KnowledgeDocument.id).limit(1))
    if count is not None:
        return

    # 1. Historical 2025 Membership Rules (to demonstrate version superseding)
    rules_2025 = ingest_knowledge_document(
        db,
        title_bn='সদস্যপদ বিধিমালা ২০২৫ (Membership Rules 2025)',
        title_en='Membership Rules 2025',
        category='MEMBERSHIP_GUIDELINES',
        version='2025.1',
        source_type='PDF',
        access_level='PUBLIC',
        approval_status='SUPERSEDED',
        is_current=False,
        publication_date=datetime(2025, 1, 15),
        sections=[
            {
                'section': 'Section 4.1: Annual Renewal (2025)',
                'page': 12,
                'content': (
                    'Under the 2025 Membership Rules, the annual membership renewal fee was 1,500 BDT per year. '
                    'This 2025 provision has been superseded by the Membership Guidelines 2026.'
                ),
            }
        ],
    )

    # 2. Current Authoritative Membership Guidelines 2026 (supersedes 2025)
    ingest_knowledge_document(
        db,
        title_bn='সদস্যপদ নির্দেশিকা ২০২৬ (Membership Guidelines 2026)',
        title_en='Membership Guidelines 2026',
        category='MEMBERSHIP_GUIDELINES',
        version='2026.1',
        source_type='PDF',
        access_level='PUBLIC',
        approval_status='PUBLISHED',
        is_current=True,
        supersedes_id=rules_2025.id,
        publication_date=datetime(2026, 1, 10),
        sections=[
            {
                'section': 'Section 2.1: Eligibility & Registration',
                'page': 5,
                'content': (
                    'All Diploma Engineers serving in Power Grid Bangladesh PLC (PGCB) as Sub-Assistant Engineer '
                    'or above are eligible for membership. Applicants must submit their Employee ID, Grid Circle, '
                    'Diploma Certificate, NID, and passport photograph via the online portal.'
                ),
            },
            {
                'section': 'Section 4.2: Membership Renewal & Fee Structure',
                'page': 14,
                'content': (
                    'According to the current Membership Guidelines 2026, members may renew their membership online '
                    'through the Member Portal. Standard renewal fees are: 1-Year Renewal: 2,000 BDT (RENEWAL_1YR), '
                    '2-Year Renewal: 4,000 BDT (RENEWAL_2YR), and Lifetime Membership: 10,000 BDT (LIFE). '
                    'Automated renewal reminders are sent at 60 days, 30 days, 7 days, and on the day of expiry.'
                ),
            },
            {
                'section': 'Section 6.1: Digital Membership Card & Certificate Verification',
                'page': 21,
                'content': (
                    'Every active member receives a cryptographically verifiable Digital ID Card (PGD-YYYY-XXXX) '
                    'and Membership Certificate with QR verification. No sensitive PII such as NID is embedded in public QR codes.'
                ),
            },
        ],
    )

    # 3. Circular 04/2026
    ingest_knowledge_document(
        db,
        title_bn='সার্কুলার ০৪/২০২৬: অনলাইন সদস্যপদ নবায়ন ও ডিজিটাল রসিদ',
        title_en='Circular 04/2026: Online Membership Renewal & Digital Receipt',
        category='CIRCULAR',
        version='2026.04',
        source_type='PDF',
        access_level='PUBLIC',
        approval_status='PUBLISHED',
        is_current=True,
        publication_date=datetime(2026, 2, 1),
        sections=[
            {
                'section': 'Section 2: Payment Verification & Official Receipt',
                'page': 2,
                'content': (
                    'Circular 04/2026 mandates that all membership renewal payments (1-year 2,000 BDT, 2-year 4,000 BDT, '
                    'or Lifetime 10,000 BDT) are verified server-side before activating membership validity and issuing '
                    'an official PDF receipt.'
                ),
            }
        ],
    )

    # 4. PGCB Association Constitution 2026
    ingest_knowledge_document(
        db,
        title_bn='পাওয়ার গ্রিড প্রকৌশলী সমিতির গঠনতন্ত্র ২০২৬ (PGCB Constitution 2026)',
        title_en='PGCB Engineers Association Constitution 2026',
        category='CONSTITUTION',
        version='2026.1',
        source_type='PDF',
        access_level='PUBLIC',
        approval_status='PUBLISHED',
        is_current=True,
        publication_date=datetime(2026, 1, 1),
        sections=[
            {
                'section': 'Article 1: Organization Identity & 9 Grid Circles',
                'page': 1,
                'content': (
                    'The PGCB Diploma Engineers Association is the official professional organization of engineers '
                    'working at Power Grid Bangladesh PLC, structured across the Central Executive Committee and '
                    '9 official Grid Circles (Circle 01 through Circle 09).'
                ),
            },
            {
                'section': 'Article 8: Member Rights & Welfare Fund',
                'page': 9,
                'content': (
                    'Active members enjoy full voting rights in Central and Circle elections, participation in the '
                    'Annual General Meeting (AGM), technical publications, and emergency welfare fund assistance.'
                ),
            },
        ],
    )


def search_knowledge_base(
    db: Session,
    *,
    query: str,
    user: User | None = None,
    category: str | None = None,
    document_type: str | None = None,
    year: int | None = None,
    circle_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    include_historical: bool = False,
    limit: int = 8,
) -> dict[str, Any]:
    ensure_default_knowledge_seeded(db)

    q_clean = clean_text(query)
    q_tokens = set(compute_semantic_tokens(q_clean))
    q_vec = compute_embedding_vector(q_clean)

    stmt = select(KnowledgeDocument)
    if not include_historical:
        stmt = stmt.where(
            KnowledgeDocument.is_current == True,
            KnowledgeDocument.approval_status == 'PUBLISHED',
        )
    else:
        stmt = stmt.where(KnowledgeDocument.approval_status.in_(['PUBLISHED', 'SUPERSEDED']))

    effective_cat = (category or document_type or '').strip().upper()
    if effective_cat:
        stmt = stmt.where(KnowledgeDocument.category == effective_cat)

    if circle_id is not None:
        stmt = stmt.where(KnowledgeDocument.circle_id == circle_id)

    all_docs = db.scalars(stmt).all()

    # Filter by RBAC access level & date/year filters
    authorized_docs: dict[int, KnowledgeDocument] = {}
    for doc in all_docs:
        if not can_user_access_document(user, doc, db=db):
            continue
        if year is not None and doc.publication_date and doc.publication_date.year != int(year):
            continue
        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from)
                if doc.publication_date and doc.publication_date < dt_from:
                    continue
            except ValueError:
                pass
        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to)
                if doc.publication_date and doc.publication_date > dt_to:
                    continue
            except ValueError:
                pass
        authorized_docs[doc.id] = doc

    if not authorized_docs:
        return {'query': query, 'documents_searched': 0, 'count': 0, 'results': []}

    chunks = db.scalars(
        select(KnowledgeChunk).where(KnowledgeChunk.document_id.in_(list(authorized_docs.keys())))
    ).all()

    scored_results: list[dict[str, Any]] = []
    q_lower = q_clean.lower()

    for ch in chunks:
        doc = authorized_docs[ch.document_id]
        try:
            ch_tokens = set(json.loads(ch.tokens_json or '[]'))
        except Exception:
            ch_tokens = set(compute_semantic_tokens(ch.content))

        try:
            ch_vec = json.loads(ch.embedding_json or '[]')
        except Exception:
            ch_vec = compute_embedding_vector(ch.content)

        # Lexical + Concept overlap score
        overlap = q_tokens & ch_tokens
        concept_overlap = {t for t in overlap if t.startswith('__concept_')}
        word_overlap = overlap - concept_overlap

        lexical_score = 0.0
        if q_tokens:
            lexical_score = (len(word_overlap) * 1.0 + len(concept_overlap) * 2.5) / max(len(q_tokens), 1)

        # Cosine vector similarity
        vec_score = cosine_similarity(q_vec, ch_vec)

        # Direct substring boost
        substring_boost = 0.25 if (len(q_lower) >= 3 and q_lower in ch.content.lower()) else 0.0

        # Authoritative current version boost
        version_multiplier = 1.15 if doc.is_current else 0.65

        raw_score = (lexical_score * 0.55 + vec_score * 0.45 + substring_boost) * version_multiplier
        if raw_score < 0.12 and not overlap and substring_boost == 0.0:
            continue

        score = round(min(0.99, raw_score), 4)
        scored_results.append(
            {
                'chunk_id': ch.id,
                'document_id': doc.id,
                'title': doc.title_en or doc.title_bn,
                'title_bn': doc.title_bn,
                'title_en': doc.title_en or doc.title_bn,
                'category': doc.category,
                'document_type': doc.source_type,
                'version': doc.version,
                'is_current': doc.is_current,
                'approval_status': doc.approval_status,
                'superseded_by_id': doc.superseded_by_id,
                'section': ch.section_title or 'Section 1',
                'page': ch.page_number,
                'snippet': ch.content,
                'score': score,
                'relevance': score,
                'access_level': doc.access_level,
                'circle_id': doc.circle_id,
                'publication_date': doc.publication_date.isoformat() if doc.publication_date else None,
                'view_source_url': doc.source_url or f'/api/v1/knowledge/documents/{doc.id}/source',
            }
        )

    scored_results.sort(key=lambda r: (r['is_current'], r['score']), reverse=True)
    top_results = scored_results[:limit]
    if include_historical and not any(not r['is_current'] for r in top_results):
        hist_candidates = [r for r in scored_results if not r['is_current']]
        if hist_candidates:
            hist_candidates.sort(key=lambda r: r['score'], reverse=True)
            if len(top_results) >= limit:
                top_results[-1] = hist_candidates[0]
            else:
                top_results.append(hist_candidates[0])

    return {
        'query': query,
        'documents_searched': len(authorized_docs),
        'count': len(top_results),
        'results': top_results,
    }
