"""
Official Payment Receipt & Membership Payment Lifecycle Service for PGCB Portal.
Generates cryptographic receipt numbers (PGCB-RCP-YYYY-NNNNNN), QR verification tokens,
print-ready PDF receipts, server-side fee calculations, and automatic membership activation.
"""

from __future__ import annotations

import hashlib
import hmac
import io
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from PIL import Image, ImageDraw, ImageFont
import qrcode

from app.core.config import settings
from app.domain.membership import renew_membership
from app.models import Certificate, Event, Member, MembershipRenewal, Notification, PaymentTransaction, SiteSetting, User
from app.services import next_membership_id
from app.services.email import EmailService


DEFAULT_FEES = {
    "ANNUAL_STANDARD": 2000,
    "GENERAL": 2000,
    "REGULAR": 2000,
    "LIFE": 10000,
    "RENEWAL": 2000,
    "APPLICATION": 500,
    "ASSOCIATE": 1500,
    "STUDENT": 500,
}

MEMBERSHIP_PLAN_FEES = {
    "ANNUAL_STANDARD": 2000,
    "ANNUAL_GENERAL": 2000,
    "GENERAL": 2000,
    "REGULAR": 2000,
    "ANNUAL_RENEWAL": 2000,
    "RENEWAL": 2000,
    "RENEWAL_1YR": 2000,
    "RENEWAL_2YR": 4000,
    "APPLICATION": 500,
    "NEW_APPLICATION": 500,
    "ASSOCIATE": 1500,
    "ANNUAL_ASSOCIATE": 1500,
    "STUDENT": 500,
    "ANNUAL_STUDENT": 500,
    "LIFE": 10000,
    "LIFETIME": 10000,
}

PURPOSE_LABELS = {
    "MEMBERSHIP": "Annual Membership Fee (বার্ষিক সদস্যপদ ফি)",
    "MEMBERSHIP_FEE": "Annual Membership Fee (বার্ষিক সদস্যপদ ফি)",
    "RENEWAL": "Membership Renewal Fee (সদস্যপদ নবায়ন ফি)",
    "APPLICATION": "Membership Application Fee (সদস্যপদ আবেদন ফি)",
    "EVENT": "Event Registration Fee (ইভেন্ট নিবন্ধন ফি)",
    "DONATION": "Institutional Welfare Contribution (কল্যাণ তহবিল অনুদান)",
}


def get_fee_schedule(db: Session) -> dict[str, int]:
    """Return the authoritative server-side membership fee schedule in BDT."""
    schedule = dict(DEFAULT_FEES)
    rows = db.scalars(
        select(SiteSetting).where(
            SiteSetting.key.in_([
                "membership_fee_general",
                "membership_fee_life",
                "membership_fee_renewal",
                "membership_fee_application",
            ])
        )
    ).all()
    key_map = {
        "membership_fee_general": "GENERAL",
        "membership_fee_life": "LIFE",
        "membership_fee_renewal": "RENEWAL",
        "membership_fee_application": "APPLICATION",
    }
    for row in rows:
        if row.value and row.key in key_map:
            try:
                val = int(float(row.value))
                if val > 0:
                    schedule[key_map[row.key]] = val
            except ValueError:
                pass
    schedule["REGULAR"] = schedule["GENERAL"]
    schedule["ANNUAL_STANDARD"] = schedule["GENERAL"]
    return schedule


def resolve_plan_amount(db: Session, membership_plan_id: str) -> int:
    """Resolve authoritative server-side BDT fee from membership_plan_id."""
    code = (membership_plan_id or "").strip().upper()
    if not code:
        raise ValueError("membership_plan_id cannot be empty")
    schedule = get_fee_schedule(db)
    if code in schedule:
        return int(schedule[code])
    if code in MEMBERSHIP_PLAN_FEES:
        return int(MEMBERSHIP_PLAN_FEES[code])
    raise ValueError(f"Unsupported membership_plan_id: {membership_plan_id}")


