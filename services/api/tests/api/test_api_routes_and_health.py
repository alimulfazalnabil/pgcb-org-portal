from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_ready_endpoints():
    health = client.get('/health')
    assert health.status_code == 200
    data = health.json()
    assert data['status'] == 'ok'
    assert data['database'] == 'connected'
    assert data['version'] == '1.0.0-rc1'

    v1_health = client.get('/api/v1/health')
    assert v1_health.status_code == 200
    assert v1_health.json()['database'] == 'connected'

    ready = client.get('/ready')
    assert ready.status_code == 200
    assert ready.json()['status'] == 'ready'


def test_public_cms_and_directory_endpoints():
    for path in (
        '/api/v1/public/settings',
        '/api/v1/public/members',
        '/api/v1/public/circulars',
        '/api/v1/public/events',
        '/api/v1/public/committee',
        '/api/v1/public/circles',
        '/api/v1/notices',
        '/api/v1/documents',
    ):
        res = client.get(path)
        assert res.status_code == 200, f'Failed endpoint {path}: {res.text}'


def test_cms_create_review_publish_and_notifications():
    """
    Validate CMS (Create -> Review -> Publish) and Notifications (In-app delivery):
    1. CONTENT_EDITOR creates draft notice (cannot publish directly -> 403)
    2. CONTENT_ADMIN reviews and publishes notice -> 200
    3. Public notice feed reflects the published notice
    4. Active members receive in-app notification of publication
    """
    from datetime import datetime
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.models import Member, User

    ts = int(datetime.utcnow().timestamp() * 1000) + 909
    editor_email = f'cms_editor_{ts}@pgcb.gov.bd'
    publisher_email = f'cms_publisher_{ts}@pgcb.gov.bd'
    member_email = f'cms_reader_{ts}@pgcb.gov.bd'
    password = 'CmsWorkflowPass123!'

    for em, name_en, pfx in (
        (editor_email, 'CMS Editor', '017'),
        (publisher_email, 'CMS Publisher', '018'),
        (member_email, 'CMS Reader', '019'),
    ):
        r = client.post(
            '/api/v1/auth/register',
            json={
                'name_bn': name_en,
                'name_en': name_en,
                'email': em,
                'phone': f'{pfx}{ts % 100000000:08d}',
                'password': password,
                'designation_bn': 'সহকারী প্রকৌশলী',
            },
        )
        assert r.status_code in (200, 201)

    with SessionLocal() as db:
        ed = db.scalar(select(User).where(User.email == editor_email))
        ed.email_verified = True
        ed.role = 'CONTENT_EDITOR'

        pub = db.scalar(select(User).where(User.email == publisher_email))
        pub.email_verified = True
        pub.role = 'CONTENT_ADMIN'

        rd = db.scalar(select(User).where(User.email == member_email))
        rd.email_verified = True
        rd_member = db.scalar(select(Member).where(Member.user_id == rd.id))
        rd_member.status = 'ACTIVE'
        db.commit()

    ed_login = client.post('/api/v1/auth/login', json={'email': editor_email, 'password': password})
    ed_headers = {'Authorization': f"Bearer {ed_login.cookies.get('pgcb_access_token') or ed_login.json().get('access_token')}"}

    pub_login = client.post('/api/v1/auth/login', json={'email': publisher_email, 'password': password})
    pub_headers = {'Authorization': f"Bearer {pub_login.cookies.get('pgcb_access_token') or pub_login.json().get('access_token')}"}

    rd_login = client.post('/api/v1/auth/login', json={'email': member_email, 'password': password})
    rd_headers = {'Authorization': f"Bearer {rd_login.cookies.get('pgcb_access_token') or rd_login.json().get('access_token')}"}

    # 1a. CONTENT_EDITOR cannot publish directly
    direct_pub = client.post(
        '/api/v1/notices',
        headers=ed_headers,
        json={
            'title_bn': f'আরসি-১ জরুরি বিজ্ঞপ্তি #{ts}',
            'title_en': f'RC1 Urgent Notice #{ts}',
            'content_bn': 'কেন্দ্রীয় কমিটির সভা সংক্রান্ত বিজ্ঞপ্তি।',
            'priority': 'URGENT',
            'category': 'GENERAL',
            'is_published': True,
        },
    )
    assert direct_pub.status_code == 403

    # 1b. CONTENT_EDITOR creates DRAFT notice
    draft_res = client.post(
        '/api/v1/notices',
        headers=ed_headers,
        json={
            'title_bn': f'আরসি-১ জরুরি বিজ্ঞপ্তি #{ts}',
            'title_en': f'RC1 Urgent Notice #{ts}',
            'content_bn': 'কেন্দ্রীয় কমিটির সভা সংক্রান্ত বিজ্ঞপ্তি।',
            'priority': 'URGENT',
            'category': 'GENERAL',
            'is_published': False,
        },
    )
    assert draft_res.status_code == 201
    notice_id = draft_res.json()['id']
    assert draft_res.json()['is_published'] is False

    # Draft notice must not be publicly accessible yet
    assert client.get(f'/api/v1/notices/{notice_id}').status_code == 404

    # 2. CONTENT_ADMIN reviews and publishes the notice
    publish_res = client.put(
        f'/api/v1/notices/{notice_id}',
        headers=pub_headers,
        json={'is_published': True, 'is_pinned': True},
    )
    assert publish_res.status_code == 200
    assert publish_res.json()['is_published'] is True

    # 3. Public notice endpoint now serves the published notice
    pub_view = client.get(f'/api/v1/notices/{notice_id}')
    assert pub_view.status_code == 200
    assert pub_view.json()['title_en'] == f'RC1 Urgent Notice #{ts}'

    # 4. Member receives in-app notification of the published notice
    notifs = client.get('/api/v1/member/notifications', headers=rd_headers)
    assert notifs.status_code == 200
    assert any(f'#{ts}' in (n.get('title_bn') or '') or f'#{ts}' in (n.get('body_bn') or '') or n.get('type') in ('NOTICE', 'CMS') for n in notifs.json())

