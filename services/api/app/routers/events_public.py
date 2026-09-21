from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Event

router = APIRouter(prefix='/event', tags=['event-detail'])

@router.get('/{event_id}')
def event_detail(event_id: int, db: Session = Depends(get_db)):
    item = db.scalar(select(Event).where(Event.id == event_id, Event.is_published == True))
    if not item:
        raise HTTPException(404, 'Event not found')
    return {'id': item.id, 'title_bn': item.title_bn, 'title_en': item.title_en, 'description_bn': item.description_bn, 'event_date': item.event_date, 'location_bn': item.location_bn, 'cover_image_url': item.cover_image_url, 'registration_enabled': item.registration_enabled, 'capacity': item.capacity, 'registration_deadline': item.registration_deadline, 'fee_amount': item.fee_amount, 'fee_currency': item.fee_currency}