def calculate_official_fee(
    db: Session,
    purpose: str,
    membership_type: str = "GENERAL",
    event_id: int | None = None,
    membership_plan_id: str | None = None,
) -> int | None:
    """Return the required server-side fee for a purpose or plan, or None if variable (e.g. DONATION)."""
    if membership_plan_id:
        return resolve_plan_amount(db, membership_plan_id)
    p = (purpose or "MEMBERSHIP").strip().upper()
    schedule = get_fee_schedule(db)
    if p == "EVENT" and event_id:
        evt = db.get(Event, event_id)
        return int(evt.fee_amount) if evt and evt.fee_amount else 0
    if p == "RENEWAL":
        return schedule["RENEWAL"]
    if p == "APPLICATION":
        return schedule["APPLICATION"]
    if p in {"MEMBERSHIP", "MEMBERSHIP_FEE"}:
        mtype = (membership_type or "GENERAL").strip().upper()
        return schedule.get(mtype, schedule["GENERAL"])
    return None



def receipt_number_for(payment: PaymentTransaction) -> str:
    year = (payment.updated_at or payment.created_at or datetime.utcnow()).year
    return f"PGCB-RCP-{year}-{int(payment.id):06d}"


def receipt_verification_token(receipt_no: str) -> str:
    sig = hmac.new(settings.jwt_secret.encode(), receipt_no.encode(), hashlib.sha256).hexdigest()[:24]
    return f"{receipt_no}.{sig}"


def verify_receipt_token(token_or_no: str) -> tuple[bool, str]:
    cleaned = token_or_no.strip()
    if "." in cleaned:
        receipt_no, sig = cleaned.rsplit(".", 1)
        expected = hmac.new(settings.jwt_secret.encode(), receipt_no.encode(), hashlib.sha256).hexdigest()[:24]
        return hmac.compare_digest(expected, sig), receipt_no
    return cleaned.startswith("PGCB-RCP-"), cleaned


def ensure_receipt_metadata(payment: PaymentTransaction) -> tuple[str, str]:
    receipt_no = receipt_number_for(payment)
    token = receipt_verification_token(receipt_no)
    payload = dict(payment.provider_payload) if isinstance(payment.provider_payload, dict) else {}
    payload["receipt_no"] = receipt_no
    payload["receipt_token"] = token
    payload.setdefault("paid_at", datetime.utcnow().isoformat())
    payment.provider_payload = payload
    return receipt_no, token


