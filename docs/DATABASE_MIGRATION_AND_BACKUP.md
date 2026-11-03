# PGCB Organization Portal — Database Migration & Backup Guide
**Project:** PGCB Organization Portal (`pgcb-org-portal`)  
**Database:** PostgreSQL (Psycopg 3)  
**Migration Tool:** Alembic  
**Target Platform:** HostSeba cPanel Shared Hosting

---

## 1. Database Architecture & Alembic Revisions

The PGCB Organization Portal database schema consists of 21 core institutional tables managed through sequential Alembic revisions:

```text
services/api/alembic/versions/
├── bca12bda0867_initial_portal_schema.py
├── 7e3d5d4c1f20_v03_security_and_reset_tokens.py
├── ab42d1ef6c70_v04_admin_mfa.py
├── cd57f8a2e1b9_v05_operations_and_sessions.py
├── ef6c3a8a2e10_v06_account_security.py
├── f91a2c7d4e10_v07_transactions_workflows_certificates.py
├── a8d4f1e2c901_v08_notices_and_documents.py
├── c2048b9f1d09_v09_member_search_indexes.py
├── d41f9a8b3c12_v10_sprint1_payment_and_schema_hardening.py
├── e52b1c9d4a23_v11_cms_and_communications.py
├── f83a2d7e9b12_v12_institutional_intelligence_ai.py
├── a94b3e8f1c25_v13_rc1_roles_and_applications.py
├── b72c9f4e8d11_v14_rc1_complete_21_table_schema.py
└── e8f4a1b9c321_v15_phase6_events_notifications_phase7_support_tickets.py [HEAD]
```

---

## 2. Running Migrations in Production

### Method A — Via cPanel Web UI (No SSH Required)
This is the recommended method on HostSeba shared hosting where SSH terminal access is disabled.

1. In cPanel, navigate to **Software $\to$ Setup Python App**.
2. Click the edit icon for `api.powergriddiprocoush.org`.
3. Verify that `DATABASE_URL` is properly configured in the **Environment variables** table.
4. Scroll down to the **Execute python script** box:
   - Enter: `scripts/run_migrations.py`
   - Click **Run Script**.
5. Inspect the execution log:
   - In cPanel **File Manager**, open `/home/powergri/repositories/pgcb-org-portal/services/api/migration_run.log`.
   - Confirm that the log ends with:
     ```text
     [SUCCESS] Database schema is now at HEAD (latest revision).
     Migration completed successfully.
     ```

### Method B — Via Command Line / SSH (If Enabled)
If SSH access is available:
```bash
source /home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11/bin/activate
cd /home/powergri/repositories/pgcb-org-portal/services/api

# Run migrations to HEAD
python scripts/run_migrations.py

# Or directly via alembic CLI:
alembic upgrade head
```

---

## 3. Database Backup Procedures

### 3.1 Automated Script Backups (`backup_pgcb.py`)
The repository includes a dedicated backup utility: `services/api/scripts/backup_pgcb.py`.
- Generates compressed gzip archives (`pgcb_backup_<timestamp>.sql.gz`).
- Computes SHA-256 integrity checksums saved to manifest files.
- Enforces tiered retention:
  - Daily backups: 14 retained
  - Weekly backups: 8 retained
  - Monthly backups: 12 retained
- Masks all database credentials in log output.

**Running the backup script via cPanel:**
1. In cPanel **Setup Python App**, scroll to **Execute python script**.
2. Enter: `scripts/backup_pgcb.py`
3. Click **Run Script**.
4. Backups are stored in `/home/powergri/storage/backups/`.

### 3.2 Manual Backups via cPanel phpPgAdmin
If you prefer exporting backups directly through the web browser:
1. In cPanel, navigate to **Databases $\to$ phpPgAdmin**.
2. Click your database (`powergri_pgcb_prod`) in the left sidebar.
3. Click the **Export** tab in the top navigation.
4. Select:
   - Format: **SQL**
   - Options: **Structure and Data**
   - Compression: **Gzip**
5. Click **Export** to download the database dump directly to your local workstation.

---

## 4. Disaster Recovery & Database Restoration

### Restoring via cPanel phpPgAdmin
1. Log in to cPanel $\to$ **phpPgAdmin**.
2. Select your target database (`powergri_pgcb_prod`).
3. Click **SQL** in the top navigation.
4. Upload or paste your SQL backup script.
5. Click **Execute**.

### Restoring via Command Line
```bash
gunzip -c /home/powergri/storage/backups/pgcb_backup_20261103.sql.gz | psql -U powergri_pgcbuser -d powergri_pgcb_prod -h localhost
```
