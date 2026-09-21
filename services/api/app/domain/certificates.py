from __future__ import annotations

from datetime import datetime
from pathlib import Path
import secrets
import hashlib

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.models import Certificate, EventRegistration, Member
from app.services import BASE_STORAGE


def _font(size: int):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def generate_event_certificate(db: Session, registration: EventRegistration, event_title_bn: str, member: Member | None = None):
    certificate_no = f'PGCB-CERT-{datetime.utcnow().year}-{secrets.token_hex(5).upper()}'
    raw_token = secrets.token_urlsafe(28)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    canvas = Image.new('RGB', (1600, 1100), 'white')
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((40, 40, 1560, 1060), outline=(10, 30, 55), width=8)
    draw.rectangle((65, 65, 1535, 1035), outline=(0, 168, 120), width=3)
    draw.text((800, 170), 'POWER GRID DIPLOMA ENGINEERS ASSOCIATION', anchor='mm', font=_font(46), fill=(10, 30, 55))
    draw.text((800, 280), 'CERTIFICATE OF PARTICIPATION', anchor='mm', font=_font(58), fill=(242, 140, 0))
    draw.text((800, 430), 'This certificate is proudly presented to', anchor='mm', font=_font(30), fill=(70, 70, 70))
    draw.text((800, 540), registration.name, anchor='mm', font=_font(60), fill=(0, 110, 90))
    draw.text((800, 660), f'for participation in {event_title_bn}', anchor='mm', font=_font(28), fill=(70, 70, 70))
    draw.text((800, 755), f'Certificate No: {certificate_no}', anchor='mm', font=_font(24), fill=(30, 50, 80))
    draw.text((800, 810), f'Issued: {datetime.utcnow():%d %B %Y}', anchor='mm', font=_font(24), fill=(30, 50, 80))
    draw.text((800, 935), 'Officially verifiable certificate', anchor='mm', font=_font(23), fill=(0, 168, 120))

    folder = BASE_STORAGE / 'certificates'
    folder.mkdir(parents=True, exist_ok=True)
    png_path = folder / f'{certificate_no}.png'
    pdf_path = folder / f'{certificate_no}.pdf'
    canvas.save(png_path, format='PNG', optimize=True)
    canvas.save(pdf_path, format='PDF', resolution=150.0)

    cert = Certificate(
        certificate_no=certificate_no,
        recipient_name=registration.name,
        title_bn=f'Participation — {event_title_bn}',
        issue_date=datetime.utcnow(),
        event_registration_id=registration.id,
        member_id=member.id if member else None,
        verification_token_hash=token_hash,
        storage_path=str(png_path),
        pdf_path=str(pdf_path),
    )
    db.add(cert)
    db.flush()
    return cert, raw_token
