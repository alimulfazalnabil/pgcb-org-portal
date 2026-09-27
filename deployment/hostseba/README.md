# HostSeba Production Deployment Guide (`PGCB Portal v1.1`)

## Step 1 — HostSeba / cPanel Intake Checklist (Collect When Active)

Once your HostSeba hosting account becomes active, record the following environment details (do **not** commit passwords or API secrets to Git):

| Item | Value / Status | Notes |
|---|---|---|
| **cPanel URL** | `https://...:2083` | HostSeba control panel URL |
| **Username** | `pgcborg` (example) | Linux home directory `/home/<username>` |
| **SSH access** | Enabled / Disabled | Required for `alembic upgrade head` & builds |
| **SSH port** | `22` (or custom port) | Check HostSeba welcome email |
| **PHP version** | 8.x (informational) | Not used by FastAPI/Next.js stack |
| **Python/Node.js support** | CloudLinux Selector / PM2 | Setup Python App & Setup Node.js App in cPanel |
| **Python version** | `3.11+` | For `services/api` |
| **Node.js version** | `20 LTS` | For `apps/web` |
| **PostgreSQL availability** | PostgreSQL `15+` / `16+` | Required (`postgresql+psycopg://...`) |
| **Database hostname** | `127.0.0.1` | Local socket or loopback |
| **Database name / user** | `pgcb_prod` / `pgcb_user` | Provisioned via cPanel PostgreSQL Databases |
| **Git deployment support** | cPanel Git Version Control | Pull from `main` branch |
| **Cron support** | cPanel Cron Jobs | Used for daily backups, notifications, expiry |
| **Available disk space** | `>= 10 GB` NVMe | For DB, uploads, and 30-day rolling backups |
| **RAM / process limits** | `>= 2 GB` RAM | Use `--workers 2` on shared/VPS hosting |
| **SSL status** | AutoSSL + Cloudflare Full (Strict) | HTTPS termination |

---

## Step 2 — Directory Structure on HostSeba

```text
/home/<cpanel_user>/
├── pgcb-org-portal/
│   ├── apps/web/                     # Next.js 15 Frontend (port 3000)
│   ├── services/api/                 # FastAPI Backend (port 8000)
│   │   ├── alembic/                  # PostgreSQL migrations
│   │   └── scripts/                  # Production contract, backup, & PGD-TEST-0001 verification
│   └── deployment/hostseba/
│       ├── README.md
│       ├── environment.example
│       ├── startup/
│       │   ├── passenger_wsgi.py
│       │   ├── start_api.sh
│       │   └── start_web.sh
│       ├── cron/
│       │   ├── crontab.txt
│       │   └── run_cron_jobs.sh
│       └── backup/
│           ├── backup_db_and_uploads.sh
│           └── restore_db_and_uploads.sh
├── pgcb_data/
│   ├── uploads/                      # Persistent member documents, photos, certificates
│   └── backups/                      # Daily encrypted/compressed DB + document archives
└── logs/                             # API, Web, and Cron logs
```

---

## Step 3 & 4 — PostgreSQL Setup, Migrations & Safe System Seed

1. **Create persistent directories**:
   ```bash
   mkdir -p ~/pgcb_data/uploads ~/pgcb_data/backups ~/logs
   chmod 750 ~/pgcb_data/uploads ~/pgcb_data/backups
   ```
2. **Configure production environment variables**:
   ```bash
   cp deployment/hostseba/environment.example services/api/.env
   nano services/api/.env
   ```
3. **Install backend dependencies & run Alembic migrations**:
   ```bash
   cd ~/pgcb-org-portal/services/api
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt

   # Verify production contract before touching the database
   python scripts/verify_production_contract.py --mode production

   # Apply PostgreSQL schema migrations
   alembic upgrade head

   # Seed ONLY required system data (9 official Grid Circles + optional ADMIN_EMAIL/ADMIN_PASSWORD)
   # NEVER populates fake member records in production
   python -m app.db.seed --production
   ```

---

## Step 5 & 6 — Build & Start Services

```bash
# Start FastAPI Backend (Port 8000)
bash ~/pgcb-org-portal/deployment/hostseba/startup/start_api.sh

# Build and Start Next.js Frontend (Port 3000)
bash ~/pgcb-org-portal/deployment/hostseba/startup/start_web.sh
```

---

## Step 7 — Configure Cron & Verify Backup/Restore Before Real Users

1. Install crontab entries from `deployment/hostseba/cron/crontab.txt`:
   ```bash
   crontab ~/pgcb-org-portal/deployment/hostseba/cron/crontab.txt
   ```
2. Run a full backup and restore verification test before allowing real members:
   ```bash
   bash ~/pgcb-org-portal/deployment/hostseba/backup/backup_db_and_uploads.sh
   ```

---

## Step 8 — First Production Test (`TEST MEMBER` / `PGD-TEST-0001`)

Before opening the portal to real members, execute the automated 11-step production verification (`Register -> Login -> Profile -> Document -> Membership application -> Admin approval (PGD-TEST-0001) -> Test payment -> Digital ID -> QR verification -> Certificate -> Notification`):

```bash
cd ~/pgcb-org-portal/services/api
source .venv/bin/activate
python scripts/run_first_production_test.py
```
