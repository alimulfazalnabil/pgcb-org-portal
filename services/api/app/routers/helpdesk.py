from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Circle, Circular, CommitteeMember, Document, Event, Notice
from app.services.receipt_service import get_fee_schedule

router = APIRouter(prefix='/public/helpdesk', tags=['helpdesk'])


class HelpdeskAskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    language: str = Field(default='bn', pattern=r'^(bn|en)$')


HELPDESK_TOPICS: list[dict[str, Any]] = [
    {
        'id': 'membership_application',
        'title_bn': 'সদস্যপদ আবেদনের নিয়মাবলী',
        'title_en': 'How to Apply for Membership',
        'keywords': [
            'apply', 'application', 'membership', 'join', 'register', 'eligibility',
            'সদস্য', 'সদস্যপদ', 'আবেদন', 'নিবন্ধন', 'যোগ্যতা', 'কিভাবে সদস্য',
        ],
        'answer_bn': (
            'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির সদস্যপদের জন্য অনলাইনে `/apply` বা `/register` পেজে আবেদন করুন। '
            'প্রয়োজনীয় যোগ্যতা ও কাগজপত্র:\n'
            '১. পিজিসিবি-তে কর্মরত ডিপ্লোমা প্রকৌশলী (উপ-সহকারী প্রকৌশলী বা তদূর্ধ্ব)\n'
            '২. অফিসিয়াল পিজিসিবি এমপ্লয়ি আইডি ও গ্রিড সার্কেল নির্বাচন\n'
            '৩. ডিপ্লোমা-ইন-ইঞ্জিনিয়ারিং সনদ, পিজিসিবি আইডি কার্ড ও পাসপোর্ট সাইজ ছবি আপলোড\n'
            '৪. প্রাথমিক যাচাই শেষে নির্ধারিত ফি পরিশোধের পর সদস্য আইডি (`PGD-YYYY-NNNN`), ডিজিটাল আইডি কার্ড ও সনদপত্র স্বয়ংক্রিয়ভাবে ইস্যু হবে।'
        ),
        'answer_en': (
            'To apply for membership in the PGCB Diploma Engineers Association:\n'
            '1. Visit `/apply` or `/register` and complete your engineer profile.\n'
            '2. Provide your PGCB Employee ID, Grid Circle, and Diploma institution details.\n'
            '3. Upload your Diploma Certificate, PGCB Employee ID Card, and passport photo.\n'
            '4. After eligibility review and official fee payment, your Membership ID (`PGD-YYYY-NNNN`), Digital ID Card, and Certificate are issued automatically.'
        ),
        'suggested_links': [
            {'label_bn': 'সদস্যপদ আবেদন', 'label_en': 'Apply for Membership', 'url': '/apply'},
            {'label_bn': 'সদস্য পোর্টাল', 'label_en': 'Member Portal', 'url': '/portal'},
        ],
    },
    {
        'id': 'membership_fees',
        'title_bn': 'সদস্যপদ ফি ও নবায়ন চার্জ',
        'title_en': 'Membership Fees & Renewal Schedule',
        'keywords': [
            'fee', 'fees', 'cost', 'price', 'renewal', 'amount', 'subscription', 'bdt',
            'ফি', 'চাঁদা', 'নবায়ন', 'কত টাকা', 'বার্ষিক ফি', 'আজীবন',
        ],
        'answer_bn': (
            'অফিসিয়াল সদস্যপদ ফি কাঠামো (BDT):\n'
            '• নতুন সদস্যপদ (ভর্তি ফি ১,০০০ + বার্ষিক চাঁদা ১,৫০০): মোট ২,৫০০ টাকা\n'
            '• বার্ষিক সদস্যপদ নবায়ন (বিলম্ব ফি ছাড়া): ১,৫০০ টাকা\n'
            '• কল্যাণ তহবিল ও স্ট্যান্ডার্ড বার্ষিক চাঁদা বিকল্প: ৫০০ / ১,০০০ / ২,০০০ টাকা\n'
            '• আজীবন সদস্যপদ (এককালীন): ১০,০০০ টাকা\n'
            '• বিলম্ব নবায়ন জরিমানা (মেয়াদোত্তীর্ণের পরে): প্রতি মাসে ১০০ টাকা (সর্বোচ্চ ৫০০ টাকা)'
        ),
        'answer_en': (
            'Official PGCB Association Membership Fee Schedule (BDT):\n'
            '• New Membership (Admission 1,000 + Annual Subscription 1,500): 2,500 BDT\n'
            '• Annual Renewal (on time): 1,500 BDT\n'
            '• Welfare / Standard Tiers: 500 / 1,000 / 2,000 BDT\n'
            '• Lifetime Membership: 10,000 BDT\n'
            '• Late Renewal Surcharge: 100 BDT/month after expiry (capped at 500 BDT)'
        ),
        'suggested_links': [
            {'label_bn': 'পেমেন্ট পোর্টাল', 'label_en': 'Payment Portal', 'url': '/portal/payments'},
        ],
    },
    {
        'id': 'payment_instructions',
        'title_bn': 'পেমেন্ট পদ্ধতি ও ডিজিটাল রসিদ',
        'title_en': 'Payment Methods & Official Receipts',
        'keywords': [
            'payment', 'pay', 'bkash', 'nagad', 'sslcommerz', 'bank', 'receipt', 'invoice', 'transaction',
            'পেমেন্ট', 'বিকাশ', 'নগদ', 'ব্যাংক', 'রসিদ', 'ট্রানজেকশন',
        ],
        'answer_bn': (
            'আপনি সদস্য পোর্টালের `/portal/payments` থেকে SSLCommerz, bKash, Nagad অথবা ব্যাংক ট্রান্সফারের মাধ্যমে ফি পরিশোধ করতে পারেন। '
            'সার্ভার-টু-সার্ভার পেমেন্ট যাচাই সম্পন্ন হলে সাথে সাথে কিউআর কোডযুক্ত অফিসিয়াল রসিদ (`PGCB-RCP-YYYY-NNNNNN`) এবং ৩০০-ডিপিআই পিডিএফ ডাউনলোড করা যাবে।'
        ),
        'answer_en': (
            'Payments can be completed via `/portal/payments` using SSLCommerz, bKash, Nagad, or Bank Transfer. '
            'Once verified server-to-server, an official receipt (`PGCB-RCP-YYYY-NNNNNN`) with a cryptographic QR code and 300-DPI PDF is generated immediately.'
        ),
        'suggested_links': [
            {'label_bn': 'পেমেন্ট ও রসিদ', 'label_en': 'Payments & Receipts', 'url': '/portal/payments'},
        ],
    },
    {
        'id': 'constitution_and_benefits',
        'title_bn': 'গঠনতন্ত্র ও সদস্য সুবিধা',
        'title_en': 'Constitution & Member Benefits',
        'keywords': [
            'constitution', 'rules', 'bylaws', 'benefit', 'welfare', 'rights', 'grade',
            'গঠনতন্ত্র', 'বিধিমালা', 'সুবিধা', 'কল্যাণ', 'অধিকার', '১০ম গ্রেড',
        ],
        'answer_bn': (
            'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির সংশোধিত গঠনতন্ত্র ২০২৬ অনুযায়ী সকল সক্রিয় সদস্য ভোটাধিকার, বার্ষিক সাধারণ সভায় অংশগ্রহণ, '
            'পেশাগত উন্নয়ন কর্মশালা, কারিগরি জার্নাল প্রকাশনা এবং জরুরি কল্যাণ তহবিল সহায়তার অধিকারী। গঠনতন্ত্রের পূর্ণাঙ্গ পিডিএফ `/documents` পেজে পাওয়া যাবে।'
        ),
        'answer_en': (
            'Under the Amended Constitution 2026 of the PGCB Diploma Engineers Association, active members receive voting rights, '
            'delegate representation at the Annual General Conference, emergency welfare fund coverage, technical training workshops, and digital credentials.'
        ),
        'suggested_links': [
            {'label_bn': 'ডকুমেন্ট লাইব্রেরি', 'label_en': 'Document Library', 'url': '/documents'},
            {'label_bn': 'জার্নাল ও প্রকাশনা', 'label_en': 'Journals & Publications', 'url': '/journals'},
        ],
    },
    {
        'id': 'verification',
        'title_bn': 'সনদপত্র ও আইডি কার্ড যাচাই',
        'title_en': 'Certificate & Digital ID Verification',
        'keywords': [
            'verify', 'verification', 'certificate', 'id card', 'qr', 'authentic',
            'যাচাই', 'সনদ', 'সনদপত্র', 'আইডি কার্ড', 'কিউআর',
        ],
        'answer_bn': (
            'যেকোনো সদস্যের ডিজিটাল আইডি কার্ড, সনদপত্র বা পেমেন্ট রসিদে থাকা কিউআর কোড স্ক্যান করে অথবা `/verify` ও `/verify-certificate` পেজে গিয়ে '
            'তাৎক্ষণিকভাবে সত্যতা যাচাই করা যায়। গোপনীয়তার স্বার্থে কিউআর কোডে কোনো ব্যক্তিগত সংবেদনশীল তথ্য (যেমন NID) সংরক্ষিত থাকে না।'
        ),
        'answer_en': (
            'Verify any Digital ID Card, Certificate, or Payment Receipt by scanning its QR code or visiting `/verify` and `/verify-certificate`. '
            'For privacy protection, QR codes only carry a cryptographic verification token and never expose raw NID or personal phone numbers.'
        ),
        'suggested_links': [
            {'label_bn': 'সদস্য যাচাই', 'label_en': 'Verify Member ID', 'url': '/verify'},
            {'label_bn': 'সনদ যাচাই', 'label_en': 'Verify Certificate', 'url': '/verify-certificate'},
        ],
    },
    {
        'id': 'circles_and_contact',
        'title_bn': '৯টি গ্রিড সার্কেল ও যোগাযোগ',
        'title_en': '9 PGCB Grid Circles & Secretariat Contact',
        'keywords': [
            'circle', 'grid', 'contact', 'office', 'address', 'phone', 'email', 'help', 'dhaka', 'chattogram',
            'সার্কেল', 'গ্রিড', 'যোগাযোগ', 'ঠিকানা', 'অফিস', 'হটলাইন', 'ঢাকা', 'চট্টগ্রাম',
        ],
        'answer_bn': (
            'সমিতির কার্যক্রম পিজিসিবি-র ৯টি অফিসিয়াল গ্রিড সার্কেলে বিস্তৃত: ঢাকা, চট্টগ্রাম, কুমিল্লা, সিলেট, খুলনা, রাজশাহী, রংপুর, ময়মনসিংহ ও বরিশাল। '
            'কেন্দ্রীয় কার্যালয়: পিজিসিবি হেড অফিস, আফতাবনগর, বাড্ডা, ঢাকা-১২১২। বিস্তারিত যোগাযোগের জন্য `/contact` বা `/circles` পেজ দেখুন।'
        ),
        'answer_en': (
            'The association operates across all 9 official PGCB Grid Circles: Dhaka, Chattogram, Cumilla, Sylhet, Khulna, Rajshahi, Rangpur, Mymensingh, and Barishal. '
            'Central Secretariat: PGCB Head Office, Aftabnagar, Badda, Dhaka-1212. Visit `/contact` or `/circles` for circle-specific contacts.'
        ),
        'suggested_links': [
            {'label_bn': 'গ্রিড সার্কেলসমূহ', 'label_en': 'Grid Circles', 'url': '/circles'},
            {'label_bn': 'যোগাযোগ', 'label_en': 'Contact Secretariat', 'url': '/contact'},
        ],
    },
]


