import io
from pathlib import Path
import hashlib, hmac
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from PIL import Image, ImageDraw, ImageFont
import qrcode

from app.core.config import settings
from app.core.deps import current_user, RoleChecker
from app.db.session import get_db
from app.models import Member, User, MemberDocument
from app.services import BASE_STORAGE
from app.utils.storage import is_local_path, get_file_bytes

router = APIRouter(prefix='/member', tags=['card'])


def verification_token(membership_id: str) -> str:
    sig = hmac.new(settings.jwt_secret.encode(), membership_id.encode(), hashlib.sha256).hexdigest()[:32]
    return f'{membership_id}.{sig}'


def _get_font(size: int, bold: bool = False, bengali: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    """Robust font loader checking Windows, Linux and fallback systems."""
    candidates = []
    if bengali:
        candidates += [
            'C:/Windows/Fonts/vrindab.ttf' if bold else 'C:/Windows/Fonts/vrinda.ttf',
            'C:/Windows/Fonts/NirmalaB.ttf' if bold else 'C:/Windows/Fonts/Nirmala.ttf',
            '/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf' if bold else '/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf',
            'C:/Windows/Fonts/ARIALUNI.ttf',
        ]
    if bold:
        candidates += [
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/NotoSans-Bold.ttf',
            'C:/Windows/Fonts/segoeuib.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        ]
    else:
        candidates += [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/NotoSans-Regular.ttf',
            'C:/Windows/Fonts/segoeui.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def build_card(member: Member, user: User | None = None) -> Path:
    """Build a print-ready, high-fidelity institutional digital ID card (1050 x 640)."""
    folder = BASE_STORAGE / 'cards'
    folder.mkdir(parents=True, exist_ok=True)
    png_path = folder / f'{member.membership_id}.png'

    width, height = 1050, 640
    img = Image.new('RGB', (width, height), '#0B132B')
    draw = ImageDraw.Draw(img)

    # Load typography
    font_bn_title = _get_font(21, bold=True, bengali=True)
    font_bn_sub = _get_font(19, bold=True, bengali=True)
    font_bn_name = _get_font(26, bold=True, bengali=True)
    font_bn_body = _get_font(15, bold=False, bengali=True)
    font_bn_body_bold = _get_font(15, bold=True, bengali=True)

    font_en_header = _get_font(12, bold=True)
    font_en_name = _get_font(17, bold=True)
    font_en_desig = _get_font(16, bold=True)
    font_en_id = _get_font(23, bold=True)
    font_en_badge = _get_font(13, bold=True)
    font_en_sm = _get_font(11, bold=False)
    font_en_tiny = _get_font(10, bold=False)

    # Outer card rounded border
    draw.rounded_rectangle((10, 10, width - 10, height - 10), radius=22, outline='#1E293B', width=2, fill='#0B132B')

    # Top Header Banner
    draw.rounded_rectangle((12, 12, width - 12, 120), radius=18, fill='#0F1E42')
    # Header Bottom Gold Accent Line
    draw.rectangle((12, 118, width - 12, 122), fill='#F59E0B')

    # Official Emblem / Circular Seal on Header Left
    seal_box = (35, 24, 115, 104)
    draw.ellipse(seal_box, fill='#070D1E', outline='#F59E0B', width=3)
    draw.ellipse((42, 31, 108, 97), outline='#3B82F6', width=1)
    draw.text((54, 42), 'PGCB', font=font_en_badge, fill='#F59E0B')
    draw.text((53, 62), '★ ★ ★', font=font_en_tiny, fill='#93C5FD')
    draw.text((61, 78), 'BD', font=font_en_tiny, fill='#10B981')

    # Header Titles
    draw.text((135, 24), 'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ লিমিটেড', font=font_bn_title, fill='#FBBF24')
    draw.text((135, 54), 'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতি (পিজিডিইএ)', font=font_bn_sub, fill='#FFFFFF')
    draw.text((135, 87), 'POWER GRID DIPLOMA ENGINEERS ASSOCIATION • OFFICIAL IDENTITY CARD', font=font_en_header, fill='#93C5FD')

    # 1. Left Column: Photo Frame & Status
    photo_box = (45, 140, 275, 425)
    draw.rounded_rectangle(photo_box, radius=16, outline='#F59E0B', width=2, fill='#142144')

    # Photo Insertion: check member documents or photo_url
    photo_inserted = False
    photo_target_size = (226, 281)

    if member.documents:
        for doc in member.documents:
            if doc.document_type == 'PHOTO' and doc.storage_path:
                try:
                    p_bytes = get_file_bytes(doc.storage_path)
                    p_img = Image.open(io.BytesIO(p_bytes)).convert('RGB')
                    p_img = p_img.resize(photo_target_size, Image.Resampling.LANCZOS)
                    img.paste(p_img, (47, 142))
                    photo_inserted = True
                    break
                except Exception:
                    pass

    if not photo_inserted and member.photo_url:
        try:
            p_bytes = get_file_bytes(member.photo_url)
            p_img = Image.open(io.BytesIO(p_bytes)).convert('RGB')
            p_img = p_img.resize(photo_target_size, Image.Resampling.LANCZOS)
            img.paste(p_img, (47, 142))
            photo_inserted = True
        except Exception:
            pass

    if not photo_inserted:
        # Sleek placeholder silhouette
        draw.ellipse((120, 205, 200, 285), fill='#233358', outline='#3B82F6', width=2)
        draw.chord((90, 290, 230, 420), start=180, end=360, fill='#233358', outline='#3B82F6', width=2)
        draw.text((115, 370), 'MEMBER PHOTO', font=font_en_sm, fill='#94A3B8')

    # Status Pill Below Photo
    draw.rounded_rectangle((45, 440, 275, 482), radius=10, fill='#064E3B', outline='#10B981', width=2)
    draw.text((75, 451), '● ACTIVE MEMBER', font=font_en_badge, fill='#34D399')

    # Employee ID Box Below Status
    draw.rounded_rectangle((45, 494, 275, 532), radius=10, fill='#1E293B', outline='#334155', width=1)
    emp_text = f"EMP ID: {member.employee_id or 'PGCB-STAFF'}"
    draw.text((70, 505), emp_text, font=font_en_sm, fill='#93C5FD')

    # 2. Center Column: Bio & Credentials
    name_bn = (user.name_bn if user else None) or getattr(member, 'full_name_bn', None) or getattr(member, 'name_bn', None) or '—'
    name_en = (user.name_en if user else None) or getattr(member, 'full_name_en', None) or getattr(member, 'name_en', None) or ''
    desig = member.designation_bn or member.designation_en or 'ডিগ্রি/ডিপ্লোমা প্রকৌশলী'
    circle_name = (member.circle.name_bn if member.circle else 'কেন্দ্রীয় সচিবালয়')
    circle_en = (member.circle.name_en if member.circle else 'Central')
    inst = member.diploma_institution or 'Polytechnic Institute / Engineering College'

    draw.text((298, 140), name_bn, font=font_bn_name, fill='#FFFFFF')
    if name_en:
        draw.text((300, 182), name_en.upper(), font=font_en_name, fill='#FDE68A')
    draw.text((300, 214), desig, font=font_en_desig, fill='#38BDF8')

    # Grid Circle
    draw.text((300, 252), 'Grid Circle / কর্মক্ষেত্র:', font=font_bn_body, fill='#94A3B8')
    draw.text((300, 274), f'{circle_name} ({circle_en})', font=font_bn_body_bold, fill='#F8FAFC')

    # Diploma Institution
    draw.text((300, 308), 'Diploma Institute / পলিটেকনিক:', font=font_bn_body, fill='#94A3B8')
    draw.text((300, 328), inst, font=font_bn_body_bold, fill='#F8FAFC')

    # Membership Number Pill
    draw.rounded_rectangle((298, 368, 730, 432), radius=12, fill='#132042', outline='#F59E0B', width=2)
    draw.text((314, 376), 'OFFICIAL MEMBERSHIP NUMBER', font=font_en_tiny, fill='#FDE68A')
    draw.text((314, 394), member.membership_id or 'PGD-2026-0000', font=font_en_id, fill='#F59E0B')

    # Validity & Issue Dates
    draw.rounded_rectangle((298, 444, 730, 486), radius=8, fill='#101C38', outline='#334155', width=1)
    val_str = member.validity_date.strftime('%d-%m-%Y') if (member.validity_date and hasattr(member.validity_date, 'strftime')) else '31-12-2027'
    iss_str = member.issue_date.strftime('%d-%m-%Y') if (member.issue_date and hasattr(member.issue_date, 'strftime')) else '01-01-2025'
    draw.text((314, 456), f'VALID THRU: {val_str}   •   ISSUED: {iss_str}', font=font_en_badge, fill='#A7F3D0')

    # Security Affiliation note
    draw.text((300, 504), 'Affiliated: IDEB Central Unit • Non-transferable Identity Credential', font=font_en_sm, fill='#64748B')

    # 3. Right Column: QR Code & Verification
    qr_box = (755, 140, 1005, 415)
    draw.rounded_rectangle(qr_box, radius=16, fill='#FFFFFF', outline='#F59E0B', width=2)

    token = verification_token(member.membership_id)
    qr_url = f"{settings.frontend_url.rstrip('/')}/verify?token={token}"
    qr = qrcode.QRCode(box_size=5, border=1)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0B132B", back_color="#FFFFFF").convert('RGB').resize((195, 195))
    img.paste(qr_img, (782, 155))

    draw.text((800, 362), 'OFFICIAL QR VERIFICATION', font=font_en_badge, fill='#0B132B')
    draw.text((818, 385), 'Scan with mobile camera', font=font_en_tiny, fill='#64748B')

    # Cryptographic Badge below QR box
    draw.rounded_rectangle((755, 430, 1005, 482), radius=10, fill='#1E293B', outline='#3B82F6', width=1)
    draw.text((780, 441), 'CRYPTOGRAPHICALLY SIGNED', font=font_en_badge, fill='#38BDF8')
    draw.text((815, 460), 'HMAC-SHA256 SECURED', font=font_en_tiny, fill='#94A3B8')

    # Direct portal verification link
    draw.text((770, 498), 'Official Verify Portal:', font=font_en_tiny, fill='#64748B')
    draw.text((770, 513), 'pgcb.org.bd/verify', font=font_en_badge, fill='#F59E0B')

    # 4. Bottom Institutional Footer
    draw.rectangle((12, 555, width - 12, height - 12), fill='#070D1E')
    draw.line((12, 555, width - 12, 555), fill='#1E293B', width=1)
    draw.text((35, 575), 'গণপ্রজাতন্ত্রী বাংলাদেশ সরকার অনুমোদিত সংগঠন • CENTRAL EXECUTIVE COUNCIL', font=font_bn_body, fill='#94A3B8')
    draw.text((710, 578), 'ELECTRONIC CREDENTIAL • PGCB PORTAL V1.0', font=font_en_tiny, fill='#64748B')

    img.save(png_path, 'PNG', optimize=True)
    return png_path


@router.get('/card')
def digital_card(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = db.scalar(
        select(Member)
        .options(selectinload(Member.circle), selectinload(Member.user), selectinload(Member.documents))
        .where(Member.user_id == user.id)
    )
    if not m or m.status != 'ACTIVE' or not m.membership_id:
        raise HTTPException(409, 'Active membership is required')
    path = build_card(m, user)
    return FileResponse(path, media_type='image/png', filename=path.name)


@router.get('/card/pdf')
def digital_card_pdf(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = db.scalar(
        select(Member)
        .options(selectinload(Member.circle), selectinload(Member.user), selectinload(Member.documents))
        .where(Member.user_id == user.id)
    )
    if not m or m.status != 'ACTIVE' or not m.membership_id:
        raise HTTPException(409, 'Active membership is required')
    png_path = build_card(m, user)
    pdf_path = png_path.with_suffix('.pdf')
    Image.open(png_path).convert('RGB').save(pdf_path, 'PDF', resolution=300.0)
    return FileResponse(pdf_path, media_type='application/pdf', filename=pdf_path.name)


@router.get('/cards/{member_id}/png')
def admin_download_card(
    member_id: int,
    user: User = Depends(RoleChecker(['SUPER_ADMIN', 'MEMBERSHIP_OFFICER', 'CONTENT_EDITOR'])),
    db: Session = Depends(get_db)
):
    """Allows administrators to inspect and download the digital ID card for any approved member."""
    m = db.scalar(
        select(Member)
        .options(selectinload(Member.circle), selectinload(Member.user), selectinload(Member.documents))
        .where(Member.id == member_id)
    )
    if not m or not m.membership_id:
        raise HTTPException(404, 'Approved member with membership ID not found')
    path = build_card(m, m.user)
    return FileResponse(path, media_type='image/png', filename=path.name)


@router.get('/cards/{member_id}/pdf')
def admin_download_card_pdf(
    member_id: int,
    user: User = Depends(RoleChecker(['SUPER_ADMIN', 'MEMBERSHIP_OFFICER', 'CONTENT_EDITOR'])),
    db: Session = Depends(get_db)
):
    """Allows administrators to download the print-ready PDF card for any approved member."""
    m = db.scalar(
        select(Member)
        .options(selectinload(Member.circle), selectinload(Member.user), selectinload(Member.documents))
        .where(Member.id == member_id)
    )
    if not m or not m.membership_id:
        raise HTTPException(404, 'Approved member with membership ID not found')
    png_path = build_card(m, m.user)
    pdf_path = png_path.with_suffix('.pdf')
    Image.open(png_path).convert('RGB').save(pdf_path, 'PDF', resolution=300.0)
    return FileResponse(pdf_path, media_type='application/pdf', filename=pdf_path.name)
