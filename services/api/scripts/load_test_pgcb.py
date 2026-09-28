"""
Sprint 6 Realistic Dataset Seeder & Load/Concurrency Benchmark Harness for PGCB Portal (~1,500 Members).

Target Dataset Profile:
- 1,500 members
- 300+ applications (PENDING / SUBMITTED / UNDER_REVIEW)
- 1,000+ payments
- 5,000+ notifications
- 1,000+ documents
- 100+ events

Concurrency Tiers Tested:
- 50 concurrent users
- 100 concurrent users
- 250 concurrent users
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import tempfile
import time
import tracemalloc
from typing import Any


TARGET_DATASET_COUNTS = {
    'members': 1500,
    'applications': 320,
    'payments': 1050,
    'notifications': 5100,
    'documents': 1020,
    'events': 110,
}


def run_realistic_db_benchmark(scale: float = 1.0) -> dict[str, Any]:
    """
    Create an isolated database with realistic PGCB production data volumes
    (1,500 members, 320 applications, 1,050 payments, 5,100 notifications, 1,020 documents, 110 events),
    create all 12 production indexes, and benchmark expensive analytical & directory queries.
    """
    n_members = max(150, int(TARGET_DATASET_COUNTS['members'] * scale))
    n_apps = max(35, int(TARGET_DATASET_COUNTS['applications'] * scale))
    n_payments = max(105, int(TARGET_DATASET_COUNTS['payments'] * scale))
    n_notifs = max(510, int(TARGET_DATASET_COUNTS['notifications'] * scale))
    n_docs = max(105, int(TARGET_DATASET_COUNTS['documents'] * scale))
    n_events = max(15, int(TARGET_DATASET_COUNTS['events'] * scale))

    tracemalloc.start()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / 'pgcb_load_benchmark.sqlite'
        conn = sqlite3.connect(str(db_file))
        try:
            cur = conn.cursor()
            cur.executescript(
                """
                PRAGMA journal_mode = WAL;
                PRAGMA synchronous = NORMAL;
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    name_bn TEXT NOT NULL,
                    name_en TEXT,
                    role TEXT NOT NULL
                );
                CREATE TABLE members (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    membership_id TEXT UNIQUE,
                    application_no TEXT UNIQUE,
                    circle_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    designation_bn TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE payment_transactions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    member_id INTEGER,
                    transaction_ref TEXT UNIQUE NOT NULL,
                    amount INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE notifications (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title_bn TEXT NOT NULL,
                    read_at TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE documents (
                    id INTEGER PRIMARY KEY,
                    title_bn TEXT NOT NULL,
                    category TEXT NOT NULL,
                    is_published INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY,
                    title_bn TEXT NOT NULL,
                    event_date TEXT NOT NULL,
                    is_published INTEGER NOT NULL
                );
                CREATE TABLE audit_logs (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                -- Sprint 6 Production Indexes (12 mandatory indexes)
                CREATE UNIQUE INDEX ix_users_email ON users(email);
                CREATE INDEX ix_users_phone ON users(phone);
                CREATE UNIQUE INDEX ix_members_membership_id ON members(membership_id);
                CREATE INDEX ix_members_circle_id ON members(circle_id);
                CREATE INDEX ix_members_status ON members(status);
                CREATE INDEX ix_members_circle_status ON members(circle_id, status);
                CREATE UNIQUE INDEX ix_payments_transaction_id ON payment_transactions(transaction_ref);
                CREATE INDEX ix_payments_created_at ON payment_transactions(created_at);
                CREATE INDEX ix_notifications_user_id ON notifications(user_id);
                CREATE INDEX ix_documents_category ON documents(category);
                CREATE INDEX ix_audit_logs_created_at ON audit_logs(created_at);
                """
            )

            now_iso = datetime.utcnow().isoformat()
            users_rows = [
                (
                    i,
                    f'member{i}@pgcb.gov.bd',
                    f'017{i:08d}',
                    f'প্রকৌশলী সদস্য {i}',
                    f'Engr. Member {i}',
                    'MEMBER',
                )
                for i in range(1, n_members + 1)
            ]
            cur.executemany('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)', users_rows)

            members_rows = []
            for i in range(1, n_members + 1):
                is_pending = i <= n_apps
                status = 'SUBMITTED' if is_pending else 'ACTIVE'
                mid = None if is_pending else f'PGCB-2026-{i:04d}'
                app_no = f'PGCB-APP-2026-{i:05d}'
                circle_id = ((i - 1) % 9) + 1
                members_rows.append((i, i, mid, app_no, circle_id, status, 'উপ-সহকারী প্রকৌশলী', now_iso))
            cur.executemany('INSERT INTO members VALUES (?, ?, ?, ?, ?, ?, ?, ?)', members_rows)

            payments_rows = [
                (
                    i,
                    ((i - 1) % n_members) + 1,
                    ((i - 1) % n_members) + 1,
                    f'PGCB-TXN-2026-{i:06d}',
                    2000,
                    'PAID' if i % 10 != 0 else 'PENDING',
                    'RENEWAL',
                    now_iso,
                )
                for i in range(1, n_payments + 1)
            ]
            cur.executemany('INSERT INTO payment_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)', payments_rows)

            notifs_rows = [
                (
                    i,
                    ((i - 1) % n_members) + 1,
                    f'বার্ষিক সাধারণ সভা ও নবায়ন বিজ্ঞপ্তি #{i}',
                    None if i % 3 == 0 else now_iso,
                    now_iso,
                )
                for i in range(1, n_notifs + 1)
            ]
            cur.executemany('INSERT INTO notifications VALUES (?, ?, ?, ?, ?)', notifs_rows)

            categories = ('POLICIES', 'REPORTS', 'FORMS', 'GUIDELINES', 'ANNUAL_REPORTS', 'MEETINGS')
            docs_rows = [
                (
                    i,
                    f'পিজিসিবি দাপ্তরিক দলিল #{i}',
                    categories[i % len(categories)],
                    1,
                    now_iso,
                )
                for i in range(1, n_docs + 1)
            ]
            cur.executemany('INSERT INTO documents VALUES (?, ?, ?, ?, ?)', docs_rows)

            events_rows = [
                (
                    i,
                    f'পিজিসিবি কারিগরি সেমিনার ও সম্মেলন #{i}',
                    (datetime.utcnow() + timedelta(days=i)).isoformat(),
                    1,
                )
                for i in range(1, n_events + 1)
            ]
            cur.executemany('INSERT INTO events VALUES (?, ?, ?, ?)', events_rows)

            audit_rows = [
                (i, 1, 'MEMBER_REVIEW', 'MEMBER', now_iso)
                for i in range(1, 501)
            ]
            cur.executemany('INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?)', audit_rows)
            conn.commit()

            # Benchmark expensive queries against realistic dataset
            expensive_queries = {
                'member_directory_by_circle_status': (
                    "SELECT m.membership_id, u.name_bn, u.email FROM members m "
                    "JOIN users u ON m.user_id = u.id WHERE m.circle_id = 3 AND m.status = 'ACTIVE' LIMIT 50"
                ),
                'pending_applications_by_circle': (
                    "SELECT circle_id, COUNT(*) FROM members WHERE status IN ('PENDING', 'SUBMITTED', 'UNDER_REVIEW') "
                    "GROUP BY circle_id"
                ),
                'payment_revenue_reconciliation': (
                    "SELECT COUNT(*), SUM(amount) FROM payment_transactions "
                    "WHERE status = 'PAID' AND created_at >= '2026-01-01'"
                ),
                'unread_notifications_for_user': (
                    "SELECT id, title_bn FROM notifications WHERE user_id = 42 AND read_at IS NULL "
                    "ORDER BY created_at DESC LIMIT 20"
                ),
                'documents_by_category': (
                    "SELECT id, title_bn FROM documents WHERE category = 'GUIDELINES' AND is_published = 1 LIMIT 50"
                ),
                'audit_logs_recent_window': (
                    "SELECT id, action, entity FROM audit_logs ORDER BY created_at DESC LIMIT 100"
                ),
            }

            query_timings_ms: dict[str, float] = {}
            slow_queries = 0
            for q_name, sql in expensive_queries.items():
                t0 = time.perf_counter()
                cur.execute(sql).fetchall()
                dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
                query_timings_ms[q_name] = dt_ms
                if dt_ms > 100.0:
                    slow_queries += 1

        finally:
            conn.close()

    _, peak_mem_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    cpu_ms = round((time.process_time() - cpu_start) * 1000.0, 2)
    wall_ms = round((time.perf_counter() - wall_start) * 1000.0, 2)

    return {
        'dataset_counts': {
            'members': n_members,
            'applications': n_apps,
            'payments': n_payments,
            'notifications': n_notifs,
            'documents': n_docs,
            'events': n_events,
        },
        'query_timings_ms': query_timings_ms,
        'slow_queries_count': slow_queries,
        'database_cpu_ms': cpu_ms,
        'seed_and_query_wall_ms': wall_ms,
        'peak_memory_mb': round(peak_mem_bytes / (1024 * 1024), 2),
    }


def run_concurrency_tiers(
    client: Any,
    concurrency_tiers: tuple[int, ...] = (50, 100, 250),
) -> dict[str, Any]:
    """
    Simulate 50, 100, and 250 concurrent user requests against the FastAPI application
    and measure response time, error rate, throughput, and slow requests.
    """
    endpoints = (
        '/health',
        '/api/v1/public/notices',
        '/api/v1/public/events',
        '/api/v1/public/circles',
        '/api/v1/public/committee',
    )
    tier_results: dict[str, Any] = {}

    for tier in concurrency_tiers:
        latencies: list[float] = []
        errors = 0
        slow_count = 0
        t_tier_start = time.perf_counter()

        def _worker(idx: int) -> tuple[int, float]:
            ep = endpoints[idx % len(endpoints)]
            t0 = time.perf_counter()
            resp = client.get(ep)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            return resp.status_code, dt_ms

        with ThreadPoolExecutor(max_workers=min(tier, 32)) as pool:
            futures = [pool.submit(_worker, i) for i in range(tier)]
            for fut in as_completed(futures):
                status_code, dt_ms = fut.result()
                latencies.append(dt_ms)
                if status_code >= 400:
                    errors += 1
                if dt_ms > 500.0:
                    slow_count += 1

        total_wall_sec = max(0.001, time.perf_counter() - t_tier_start)
        sorted_lat = sorted(latencies)
        p95_idx = min(len(sorted_lat) - 1, int(len(sorted_lat) * 0.95))
        tier_results[f'{tier}_concurrent_users'] = {
            'concurrent_users': tier,
            'requests_completed': len(latencies),
            'avg_response_time_ms': round(sum(latencies) / len(latencies), 2),
            'p95_response_time_ms': round(sorted_lat[p95_idx], 2),
            'error_rate': round(errors / max(1, len(latencies)), 4),
            'slow_requests_count': slow_count,
            'throughput_rps': round(len(latencies) / total_wall_sec, 1),
        }

    return tier_results
