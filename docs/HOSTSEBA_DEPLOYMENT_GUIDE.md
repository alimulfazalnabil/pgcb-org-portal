# HostSeba cPanel Production Deployment Guide
**Project:** PGCB Organization Portal (`pgcb-org-portal`)  
**Target Environment:** HostSeba Shared Hosting / cPanel / CloudLinux / Phusion Passenger / LiteSpeed  
**Backend API:** `https://api.powergriddiprocoush.org`  
**Frontend Website:** `https://powergriddiprocoush.org`  
**Deployment Strategy:** **100% Manual cPanel Web UI Deployment (No SSH or Terminal Required)**

---

## 1. Prerequisites Checklist

Before beginning the deployment, confirm you have access to:
1. **HostSeba cPanel Dashboard** (`https://hydra.hostseba.com:2083` or your account cPanel URL).
2. Domain and DNS records configured:
   - `powergriddiprocoush.org` $\to$ Server IP (DocumentRoot: `public_html` or designated web root)
   - `api.powergriddiprocoush.org` $\to$ Server IP (DocumentRoot: `api.powergriddiprocoush.org`)
3. A clean ZIP archive of the backend code (`services/api` including `alembic/`, `app/`, `scripts/`, `passenger_wsgi.py`, `wsgi.py`, `requirements.txt`).

---

## 2. Step-by-Step Deployment Procedure

### Step 1 — Create PostgreSQL Database & User in cPanel
HostSeba provides PostgreSQL management directly inside the cPanel dashboard.

1. Log in to cPanel.
2. In the **Databases** section, click **PostgreSQL Databases**.
3. Under **Create New Database**:
   - Enter database name: `pgcb_prod` (cPanel prefixes this with your account username, e.g., `powergri_pgcb_prod`).
   - Click **Create Database**.
4. Under **PostgreSQL Users $\to$ Add New User**:
   - Username: `pgcbuser` (resulting in `powergri_pgcbuser`).
   - Password: Click **Password Generator** to create a strong, random password (minimum 20 characters).
   - **Important:** Copy and securely save this password in your password manager.
   - Click **Create User**.
5. Under **Add User to Database**:
   - Select User: `powergri_pgcbuser`.
   - Select Database: `powergri_pgcb_prod`.
   - Click **Submit**.
   - Check **ALL PRIVILEGES** and click **Make Changes**.

---

### Step 2 — Create Persistent File Storage Directory (Outside Web Root)
Uploaded member documents, receipts, and photos must be stored safely outside the public web root to prevent unauthorized direct file access.

1. In cPanel, open **File Manager**.
2. Navigate to your user home directory (`/home/powergri/`).
3. Click **+ Folder** in the top toolbar:
   - Folder Name: `storage`
   - Location: `/home/powergri`
   - Click **Create New Folder**.
4. Double-click into `/home/powergri/storage` and create subfolder:
   - Folder Name: `uploads`
   - Location: `/home/powergri/storage`
5. Verify folder permissions are set to `755` (Read & Execute by server, Write by owner).

---

### Step 3 — Upload Backend Files via File Manager
1. In cPanel **File Manager**, navigate to your application root directory:
   - Target path: `/home/powergri/repositories/pgcb-org-portal/services/api`
   - *(If this directory does not exist, create it via File Manager)*.
2. Click **Upload** in the top toolbar.
3. Select and upload your deployment ZIP archive (e.g., `hostseba-update-api-fix.zip`).
4. Once upload completes (100%), return to File Manager, right-click the uploaded ZIP file, and click **Extract**.
5. Ensure the extracted files sit directly in `/home/powergri/repositories/pgcb-org-portal/services/api/`:
   ```text
   /home/powergri/repositories/pgcb-org-portal/services/api/
   ├── alembic/
   ├── alembic.ini
   ├── app/
   ├── passenger_wsgi.py
   ├── wsgi.py
   ├── requirements.txt
   └── scripts/
       ├── run_migrations.py
       └── backup_pgcb.py
   ```

---

### Step 4 — Configure CloudLinux Python Selector App
1. Return to the cPanel main dashboard.
2. In the **Software** section, click **Setup Python App**.
3. Under **Web Applications**, click the edit pencil icon next to `api.powergriddiprocoush.org` (or click **Create Application** if configuring freshly):
   - **Python version:** Select `3.11` (specifically `3.11.17` or latest 3.11.x).
   - **Application root:** `repositories/pgcb-org-portal/services/api`
   - **Application URL:** `api.powergriddiprocoush.org`
   - **Application startup file:** `passenger_wsgi.py`
   - **Application Entry point:** `application`
4. Under **Environment variables**, click **Add variable** for each of the following required production settings:

| Name | Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Enforces production security and strict validation |
| `DATABASE_URL` | `postgresql+psycopg://<CPANEL_DB_USER>:<URL_ENCODED_PASSWORD>@localhost:5432/<CPANEL_DB_NAME>` | Full Psycopg 3 connection string |
| `JWT_SECRET` | *(64-character random string)* | Used for HS256 signing of auth tokens |
| `MFA_ENCRYPTION_KEY` | *(32-byte base64 Fernet key)* | For encrypting TOTP secrets |
| `FRONTEND_URL` | `https://powergriddiprocoush.org` | Primary frontend domain |
| `ALLOWED_ORIGINS` | `https://powergriddiprocoush.org` | CORS and CSRF allowed origin |
| `STORAGE_BACKEND` | `local` | HostSeba filesystem storage |
| `STORAGE_ROOT` | `/home/powergri/storage` | Persistent storage root outside web root |
| `UPLOAD_DIR` | `/home/powergri/storage/uploads` | Uploaded document storage directory |
| `ALLOW_STARTUP_FALLBACK` | `false` | Fails fast on misconfiguration |
| `RATE_LIMIT_ENABLED` | `true` | Enables in-memory sliding window rate limiting |
| `COOKIE_NAME` | `pgcb_access_token` | Session cookie identifier |

5. Click **Save** at the top of the page.

---

### Step 5 — Install Dependencies via cPanel
1. In the **Setup Python App** interface for `api.powergriddiprocoush.org`:
2. Locate the **Configuration files** section.
3. Ensure `requirements.txt` is listed. If not, type `requirements.txt` in the box and click **Add**.
4. Click the **Run Pip Install** button next to `requirements.txt`.
5. Wait for the notification stating that pip installation succeeded. CloudLinux will install all required packages (including FastAPI, SQLAlchemy, Psycopg 3, a2wsgi, cryptography, pydantic-settings) into the isolated Python 3.11 virtual environment.

---

### Step 6 — Run Database Migrations (Zero Terminal Required)
You can execute Python scripts directly through the cPanel Python Selector interface without an SSH shell:

1. In **Setup Python App**, scroll down to the **Execute python script** section.
2. In the input box **"Enter the path to the script file"**, enter:
   ```text
   scripts/run_migrations.py
   ```
3. Click **Run Script**.
4. The script will initialize Alembic, apply all version migrations up to HEAD, and record the result.
5. **Verify the migration:**
   - In cPanel **File Manager**, navigate to `/home/powergri/repositories/pgcb-org-portal/services/api/`.
   - Open `migration_run.log`.
   - Confirm the log concludes with:
     ```text
     [SUCCESS] Database schema is now at HEAD (latest revision).
     Migration completed successfully.
     ```

---

### Step 7 — Bootstrap the Super Administrator Account
To create or update the initial Super Administrator login:

1. In **Setup Python App**, temporarily add these two environment variables:
   - `ADMIN_EMAIL` = `secretariat@powergriddiprocoush.org`
   - `ADMIN_PASSWORD` = `YourStrongAdminPassword123!`
   - `ADMIN_NAME` = `সিস্টেম অ্যাডমিন`
2. Click **Save**.
3. In the **Execute python script** field, enter:
   ```text
   app/scripts/create_admin.py
   ```
4. Click **Run Script**.
5. Once complete, you may remove `ADMIN_PASSWORD` from the environment variables in cPanel for security.

---

### Step 8 — Restart Application & Verification
1. In **Setup Python App**, click the **Restart** button at the top of the page.
   *(Alternatively, in File Manager create or touch `/home/powergri/repositories/pgcb-org-portal/services/api/tmp/restart.txt`)*.
2. Test the API in your browser or with cURL:
   - **Process Liveness:**  
     `https://api.powergriddiprocoush.org/live` $\to$ `{"status": "alive", "service": "pgcb-api"}`
   - **Database Health Check:**  
     `https://api.powergriddiprocoush.org/health` $\to$ `{"status": "ok", "database": "connected"}`
   - **API Readiness Check:**  
     `https://api.powergriddiprocoush.org/ready` $\to$ `{"status": "ready", "database": "ok"}`
   - **Swagger OpenAPI Documentation:**  
     `https://api.powergriddiprocoush.org/docs`

---

## 3. Maintenance & Troubleshooting

### Viewing Logs via File Manager
If the application fails to start or an error occurs:
1. Open cPanel **File Manager**.
2. Navigate to `/home/powergri/repositories/pgcb-org-portal/services/api/`.
3. Check these log files:
   - `passenger_startup.log`: Captures any import error, missing package, or configuration validation failure at startup with sensitive credentials masked.
   - `migration_run.log`: Captures output from Alembic database migrations.
   - `stderr.log` / `error_log`: LiteSpeed and Passenger web server error logs.

### Rolling Back or Emergency Overrides
If PostgreSQL credentials need updating:
1. Update the `DATABASE_URL` in cPanel **Setup Python App** $\to$ **Environment variables**.
2. Click **Save**.
3. Click **Restart**.