def activate_membership_from_payment(
    db: Session,
    payment: PaymentTransaction,
) -> Member | None:
    """
    Complete the membership payment lifecycle when a payment is verified as PAID:
    Application -> Eligibility Review -> Fee Calculation -> Payment -> Verification
    -> Membership Approval -> Membership ID -> Digital ID Card -> Certificate.
    """
    ensure_receipt_metadata(payment)
    if not payment.member_id and payment.user_id:
        member = db.scalar(select(Member).where(Member.user_id == payment.user_id))
        if member:
            payment.member_id = member.id
    else:
        member = db.get(Member, payment.member_id) if payment.member_id else None

    if not member or payment.purpose not in {"MEMBERSHIP", "MEMBERSHIP_FEE", "RENEWAL", "APPLICATION"}:
        return member

    user = db.get(User, member.user_id) if member.user_id else None
    if not member.membership_id:
        member.membership_id = next_membership_id(db)

    existing_renewal = db.scalar(select(MembershipRenewal).where(MembershipRenewal.payment_id == payment.id))
    is_first_activation = existing_renewal is None
    if is_first_activation:
        renew_membership(
            db,
            member,
            payment.id,
            int(payment.amount),
            payment.currency,
            plan_code=payment.membership_plan_id,
        )
    else:
        member.status = "ACTIVE"

    val_str = member.validity_date.strftime("%d %b %Y") if member.validity_date else "N/A"
    member.application_note = (
        f"Membership active until {val_str}. Verified payment {payment.transaction_ref or payment.id} "
        f"(Receipt: {payment.receipt_no})."
    )
    from app.models import Membership, MembershipApplication, Payment as CanonicalPayment
    app_row = db.scalar(select(MembershipApplication).where(MembershipApplication.member_id == member.id))
    if app_row:
        app_row.status = "ACTIVE"
    if member.membership_id:
        mem_rec = db.scalar(select(Membership).where(Membership.membership_id == member.membership_id))
        if not mem_rec:
            db.add(
                Membership(
                    member_id=member.id,
                    membership_id=member.membership_id,
                    membership_type=member.membership_type or "GENERAL",
                    status="ACTIVE",
                    issue_date=member.issue_date or datetime.utcnow(),
                    validity_date=member.validity_date,
                )
            )
        else:
            mem_rec.status = "ACTIVE"
            mem_rec.validity_date = member.validity_date
    tx_ref = payment.transaction_ref or payment.provider_transaction_id or f"PGCB-TX-{payment.id}"
    if not db.scalar(select(CanonicalPayment).where(CanonicalPayment.transaction_id == tx_ref)):
        db.add(
            CanonicalPayment(
                user_id=payment.user_id,
                member_id=member.id,
                transaction_id=tx_ref,
                receipt_no=payment.receipt_no,
                provider=payment.provider or "BKASH",
                purpose=payment.purpose or "MEMBERSHIP",
                amount=int(payment.amount),
                currency=payment.currency or "BDT",
                status="PAID",
                paid_at=datetime.utcnow(),
            )
        )
    db.flush()

    # Automatically issue Membership Certificate if not yet issued for this member
    existing_cert = db.scalar(select(Certificate).where(Certificate.member_id == member.id))
    if not existing_cert and user:
        try:
            from app.services.certificate_service import CertificateService
            CertificateService.issue_certificate(
                db=db,
                admin_user=user,
                recipient_user_id=user.id,
                certificate_type="MEMBERSHIP",
                recipient_name=user.name_bn or user.name_en or member.membership_id,
            )
        except Exception:
            pass

    # Pre-generate Digital ID Card
    try:
        from app.routers.card import build_card
        build_card(member, user)
    except Exception:
        pass

    if user and is_first_activation:
        is_renewal = (payment.purpose or "").upper() == "RENEWAL"
        title_bn = "সদস্যপদ নবায়ন সফল হয়েছে" if is_renewal else "পেমেন্ট ও সদস্যপদ সক্রিয়করণ সফল"
        body_bn = (
            f"আপনার ৳{payment.amount} পেমেন্ট যাচাই সম্পন্ন হয়েছে (রসিদ নং: {payment.receipt_no})। "
            f"সদস্য আইডি: {member.membership_id} • নতুন মেয়াদ: {val_str}।"
        )
        db.add(
            Notification(
                user_id=user.id,
                title_bn=title_bn,
                body_bn=body_bn,
                notification_type="PAYMENT",
            )
        )
        try:
            EmailService.send_payment_receipt(
                to_email=user.email,
                payer_name=user.name_bn or user.name_en or "প্রকৌশলী",
                amount=f"৳{payment.amount:,.2f}",
                transaction_id=f"{payment.transaction_ref or payment.id} ({payment.receipt_no})",
                purpose=payment.purpose,
            )
        except Exception:
            pass

    return member



