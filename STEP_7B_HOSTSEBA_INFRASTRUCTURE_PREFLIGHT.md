# Step 7B: HostSeba Infrastructure Preflight Checklist

**Project:** PGCB Organization Portal (`pgcb-org-portal`)  
**Target Environment:** HostSeba Shared Hosting / CloudLinux / Phusion Passenger / LiteSpeed / PostgreSQL  
**Staging Subdomain:** `staging-api.powergriddiprocoush.org`  
**Target Python Version:** `3.11`  
**Candidate Release Package:** `dist/hostseba-pgcb-api-v1.0.0-final.zip` (`5b05454cc09faaf820c284edb779b9f218dbb59f518e1ab1deaabb71b82024d3`)  
**Purpose:** Pre-deployment verification checklist for the server operator to determine whether the HostSeba cPanel hosting account satisfies all infrastructure requirements before attempting staging deployment.

---

> [!IMPORTANT]
> **SAFETY NOTICE: PRE-FLIGHT VERIFICATION ONLY**  
> This checklist is an inspection guide for manual cPanel audit. **Do not upload the application, do not run migrations, do not alter production DNS, and do not modify existing databases** during this audit.

---

## Preflight Summary Matrix

| # | Inspection Item | cPanel Location | Verification Target | Staging Blocker? | Operator Status |
|---|---|---|---|:---:|:---:|
| **1.1** | Python 3.11 Availability | **Software $\to$ Setup Python App** | Python `3.11` exists in version dropdown | **BLOCKER** | `[ ] PENDING` |
| **1.2** | Python App Configuration UI | **Software $\to$ Setup Python App** | Form allows setting App root, startup file, entry point | **BLOCKER** | `[ ] PENDING` |
| **1.3** | Standalone Script Execution | **Setup Python App $\to$ Execute Script** | UI provides "Execute python script" box | **WARNING** (Workaround available) | `[ ] PENDING` |
| **2.1** | PostgreSQL Databases Feature | **Databases $\to$ PostgreSQL Databases** | Tool allows creating databases & users | **BLOCKER** | `[ ] PENDING` |
| **2.2** | PostgreSQL User Privileges | **PostgreSQL Databases $\to$ Add User** | `ALL PRIVILEGES` grantable to DB user | **BLOCKER** | `[ ] PENDING` |
| **2.3** | Local Connection Host & Port | cPanel Info / Server Specs | `localhost` or socket on port `5432` reachable | **BLOCKER** | `[ ] PENDING` |
| **2.4** | phpPgAdmin Management Tool | **Databases $\to$ phpPgAdmin** | phpPgAdmin interface loads and authenticates | **WARNING** | `[ ] PENDING` |
| **3.1** | cPanel Pip Installer Support | **Setup Python App $\to$ Configuration files** | "Run Pip Install" button present for `requirements.txt` | **BLOCKER** | `[ ] PENDING` |
| **3.2** | Outbound PyPI Network Access | Server / Python App Environment | Server allows outbound HTTP/HTTPS to `pypi.org` | **BLOCKER** | `[ ] PENDING` |
| **3.3** | Linux x86_64 Binary Wheel Support | Virtualenv pip engine | Pip installs pre-compiled binary wheels (`psycopg`, etc.) | **BLOCKER** | `[ ] PENDING` |
| **4.1** | Phusion Passenger Startup | Web server / LiteSpeed integration | Passenger executes `passenger_wsgi.py` via LiteSpeed | **BLOCKER** | `[ ] PENDING` |
| **4.2** | Environment Variables UI | **Setup Python App $\to$ Environment variables** | Allows adding key-value environment variables | **WARNING** (Fallback: `.env`) | `[ ] PENDING` |
| **4.3** | App Restart Mechanism | **Setup Python App** or `tmp/restart.txt` | "Restart" button or `touch tmp/restart.txt` triggers reload | **BLOCKER** | `[ ] PENDING` |
| **5.1** | Subdomain Creation Capability | **Domains $\to$ Domains / Subdomains** | Can create `staging-api.powergriddiprocoush.org` | **BLOCKER** | `[ ] PENDING` |
| **5.2** | Document Root Isolation | **Domains $\to$ Document Root** | Isolated root (not nested inside `public_html`) | **BLOCKER** | `[ ] PENDING` |
| **5.3** | SSL Certificate (AutoSSL/Let's Encrypt) | **Security $\to$ SSL/TLS Status** | Free AutoSSL / Let's Encrypt available for subdomain | **BLOCKER** | `[ ] PENDING` |
| **6.1** | Storage Directory Location | **Files $\to$ File Manager** | Can create `/home/powergri/storage` outside web root | **BLOCKER** | `[ ] PENDING` |
| **6.2** | Disk Quota and Permissions | **cPanel Stats $\to$ Disk Usage** | Sufficient disk space ($\ge 500\text{ MB}$) and `0750` permissions | **BLOCKER** | `[ ] PENDING` |

---

## Detailed Inspection Protocols

### 1. Python Application Support

#### 1.1 Python 3.11 Availability
- **cPanel Path:** `Software` $\to$ `Setup Python App`
- **What to verify:**
  1. Open the **Setup Python App** interface.
  2. Click **Create Application**.
  3. Inspect the **Python version** dropdown menu.
  4. Confirm that Python `3.11` (e.g., `3.11.17` or latest `3.11.x`) is available as a selectable option.
- **What result to record:**
  - Exact Python 3.11 minor version shown in dropdown (e.g., `3.11.17`, `3.11.10`, etc.).
- **Staging Blocker:** **YES (BLOCKER)**. The backend codebase requires Python $\ge 3.11$ features (standard library additions, typing, and dependency compatibility).

#### 1.2 Python Application Configuration Fields
- **cPanel Path:** `Software` $\to$ `Setup Python App` $\to$ `Create Application`
- **What to verify:**
  1. Verify the form contains:
     - **Application root:** (text input for application directory path).
     - **Application URL:** (dropdown/input for domain/subdomain).
     - **Application startup file:** (field for `passenger_wsgi.py`).
     - **Application Entry point:** (field for callable `application`).
- **What result to record:**
  - Confirm all four configuration fields exist and are editable.
- **Staging Blocker:** **YES (BLOCKER)**.

#### 1.3 Standalone Script Execution UI
- **cPanel Path:** `Software` $\to$ `Setup Python App` (inside an existing or newly created app view)
- **What to verify:**
  1. Scroll down to the bottom of the application details page.
  2. Check whether a section titled **"Execute python script"** or an input labeled **"Enter path to script file"** is present.
- **What result to record:**
  - Record: `PRESENT` or `NOT PRESENT`.
- **Staging Blocker:** **NO (WARNING)**. If present, migrations and admin bootstrapping can be triggered with one click in the web UI. If absent, alternative execution via cPanel Cron Jobs (`/home/powergri/virtualenv/.../bin/python scripts/run_migrations.py`) or SSH is required.

---

### 2. PostgreSQL Infrastructure

#### 2.1 PostgreSQL Database & User Creation
- **cPanel Path:** `Databases` $\to$ `PostgreSQL Databases`
- **What to verify:**
  1. Verify the **PostgreSQL Databases** icon exists and opens without license or feature restriction errors.
  2. Verify the **Create New Database** form is functional.
  3. Verify the **PostgreSQL Users $\to$ Add New User** form is functional with password generator.
- **What result to record:**
  - Confirm the account username prefix (e.g., `powergri_`).
- **Staging Blocker:** **YES (BLOCKER)**. Production and staging require PostgreSQL (SQLite is blocked by safety validators in production/staging mode).

#### 2.2 Database User Privileges
- **cPanel Path:** `Databases` $\to$ `PostgreSQL Databases` $\to$ `Add User to Database`
- **What to verify:**
  1. Check the privilege assignment screen when linking a user to a database.
  2. Confirm **ALL PRIVILEGES** checkbox exists and grants table creation, schema modification, index creation, sequence manipulation, and data modification.
- **What result to record:**
  - Confirm `ALL PRIVILEGES` is available.
- **Staging Blocker:** **YES (BLOCKER)**. Alembic migrations create tables, constraints, indexes, and write migration revisions.

#### 2.3 Connection Host, Port, and Protocol
- **cPanel Path:** `Databases` $\to$ `PostgreSQL Databases` / Server Info
- **What to verify:**
  1. Confirm local PostgreSQL connections are accepted at hostname `localhost` or `127.0.0.1`.
  2. Confirm TCP port `5432` is open locally, or note whether a Unix socket path is standard on the server.
- **What result to record:**
  - Connection hostname (typically `localhost`) and port (`5432`).
- **Staging Blocker:** **YES (BLOCKER)**.

#### 2.4 phpPgAdmin Access
- **cPanel Path:** `Databases` $\to$ `phpPgAdmin`
- **What to verify:**
  1. Click **phpPgAdmin**.
  2. Confirm the phpPgAdmin web interface opens and displays the databases created in cPanel.
- **What result to record:**
  - Record: `ACCESSIBLE` or `INACCESSIBLE`.
- **Staging Blocker:** **NO (WARNING)**. phpPgAdmin is useful for manual query inspection and emergency SQL dumps, but application operations use Alembic.

---

### 3. Python Dependency Resolution & Pip

#### 3.1 cPanel Requirements.txt Installation Support
- **cPanel Path:** `Software` $\to$ `Setup Python App` $\to$ `Configuration files`
- **What to verify:**
  1. Locate the **Configuration files** section.
  2. Confirm an input box exists where `requirements.txt` can be added.
  3. Confirm the **Run Pip Install** button appears next to the filename.
- **What result to record:**
  - Confirm "Run Pip Install" UI is operational.
- **Staging Blocker:** **YES (BLOCKER)**.

#### 3.2 Outbound PyPI Network Access
- **cPanel Path:** Setup Python App / CloudLinux environment
- **What to verify:**
  1. Verify the server's firewall allows outbound HTTPS traffic from CloudLinux LVE processes to `pypi.org` and `files.pythonhosted.org`.
  2. *(Testable by running pip install on a simple package or checking with HostSeba support if outgoing pip connections are filtered).*
- **What result to record:**
  - Record whether pip downloads succeed without timeout or connection refused errors.
- **Staging Blocker:** **YES (BLOCKER)**.

#### 3.3 Binary Wheel Installation (Psycopg 3, CFFI, Cryptography)
- **cPanel Path:** CloudLinux Python Virtual Environment
- **What to verify:**
  1. Verify the environment accepts `manylinux` x86_64 pre-compiled binary wheels (specifically `psycopg[binary]`, `argon2-cffi`, `cryptography`, `pillow`).
  2. Confirm shared hosting GCC compilers are not required for these binary wheels.
- **What result to record:**
  - Confirm binary wheel support is active.
- **Staging Blocker:** **YES (BLOCKER)**. Shared hosting accounts do not typically have access to `gcc`, `make`, or kernel development headers.

---

### 4. Phusion Passenger Web Server Integration

#### 4.1 Passenger Application Startup
- **cPanel Path:** `Setup Python App` / LiteSpeed Web Server
- **What to verify:**
  1. Confirm HostSeba runs Phusion Passenger under LiteSpeed / Apache.
  2. Confirm passenger executes `passenger_wsgi.py` in the application root directory when HTTP requests arrive.
- **What result to record:**
  - Web server type (LiteSpeed with Passenger extension).
- **Staging Blocker:** **YES (BLOCKER)**.

#### 4.2 Environment Variables Management
- **cPanel Path:** `Software` $\to$ `Setup Python App` $\to$ `Environment variables`
- **What to verify:**
  1. Confirm the UI has an **Add variable** button allowing input of `Name` and `Value`.
  2. Confirm variables such as `APP_ENV`, `DATABASE_URL`, `JWT_SECRET`, and `STORAGE_ROOT` can be saved.
- **What result to record:**
  - Record: `SUPPORTED` or `NOT SUPPORTED`.
- **Staging Blocker:** **NO (WARNING)**. If the GUI variable table fails to propagate under LiteSpeed, the backend's `passenger_wsgi.py` includes built-in fallback logic that automatically loads `/home/powergri/.../.env` or `.env.production`.

#### 4.3 Application Restart Mechanism
- **cPanel Path:** `Setup Python App` / `File Manager`
- **What to verify:**
  1. In **Setup Python App**, check for the **Restart** button at the top of the interface.
  2. In **File Manager**, verify that creating or updating `tmp/restart.txt` inside the application directory causes Passenger to reload workers.
- **What result to record:**
  - Confirm Restart button or `tmp/restart.txt` functionality.
- **Staging Blocker:** **YES (BLOCKER)**. Required to apply code updates and restart workers cleanly.

---

### 5. Domains and Routing

#### 5.1 Staging Subdomain Creation
- **cPanel Path:** `Domains` $\to$ `Domains` (or `Subdomains`)
- **What to verify:**
  1. Confirm you can create the staging subdomain:  
     `staging-api.powergriddiprocoush.org`
  2. Verify that DNS for `powergriddiprocoush.org` resolves to HostSeba or that an `A` record can be added pointing `staging-api` to the server IP.
- **What result to record:**
  - Record server IP address and DNS propagation status.
- **Staging Blocker:** **YES (BLOCKER)**.

#### 5.2 Document Root Isolation
- **cPanel Path:** `Domains` $\to$ `Domains` $\to$ Document Root setting
- **What to verify:**
  1. Verify the DocumentRoot for `staging-api.powergriddiprocoush.org` is completely isolated from the main website:
     - Recommended DocumentRoot: `/home/powergri/staging-api.powergriddiprocoush.org`
     - **NOT** inside `/home/powergri/public_html/staging-api/`
- **What result to record:**
  - Exact Document Root path assigned in cPanel.
- **Staging Blocker:** **YES (BLOCKER)**. Nesting backend APIs inside `public_html` risks file leakage and rewrite collisions with frontend routing.

#### 5.3 SSL Certificate Availability (AutoSSL / Let's Encrypt)
- **cPanel Path:** `Security` $\to$ `SSL/TLS Status`
- **What to verify:**
  1. Locate `staging-api.powergriddiprocoush.org` in the SSL/TLS Status list.
  2. Verify that cPanel AutoSSL (Sectigo or Let's Encrypt) is enabled and can issue a valid certificate for the subdomain.
- **What result to record:**
  - AutoSSL provider (e.g., Let's Encrypt / cPanel Sectigo) and certificate status.
- **Staging Blocker:** **YES (BLOCKER)**. Cookie-based authentication and secure API transport require HTTPS.

---

### 6. Storage and Permissions

#### 6.1 Persistent Storage Outside Web Root
- **cPanel Path:** `Files` $\to$ `File Manager`
- **What to verify:**
  1. In `/home/powergri/`, verify you can create a top-level directory named `storage` (`/home/powergri/storage`).
  2. Confirm this path is **outside** `public_html` so files cannot be directly downloaded via web browser requests without going through the authenticated API.
- **What result to record:**
  - Full path created (e.g., `/home/powergri/storage`).
- **Staging Blocker:** **YES (BLOCKER)**. Prevents unauthenticated direct access to official member documents and payment receipts.

#### 6.2 Disk Space Quota & File Permissions
- **cPanel Path:** `Files` $\to$ `Disk Usage` and `cPanel Stats` sidebar
- **What to verify:**
  1. Check account disk space quota. Confirm at least **500 MB** of free disk space is available for Python virtualenv packages, database tables, and uploaded member assets.
  2. In File Manager, right-click `/home/powergri/storage` $\to$ **Change Permissions**. Confirm permissions can be set to `0750` or `0755`.
- **What result to record:**
  - Available disk space (MB/GB) and confirmed directory permission octal.
- **Staging Blocker:** **YES (BLOCKER)**.

---

## Operator Action Log Template

When executing this preflight audit on the HostSeba cPanel dashboard, record your observed findings in this table:

```text
================================================================================
HOSTSEBA INFRASTRUCTURE PREFLIGHT AUDIT LOG
Date of Audit: _______________
Operator Name: _______________
cPanel Account: powergri (https://hydra.hostseba.com:2083)
--------------------------------------------------------------------------------
1. Python 3.11 Available:            [ ] YES (Ver: ________)  [ ] NO
2. Setup Python App Configurable:    [ ] YES                  [ ] NO
3. Execute Script UI Available:      [ ] YES                  [ ] NO (Use cron)
4. PostgreSQL DB Creation:           [ ] YES (Prefix: _______)[ ] NO
5. PostgreSQL User ALL PRIVILEGES:   [ ] YES                  [ ] NO
6. PostgreSQL Local Host/Port:       [ ] localhost:5432       [ ] Other: _______
7. phpPgAdmin Functional:            [ ] YES                  [ ] NO
8. Pip Install UI Present:           [ ] YES                  [ ] NO
9. Outbound PyPI Access Working:     [ ] YES                  [ ] NO
10. Binary Wheels Supported:         [ ] YES                  [ ] NO
11. LiteSpeed / Passenger Active:    [ ] YES                  [ ] NO
12. Env Variables GUI Working:       [ ] YES                  [ ] NO (Use .env)
13. App Restart Working:             [ ] YES                  [ ] NO
14. Subdomain Created:               [ ] YES (staging-api)    [ ] NO
15. Document Root Isolated:          [ ] YES (Path: _________)[ ] NO
16. SSL Certificate Issued:          [ ] YES                  [ ] NO
17. Storage Dir Outside public_html: [ ] YES (/home/powergri/storage) [ ] NO
18. Disk Space Quota Available:      [ ] YES (Free: _____ MB) [ ] NO
--------------------------------------------------------------------------------
OVERALL AUDIT OUTCOME:
[ ] ALL BLOCKERS PASSED -> PROCEED TO STAGING DEPLOYMENT (STEP 7C)
[ ] ONE OR MORE BLOCKERS FAILED -> CONTACT HOSTSEBA SUPPORT OR REMEDIATE
================================================================================
```

---

## Next Steps

1. **If all BLOCKER items pass:**  
   The HostSeba infrastructure is confirmed compatible. You may proceed to prepare the Staging Deployment Plan (Step 7C) using the approved release package `dist/hostseba-pgcb-api-v1.0.0-final.zip`.
2. **If any BLOCKER item fails:**  
   Do not attempt staging deployment. Contact HostSeba technical support with the specific failed checklist item (e.g., requesting Python 3.11 activation, PostgreSQL user privilege grant, or PyPI network unblocking).
