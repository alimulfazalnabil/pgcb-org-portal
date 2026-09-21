from datetime import datetime
from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Circle, Circular, CommitteeMember, Event, Journal, MediaAsset, Member, SiteSetting, User

CIRCLES = ['ঢাকা','চট্টগ্রাম','কুমিল্লা','সিলেট','খুলনা','রাজশাহী','রংপুর','ময়মনসিংহ','বরিশাল']


def get_or_create_user(db, email, password, name_bn, role='MEMBER', phone=None):
    u = db.scalar(select(User).where(User.email == email))
    if not u:
        u = User(email=email, password_hash=hash_password(password), name_bn=name_bn, role=role, phone=phone, email_verified=True)
        db.add(u); db.flush()
    u.email_verified = True
    return u


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for n in CIRCLES:
            if not db.scalar(select(Circle).where(Circle.name_bn == n)):
                db.add(Circle(name_bn=n, name_en=n, active=True))
        db.commit()

        get_or_create_user(db, 'admin@example.org', 'ChangeMe123!', 'সিস্টেম অ্যাডমিন', 'SUPER_ADMIN')
        get_or_create_user(db, 'content@example.org', 'ChangeMe123!', 'কনটেন্ট এডিটর', 'CONTENT_EDITOR')
        user = get_or_create_user(db, 'member@example.org', 'ChangeMe123!', 'ডেমো প্রকৌশলী', 'MEMBER', '01700000000')
        db.commit()

        dhaka = db.scalar(select(Circle).where(Circle.name_bn == 'ঢাকা'))
        member = db.scalar(select(Member).where(Member.user_id == user.id))
        if not member:
            member = Member(user_id=user.id)
            db.add(member); db.flush()
        member.membership_id = 'PGD-2026-1001'; member.designation_bn='ডিপ্লোমা প্রকৌশলী'; member.designation_en='Diploma Engineer'; member.circle_id=dhaka.id; member.status='ACTIVE'; member.issue_date=datetime(2026,1,1); member.validity_date=datetime(2027,1,1); member.diploma_institution='Dhaka Polytechnic Institute'; member.graduation_year=2016

        if db.scalar(select(Circular)) is None:
            db.add_all([
                Circular(category='CIRCULAR', reference_no='PGDA/2026/071', title_bn='পাওয়ার গ্রিড ডিপ্লোমা-প্রকৌশল সমিতির ১২তম বার্ষিক সাধারণ সম্মেলন ও কাউন্সিল ২০২৬-এর অফিসিয়াল সার্কুলার', summary_bn='কেন্দ্রীয় সম্মেলনের প্রতিনিধি নিবন্ধন ও সাংগঠনিক নির্দেশনা।', published_at=datetime(2026,7,25),is_published=True,priority=100),
                Circular(category='CIRCULAR', reference_no='PGDA/2026/068', title_bn='পিজিসিবি ডিপ্লোমা প্রকৌশলীদের ১০ম গ্রেড বাস্তবায়নে বিশেষ স্মারকপত্র সংক্রান্ত বিজ্ঞপ্তি', summary_bn='পাওয়ার ডিভিশনে প্রেরিত স্মারকপত্রের সারসংক্ষেপ।', published_at=datetime(2026,7,20),is_published=True,priority=90),
                Circular(category='GENERAL', title_bn='বর্ষা মৌসুমে গ্রিড সাবস্টেশন সুরক্ষা ও ক্ষমতা অটোমেশন ব্যবস্থা', summary_bn='সেফটি ও প্রিভেনটিভ মেইনটেন্যান্স সম্পর্কিত সাধারণ নির্দেশনা।', published_at=datetime(2026,7,15),is_published=True,priority=50),
                Circular(category='WELFARE', title_bn='পিজিসিবি প্রকৌশলী পরিবারের জন্য জরুরি কল্যাণ হটলাইন আবেদন ও সহায়তা কার্যক্রম', summary_bn='কল্যাণ ডেস্কের সহায়তা ও যোগাযোগ নির্দেশিকা।', published_at=datetime(2026,7,2),is_published=True,priority=40),
            ])

        if db.scalar(select(CommitteeMember)) is None:
            db.add_all([
                CommitteeMember(name_bn='প্রকৌ. মোঃ শামসুল আলম',name_en='Engr. Md. Shamsul Alam',designation_bn='কেন্দ্রীয় সভাপতি',designation_en='President',message_bn='পেশাগত উন্নয়ন, সদস্যসেবা এবং সাংগঠনিক শৃঙ্খলা শক্তিশালী করার অঙ্গীকার।',term_start=2025,term_end=2027,display_order=1),
                CommitteeMember(name_bn='প্রকৌ. কাজী রফিকুল ইসলাম',name_en='Engr. Kazi Rafiqul Islam',designation_bn='সাধারণ সম্পাদক',designation_en='General Secretary',message_bn='সদস্যদের পেশাগত অধিকার, কারিগরি সক্ষমতা এবং স্বচ্ছ প্রশাসনের প্রতি অঙ্গীকার।',term_start=2025,term_end=2027,display_order=2),
                CommitteeMember(name_bn='প্রকৌ. মোঃ দেলোয়ার হোসেন',name_en='Engr. Md. Delowar Hossain',designation_bn='যুগ্ম-সাধারণ সম্পাদক',designation_en='Joint General Secretary',term_start=2025,term_end=2027,display_order=3),
                CommitteeMember(name_bn='প্রকৌ. রেজাউল করিম',designation_bn='সাংগঠনিক সম্পাদক',term_start=2025,term_end=2027,display_order=4),
                CommitteeMember(name_bn='প্রকৌ. মিজানুর রহমান',designation_bn='অর্থ সম্পাদক',term_start=2025,term_end=2027,display_order=5),
                CommitteeMember(name_bn='প্রকৌ. সাইফুল ইসলাম',designation_bn='নির্বাহী পরিষদ সদস্য',term_start=2025,term_end=2027,display_order=6),
            ])

        if db.scalar(select(Journal)) is None:
            db.add_all([
                Journal(category='CONSTITUTION',title_bn='পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশল সমিতি - গঠনতন্ত্র ও পরিচালনা বিধিমালা',edition='২০২৬ Edition',publication_date=datetime(2026,6,1),abstract_bn='সংগঠনের গঠনতন্ত্র, নির্বাচন বিধি, আচরণবিধি ও প্রশাসনিক কাঠামো।',document_url='#',is_published=True),
                Journal(category='JOURNAL',title_bn='পাওয়ার গ্রিড কারিগরি পরিচালনা: উচ্চ-ভোল্টেজ সুরক্ষা ও রিলে সমন্বয়',edition='June 2026',publication_date=datetime(2026,6,15),abstract_bn='Numeric relay configuration, differential protection and busbar fault prevention in 400kV/230kV substations.',document_url='#',is_published=True),
                Journal(category='REPORT',title_bn='জাতীয় সমন্বিত গ্রিড আধুনিকীকরণ ও হট ওয়েভ অটোমেশন রিকমেন্ডেশন',edition='March 2026',publication_date=datetime(2026,3,10),abstract_bn='Real-time grid monitoring, frequency control and automatic load shedding protocol guidance.',document_url='#',is_published=True),
            ])

        if db.scalar(select(Event)) is None:
            db.add_all([
                Event(title_bn='১২তম বার্ষিক সাধারণ সম্মেলন ও কাউন্সিল ২০২৬',title_en='12th Annual General Conference & Council 2026',description_bn='কেন্দ্রীয় বার্ষিক সম্মেলন ও প্রতিনিধি অধিবেশন।',event_date=datetime(2026,8,20,10),location_bn='পিজিসিবি হেড অফিস অডিটোরিয়াম, ঢাকা',is_published=True,registration_enabled=True),
                Event(title_bn='National Polytechnic Robotics & Innovation Expo',title_en='National Polytechnic Robotics & Innovation Expo',description_bn='কারিগরি উদ্ভাবন ও রোবটিক্স প্রদর্শনী।',event_date=datetime(2026,9,12,10),location_bn='ঢাকা',is_published=True),
                Event(title_bn='Professional Competency Assessment Workshop',title_en='Professional Competency Assessment Workshop',description_bn='প্রকৌশলীদের কারিগরি দক্ষতা ও পেশাগত সক্ষমতা উন্নয়ন কর্মশালা।',event_date=datetime(2026,10,5,9),location_bn='ঢাকা',is_published=True),
            ])

        if db.scalar(select(MediaAsset)) is None:
            db.add_all([
                MediaAsset(media_type='PHOTO',title_bn='53rd IDEB National Convention Delegate Assembly',url='#',published=True),
                MediaAsset(media_type='PHOTO',title_bn='National Polytechnic Robotics & Innovation Expo',url='#',published=True),
                MediaAsset(media_type='PHOTO',title_bn='Central Executive Committee Delegation Meeting',url='#',published=True),
                MediaAsset(media_type='VIDEO',title_bn='IDEB Golden Jubilee Documentary: 50 Years of Engineering Excellence',url='#',published=True),
                MediaAsset(media_type='PHOTO',title_bn='Voluntary Blood Donation Drive across 64 District IDEB Branches',url='#',published=True),
                MediaAsset(media_type='PHOTO',title_bn='Diploma Engineers Professional Competency Assessment Workshop',url='#',published=True),
            ])

        db.commit()
        print('Seed complete')
    finally:
        db.close()

if __name__ == '__main__': main()