def build_receipt_payload(db: Session, payment: PaymentTransaction) -> dict:
    member = db.get(Member, payment.member_id) if payment.member_id else None
    if not member and payment.user_id:
        member = db.scalar(select(Member).where(Member.user_id == payment.user_id))
    user = db.get(User, payment.user_id) if payment.user_id else (db.get(User, member.user_id) if member and member.user_id else None)

    is_paid = payment.status in {"PAID", "SUCCESS", "COMPLETED"}
    receipt_no = payment.receipt_no or (receipt_number_for(payment) if is_paid else None)
    token = receipt_verification_token(receipt_no) if receipt_no else None
    verify_url = f"{settings.frontend_url.rstrip('/')}/verify?receipt={token}" if token else None
    paid_date = payment.completed_at or payment.updated_at or payment.created_at or datetime.utcnow()

    return {
        "payment_id": payment.id,
        "receipt_no": receipt_no,
        "transaction_ref": payment.transaction_ref or f"PGCB-TX-{paid_date.year}-{payment.id:06d}",
        "member_name_bn": (user.name_bn if user else None) or "—",
        "member_name_en": (user.name_en if user else None) or (user.name_bn if user else "Member"),
        "membership_id": (member.membership_id if member else None) or "PENDING-ASSIGNMENT",
        "purpose": payment.purpose,
        "purpose_label": PURPOSE_LABELS.get(payment.purpose, payment.purpose),
        "amount": float(payment.amount),
        "amount_formatted": f"৳{int(payment.amount):,}",
        "currency": payment.currency or "BDT",
        "payment_method": payment.provider,
        "status": "PAID" if is_paid else payment.status,
        "paid_at": paid_date.strftime("%d %B %Y"),
        "paid_at_iso": paid_date.isoformat(),
        "verification_token": token,
        "verification_url": verify_url,
        "verified": is_paid,
    }


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    from pathlib import Path
    candidates = (
        [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        ]
    )
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_receipt_pdf_bytes(receipt_data: dict) -> bytes:
    """Render an institutional printable A4-proportioned Payment Receipt PDF with QR verification."""
    width, height = 1240, 1754
    img = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    font_h1 = _load_font(34, bold=True)
    font_h2 = _load_font(24, bold=True)
    font_label = _load_font(20, bold=False)
    font_val = _load_font(22, bold=True)
    font_sm = _load_font(16, bold=False)

    # Outer institutional frame
    draw.rectangle((40, 40, width - 40, height - 40), outline="#0F1E42", width=4)
    draw.rectangle((52, 52, width - 52, 250), fill="#0F1E42")
    draw.rectangle((52, 244, width - 52, 254), fill="#F59E0B")

    draw.text((90, 85), "PGCB — POWER GRID DIPLOMA ENGINEERS ASSOCIATION", font=font_h2, fill="#FBBF24")
    draw.text((90, 130), "OFFICIAL DIGITAL PAYMENT RECEIPT", font=font_h1, fill="#FFFFFF")
    draw.text((90, 185), "Power Grid Company of Bangladesh PLC • Central Secretariat, Aftabnagar, Dhaka", font=font_sm, fill="#93C5FD")

    # Status Badge
    draw.rounded_rectangle((width - 300, 95, width - 90, 175), radius=12, fill="#065F46", outline="#10B981", width=2)
    draw.text((width - 255, 120), f"STATUS: {receipt_data['status']}", font=font_val, fill="#ECFDF5")

    # Receipt metadata rows
    rows = [
        ("Receipt No", str(receipt_data.get("receipt_no") or "—")),
        ("Transaction", str(receipt_data.get("transaction_ref") or "—")),
        ("Member", str(receipt_data.get("member_name_en") or receipt_data.get("member_name_bn") or "—")),
        ("Membership ID", str(receipt_data.get("membership_id") or "—")),
        ("Purpose", str(receipt_data.get("purpose") or "MEMBERSHIP")),
        ("Amount", f"BDT {int(receipt_data.get('amount', 0)):,} ({receipt_data.get('amount_formatted', '')})"),
        ("Payment Method", str(receipt_data.get("payment_method") or "—")),
        ("Status", str(receipt_data.get("status") or "PAID")),
        ("Date", str(receipt_data.get("paid_at") or "—")),
    ]

    y = 320
    for label, val in rows:
        draw.rectangle((90, y, width - 90, y + 86), fill="#F8FAFC", outline="#E2E8F0", width=2)
        draw.text((120, y + 28), f"{label}:", font=font_label, fill="#475569")
        draw.text((440, y + 26), val, font=font_val, fill="#0F172A")
        y += 104

    # QR Verification block
    qr_url = receipt_data.get("verification_url") or f"{settings.frontend_url.rstrip('/')}/verify"
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0F1E42", back_color="#FFFFFF").convert("RGB").resize((240, 240))
    img.paste(qr_img, (90, 1320))

    draw.text((360, 1345), "CRYPTOGRAPHIC QR VERIFICATION", font=font_h2, fill="#0F1E42")
    draw.text((360, 1390), "Scan the QR code to verify this receipt against the PGCB ledger.", font=font_label, fill="#334155")
    draw.text((360, 1430), f"Verification URL: {qr_url}", font=font_sm, fill="#64748B")
    draw.text((360, 1475), "This is a computer-generated official receipt and requires no physical signature.", font=font_sm, fill="#64748B")

    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=300.0)
    return buf.getvalue()
