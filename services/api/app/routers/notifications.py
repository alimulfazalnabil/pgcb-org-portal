"""
Member Notification Center & Settings Router for PGCB Organization Portal.
Supports notification feeds with actionable links, unread counters, bulk read actions,
and category/channel preference settings matrix.
"""

from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import current_user
from app.db.session import get_db
from app.models import Notification, NotificationPreference, User
from app.services.notification_service import NotificationService

router = APIRouter(prefix='/member', tags=['member-notifications'])


def _relative_time_display(dt: datetime, now: datetime) -> tuple[str, str]:
    diff = now - dt
    secs = int(diff.total_seconds())
    if secs < 60:
        return 'just now', 'এইমাত্র'
    if secs < 3600:
        mins = secs // 60
        return f'{mins}m ago', f'{mins} মিনিট আগে'
    if secs < 86400:
        hrs = secs // 3600
        return f'{hrs}h ago', f'{hrs} ঘণ্টা আগে'
    days = secs // 86400
    if days == 1:
        return 'yesterday', 'গতকাল'
    return f'{days}d ago', f'{days} দিন আগে'


@router.get('/notifications')
def list_member_notifications(
    request: Request,
    status: str | None = Query(None, pattern='^(all|unread)$'),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    List member notifications with unread counts and actionable link cards.
    """
    now = datetime.utcnow()
    base_filter = [Notification.user_id == user.id]

    if status == 'unread':
        base_filter.append(Notification.read_at.is_(None))

    rows = db.scalars(
        select(Notification)
        .where(*base_filter)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    unread_count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id,
            Notification.read_at.is_(None),
        )
    ) or 0

    total_count = db.scalar(
        select(func.count(Notification.id)).where(Notification.user_id == user.id)
    ) or 0

    items = []
    for n in rows:
        time_en, time_bn = _relative_time_display(n.created_at, now)
        action_data = None
        if n.data_json and isinstance(n.data_json, dict) and 'action' in n.data_json:
            action_data = n.data_json['action']

        items.append({
            'id': n.id,
            'title_bn': n.title_bn,
            'title_en': n.title_en or n.title_bn,
            'body_bn': n.body_bn,
            'body_en': n.body_en or n.body_bn,
            'type': n.notification_type,
            'priority': n.priority or 'NORMAL',
            'is_read': n.read_at is not None,
            'indicator': '○' if n.read_at is not None else '●',
            'relative_time': time_en,
            'read_at': n.read_at.isoformat() if n.read_at else None,
            'created_at': n.created_at.isoformat() if n.created_at else None,
            'relative_time_en': time_en,
            'relative_time_bn': time_bn,
            'action': action_data,
            'data': n.data_json,
        })

    # Backward compatibility: legacy callers expecting raw list when no ?status= filter is passed
    if 'status' not in request.query_params:
        return items

    return {
        'items': items,
        'unread_count': unread_count,
        'total_count': total_count,
    }


@router.get('/notifications/unread-count')
def get_member_unread_count(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Return count of unread notifications for active user."""
    count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id,
            Notification.read_at.is_(None),
        )
    ) or 0
    return {'unread_count': count}


@router.post('/notifications/{notification_id}/read')
def mark_notification_as_read(
    notification_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read."""
    n = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
    )
    if not n:
        raise HTTPException(404, 'Notification not found')

    if not n.read_at:
        n.read_at = datetime.utcnow()
        db.commit()

    return {'ok': True, 'id': n.id, 'read_at': n.read_at.isoformat()}


@router.post('/notifications/read-all')
def mark_all_notifications_as_read(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Mark all unread notifications for user as read."""
    now = datetime.utcnow()
    unread_rows = db.scalars(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.read_at.is_(None),
        )
    ).all()

    for r in unread_rows:
        r.read_at = now
    db.commit()

    return {'ok': True, 'updated': len(unread_rows)}


@router.get('/notification-settings')
def get_notification_settings(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full matrix of notification preferences."""
    preferences = NotificationService.get_user_preferences(db, user.id)
    return {
        'ok': True,
        'preferences': preferences,
        'categories': [
            {
                'id': 'MEMBERSHIP',
                'title_bn': 'সদস্যপদ ও নবায়ন (Membership & Renewal)',
                'description_bn': 'সদস্যপদ অনুমোদন, মেয়াদ শেষ ও নবায়ন সংক্রান্ত নোটিফিকেশন',
            },
            {
                'id': 'EVENTS',
                'title_bn': 'ইভেন্ট ও সম্মেলন (Events & Conferences)',
                'description_bn': 'ইভেন্ট নিবন্ধন নিশ্চিতকরণ, রিমাইন্ডার ও টিকিট সংক্রান্ত তথ্য',
            },
            {
                'id': 'PAYMENTS',
                'title_bn': 'পেমেন্ট ও রসিদ (Payments & Receipts)',
                'description_bn': 'পেমেন্ট নিশ্চিতকরণ, চালান ও অফিশিয়াল মানি রিসিট',
            },
            {
                'id': 'SYSTEM',
                'title_bn': 'সিকিউরিটি ও সিস্টেম (Security & System)',
                'description_bn': 'লগইন অ্যালার্ট, পাসওয়ার্ড পরিবর্তন ও গুরুত্বপূর্ণ নিরাপত্তা বার্তা',
            },
            {
                'id': 'ANNOUNCEMENTS',
                'title_bn': 'অফিশিয়াল সার্কুলার ও নোটিশ (Notices & Circulars)',
                'description_bn': 'কেন্দ্রীয় নির্বাহী কমিটির সার্কুলার, প্রেস রিলিজ ও জরুরি নোটিশ',
            },
        ],
    }


@router.patch('/notification-settings')
@router.put('/notification-settings')
def update_notification_settings(
    payload: dict,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Update user notification preferences across channels."""
    settings_data = payload.get('preferences') or payload
    updated_prefs = NotificationService.update_user_preferences(
        db=db,
        user_id=user.id,
        updates=settings_data,
    )
    return {
        'ok': True,
        'message': 'নোটিফিকেশন সেটিংস সফলভাবে সংরক্ষিত হয়েছে।',
        'preferences': updated_prefs,
    }
