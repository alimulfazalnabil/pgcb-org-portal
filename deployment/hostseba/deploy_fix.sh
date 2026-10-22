#!/usr/bin/env bash
set -e

echo "=== Hostseba PGCB API Deployment Fix ==="

REPO_DIR="/home/powergri/repositories/pgcb-org-portal"
API_DIR="$REPO_DIR/services/api"
VENV_PYTHON="/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11/bin/python"
NESTED_DOCROOT="/home/powergri/home/powergri/api.powergriddiprocoush.org"
PRIMARY_DOCROOT="/home/powergri/api.powergriddiprocoush.org"

# 1. Create canonical wsgi.py in services/api by delegating to passenger_wsgi
echo "[1/5] Creating canonical wsgi.py..."
cat > "$API_DIR/wsgi.py" <<'PYEOF'
import sys
from pathlib import Path

_API_DIR = Path(__file__).resolve().parent
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

import passenger_wsgi

application = passenger_wsgi.application
PYEOF
chmod 644 "$API_DIR/wsgi.py"
echo "      wsgi.py created successfully."

# 2. Generate hardened .htaccess
echo "[2/5] Writing clean .htaccess..."
HTACCESS_CONTENT=$(cat <<'HTEOF'
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
PassengerAppRoot "/home/powergri/repositories/pgcb-org-portal/services/api"
PassengerBaseURI "/"
PassengerPython "/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11/bin/python"
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END

PassengerEnabled on
PassengerAppType wsgi
PassengerStartupFile passenger_wsgi.py

Options -Indexes -MultiViews
RewriteEngine On

RewriteCond %{HTTPS} !=on
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

<IfModule mod_headers.c>
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>
HTEOF
)

if [ -d "$NESTED_DOCROOT" ]; then
    echo "$HTACCESS_CONTENT" > "$NESTED_DOCROOT/.htaccess"
    chmod 644 "$NESTED_DOCROOT/.htaccess"
    echo "      Updated $NESTED_DOCROOT/.htaccess"
fi

mkdir -p "$PRIMARY_DOCROOT"
echo "$HTACCESS_CONTENT" > "$PRIMARY_DOCROOT/.htaccess"
chmod 644 "$PRIMARY_DOCROOT/.htaccess"
echo "      Updated $PRIMARY_DOCROOT/.htaccess"

# 3. Create entrypoint aliases in DocumentRoots for LSAPI scanner
echo "[3/5] Mirroring entrypoint files into DocumentRoots..."
for DOCROOT in "$NESTED_DOCROOT" "$PRIMARY_DOCROOT"; do
    if [ -d "$DOCROOT" ]; then
        cp -f "$API_DIR/wsgi.py" "$DOCROOT/wsgi.py"
        cp -f "$API_DIR/passenger_wsgi.py" "$DOCROOT/passenger_wsgi.py"
        chmod 644 "$DOCROOT/wsgi.py" "$DOCROOT/passenger_wsgi.py"
    fi
done
echo "      Entrypoints mirrored."

# 4. Signal Passenger and LiteSpeed to restart
echo "[4/5] Signaling Passenger reload..."
mkdir -p "$API_DIR/tmp"
touch "$API_DIR/tmp/restart.txt"
if [ -d "$NESTED_DOCROOT" ]; then
    touch "$NESTED_DOCROOT/.htaccess"
fi
touch "$PRIMARY_DOCROOT/.htaccess"
echo "      Restart triggers touched."

# 5. Verification
echo "[5/5] Testing health endpoint..."
curl -i https://api.powergriddiprocoush.org/health

echo ""
echo "=== Done ==="
