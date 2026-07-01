"""
Standalone connection test — run this BEFORE wiring the server into Claude Desktop.

Usage:
    pip install -r requirements.txt
    cp .env.example .env   # then fill in FUSION_PASSWORD
    python test_connection.py
"""

import os
import sys
import base64
import httpx
from dotenv import load_dotenv

load_dotenv()

REQUIRED = ["FUSION_BASE_URL", "FUSION_USER", "FUSION_PASSWORD"]
missing = [k for k in REQUIRED if not os.environ.get(k)]
if missing:
    print(f"[ERROR] Missing env vars: {missing}. Did you create .env from .env.example?")
    sys.exit(1)

BASE = os.environ["FUSION_BASE_URL"].rstrip("/")
USER = os.environ["FUSION_USER"]
PASSWORD = os.environ["FUSION_PASSWORD"]

token = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
url = f"{BASE}/fscmRestApi/resources/11.13.18.05/suppliers"

print(f"Testing connection to {BASE} as {USER} ...")
try:
    resp = httpx.get(url, headers=headers, params={"limit": 1}, timeout=30)
except httpx.ConnectError as e:
    print(f"[ERROR] Could not reach host: {e}")
    sys.exit(1)

if resp.status_code == 200:
    print("[OK] Authenticated successfully.")
    print(resp.json())
elif resp.status_code == 401:
    print("[ERROR] 401 Unauthorized — check username/password, or MFA may be blocking Basic Auth.")
elif resp.status_code == 403:
    print("[ERROR] 403 Forbidden — user lacks required data role for this resource.")
else:
    print(f"[ERROR] Unexpected status {resp.status_code}: {resp.text[:500]}")