@router.get('/topics')
def list_helpdesk_topics():
    return {
        'assistant_name_bn': 'পিজিসিবি সহায়তা সহকারী',
        'assistant_name_en': 'PGCB Institutional Assistant',
        'topics': [
            {
                'id': t['id'],
                'title_bn': t['title_bn'],
                'title_en': t['title_en'],
                'suggested_links': t['suggested_links'],
            }
            for t in HELPDESK_TOPICS
        ],
        'sample_questions': [
            'কিভাবে সদস্যপদ আবেদন করব?',
            'সদস্যপদ ফি ও বার্ষিক নবায়ন চার্জ কত?',
            'ডিজিটাল আইডি কার্ড ও সনদপত্র কিভাবে যাচাই করা যায়?',
            'সর্বশেষ সার্কুলার, নোটিশ ও আসন্ন ইভেন্ট কী কী?',
            'কেন্দ্রীয় কার্যনির্বাহী কমিটির সদস্য কারা?',
        ],
    }


@router.post('/ask')
def ask_helpdesk(payload: HelpdeskAskRequest, db: Session = Depends(get_db)):
    q_raw = payload.question.strip()
    q_lower = q_raw.lower()

    citations: list[dict[str, Any]] = []

    # Check live database entities when the user asks about circulars, notices, events, committee, or circles
    if any(k in q_lower for k in ('circular', 'সার্কুলার', 'বিজ্ঞপ্তি', 'order', 'স্মারক')):
        circulars = db.scalars(
            select(Circular).where(Circular.is_published == True).order_by(Circular.published_at.desc()).limit(3)
        ).all()
        for c in circulars:
            citations.append({'type': 'CIRCULAR', 'id': c.id, 'title': c.title_bn, 'url': '/circulars'})
        if circulars:
            titles = '؛ '.join(c.title_bn for c in circulars)
            return {
                'question': q_raw,
                'matched_topic': 'circulars',
                'confidence': 0.94,
                'answer_bn': f'সর্বশেষ প্রকাশিত অফিসিয়াল সার্কুলারসমূহ: {titles}। সব সার্কুলার দেখতে `/circulars` পেজ ভিজিট করুন।',
                'answer_en': f'Latest published official circulars: {titles}. Visit `/circulars` for the full archive.',
                'citations': citations,
                'suggested_links': [{'label_bn': 'সকল সার্কুলার', 'label_en': 'All Circulars', 'url': '/circulars'}],
                'follow_up_questions': ['সদস্যপদ ফি কত?', 'আসন্ন ইভেন্ট কী কী?'],
            }

    if any(k in q_lower for k in ('notice', 'নোটিশ', 'সভা', 'meeting')):
        notices = db.scalars(
            select(Notice).where(Notice.is_published == True).order_by(Notice.published_at.desc()).limit(3)
        ).all()
        for n in notices:
            citations.append({'type': 'NOTICE', 'id': n.id, 'title': n.title_bn, 'url': '/notices'})
        if notices:
            titles = '؛ '.join(n.title_bn for n in notices)
            return {
                'question': q_raw,
                'matched_topic': 'notices',
                'confidence': 0.93,
                'answer_bn': f'সর্বশেষ অফিসিয়াল নোটিশসমূহ: {titles}। বিস্তারিত দেখতে `/notices` পেজ দেখুন।',
                'answer_en': f'Latest official notices: {titles}. See `/notices` for full details.',
                'citations': citations,
                'suggested_links': [{'label_bn': 'নোটিশ বোর্ড', 'label_en': 'Notice Board', 'url': '/notices'}],
                'follow_up_questions': ['কিভাবে সদস্যপদ নবায়ন করব?', 'কেন্দ্রীয় কমিটির তালিকা'],
            }

    if any(k in q_lower for k in ('event', 'conference', 'workshop', 'ইভেন্ট', 'সম্মেলন', 'কর্মশালা')):
        events = db.scalars(
            select(Event).where(Event.is_published == True).order_by(Event.event_date.asc()).limit(3)
        ).all()
        for e in events:
            citations.append({'type': 'EVENT', 'id': e.id, 'title': e.title_bn, 'url': '/events'})
        if events:
            titles = '؛ '.join(f'{e.title_bn} ({e.location_bn})' for e in events)
            return {
                'question': q_raw,
                'matched_topic': 'events',
                'confidence': 0.94,
                'answer_bn': f'আসন্ন ইভেন্ট ও সম্মেলনসমূহ: {titles}। অনলাইনে নিবন্ধন করতে `/events` পেজে যান।',
                'answer_en': f'Upcoming events and conferences: {titles}. Register online via `/events`.',
                'citations': citations,
                'suggested_links': [{'label_bn': 'ইভেন্টসমূহ', 'label_en': 'Events', 'url': '/events'}],
                'follow_up_questions': ['ইভেন্টে কিভাবে রেজিস্ট্রেশন করব?', 'সদস্যপদ আবেদনের নিয়ম কী?'],
            }

    if any(k in q_lower for k in ('committee', 'president', 'secretary', 'কমিটি', 'সভাপতি', 'সম্পাদক')):
        leaders = db.scalars(select(CommitteeMember).order_by(CommitteeMember.display_order.asc()).limit(4)).all()
        for l in leaders:
            citations.append({'type': 'COMMITTEE', 'id': l.id, 'title': f'{l.name_bn} ({l.designation_bn})', 'url': '/committee'})
        if leaders:
            leader_summary = ', '.join(f'{l.name_bn} ({l.designation_bn})' for l in leaders)
            return {
                'question': q_raw,
                'matched_topic': 'committee',
                'confidence': 0.95,
                'answer_bn': f'কেন্দ্রীয় কার্যনির্বাহী কমিটির নেতৃবৃন্দ: {leader_summary}। পূর্ণাঙ্গ তালিকা `/committee` পেজে দেখুন।',
                'answer_en': f'Central Executive Committee leadership: {leader_summary}. View the full roster at `/committee`.',
                'citations': citations,
                'suggested_links': [{'label_bn': 'কার্যনির্বাহী কমিটি', 'label_en': 'Executive Committee', 'url': '/committee'}],
                'follow_up_questions': ['৯টি গ্রিড সার্কেল কী কী?', 'সমিতির গঠনতন্ত্র কোথায় পাব?'],
            }

    # Score static knowledge topics
    best_topic = None
    best_score = 0
    for topic in HELPDESK_TOPICS:
        score = sum(2 if kw in q_lower else 0 for kw in topic['keywords'])
        if score > best_score:
            best_score = score
            best_topic = topic

    if best_topic is not None and best_score > 0:
        if best_topic['id'] == 'membership_fees':
            schedule = get_fee_schedule(db)
            citations.append({
                'type': 'FEE_SCHEDULE',
                'id': 1,
                'title': f"General Membership: {schedule['GENERAL']} BDT | Annual Renewal: {schedule['RENEWAL']} BDT | Life: {schedule['LIFE']} BDT",
                'url': '/portal/payments',
            })
        elif best_topic['id'] == 'circles_and_contact':
            circles = db.scalars(select(Circle).where(Circle.active == True).order_by(Circle.id.asc())).all()
            for c in circles[:9]:
                citations.append({'type': 'CIRCLE', 'id': c.id, 'title': f'{c.name_bn} ({c.name_en or c.name_bn})', 'url': f'/circles'})
        elif best_topic['id'] == 'constitution_and_benefits':
            docs = db.scalars(select(Document).where(Document.is_published == True).limit(2)).all()
            for d in docs:
                citations.append({'type': 'DOCUMENT', 'id': d.id, 'title': d.title_bn, 'url': '/documents'})

        return {
            'question': q_raw,
            'matched_topic': best_topic['id'],
            'confidence': min(0.98, 0.75 + 0.05 * best_score),
            'answer_bn': best_topic['answer_bn'],
            'answer_en': best_topic['answer_en'],
            'citations': citations,
            'suggested_links': best_topic['suggested_links'],
            'follow_up_questions': [
                'কিভাবে সদস্যপদ আবেদন করব?',
                'সদস্যপদ ফি ও নবায়ন চার্জ কত?',
                'ডিজিটাল সনদপত্র কিভাবে যাচাই করব?',
            ],
        }

    # Default institutional fallback response
    return {
        'question': q_raw,
        'matched_topic': 'general_overview',
        'confidence': 0.7,
        'answer_bn': (
            'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতি পোর্টালে স্বাগতম। আপনি সদস্যপদ আবেদন (`/apply`), '
            'সদস্যপদ ফি ও রসিদ (`/portal/payments`), সার্কুলার (`/circulars`), নোটিশ (`/notices`), ইভেন্ট (`/events`), '
            'ডকুমেন্ট ও গঠনতন্ত্র (`/documents`), এবং সনদপত্র যাচাই (`/verify-certificate`) সম্পর্কে যেকোনো প্রশ্ন করতে পারেন।'
        ),
        'answer_en': (
            'Welcome to the PGCB Diploma Engineers Association Portal Assistant. You can ask about membership applications (`/apply`), '
            'official fee schedules and receipts (`/portal/payments`), circulars (`/circulars`), notices (`/notices`), events (`/events`), '
            'constitution documents (`/documents`), and certificate/ID verification (`/verify-certificate`).'
        ),
        'citations': citations,
        'suggested_links': [
            {'label_bn': 'সদস্যপদ আবেদন', 'label_en': 'Apply for Membership', 'url': '/apply'},
            {'label_bn': 'সার্কুলার', 'label_en': 'Circulars', 'url': '/circulars'},
            {'label_bn': 'যোগাযোগ', 'label_en': 'Contact Us', 'url': '/contact'},
        ],
        'follow_up_questions': [
            'কিভাবে সদস্যপদ আবেদন করব?',
            'সদস্যপদ ফি ও বার্ষিক নবায়ন চার্জ কত?',
            '৯টি গ্রিড সার্কেল কী কী?',
        ],
    }
